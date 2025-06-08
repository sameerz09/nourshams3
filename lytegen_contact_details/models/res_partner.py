# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import ast
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, AccessError, UserError
import re
import logging
_logger = logging.getLogger(__name__)
import gspread
import logging
import traceback  # ✅ Import this module to avoid unresolved reference errors
from odoo import models, fields, api
from oauth2client.service_account import ServiceAccountCredentials


class ResUsers(models.Model):
    _inherit = 'res.users'

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if not self.env.context.get('group_update'):
            for record in self:
                if record.has_group('lytegen_contact_details.group_user_role_confirmation_specialist'):
                    record.with_context(group_update=1).write({
                        "groups_id" : [(3, self.env.ref('lytegen_contact_details.group_user_hide_menu').id), (4, self.env.ref('lytegen_contact_details.group_user_show_calender_menu').id), (3, self.env.ref('lytegen_contact_details.group_user_show_design_menu').id)]
                    })
                # elif record.has_group('lytegen_contact_details.group_sales_consultant') and not record.has_group('lytegen_contact_details.group_user_role_dispatch_manager'):
                #     record.with_context(group_update=1).write({
                #         "groups_id" : [(3, self.env.ref('lytegen_contact_details.group_user_hide_menu').id), (3, self.env.ref('lytegen_contact_details.group_user_show_calender_menu').id), (4, self.env.ref('lytegen_contact_details.group_user_show_design_menu').id)]
                #     })
                # else:
                #     record.with_context(group_update=1).write({
                #         "groups_id" : [(4, self.env.ref('lytegen_contact_details.group_user_hide_menu').id), (4, self.env.ref('lytegen_contact_details.group_user_show_calender_menu').id), (4, self.env.ref('lytegen_contact_details.group_user_show_design_menu').id)]
                #     })

        return res

class ResPartner(models.Model):
    _inherit = 'res.partner'

    phone = fields.Char(string="Phone", required=True, tracking=True)

    # Fields with `_2` suffix with tracking enabled
    language_2 = fields.Selection(
        string="Language",
        selection=[
            ('en', 'English'),
            # ('fr', 'French'),
            ('es', 'Spanish'),
            ('ot', 'Other Language'),
            # ('ar', 'Arabic'),
            # ('zh', 'Chinese'),
        ],
        help="Select the preferred language for this contact.",
        tracking=True
    )
    address_2 = fields.Char(string="Address", tracking=True)
    state_2 = fields.Char(string="State", tracking=True)
    state_2 = fields.Char(string="State", tracking=True)
    city_2 = fields.Char(string="City", tracking=True)
    postal_code_2 = fields.Char(string="Postal Code", tracking=True)
    average_bill_2 = fields.Char(string="Average Bill", tracking=True)

    opener_2 = fields.Char(
        string="Opener",
        help="Enter the name of the Opener for this contact.",
        tracking=True
    )
    setter_2 = fields.Char(
        string="Setter",
        help="Enter the name of the Setter for this contact.",
        tracking=True
    )
    sales_consultant_2 = fields.Char(
        string="Sales Consultant",
        help="Enter the name of the Sales Consultant for this contact.",
        tracking=True
    )
    first_name = fields.Char(string="First Name", compute="_compute_first_name", store=True)
    last_name = fields.Char(string="Last Name")

    full_name = fields.Char(string="Full Name", compute='_compute_full_name', store=True)

    @api.depends('name')
    def _compute_first_name(self):
        for rec in self:
            rec.first_name = rec.name

    @api.depends('name', 'last_name')
    def _compute_full_name(self):
        for rec in self:
            names = filter(None, [rec.name, rec.last_name])
            rec.full_name = " ".join(names)
    # sales_consultant_id = fields.Many2one(
    #     'res.users',
    #     string="Sales Consultant",
    #     help="Sales Consultant assigned to this Customer."
    # )
    origin_file = fields.Char(
        string="Origin File",
        help="Stores the origin file associated with this partner."
    )
    name = fields.Char(string="First Name", index=True, default_export_compatible=True)

    full_name = fields.Char(string="Full Name", compute='_compute_full_name', store=True)

    @api.depends('name', 'last_name')
    def _compute_full_name(self):
        for rec in self:
            names = filter(None, [rec.name, rec.last_name])
            rec.full_name = " ".join(names)
    # name = fields.Char(compute='_compute_name', store=True)

    # @api.depends('first_name', 'last_name')
    # def _compute_name(self):
    #     for rec in self:
    #         full_name = (rec.first_name or '') + ' ' + (rec.last_name or '')
    #         rec.name = full_name.strip()

    @api.onchange('first_name', 'last_name')
    def _onchange_names(self):
        """Update the name field when first name or last name changes"""
        for record in self:
            record.name = f"{record.first_name or ''} {record.last_name or ''}".strip()

    def default_domin_sale_consultant2(self):
        user_id = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('lytegen_contact_details.group_sales_consultant') and not user.has_group(
                    'lytegen_contact_details.group_user_role_dispatch_manager') and not user.has_group(
                    'lytegen_contact_details.group_user_role_admin'):
                user_id.append(user.id)
        return [('id', 'in', user_id)]

    sales_consultant_id = fields.Many2one(
        'res.users',
        string="Sales Consultant",
        domain=default_domin_sale_consultant2,
        help="Sales Consultant assigned to this event.",
        tracking=True
    )

    date_booked = fields.Date(string="Date Booked", tracking=True)
    date_appointment = fields.Date(string="Date Appointment", tracking=True)
    proposal_requested_date = fields.Date(string="Date Proposal Requested", tracking=True)

    time_appointment = fields.Char(
        string="Time Appointment",
        help="Time of the appointment in 24-hour format",
        tracking=True
    )
    # qa_outcome = fields.Selection([
    #     ('approved', 'Approved'),
    #     ('dq', 'DQ'),
    #     ('duplicate', 'Duplicate'),
    #     ('information_pending', 'Information Pending'),
    #     ('ooc', 'OOC')
    # ], string="QA Outcome", help="The outcome of the QA review process", tracking=True)

    qa_outcome = fields.Selection(
        [
            ('approved', 'Approved'),
            ('dq', 'DQ Invalid'),
            ('dq_viable', 'DQ Viable'),
            ('duplicate', 'Duplicate'),
            ('information_pending', 'Information Pending'),
            ('ooc', 'OOC')
        ],
        string="QA Outcome",
        required=False,
        tracking=True  # Track changes
    )

    map_link = fields.Char(
        string="Map Link",
        help="Hyperlink to the map location",
        tracking=True
    )

    readymode_disposition = fields.Char(
        string="Readymode Disposition",
        tracking=True
    )

    date_transferred = fields.Date(string="Date Transferred", tracking=True)
    date_sit = fields.Date(string="Date Sit", tracking=True)
    date_design_requested = fields.Date(string="Date Design Requested", tracking=True)
    date_signed = fields.Date(string="Date Signed", tracking=True)

    appointment_status = fields.Selection(
        selection=[
            ('booked', 'Booked'),
            ('showed', 'Showed'),
            ('no_show', 'No Show'),
            ('cancelled', 'Cancelled'),
            ('invalid', 'Invalid'),
            ('no_consultant', 'No Consultant'),
        ],
        string='Appointment Status',
        tracking=True,  # Track changes
    )
    auditor_notes = fields.Text(
        string="Auditor's Notes",
        tracking=True  # Track changes
    )
    source_file = fields.Char(
        string="Source File",
        tracking=True
    )

    @api.model
    def web_search_read(self, domain, offset=0, limit=None, order=None, **kwargs):
        if not order or 'is_favorite' in order:
            order = 'id desc'
        return super(ResPartner, self).web_search_read(domain, offset=offset, limit=limit, order=order, **kwargs)

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        """ Prevent automatic formatting of phone numbers """
        pass  # Do nothing to stop Odoo from changing the number

    # def unlink(self):
    #     """Prevent users in specific groups from deleting leads."""
    #     if self and self._ids:  # Ensure we are actually deleting records, not updating them
    #         restricted_groups = [
    #             'lytegen_contact_details.group_user_role_confirmation_specialist',
    #             'lytegen_contact_details.group_user_role_auditor',
    #             'lytegen_contact_details.group_sales_manager',
    #             'lytegen_contact_details.group_sales_consultant',
    #             'lytegen_contact_details.group_designer',
    #             'lytegen_contact_details.group_user_role_dispatch_manager',
    #         ]
    #         if any(self.env.user.has_group(group) for group in restricted_groups):
    #             raise UserError(
    #                 _("You do not have the permission to delete leads.")
    #             )
    #     return super(ResUsers, self).unlink()


    # @api.constrains('phone')
    # def _check_phone(self):
    #     for record in self:
    #         if record.phone:
    #             if not record.phone.isdigit():
    #                 raise ValidationError("Phone must contain only numbers.")
    #             if len(record.phone) != 10:
    #                 raise ValidationError("Phone must be exactly 10 digits.")

    # @api.constrains('phone')
    # def _check_phone(self):
    #     for record in self:
    #         if record.phone:
    #             if not re.fullmatch(r'\+?\d{11}', record.phone):
    #                 raise ValidationError("Phone Number must contain exactly 11 digits and may start with '+'.")

    @api.onchange('sales_consultant_id')
    def _onchange_sales_consultant_id(self):
        user_id = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('lytegen_contact_details.group_sales_consultant') and not user.has_group(
                    'lytegen_contact_details.group_user_role_dispatch_manager') and not user.has_group(
                    'lytegen_contact_details.group_user_role_admin'):
                user_id.append(user.id)
        return {
            'domain': {
                'sales_consultant_id': [('id', 'in', user_id)],
            }
        }



    def schedule_meeting(self):
        """Open the list view for meetings instead of the calendar view."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Meetings',
            'res_model': 'calendar.event',
            'view_mode': 'list,form',  # Change view mode to list (tree) and form
            'domain': [('partner_ids', 'in', self.id)],  # Filter meetings for this partner
            'context': {
                'default_partner_id': self.id,
                'default_name': f'Meeting with {self.name}',
            },
        }


    def default_domin_sale_consultant2(self):
        user_id = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('lytegen_contact_details.group_sales_consultant') and not user.has_group('lytegen_contact_details.group_user_role_dispatch_manager') and not user.has_group('lytegen_contact_details.group_user_role_admin'):
                user_id.append(user.id)
        return [('id', 'in', user_id)]

    def cleanup_unlinked_contacts(self):
        _logger.info("Starting partner cleanup with ID > 20")

        domain = [
            ('id', '>', 20),
            ('user_ids', '=', False),
            ('company_type', '=', 'person'),
        ]

        if 'customer_rank' in self._fields:
            domain.append(('customer_rank', '=', 0))
        if 'supplier_rank' in self._fields:
            domain.append(('supplier_rank', '=', 0))

        _logger.info("🔍 Using domain: %s", domain)

        partners_to_delete = self.search(domain)
        count = len(partners_to_delete)
        _logger.info("Found %d partner(s) to delete.", count)

        for partner in partners_to_delete:
            _logger.debug(
                "Deleting Partner → ID: %s | Name: %s | Email: %s | Phone: %s",
                partner.id, partner.name or 'N/A', partner.email or 'N/A', partner.phone or 'N/A'
            )

        try:
            partners_to_delete.unlink()
            _logger.info("🗑️ Successfully deleted %d partner(s)", count)
        except Exception as e:
            _logger.exception("Deletion failed: %s", str(e))

        _logger.info("Partner cleanup completed.")

    # @api.model
    # def create(self, vals):
    #     # Create the contact as usual
    #     partner = super(ResPartner, self).create(vals)
    #
    #     # Ensure the phone field exists
    #     if vals.get('phone'):
    #         # Check if a lead with the same phone number exists
    #         existing_lead = self.env['crm.lead'].search([('phone', '=', vals.get('phone'))], limit=1)
    #
    #         if existing_lead:
    #             # Update the existing lead with new data
    #             existing_lead.write({
    #                 'name': vals.get('name', 'New Lead'),
    #                 'partner_id': partner.id,
    #                 'contact_name': vals.get('name'),
    #                 'email_from': vals.get('email'),
    #                 'phone': vals.get('phone'),
    #                 'description': 'Created from Contact',
    #                 'language': vals.get('language_2'),
    #                 'street': vals.get('address_2'),
    #                 'state': vals.get('state_2'),
    #                 'city': vals.get('city_2'),
    #                 'zip': vals.get('postal_code_2'),
    #                 'average_bill': vals.get('average_bill_2'),
    #             })
    #         else:
    #             # Create a new lead if no matching lead exists
    #             self.env['crm.lead'].create({
    #                 'name': vals.get('name', 'New Lead'),
    #                 'partner_id': partner.id,
    #                 'contact_name': vals.get('name'),
    #                 'email_from': vals.get('email'),
    #                 'phone': vals.get('phone'),
    #                 'description': 'Created from Contact',
    #                 'language': vals.get('language_2'),
    #                 'street': vals.get('address_2'),
    #                 'state': vals.get('state_2'),
    #                 'city': vals.get('city_2'),
    #                 'zip': vals.get('postal_code_2'),
    #                 'average_bill': vals.get('average_bill_2'),
    #             })
    #
    #         matching_events = self.env['calendar.event'].search([
    #             ('phone_number', '=', vals['phone'])
    #         ])
    #
    #         for event in matching_events:
    #             event.write({
    #                 'opener_2': partner.opener_2,
    #                 'setter_2': partner.setter_2 ,
    #                 'source_file': partner.origin_file,
    #             })
    #
    #     return partner

    @api.model
    def create(self, vals):
        """ Create partner, link/update CRM lead, and update Calendar Event if applicable. """
        partner = super(ResPartner, self).create(vals)

        phone = vals.get('phone')
        if phone:
            # 🔹 Check if a lead with the same phone number exists
            existing_lead = self.env['crm.lead'].search([('phone', '=', phone)], limit=1)

            lead_vals = {
                'name': vals.get('name', 'New Lead'),
                'partner_id': partner.id,
                'contact_name': vals.get('name'),
                'email_from': vals.get('email'),
                'phone': phone,
                'description': 'Created from Contact',
                'language': vals.get('language_2'),
                'street': vals.get('address_2'),
                # 'state': vals.get('state_2'),
                # 'city': vals.get('city_2'),
                # 'zip': vals.get('postal_code_2'),
                'average_bill': vals.get('average_bill_2'),
            }

            if existing_lead:
                # 🔹 Update existing lead with new data
                existing_lead.write(lead_vals)
            else:
                # 🔹 Create a new lead if no matching one exists
                self.env['crm.lead'].create(lead_vals)

            # 🔹 Search for calendar events linked to this phone number
            matching_events = self.env['calendar.event'].search([('phone_number', '=', phone)])

            if matching_events:
                event_updates = {
                    'opener_2': partner.opener_2,
                    'setter_2': partner.setter_2,
                    'source_file': partner.origin_file,
                }
                matching_events.write(event_updates)

                # 🔹 Log update to Google Sheets if event exists
                for event in matching_events:
                    self._log_qa_details_to_google_sheets(event)

        return partner

    def _log_qa_details_to_google_sheets(self, event):
        """ Log fields to Google Sheets if 'event_access_token' exists in Column A. """
        try:
            _logger.info("Logging fields to Google Sheets for Event ID: %s", event.id)

            env = self.env
            json_keyfile_path = env['ir.config_parameter'].sudo().get_param('json_file_path')
            if not json_keyfile_path:
                _logger.error("Google Sheets JSON keyfile path is missing.")
                return False

            creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path,
                                                                     ['https://www.googleapis.com/auth/spreadsheets'])
            client = gspread.authorize(creds)

            sheet_id = env['ir.config_parameter'].sudo().get_param('google_keys_sheet_id3')
            if not sheet_id:
                _logger.error("Google Sheet ID is missing.")
                return False

            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.worksheet("New Appointments")

            access_token = event.access_token
            if not access_token:
                _logger.warning("Event access token is missing for Event ID: %s", event.id)
                return False

            cell_list = worksheet.col_values(1)  # Column A where access tokens are stored
            if access_token in cell_list:
                row_index = cell_list.index(access_token) + 1
                columns = {
                    "Q": event.opener_2,
                    "R": event.setter_2,
                    "X": event.source_file
                }
                for col, value in columns.items():
                    cell_reference = f"{col}{row_index}"
                    worksheet.update(range_name=cell_reference, values=[[str(value)]])
            else:
                _logger.warning("No matching access token found in Google Sheets for Event ID: %s", event.id)

            _logger.info("Successfully logged fields to Google Sheets.")
            return True

        except Exception as e:
            _logger.error("Failed to log fields to Google Sheets: %s", str(e))
            _logger.error(traceback.format_exc())
            return False

    # def write(self, vals):
    #     # Call the original write method first
    #     result = super(ResPartner, self).write(vals)
    #
    #     # Iterate through the partners being updated
    #     for partner in self:
    #         phone_number = vals.get('phone') or partner.phone  # Use new or existing phone number
    #
    #         if phone_number:
    #             existing_lead = self.env['crm.lead'].search([('phone', '=', phone_number)], limit=1)
    #
    #             lead_data = {
    #                 'name': vals.get('name', partner.name),  # Use updated name or existing
    #                 'partner_id': partner.id,
    #                 'contact_name': vals.get('name', partner.name),
    #                 'email_from': vals.get('email', partner.email),
    #                 'phone': phone_number,
    #                 'description': 'Updated from Contact',
    #                 # 'language': vals.get('language_2', partner.lang),
    #                 'street': vals.get('address_2', partner.street),
    #                 'state': vals.get('state_2', partner.state_id.id),
    #                 'city': vals.get('city_2', partner.city),
    #                 'zip': vals.get('postal_code_2', partner.zip),
    #                 'average_bill': vals.get('average_bill_2'),
    #             }
    #
    #             if existing_lead:
    #                 existing_lead.write(lead_data)
    #             else:
    #                 self.env['crm.lead'].create(lead_data)
    #
    #     return result

    def write(self, vals):
        """ Update partner, link/update CRM lead, and update Calendar Event if applicable. """
        result = super(ResPartner, self).write(vals)

        for partner in self:
            phone_number = vals.get('phone') or partner.phone  # Use new or existing phone number

            if phone_number:
                # 🔹 Check if a lead with the same phone number exists
                existing_lead = self.env['crm.lead'].search([('phone', '=', phone_number)], limit=1)

                lead_data = {
                    'name': vals.get('name', partner.name),  # Use updated name or existing
                    'partner_id': partner.id,
                    'contact_name': vals.get('name', partner.name),
                    'email_from': vals.get('email', partner.email),
                    'phone': phone_number,
                    'description': 'Updated from Contact',
                    'street': vals.get('address_2', partner.street),
                    # 'state': vals.get('state_2', partner.state_id.id),
                    # 'city': vals.get('city_2', partner.city),
                    # 'zip': vals.get('postal_code_2', partner.zip),
                    'average_bill': vals.get('average_bill_2'),
                }

                if existing_lead:
                    existing_lead.with_context(from_partner_sync=True).write(lead_data)
                else:
                    self.env['crm.lead'].with_context(from_partner_sync=True).create(lead_data)


                # 🔹 Search for calendar events linked to this phone number
                matching_events = self.env['calendar.event'].search([('phone_number', '=', phone_number)])

                if matching_events:
                    event_updates = {
                        'opener_2': partner.opener_2,
                        'setter_2': partner.setter_2,
                        'source_file': partner.origin_file,
                    }
                    matching_events.write(event_updates)

                    # 🔹 Log update to Google Sheets if event exists
                    for event in matching_events:
                        self._log_qa_details_to_google_sheets(event)

        return result
