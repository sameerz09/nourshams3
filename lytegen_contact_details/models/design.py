
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError, AccessError, UserError

import requests
import json
import logging
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import traceback


_logger = logging.getLogger(__name__)

class Design(models.Model):
    _name = 'design'
    _description = 'Design'
    _rec_name = "first_name"
    _order = 'create_date desc'
    _inherit = ['mail.thread']

    def default_domin_designer(self):
        user_id = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('lytegen_contact_details.group_designer') and not user.has_group('lytegen_contact_details.group_sales_consultant') and not user.has_group('lytegen_contact_details.group_user_role_dispatch_manager') and not user.has_group('lytegen_contact_details.group_user_role_admin'):
                user_id.append(user.id)
        return [('id', 'in', user_id)]

    ref_date = fields.Datetime(
        string='Reference Date',
        default=lambda self: fields.Datetime.now(),
        tracking=True
    )

    hidden_from_designers = fields.Boolean(
        string='Hidden from Designers',
        default=False,
        tracking=True
    )

    design_name = fields.Char(string='Proposal Name', tracking=True)
    first_name = fields.Char(string='First Name', tracking=True)
    last_name = fields.Char(string='Last Name', tracking=True)
    design_link_ids = fields.One2many('design.link', 'design_id', string="Proposal Links")
    phone_number = fields.Char(
        string='Phone Number',
        placeholder='Enter 10-digit phone number',
        tracking=True
    )
    email = fields.Char(string='Email', tracking=True)
    street_address = fields.Text(string='Street Address', tracking=True)
    city = fields.Char(string='City', tracking=True)
    state = fields.Char(string='State', tracking=True)
    zip_code = fields.Char(string='Zip Code', tracking=True)
    sales_consultant_id = fields.Many2one('res.users', string='Sales Consultant', tracking=True)
    designer_id = fields.Many2one('res.users', string='Designer', domain=default_domin_designer, tracking=True)

    usage = fields.Binary(string='Usage', tracking=True)
    usage_files = fields.Many2many(
        'ir.attachment',
        relation="design_attachment_rel",
        string="Usage",
    )
    utility_provider = fields.Char(string='Utility Provider', tracking=True)
    proposal_eta = fields.Selection([
        ('thirty_minutes', '30 minutes'),
        ('four_hours', '4 hours'),
        ('next_day_eight', 'Next day 8am')
    ], string='Proposal ETA', tracking=True)
    discounts = fields.Selection([
        ('senior_citizen', 'Senior citizen'),
        ('veteran', 'Veteran'),
        ('active_military', 'Active military'),
        ('law_enforcement', 'Law enforcement'),
        ('healthcare_worker', 'Healthcare Worker'),
        ('not_applicable', 'Not applicable'),
    ], string='Discounts')
    rate_type = fields.Selection([
        ('care', 'Care'),
        ('no_care', 'No Care'),
    ], string='Rate type')


    finance_type = fields.Selection([
        ('cash', 'Cash'),
        ('enfin_loan', 'Enfin Loan'),
        ('enfin_ppa', 'Enfin PPA'),
        ('everbright_loan', 'Everbright Loan'),
        ('goodleap_ppa', 'Goodleap PPA'),
        ('goodleap_loan', 'Goodleap Loan'),
        ('lightreach_ppa', 'Lightreach PPA'),
        ('mosaic_loan', 'Mosaic Loan'),
        ('pace', 'PACE'),
        ('sunlight_loan', 'Sunlight Loan'),
        ('sunrun_ppa', 'Sunrun PPA'),
        ('thrive_ppa', 'Thrive PPA'),
    ], string='Finance Type', tracking=True)
    average_bill = fields.Integer(string='Average Bill', tracking=True)
    proposal_notes = fields.Text(string='Proposal Notes', tracking=True)
    kwh_or_dollars = fields.Selection([
        ('kwh', 'kWh'),
        ('dollars', 'Dollars')
    ], string='kWh or Dollars $', tracking=True)

    january = fields.Float(string='January', tracking=True)
    february = fields.Float(string='February', tracking=True)
    march = fields.Float(string='March', tracking=True)
    april = fields.Float(string='April', tracking=True)
    may = fields.Float(string='May', tracking=True)
    june = fields.Float(string='June', tracking=True)
    july = fields.Float(string='July', tracking=True)
    august = fields.Float(string='August', tracking=True)
    september = fields.Float(string='September', tracking=True)
    october = fields.Float(string='October', tracking=True)
    november = fields.Float(string='November', tracking=True)
    december = fields.Float(string='December', tracking=True)

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id,
        tracking=True
    )
    design_link = fields.Char(string='Proposal Link', tracking=True)

    street_address_visible = fields.Boolean(
        string="Is Street Address Visible",
        # compute='_compute_street_address_visible',
        default=False,
        store=True,
    )


    sales_consultant_employee_id = fields.Many2one(
        'hr.employee',
        string="Sales Consultant (Employee)",
        domain=lambda self: self._default_domain_sales_consultant_employee(),
        help="Sales Consultant assigned to this event (Employee)."
    )
    rate_type = fields.Selection([
        ('care', 'Care'),
        ('no_care', 'No Care'),
    ], string='Rate type')

    proposal_bills = fields.Many2many(
        'ir.attachment',
        'design_proposal_bill_rel',
        'design_id',
        'attachment_id',
        string='Proposal Bill Attachments'
    )

    document_ids = fields.Many2many('documents.document', string="Related Documents")

    create_date_formatted = fields.Char(string='Created Date/Time', compute='_compute_create_date_formatted')
    date_formatted = fields.Char(string='Created Date', compute='_compute_date_formatted')
    time_formatted = fields.Char(string='Created Time', compute='_compute_time_formatted')

    @api.depends('create_date')
    def _compute_create_date_formatted(self):
        for record in self:
            if record.create_date:
                # Format like "Apr-26, 2025 03:45 PM"
                record.create_date_formatted = record.create_date.strftime('%b-%d, %Y %I:%M %p')
            else:
                record.create_date_formatted = ''

    @api.depends('create_date')
    def _compute_date_formatted(self):
        for record in self:
            if record.create_date:
                # Format like "Apr-26, 2025 03:45 PM"
                record.date_formatted = record.create_date.strftime('%b-%d, %Y')
            else:
                record.date_formatted = ''

    @api.depends('create_date')
    def _compute_time_formatted(self):
        for record in self:
            if record.create_date:
                # Format like "Apr-26, 2025 03:45 PM"
                record.time_formatted = record.create_date.strftime('%I:%M %p')
            else:
                record.time_formatted = ''



    @api.model
    def _default_domain_sales_consultant_employee(self):
        """Return only employees with the job position 'Sales Consultant'."""
        return [('job_id.name', '=', 'Sales Consultant')]

    @api.model
    def update_street_address_visibility_design(self):
        """Scheduled action to update street_address_visible"""
        current_time = fields.Datetime.now()
        # Search for records where `street_address_visible` is False
        events = self.search([('street_address_visible', '=', False)])
        for event in events:
            # Check if the record was created more than 3 seconds ago
            if event.create_date and (current_time - event.create_date) >= timedelta(hours=2):
                event.street_address_visible = True

    # @api.constrains('phone_number')
    # def _check_phone_number(self):
    #     for record in self:
    #         if record.phone_number:
    #             if not record.phone_number.isdigit():
    #                 raise ValidationError("Phone Number must contain only numbers.")
    #             if len(record.phone_number) != 10:
    #                 raise ValidationError("Phone Number must be exactly 10 digits.")

    def _send_slack_message(self):
        """Send Slack message with design details."""
        slack_channel = self.env['slack.webhook.configuration'].sudo().search([
            ('category', '=', 'design'),
            ('status', '=', 'active')
        ], limit=1)

        if not slack_channel:
            # Fallback to the original logic if no 'project' category is found
            slack_channel = self.env['slack.webhook.configuration'].sudo().search([
                ('is_default', '=', True),
                ('status', '=', 'active')
            ], limit=1)

        if not slack_channel:
            _logger.warning("No active default Slack channel found.")
            return

        # Get the base URL from system parameters
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        for design in self:
            design_link = f"{base_url}/web#id={design.id}&model=design&view_type=form"

            usage_files_links = []
            for attachment in design.usage_files:
                if attachment.type == 'binary' and not attachment.public:
                    attachment.sudo().write({'public': True})
                download_url = f"{base_url}/web/content/{attachment.id}?download=true"
                usage_files_links.append(f"{attachment.name}: {download_url}")
            usage_files_text = '\n'.join(usage_files_links)






            # Construct the Slack message
            message = f"""
            A new design has been created:
            Energy consultant: {design.sales_consultant_employee_id.name or ''}
            Proposal Name: {design.design_name or ''}
            First Name: {design.first_name or ''}
            Last Name: {design.last_name or ''}
            Phone Number: {design.phone_number or ''}
            Email: {design.email or ''}
            Street Address: {design.street_address or ''}
            City:  {design.city or ''}
            State: {design.state or ''}
            Zip Code: {design.zip_code or ''}
            Utility Provider: {design.utility_provider or ''}
            Rate type: {dict(self._fields['rate_type'].selection).get(design.rate_type, '')}
            Discounts: {dict(self._fields['discounts'].selection).get(design.discounts, '')}
            Average Bill: {design.average_bill or ''}
            Proposal Notes: {design.proposal_notes or ''}
            Upload bill (Usage): {usage_files_text or ''}
            Proposal Link: {design_link}
            """

            payload = {'text': message.strip()}
            try:
                response = requests.post(
                    slack_channel.webhook,
                    data=json.dumps(payload),
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    _logger.info(f"Slack message sent successfully for design {design.id}")
                else:
                    _logger.error(f"Failed to send Slack message for design {design.id}: {response.text}")
            except Exception as e:
                _logger.error(f"Slack message sending failed for design {design.id}: {str(e)}")

    def unlink(self):
        """Prevent users in specific groups from deleting leads."""
        if self and self._ids:  # Ensure we are actually deleting records, not updating them
            restricted_groups = [
                'lytegen_contact_details.group_user_role_confirmation_specialist',
                'lytegen_contact_details.group_user_role_auditor',
                'lytegen_contact_details.group_sales_manager',
                'lytegen_contact_details.group_sales_consultant',
                'lytegen_contact_details.group_designer',
                'lytegen_contact_details.group_user_role_dispatch_manager',
            ]
            if any(self.env.user.has_group(group) for group in restricted_groups):
                raise UserError(
                    _("You do not have the permission to delete leads.")
                )
        return super(Design, self).unlink()

    @api.model
    def web_search_read(self, domain, offset=0, limit=None, order=None, **kwargs):
        # 🔄 Always update hidden_from_designers based on 12-hour timeout
        twelve_hours_ago = datetime.now() - timedelta(hours=12)
        outdated_designs = self.search([
            ('hidden_from_designers', '=', False),
            ('ref_date', '<=', twelve_hours_ago)
        ])
        outdated_designs.write({'hidden_from_designers': True})

        # 👁️ For designers only: filter out hidden records
        # if self.env.user.has_group('lytegen_contact_details.group_designer'):
        #     domain = domain + [('hidden_from_designers', '=', False)]

        return super(Design, self).web_search_read(domain, offset=offset, limit=limit, order=order, **kwargs)

    def action_renew_12hr_for_designer(self):
        for record in self:
            record.ref_date = fields.Datetime.now()
            record.hidden_from_designers = False

    # @api.model
    # def create(self, vals):
    #     # Create the design
    #     design = super(Design, self).create(vals)
    #
    #     # Send Slack message for the newly created design
    #     design._send_slack_message()
    #
    #     if  self.env.user.has_group('lytegen_contact_details.group_sales_manager'):
    #         raise AccessError("You do not have the necessary permissions to create this record.")
    #
    #     # Ensure 'average_bill' is provided in the create operation
    #     if 'average_bill' not in vals or vals.get('average_bill') == 0:
    #         raise exceptions.UserError("The 'Average Bill' field is mandatory.")
    #
    #     # Combine first_name and last_name into name
    #     first_name = vals.get('first_name', '').strip()
    #     last_name = vals.get('last_name', '').strip()
    #     vals['name'] = f"{first_name} {last_name}"
    #
    #     # Check if a contact with the given phone number exists
    #     phone = vals.get('phone_number')
    #     if phone:
    #         contact = self.env['res.partner'].search([('phone', '=', phone)], limit=1)
    #         if contact:
    #             # Update the existing contact
    #             contact.write({
    #                 'date_design_requested': vals.get('date_design_requested', fields.Date.today()),
    #             })
    #         else:
    #             # Create a new contact with 'date_design_requested'
    #             self.env['res.partner'].create({
    #                 'name': vals['name'],
    #                 'phone': phone,
    #                 'date_design_requested': vals.get('date_design_requested', fields.Date.today()),
    #             })
    #
    #     return design
    @api.model
    def create(self, vals):
        # Check user permissions
        if self.env.user.has_group('lytegen_contact_details.group_sales_manager'):
            raise AccessError("You do not have the necessary permissions to create this record.")

        # Ensure 'average_bill' is provided
        # if 'average_bill' not in vals or vals.get('average_bill') == 0:
        #     raise exceptions.UserError("The 'Average Bill' field is mandatory.")

        # Prepare full name for contact (if needed)
        first_name = vals.get('first_name', '').strip()
        last_name = vals.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()

        # Create the design record
        design = super(Design, self).create(vals)



        # Check and update/create related contact
        phone = vals.get('phone_number')
        if phone:
            contact = self.env['res.partner'].search([('phone', '=', phone)], limit=1)
            if contact:
                contact.write({
                    'date_design_requested': vals.get('date_design_requested', fields.Date.today()),
                })
            else:
                self.env['res.partner'].create({
                    'name': full_name or 'Unknown',
                    'phone': phone,
                    'date_design_requested': vals.get('date_design_requested', fields.Date.today()),
                })

        # ✅ Google Sheets logging after creation
        try:
            design._log_design_details_to_google_sheets()
        except Exception as e:
            _logger.error("Failed to log Design to Google Sheets on creation: %s", str(e))
            _logger.error(traceback.format_exc())

        return design

    @api.onchange('design_name', 'design_link', 'utility_provider', 'average_bill', 'designer_id',
                  'proposal_eta', 'rate_type', 'discounts', 'proposal_notes')
    def _onchange_log_to_google_sheets(self):
        """Log Design updates to Google Sheets when key fields are updated."""
        for record in self:
            if record.create_date and (datetime.now() - record.create_date) > timedelta(minutes=1):
                record._log_design_details_to_google_sheets()

    # def _log_design_details_to_google_sheets(self):
    #     """Log fields to Google Sheets if phone_number exists in Column G."""
    #     try:
    #         _logger.info("Logging Design to Google Sheets for Design ID: %s", self.id)
    #
    #         json_keyfile_path = self.env['ir.config_parameter'].sudo().get_param('json_file_path')
    #         if not json_keyfile_path:
    #             _logger.error("Google Sheets JSON keyfile path is missing.")
    #             return False
    #
    #         creds = ServiceAccountCredentials.from_json_keyfile_name(
    #             json_keyfile_path,
    #             ['https://www.googleapis.com/auth/spreadsheets']
    #         )
    #         client = gspread.authorize(creds)
    #
    #         sheet_id = self.env['ir.config_parameter'].sudo().get_param('google_keys_sheet_id4')
    #         worksheet_name = self.env['ir.config_parameter'].sudo().get_param('worksheet_name_crm')
    #
    #         if not sheet_id or not worksheet_name:
    #             _logger.error("Google Sheet ID or worksheet name is missing.")
    #             return False
    #
    #         sheet = client.open_by_key(sheet_id)
    #         worksheet = sheet.worksheet(worksheet_name)
    #
    #         phone_number = self.phone_number
    #         if not phone_number:
    #             _logger.warning("Phone number is missing for Design ID: %s", self.id)
    #             return False
    #
    #         # Phone numbers are stored in Column G (column index 7)
    #         PHONE_NUMBER_COLUMN_INDEX = 7
    #         phone_numbers = worksheet.col_values(PHONE_NUMBER_COLUMN_INDEX)
    #
    #         row_values = {
    #             "AD": self.create_date.strftime("%Y-%m-%d %H:%M:%S") if self.create_date else '',
    #             "AE": self.design_name or '',
    #             "AF": self.design_link or '',
    #             "AG": self.utility_provider or '',
    #             "AH": self.average_bill or '',
    #             "AI": self.designer_id.name or '',
    #             "AJ": dict(self._fields['proposal_eta'].selection).get(self.proposal_eta, ''),
    #             "AK": dict(self._fields['rate_type'].selection).get(self.rate_type, ''),
    #             "AL": dict(self._fields['discounts'].selection).get(self.discounts, ''),
    #             "AM": self.average_bill or '',
    #             "AN": self.proposal_notes or ''
    #         }
    #
    #         if phone_number in phone_numbers:
    #             row_index = phone_numbers.index(phone_number) + 1
    #             for column_letter, value in row_values.items():
    #                 cell_reference = f"{column_letter}{row_index}"
    #                 worksheet.update(range_name=cell_reference, values=[[str(value)]])
    #             _logger.info("Updated existing row for phone number: %s", phone_number)
    #         else:
    #             # If phone number not found, append a new row
    #             # Assuming columns A-F are before G, so we pad with empty strings
    #             new_row = [''] * (PHONE_NUMBER_COLUMN_INDEX - 1) + [phone_number]
    #             new_row += list(row_values.values())
    #             worksheet.append_row(new_row)
    #             _logger.info("Added new row for phone number: %s", phone_number)
    #
    #         _logger.info("Successfully logged Design fields to Google Sheets.")
    #         return True
    #
    #     except Exception as e:
    #         _logger.error("Failed to log Design fields to Google Sheets: %s", str(e))
    #         _logger.error(traceback.format_exc())
    #         return False

    def _log_design_details_to_google_sheets(self):
        """Log design-related fields to Google Sheets using access token from calendar event."""
        try:
            _logger.info("Logging Design to Google Sheets for Design ID: %s", self.id)

            phone = self.phone_number
            if not phone:
                _logger.warning("Phone number is missing for Design ID: %s", self.id)
                return False

            # 🔍 Step 1: Find calendar event by phone number
            calendar_event = self.env['calendar.event'].sudo().search([('phone_number', '=', phone)], limit=1)
            if not calendar_event or not calendar_event.access_token:
                _logger.warning("No calendar event or access token found for phone: %s", phone)
                return False

            access_token = calendar_event.access_token
            _logger.info("Access token retrieved: %s", access_token)

            # 🔍 Step 2: Find the row index in Google Sheets using the access token
            row_index = self._find_row_by_token_in_sheet(access_token)
            if row_index is None:
                _logger.error("Access token not found in sheet for phone: %s", phone)
                return False

            # 🔍 Step 3: Read and prepare the row
            sheet = self._get_google_sheet_4()
            existing_row = sheet.row_values(row_index)

            def column_letter_to_index(letter):
                result = 0
                for char in letter.upper():
                    result = result * 26 + (ord(char) - ord('A') + 1)
                return result - 1

            # 🔍 Step 4: Ensure the row has enough columns (until 'AN')
            last_col = 'AN'
            while len(existing_row) <= column_letter_to_index(last_col):
                existing_row.append("")

            # 🔍 Step 5: Prepare values to update
            row_values = {
                "AD": self.create_date.strftime("%Y-%m-%d %H:%M:%S") if self.create_date else '',
                "AE": self.design_name or '',
                "AF": ', '.join(self.design_link_ids.mapped('link')) if self.design_link_ids else '',
                "AG": self.utility_provider or '',
                "AH": self.average_bill or '',
                "AI": self.designer_id.name or '',
                "AJ": dict(self._fields['proposal_eta'].selection).get(self.proposal_eta, ''),
                "AK": dict(self._fields['rate_type'].selection).get(self.rate_type, ''),
                "AL": dict(self._fields['discounts'].selection).get(self.discounts, ''),
                "AM": self.average_bill or '',
                "AN": self.proposal_notes or ''
            }

            # 🔍 Step 6: Inject values into the row
            for col_letter, value in row_values.items():
                col_index = column_letter_to_index(col_letter)
                existing_row[col_index] = str(value)

            # 🔍 Step 7: Update the sheet range
            sheet.update(f"AD{row_index}:AN{row_index}", [
                existing_row[column_letter_to_index('AD'):column_letter_to_index('AN') + 1]
            ])
            _logger.info("Design data successfully updated for row %s", row_index)
            return True

        except Exception as e:
            _logger.error("Failed to log design details to Google Sheets: %s", e)
            _logger.error(traceback.format_exc())
            return False

    def _find_row_by_token_in_sheet(self, token):
        """Search for the row number in the Google Sheet by matching the access token in column B."""
        try:
            sheet = self._get_google_sheet_4()
            if not sheet:
                _logger.warning("Google Sheet is not available.")
                return None

            # Column B (index 2) is where the access token is expected
            column_b = sheet.col_values(2)

            for idx, value in enumerate(column_b, start=1):
                if value.strip() == token.strip():
                    _logger.info("Access token matched at row: %s", idx)
                    return idx

            _logger.warning("Access token '%s' not found in column B", token)
            return None

        except Exception as e:
            _logger.error("Error while searching for access token in sheet: %s", e)
            _logger.error(traceback.format_exc())
            return None

    def _get_google_sheet_4(self):
        """Returns the worksheet object for CRM Google Sheet."""
        try:
            _logger.info("Connecting to Google Sheets...")

            scope = ['https://www.googleapis.com/auth/spreadsheets']
            param = self.env['ir.config_parameter'].sudo()

            json_keyfile_path = param.get_param('json_file_path')
            if not json_keyfile_path:
                _logger.error("Google Sheets JSON keyfile path is missing.")
                return None

            creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
            client = gspread.authorize(creds)

            sheet_id = param.get_param('google_keys_sheet_id4')
            worksheet_name = param.get_param('worksheet_name_crm')

            if not sheet_id or not worksheet_name:
                _logger.error("Google Sheet ID or worksheet name is missing.")
                return None

            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.worksheet(worksheet_name)

            _logger.info("Successfully connected to worksheet: %s", worksheet_name)
            return worksheet

        except FileNotFoundError as e:
            _logger.error("JSON credentials file not found: %s", str(e))
        except gspread.SpreadsheetNotFound:
            _logger.error("Spreadsheet not found.")
        except gspread.WorksheetNotFound:
            _logger.error("Worksheet not found.")
        except Exception as e:
            _logger.error("Failed to connect to Google Sheet: %s", str(e))
            _logger.error(traceback.format_exc())

        return None

    def write(self, vals):
        # Check if the user is in the specified group
        if  self.env.user.has_group('lytegen_contact_details.group_sales_manager'):
            raise AccessError("You do not have the necessary permissions to modify this record.")

        # Ensure 'average_bill' is provided or not empty in the write operation
        # if 'average_bill' not in vals or vals.get('average_bill') == 0:
        #     raise exceptions.UserError("The 'Average Bill' field cannot be empty.")

        return super(Design, self).write(vals)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    design_id = fields.Many2one(
        'design',
        string="Design",
        help="The design associated with this project"
    )



class DesignLink(models.Model):
    _name = 'design.link'
    _description = 'Proposal Links'

    design_id = fields.Many2one('design', string="Design", required=True, ondelete="cascade")
    name = fields.Char(string="Name", required=True)
    link = fields.Char(string="Proposal Link", required=True)