from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AppointmentSlot(models.Model):
    _inherit = 'appointment.slot'

    resource_ids = fields.Many2many(
        'resource.resource',  # Replace with the appropriate model for resources
        string="Additional Resources"
    )

    @api.depends('start_hour', 'end_hour', 'weekday')
    def _compute_domain(self):
        for record in self:
            if record.start_hour is not None and record.end_hour is not None and record.weekday is not None:
                record.resource_ids_domain = [
                    ('calendar_id.attendance_ids.hour_from', '<=', record.start_hour),
                    ('calendar_id.attendance_ids.hour_to', '>=', record.end_hour),
                    ('calendar_id.attendance_ids.dayofweek', '=', str(int(record.weekday) -1)),
                ]
            else:
                record.resource_ids_domain = []

    @api.onchange('start_hour', 'end_hour', 'weekday')
    def _onchange_period(self):
        if self.start_hour:
            # Filter the current resources by the condition
            filtered_resources = self.resource_ids.filtered(
                lambda r: any(
                    attendance.hour_from <= self.start_hour and
                    attendance.hour_to >= self.end_hour and
                    attendance.dayofweek == self.weekday
                    for attendance in r.calendar_id.attendance_ids
                )
            )
            # Keep only the resources that meet the criteria
            self.resource_ids = [(6, 0, filtered_resources.ids)]

    resource_ids_domain = fields.Char(
        compute='_compute_domain',
        store=False,
    )


class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    @api.onchange('hour_from', 'hour_to', 'dayofweek')
    def _onchange_period(self):
        self._update_appointment_slots()
        self._add_resources_to_appointment_slots()

    def unlink(self):
        # Call the reusable function before deletion
        self._update_appointment_slots(force_delete=True)
        # Perform the actual deletion
        return super(ResourceCalendarAttendance, self).unlink()

    def _update_appointment_slots(self, force_delete=False):
        # Fetch all appointment slots related to this specific attendance
        for record in self:
            record_id = record.id if isinstance(record.id, int) else record.id.origin
            connected_appointment_slots = self.env['appointment.slot'].search([
                ('resource_ids.calendar_id.attendance_ids.id', '=', record_id)
            ])

            # Loop through each connected appointment slot
            for connected_appointment_slot in connected_appointment_slots:
                if connected_appointment_slot.weekday != str(int(record.dayofweek) + 1):
                    continue
                # Filter out only the current resource (self) if it is out of the updated criteria
                record_calendar_id = record.calendar_id.id if isinstance(record.calendar_id.id, int) else record.calendar_id.id.origin
                valid_resources = connected_appointment_slot.resource_ids.filtered(
                    lambda resource: resource.calendar_id.id != record_calendar_id or (
                                record.hour_from <= connected_appointment_slot.start_hour
                                and record.hour_to >= connected_appointment_slot.end_hour
                        )
                    ) if not force_delete else []
                valid_resources_ids = valid_resources.ids if valid_resources else []
                # Update the slot's resource_ids with the valid resources
                connected_appointment_slot.resource_ids = [(6, 0, valid_resources_ids)]

    def _add_resources_to_appointment_slots(self):
        # Fetch all appointment slots related to this specific attendance
        for record in self:
            record_calendar_id = record.calendar_id.id if isinstance(record.calendar_id.id, int) else record.calendar_id.id.origin
            resource_calendar_resources = self.env['resource.resource'].search([
                ('calendar_id.id', '=', record_calendar_id)
            ])
            weekday_appointment_slots = self.env['appointment.slot'].search([
                ('start_hour', '>=', record.hour_from),
                ('end_hour', '<=', record.hour_to),
                ('weekday', '=', str(int(record.dayofweek) + 1))
            ])
            # Loop through each connected appointment slot
            for connected_appointment_slot in weekday_appointment_slots:
                # Update the slot's resource_ids with the valid resources
                connected_appointment_slot.resource_ids = [(6, 0, resource_calendar_resources.ids)]
