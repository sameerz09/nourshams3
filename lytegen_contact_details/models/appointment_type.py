from odoo import models, fields, api
import ast
import calendar as cal
import random
import pytz
from datetime import datetime, timedelta, time
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from babel.dates import format_datetime, format_time
from werkzeug.urls import url_encode, url_join

from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, frozendict
from odoo.tools.misc import babel_locale_parse, get_lang
from odoo.addons.base.models.res_partner import _tz_get
import json

import logging
_logger = logging.getLogger(__name__)

class AppointmentType(models.Model):
    _inherit = 'appointment.type'

    def _prepare_calendar_event_values(
            self, asked_capacity, booking_line_values, duration,
            appointment_invite, guests, name, customer, staff_user, start, stop
    ):
        """ Returns all values needed to create the calendar event from the values outputed
            by the form submission and its processing. This should be used with values of format
            matching appointment_form_submit controller's ones.
            ...
            :param list<dict> booking_line_values: create values of booking lines
            :param str name: name filled in form
            :param <res.partner> guests: list of guest partners
            :param res.partner customer: partner who made the booking
            :param dt start: start of picked slot UTC
            :param dt stop: end of picked slot UTC
            :return: dict of values used in create method of calendar event
        """
        self.ensure_one()
        guests = guests or self.env['res.partner']  # Ensure guests is a valid recordset
        appointment_status = self._get_default_appointment_status(start, stop, asked_capacity)

        # Only include the customer in attendee_ids
        attendee_values = [Command.create({'partner_id': customer.id, 'state': 'accepted'})]

        return {
            'alarm_ids': [Command.set(self.reminder_ids.ids)],
            'allday': False,
            'appointment_booker_id': customer.id,
            'appointment_invite_id': appointment_invite.id,
            'appointment_status': appointment_status,
            'appointment_type_id': self.id,
            'attendee_ids': attendee_values,  # Only the customer as an attendee
            'booking_line_ids': [Command.create(vals) for vals in booking_line_values],
            'duration': duration,
            'location': self.location,
            'name': _('%(attendee_name)s - %(appointment_name)s Booking',
                      attendee_name=name, appointment_name=self.name),
            'partner_ids': [Command.link(customer.id)],  # Link only the customer
            'start': fields.Datetime.to_string(start),
            'start_date': fields.Datetime.to_string(start),
            'stop': fields.Datetime.to_string(stop),
            'user_id': self.create_uid.id,  # Always assign the creator as the responsible user
        }

    def _get_appointment_slots(self, timezone, filter_users=None, filter_resources=None, asked_capacity=1, reference_date=None):
        """ Fetch available slots to book an appointment.

        :param str timezone: timezone string e.g.: 'Europe/Brussels' or 'Etc/GMT+1'
        :param <res.users> filter_users: filter available slots for those users (can be a singleton
          for fixed appointment types or can contain several users, e.g. with random assignment and
          filters) If not set, use all users assigned to this appointment type.
        :param <appointment.resource> filter_resources: filter available slots for those resources
          (can be a singleton for fixed appointment types or can contain several resources,
          e.g. with random assignment and filters) If not set, use all resources assigned to this
          appointment type.
        :param int asked_capacity: the capacity the user want to book.
        :param datetime reference_date: starting datetime to fetch slots. If not
          given now (in UTC) is used instead. Note that minimum schedule hours
          defined on appointment type is added to the beginning of slots;

        :returns: list of dicts (1 per month) containing available slots per week
          and per day for each week (see ``_slots_generate()``), like
          [
            {'id': 0,
             'month': 'February 2022' (formatted month name),
             'weeks': [
                [{'day': '']
                [{...}],
             ],
            },
            {'id': 1,
             'month': 'March 2022' (formatted month name),
             'weeks': [ (...) ],
            },
            {...}
          ]
        """
        self.ensure_one()

        if not self.active:
            return []
        now = datetime.utcnow()
        if not reference_date:
            reference_date = now

        try:
            requested_tz = pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            requested_tz = self.appointment_tz

        appointment_duration_days = self.max_schedule_days
        unique_slots = self.slot_ids.filtered(lambda slot: slot.slot_type == 'unique')

        if self.category == 'custom' and unique_slots:
            # Custom appointment type, the first day should depend on the first slot datetime
            start_first_slot = unique_slots[0].start_datetime
            first_day_utc = start_first_slot if reference_date > start_first_slot else reference_date
            first_day = requested_tz.fromutc(first_day_utc + relativedelta(hours=self.min_schedule_hours))
            appointment_duration_days = (unique_slots[-1].end_datetime.date() - reference_date.date()).days
            last_day = requested_tz.fromutc(reference_date + relativedelta(days=appointment_duration_days))
        elif self.category == 'punctual':
            # Punctual appointment type, the first day is the start_datetime if it is in the future, else the first day is now
            first_day = requested_tz.fromutc(self.start_datetime if self.start_datetime > now else now)
            last_day = requested_tz.fromutc(self.end_datetime)
        else:
            # Recurring appointment type
            first_day = requested_tz.fromutc(reference_date + relativedelta(hours=self.min_schedule_hours))
            last_day = requested_tz.fromutc(reference_date + relativedelta(days=appointment_duration_days))

        # Compute available slots (ordered)
        slots = self._slots_generate(
            first_day.astimezone(pytz.utc),
            last_day.astimezone(pytz.utc),
            timezone,
            reference_date=reference_date
        )

        # No slots -> skip useless computation
        if not slots:
            return slots
        valid_users = filter_users.filtered(lambda user: user in self.staff_user_ids) if filter_users else None
        valid_resources = filter_resources.filtered(lambda resource: resource in self.resource_ids) if filter_resources else None
        # Not found staff user : incorrect configuration -> skip useless computation
        if filter_users and not valid_users:
            return []
        if filter_resources and not valid_resources:
            return []
        # Used to check availabilities for the whole last day as _slot_generate will return all slots on that date.
        last_day_end_of_day = datetime.combine(
            last_day.astimezone(pytz.timezone(self.appointment_tz)),
            time.max
        )
        if self.schedule_based_on == 'users':
            self._slots_fill_users_availability(
                slots,
                first_day.astimezone(pytz.UTC),
                last_day_end_of_day.astimezone(pytz.UTC),
                valid_users,
            )
            slot_field_label = 'available_staff_users' if self.assign_method == 'time_resource' else 'staff_user_id'
        else:
            self._slots_fill_resources_availability(
                slots,
                first_day.astimezone(pytz.UTC),
                last_day_end_of_day.astimezone(pytz.UTC),
                valid_resources,
                asked_capacity,
            )
            slot_field_label = 'available_resource_ids'

        total_nb_slots = sum(slot_field_label in slot for slot in slots)
        # If there is no slot for the minimum capacity then we return an empty list.
        # This will lead to a screen informing the customer that there is no availability.
        # We don't want to return an empty list if the capacity as been tempered by the customer
        # as he should still be able to interact with the screen and select another capacity.
        if not total_nb_slots and asked_capacity == 1:
            return []
        nb_slots_previous_months = 0

        # Compute calendar rendering and inject available slots
        today = requested_tz.fromutc(reference_date)
        start = slots[0][timezone][0] if slots else today
        locale = babel_locale_parse(get_lang(self.env).code)
        month_dates_calendar = cal.Calendar(locale.first_week_day).monthdatescalendar
        months = []
        while (start.year, start.month) <= (last_day.year, last_day.month):
            nb_slots_next_months = sum(slot_field_label in slot for slot in slots)
            has_availabilities = False
            dates = month_dates_calendar(start.year, start.month)
            for week_index, week in enumerate(dates):
                for day_index, day in enumerate(week):
                    mute_cls = weekend_cls = today_cls = None
                    today_slots = []
                    if day.weekday() in (locale.weekend_start, locale.weekend_end):
                        weekend_cls = 'o_weekend bg-light'
                    if day == today.date() and day.month == today.month:
                        today_cls = 'o_today'
                    if day.month != start.month:
                        mute_cls = 'd-none'
                    else:
                        # slots are ordered, so check all unprocessed slots from until > day
                        while slots and (slots[0][timezone][0].date() <= day):
                            if (slots[0][timezone][0].date() == day) and (slot_field_label in slots[0]):
                                slot_start_dt_tz = slots[0][timezone][0].strftime('%Y-%m-%d %H:%M:%S')
                                slot = {
                                    'datetime': slot_start_dt_tz,
                                    'available_resources': [{
                                        'id': resource.id,
                                        'name': resource.name,
                                        'capacity': resource.capacity,
                                    } for resource in slots[0]['available_resource_ids']] if self.schedule_based_on == 'resources' else False,
                                }
                                if self.schedule_based_on == 'users' and self.assign_method == 'time_resource':
                                    slot.update({'available_staff_users': [{
                                        'id': staff.id,
                                        'name': staff.name,
                                    } for staff in slots[0]['available_staff_users']]})
                                elif self.schedule_based_on == 'users':
                                    slot.update({'staff_user_id': slots[0]['staff_user_id'].id})
                                if slots[0]['slot'].allday:
                                    slot_duration = 24
                                    slot.update({
                                        'hours': _("All day"),
                                        'slot_duration': slot_duration,
                                    })
                                else:
                                    start_hour = format_time(slots[0][timezone][0].time(), format='short', locale=locale)
                                    end_hour = format_time(slots[0][timezone][1].time(), format='short', locale=locale) if self.category == 'custom' else False
                                    slot_duration = str((slots[0][timezone][1] - slots[0][timezone][0]).total_seconds() / 3600)
                                    slot.update({
                                        'start_hour': start_hour,
                                        'end_hour': end_hour,
                                        'slot_duration': slot_duration,
                                    })
                                url_parameters = {
                                    'date_time': slot_start_dt_tz,
                                    'duration': slot_duration,
                                }
                                if self.schedule_based_on == 'users' and self.assign_method != 'time_resource':
                                    url_parameters.update(staff_user_id=str(slots[0]['staff_user_id'].id))
                                elif self.schedule_based_on == 'resources':
                                    url_parameters.update(available_resource_ids=str(slots[0]['available_resource_ids'].ids))
                                slot['url_parameters'] = url_encode(url_parameters)
                                today_slots.append(slot)
                                nb_slots_next_months -= 1
                            slots.pop(0)
                    today_slots = sorted(today_slots, key=lambda d: d['datetime'])
                    dates[week_index][day_index] = {
                        'day': day,
                        'slots': today_slots,
                        'mute_cls': mute_cls,
                        'weekend_cls': weekend_cls,
                        'today_cls': today_cls
                    }

                    has_availabilities = has_availabilities or bool(today_slots)

            months.append({
                'id': len(months),
                'month': format_datetime(start, 'MMMM Y', locale=get_lang(self.env).code),
                'weeks': dates,
                'has_availabilities': has_availabilities,
                'nb_slots_previous_months': nb_slots_previous_months,
                'nb_slots_next_months': nb_slots_next_months,
            })
            nb_slots_previous_months = total_nb_slots - nb_slots_next_months
            start = start + relativedelta(months=1)
        return months

    @api.model
    def web_search_read(self, domain, offset=0, limit=None, order=None, **kwargs):
        if not order or 'sequence' in order:
            order = 'id desc'
        return super(AppointmentType, self).web_search_read(domain, offset=offset, limit=limit, order=order, **kwargs)

    def _slots_fill_users_availability(self, slots, start_dt, end_dt, filter_users=None):
        """ Fills the slot structure with an available user

        :param list slots: slots (list of slot dict), as generated by ``_slots_generate``;
        :param datetime start_dt: beginning of appointment check boundary. Timezoned to UTC;
        :param datetime end_dt: end of appointment check boundary. Timezoned to UTC;
        :param <res.users> filter_users: filter available slots for those users (can be a singleton
          for fixed appointment types or can contain several users e.g. with random assignment and
          filters) If not set, use all users assigned to this appointment type.

        :return: None but instead update ``slots`` adding ``staff_user_id`` or ``available_staff_users`` key
          containing available user(s);
        """
        # shuffle the available users into a random order to avoid having the same
        # one assigned every time, force timezone
        available_users = [
            user.with_context(tz=user.tz)
            for user in (filter_users or self.staff_user_ids)
        ]
        random.shuffle(available_users)
        available_users_tz = self.env['res.users'].concat(*available_users)

        # fetch value used for availability in batch
        availability_values = self._slot_availability_prepare_users_values(
            available_users_tz, start_dt, end_dt
        )

        for slot in slots:
            if self.assign_method == 'time_resource':
                available_staff_users = available_users_tz.filtered(
                    lambda staff_user: self._slot_availability_is_user_available(
                        slot,
                        staff_user,
                        availability_values
                    )
                )
            else:
                available_staff_users = next(
                    (staff_user for staff_user in available_users_tz if self._slot_availability_is_user_available(
                        slot,
                        staff_user,
                        availability_values
                    )),
                    False)
            if available_staff_users:
                if self.assign_method == 'time_resource':
                    slot['available_staff_users'] = available_staff_users
                else:
                    slot['staff_user_id'] = available_staff_users


    def _slot_availability_is_user_available(self, slot, staff_user, availability_values):
        """
        This method verifies if the user is available on the given slot.
        Customized to check the slot's `resource_ids` directly and determine availability.

        :param dict slot: a slot as generated by ``_slots_generate``;
        :param <res.users> staff_user: user to check against slot boundaries.
          At this point timezone should be correctly set in context;
        :param dict availability_values: dict of data used for availability check.
          See ``_slot_availability_prepare_users_values()`` for more details;
        :return: boolean: True if the slot has `resource_ids`, False otherwise.
        """
        # Extract the slot record
        slot_record = slot.get('slot')  # The slot record should be passed as part of the slot dict

        # Log the slot and its resources for debugging
        _logger.debug("Checking availability for slot: %s", slot_record)
        _logger.debug("Slot resource_ids: %s", slot_record.resource_ids if slot_record else "None")

        # Check if the slot exists and has `resource_ids`
        if slot_record and slot_record.resource_ids:
            return True

        # Return False if no `resource_ids` are found or the slot is None
        return False
