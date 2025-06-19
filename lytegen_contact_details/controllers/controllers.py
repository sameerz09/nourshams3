import logging
import json
from odoo import http
from odoo.http import request
from datetime import datetime, date
from datetime import datetime
import base64, os

from odoo.addons.appointment.controllers.appointment import AppointmentController

import json
import pytz
import re
from datetime import datetime, timedelta

from pytz.exceptions import UnknownTimeZoneError

from babel.dates import format_datetime, format_date, format_time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from markupsafe import Markup
from urllib.parse import quote, unquote_plus
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.urls import url_encode
from odoo.exceptions import ValidationError
from odoo import Command, exceptions, http, fields, _
from odoo.http import request, route
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf, email_normalize
from odoo.tools.mail import is_html_empty
from odoo.tools.misc import babel_locale_parse, get_lang
from odoo.addons.base.models.ir_qweb import keep_query
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import UserError
import traceback
import gspread
import json
import logging
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from odoo import http
from odoo.http import request
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)
import requests
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class CustomAppointmentController(AppointmentController):



    @http.route('/calendar/latest_event_by_phone', type='json', auth='public', methods=['POST'], csrf=False)
    def latest_event_by_phone(self, **kwargs):
        import json
        try:
            raw = request.httprequest.data
            data = json.loads(raw)
            phone = data.get('phone')
        except Exception as e:
            phone = None

        latest_event_id = 0
        design_options = []

        if phone:
            event = request.env['calendar.event'].sudo().search([('phone_number', '=', phone)], order='id desc',
                                                                limit=1)
            if event:
                latest_event_id = event.id
                for design in event.design_ids:
                    design_options.append({
                        'id': design.id,
                        'name': design.design_name
                    })

        return {
            'latest_event_id': latest_event_id,
            'design_options': design_options,
        }

    @http.route('/credentials/job_positions', type='json', auth='public', methods=['POST'], csrf=False)
    def get_job_positions(self):
        jobs = request.env['hr.job'].sudo().search([], order='name')
        return {
            'job_positions': [{'id': job.id, 'name': job.name} for job in jobs]
        }

    @http.route('/credit-check', type='http', auth="public", website=True)
    def credit_check_form(self, **kwargs):
        """ Renders the Credit Check Request form """
        return request.render("lytegen_contact_details.credit_check_request_form", {})


    @http.route('/submit/credit-check', type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def submit_credit_check(self, **post):
        try:
            _logger.info("Received credit check form data: %s", post)

            # Extract form data
            first_name = post.get('first_name', '').strip()
            last_name = post.get('last_name', '').strip()
            full_name = f"{first_name} {last_name}".strip()
            country_code = post.get('country_code','')
            phone = f"+{country_code}{post.get('phone', 'N/A').strip()}"
            email = post.get('email', 'N/A').strip()
            address = post.get('address', 'N/A').strip()
            city = post.get('city', 'N/A').strip()
            state = post.get('state', 'N/A').strip()
            postal_code = post.get('postal_code', 'N/A').strip()
            annual_income = post.get('annual_income', 'N/A').strip()
            other_income = post.get('other_income', 'N/A').strip()
            ssn = post.get('ssn', 'N/A').strip()
            dob = post.get('dob', 'N/A').strip()
            cosigner = post.get('cosigner_needed_credit_check', '').strip()
            cosigner_dob = post.get('cosigner_dob', 'N/A').strip()
            sales_rep = post.get('sales_rep', 'N/A').strip()
            selected_design_id = post.get('selected_design_id', '').strip()
            selected_design_name = post.get('selected_design_name', '').strip()
            create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            create_date = date.today().strftime('%Y-%m-%d')


            slack_message = f"""
                *New Credit Check Submission* 🔍
                *Full Name:* {full_name}
                *Phone:* {phone}
                *Email:* {email}
                *Address:* {address}, {city}, {state}, {postal_code}
                *Annual Income:* {annual_income}
                *Other Income:* {other_income}
                *SSN/TIN:* {ssn}
                *Date of Birth:* {dob}
                *Cosigner:* {cosigner}
                *Cosigner DOB:* {cosigner_dob}
                *Sales Rep:* {sales_rep}
                *Selected Design:* {selected_design_id or 'N/A'}
                *Selected Design Name:* {selected_design_name or 'N/A'}
            """
            self._send_slack_message_credit(slack_message)
            _logger.info("Slack message sent.")

            self._log_to_google_sheets([
                create_time, first_name, last_name, postal_code, phone, email, annual_income,
                other_income, ssn, dob, cosigner, address, city, state, sales_rep, selected_design_id,
                selected_design_name
            ])
            _logger.info("Logged to Google Sheets.")

            def column_letter_to_index(letter):
                result = 0
                for char in letter.upper():
                    result = result * 26 + (ord(char) - ord('A') + 1)
                return result - 1

            # Calendar + Google Sheet Update
            calendar_event = request.env['calendar.event'].sudo().search([('phone_number', 'ilike', phone[-10:])], limit=1)
            if calendar_event and calendar_event.access_token:
                access_token = calendar_event.access_token
                row_index = self._find_row_by_token_in_sheet(access_token)
                if row_index:
                    sheet = self._get_google_sheet_4()
                    existing_row = sheet.row_values(row_index)
                    while len(existing_row) <= column_letter_to_index('BG'):
                        existing_row.append("")

                    # Update the target columns
                    existing_row[column_letter_to_index('AO')] = create_time
                    existing_row[column_letter_to_index('AP')] = create_date
                    existing_row[column_letter_to_index('AQ')] = annual_income
                    existing_row[column_letter_to_index('AR')] = other_income
                    existing_row[column_letter_to_index('AS')] = ssn
                    existing_row[column_letter_to_index('AT')] = dob
                    existing_row[column_letter_to_index('AU')] = cosigner
                    existing_row[column_letter_to_index('AV')] = cosigner_dob
                    existing_row[column_letter_to_index('AW')] = full_name  # Cosigner full name
                    existing_row[column_letter_to_index('AY')] = ''  # Cosigner SSN placeholder
                    existing_row[column_letter_to_index('AZ')] = ''  # Cosigner Income placeholder
                    existing_row[column_letter_to_index('BA')] = ''  # Cosigner Email placeholder
                    existing_row[column_letter_to_index('BG')] = 'Submitted'  # Credit check status

                    sheet.update(f"AO{row_index}:BG{row_index}", [
                        existing_row[column_letter_to_index('AO'):column_letter_to_index('BG') + 1]
                    ])
                    _logger.info("Detailed credit check info updated for row %s", row_index)
                else:
                    _logger.warning("No row found in sheet for access token.")
            else:
                _logger.warning("No calendar event found for phone: %s", phone)

            self._log_to_odoo_calendar({
                'full_name': full_name,
                'phone': phone,
                'email': email,
                'dob': dob,
                'postal_code': postal_code,
                'annual_income': annual_income,
                'other_income': other_income,
                'ssn': ssn,
                'cosigner': cosigner,
                'cosigner_dob': cosigner_dob,
                'address': address,
                'city': city,
                'state': state,
                'sales_rep': sales_rep,
                'selected_design_name': selected_design_name,
            })
            _logger.info("Calendar event created with data.")

        except Exception as e:
            _logger.error("Error during credit check submission: %s", str(e))
            _logger.error(traceback.format_exc())

        return request.redirect('/credit-check/success')

    def _log_to_odoo_calendar(self, data):
        """Logs or updates Credit Check submission in Odoo's Calendar based on phone number"""

        try:
            _logger.info("Checking if an existing Calendar Event matches phone number: %s", data['phone'])

            # Search for an existing calendar event by phone number
            existing_event = request.env['calendar.event'].sudo().search(
                [('phone_number', '=', data['phone'])], limit=1)

            event_values = {
                'postal_code_credit_check': data['postal_code'],
                'first_name_credit_check': data['full_name'].split()[0] if ' ' in data['full_name'] else data[
                    'full_name'],
                'last_name_credit_check': data['full_name'].split()[-1] if ' ' in data['full_name'] else '',
                'phone_credit_check': data['phone'],
                'email_credit_check': data['email'],
                'annual_income_credit_check': data['annual_income'],
                'other_household_income_credit_check': data['other_income'],
                'ssn_tin_credit_check': data['ssn'],
                'date_of_birth_credit_check': data['dob'],
                'cosigner_needed_credit_check': data['cosigner'],
                'cosigner_dob_credit_check': data['cosigner_dob'] if data['cosigner'] else False,
                'address_credit_check': data['address'],
                'city_credit_check': data['city'],
                'state_credit_check': data['state'],
                'selected_design_name': data['selected_design_name'],
            }

            if existing_event:
                # Update existing event
                existing_event.sudo().write(event_values)
                _logger.info("Updated existing Calendar Event ID: %s with new credit check details.", existing_event.id)
            else:
                # Create new event if no match is found
                event_values.update({
                    'name': f"Credit Check - {data['full_name']}",
                    'start': datetime.now(),  # Event starts now
                    'stop': datetime.now() + timedelta(hours=1),  # Ends after 1 hour
                    'partner_ids': [
                        (6, 0, request.env['res.partner'].sudo().search([('email', '=', data['email'])]).ids)
                    ],
                })

                event = request.env['calendar.event'].sudo().create(event_values)
                _logger.info("Created new Calendar Event ID: %s", event.id)

        except Exception as e:
            _logger.error("Failed to log or update Odoo Calendar Event: %s", str(e))
            _logger.error(traceback.format_exc())

    def _log_to_google_sheets(self, data):
        """Logs credit check submission data to Google Sheets"""
        try:
            _logger.info("Starting Google Sheets logging process...")

            # Define scope
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            _logger.info("Scope defined: %s", scope)

            env = request.env()

            # Load credentials
            # json_keyfile_path = r'C:\Users\user\Desktop\client\lytegen\google_sheet_cred\wired-tea-264321-3b4a1aeac743.json'
            json_keyfile_path = env['ir.config_parameter'].sudo().get_param('json_file_path')
            _logger.info("Using credentials file: %s", json_keyfile_path)

            creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
            _logger.info("Successfully authenticated with Google API")

            # Connect to Google Sheets
            client = gspread.authorize(creds)
            _logger.info("Google Sheets API authorized")

            # Open the spreadsheet by ID
            # sheet_id = "1bIJjLQqXZVPwD3uPKKbDz2kJDfJtASavmxgk2d9SBJg"

            sheet_id = env['ir.config_parameter'].sudo().get_param('google_keys_sheet_id')
            _logger.info("Using Google Sheet ID: %s", sheet_id)

            sheet = client.open_by_key(sheet_id)
            _logger.info("Successfully opened Google Sheet")

            # Open the worksheet
            worksheet_name = "Sheet1"  # Change this if needed
            worksheet = sheet.worksheet(worksheet_name)
            _logger.info("Opened worksheet: %s", worksheet_name)

            # Append data
            _logger.info("Appending data to Google Sheets: %s", data)
            worksheet.append_row(data)
            _logger.info("Data successfully logged to Google Sheets")

        except FileNotFoundError as e:
            _logger.error("JSON credentials file not found: %s", str(e))
        except gspread.SpreadsheetNotFound:
            _logger.error("Spreadsheet not found for ID: %s", sheet_id)
        except gspread.WorksheetNotFound:
            _logger.error("Worksheet not found: %s", worksheet_name)
        except Exception as e:
            _logger.error("Failed to log data to Google Sheets: %s", str(e))
            _logger.error(traceback.format_exc())

    def _log_to_google_sheets2(self, data):
        """Logs credit check submission data to Google Sheets"""
        try:
            _logger.info("Starting Google Sheets logging process...")

            # Define scope
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            _logger.info("Scope defined: %s", scope)

            env = request.env()

            # Load credentials
            # json_keyfile_path = r'C:\Users\user\Desktop\client\lytegen\google_sheet_cred\wired-tea-264321-3b4a1aeac743.json'
            json_keyfile_path = env['ir.config_parameter'].sudo().get_param('json_file_path')
            _logger.info("Using credentials file: %s", json_keyfile_path)

            creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
            _logger.info("Successfully authenticated with Google API")

            # Connect to Google Sheets
            client = gspread.authorize(creds)
            _logger.info("Google Sheets API authorized")

            # Open the spreadsheet by ID
            # sheet_id = "1bIJjLQqXZVPwD3uPKKbDz2kJDfJtASavmxgk2d9SBJg"

            sheet_id = env['ir.config_parameter'].sudo().get_param('google_keys_sheet_id2')
            _logger.info("Using Google Sheet ID: %s", sheet_id)

            sheet = client.open_by_key(sheet_id)
            _logger.info("Successfully opened Google Sheet")

            # Open the worksheet
            worksheet_name = "Sheet1"  # Change this if needed
            worksheet = sheet.worksheet(worksheet_name)
            _logger.info("Opened worksheet: %s", worksheet_name)

            # Append data
            _logger.info("Appending data to Google Sheets: %s", data)
            worksheet.append_row(data)
            _logger.info("Data successfully logged to Google Sheets")

        except FileNotFoundError as e:
            _logger.error("JSON credentials file not found: %s", str(e))
        except gspread.SpreadsheetNotFound:
            _logger.error("Spreadsheet not found for ID: %s", sheet_id)
        except gspread.WorksheetNotFound:
            _logger.error("Worksheet not found: %s", worksheet_name)
        except Exception as e:
            _logger.error("Failed to log data to Google Sheets: %s", str(e))
            _logger.error(traceback.format_exc())

    def _log_to_google_sheets3(self, data):
        """Logs credit check submission data to Google Sheets, starting from column A"""
        try:
            _logger.info("Starting Google Sheets logging process...")

            # Define scope
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            _logger.info("Scope defined: %s", scope)

            env = request.env()

            # Load credentials
            json_keyfile_path = env['ir.config_parameter'].sudo().get_param('json_file_path')
            _logger.info("Using credentials file: %s", json_keyfile_path)

            creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
            _logger.info("Successfully authenticated with Google API")

            # Connect to Google Sheets
            client = gspread.authorize(creds)
            _logger.info("Google Sheets API authorized")

            # Open the spreadsheet by ID
            sheet_id = env['ir.config_parameter'].sudo().get_param('google_keys_sheet_id3')
            _logger.info("Using Google Sheet ID: %s", sheet_id)

            sheet = client.open_by_key(sheet_id)
            _logger.info("Successfully opened Google Sheet")

            # Open the worksheet
            worksheet_name = "New Appointments"
            worksheet = sheet.worksheet(worksheet_name)
            _logger.info("Opened worksheet: %s", worksheet_name)

            # Determine the next empty row
            next_row = len(worksheet.get_all_values()) + 1

            # Force insert data starting from column A
            _logger.info("Writing data to A%s: %s", next_row, data)
            worksheet.update(f"A{next_row}", [data])
            _logger.info("Data successfully logged to Google Sheets")

        except FileNotFoundError as e:
            _logger.error("JSON credentials file not found: %s", str(e))
        except gspread.SpreadsheetNotFound:
            _logger.error("Spreadsheet not found for ID: %s", sheet_id)
        except gspread.WorksheetNotFound:
            _logger.error("Worksheet not found: %s", worksheet_name)
        except Exception as e:
            _logger.error("Failed to log data to Google Sheets: %s", str(e))
            _logger.error(traceback.format_exc())

    def _log_to_google_sheets4(self, data):
        """Logs credit check submission data to Google Sheets"""
        try:
            _logger.info("Starting Google Sheets logging process...")

            # Define scope
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            _logger.info("Scope defined: %s", scope)

            env = request.env()

            # Load credentials
            json_keyfile_path = env['ir.config_parameter'].sudo().get_param('json_file_path')
            _logger.info("Using credentials file: %s", json_keyfile_path)

            creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
            _logger.info("Successfully authenticated with Google API")

            # Connect to Google Sheets
            client = gspread.authorize(creds)
            _logger.info("Google Sheets API authorized")

            # Open the spreadsheet by ID
            sheet_id = env['ir.config_parameter'].sudo().get_param('google_keys_sheet_id4')
            _logger.info("Using Google Sheet ID: %s", sheet_id)

            sheet = client.open_by_key(sheet_id)
            _logger.info("Successfully opened Google Sheet")

            # Open the worksheet
            worksheet_name = env['ir.config_parameter'].sudo().get_param('worksheet_name_crm')
            # worksheet_name = "New Appointments"

            worksheet = sheet.worksheet(worksheet_name)
            _logger.info("Opened worksheet: %s", worksheet_name)

            # Append data
            _logger.info("Appending data to Google Sheets: %s", data)
            worksheet.append_row(data)
            _logger.info("Data successfully logged to Google Sheets")

        except FileNotFoundError as e:
            _logger.error("JSON credentials file not found: %s", str(e))
        except gspread.SpreadsheetNotFound:
            _logger.error("Spreadsheet not found for ID: %s", sheet_id)
        except gspread.WorksheetNotFound:
            _logger.error("Worksheet not found: %s", worksheet_name)
        except Exception as e:
            _logger.error("Failed to log data to Google Sheets: %s", str(e))
            _logger.error(traceback.format_exc())

    def _log_project_onboarding_to_google_sheets(self, data):
        """Logs project onboarding data to the Signed Contracts Google Sheet"""
        try:
            _logger.info("Starting Google Sheets logging process...")

            scope = ['https://www.googleapis.com/auth/spreadsheets']
            env = request.env()
            json_keyfile_path = env['ir.config_parameter'].sudo().get_param('json_file_path')
            sheet_id = env['ir.config_parameter'].sudo().get_param('signed_contracts_sheet_id')
            sheet_name = env['ir.config_parameter'].sudo().get_param('signed_contracts_sheet_name')

            _logger.info("Using credentials file: %s", json_keyfile_path)
            creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
            client = gspread.authorize(creds)

            _logger.info("Google Sheets API authorized. Using Sheet ID: %s", sheet_id)
            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.worksheet(sheet_name)

            _logger.info("Appending data to Google Sheets: %s", data)
            worksheet.append_row(data)
            _logger.info("Data successfully logged to Google Sheets")

        except FileNotFoundError as e:
            _logger.error("JSON credentials file not found: %s", str(e))
        except gspread.SpreadsheetNotFound:
            _logger.error("Spreadsheet not found for ID: %s", sheet_id)
        except gspread.WorksheetNotFound:
            _logger.error("Worksheet not found: %s", sheet_name)
        except Exception as e:
            _logger.error("Failed to log data to Google Sheets: %s", str(e))
            _logger.error(traceback.format_exc())

    @http.route('/credentials', type='http', auth='public', website=True)
    def credentials_form(self, **kwargs):
        return request.render("lytegen_contact_details.credentials_request_form", {})

    @http.route('/credentials/success', type='http', auth='public', website=True)
    def credentials_success(self, **kwargs):
        return request.render("lytegen_contact_details.credentials_success_page", {})

    @http.route('/submit/credentials', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def submit_credentials_form(self, **post):
        applied_position = post.get('applied_position', '').strip()
        first_name = post.get('first_name', '').strip()
        last_name = post.get('last_name', '').strip()
        phone = post.get('phone', '').strip()
        email = post.get('email', '').strip()
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        message = f"""
                *New Credentials Request* 🧾
                *Position:* {applied_position}
                *Name:* {first_name} {last_name}
                *Phone:* {phone}
                *Email:* {email}
                *Time:* {create_time}
            """

        try:
            self._send_slack_message(message)
            _logger.info("Credentials request sent to Slack successfully.")
        except Exception as e:
            _logger.error("Slack message failed: %s", e)

        return request.redirect('/credentials/success')

    def _send_slack_message(self, message):
        # Optional Slack integration (insert webhook logic here if needed)
        pass

    # @http.route('/project_onboarding', type='http', auth='public', website=True)
    # def project_onboarding_form(self, **kwargs):
    #     sp1s = ['Alexia Jimenez', 'Bodie Parsons', 'Drake Hoffman', 'Ivan Mejia', 'James Roach', 'Jason Perez', 'James Fort', 'Johnny Whited', 'Maria Hernandez', 'Sarah McDonald', 'Simran Kaur', 'Weronika Bakai', 'Marcos Pineda', 'Zachary Cardin', 'Felix Diaz']
    #     reroof = ['Yes','No']
    #     mounts = ['Roof','Ground']
    #     mpu = ['No Fastest Install', 'Customer requested – 45 days delay']
    #     question_answer = ['Yes','No']
    #     battery = ['Grid-Tied','full_backup','No battery']
    #     utility_bill_holder = ['Customer','Cosigner on contract', 'Other']
    #     finance_type = ['Loan' ,'PPA']
    #     loanProduct = ['Sungage','Sunlight','Mosaic', 'GoodLeap', 'Enfin']
    #     ppaProduct = ['LightReach','Everbright','Sunrun','GoodLeap','Thrive']
    #     installer = ['Bright Ops','Lytegen','Thrive']
    #     lead_origin = ['Company Appt', 'Self Gen', 'Referral']
    #     return request.render("lytegen_contact_details.project_onboarding_form", {'sp1s': sp1s,'reroof': reroof,'mounts': mounts,'mpu': mpu,'question_answer': question_answer,'battery': battery,'utility_bill_holder': utility_bill_holder,'finance_type': finance_type, 'installer': installer, 'lead_origin': lead_origin, 'loanProduct': loanProduct, 'ppaProduct': ppaProduct})
    @http.route('/refuge', type='http', auth='public', website=True)
    def project_onboarding_form(self, **kwargs):

        reroof = [
            ('yes_needed', 'Yes Needed'),
            ('yes_customer_requested', 'Yes Customer Requested'),
            ('not_needed', 'Not Needed')
        ]

        mounts = [
            ('roof', 'Roof'),
            ('ground', 'Ground'),
            ('mixed', 'Mixed')
        ]

        mpu = [
            ('only_if_needed_fastest_install', 'Only if needed (Fastest install)'),
            ('customer_requested', 'Customer requested (45 days delay)')
        ]

        question_answer = [
            ('yes', 'Yes'),
            ('no', 'No')
        ]

        battery = [
            ('grid_tied', 'Grid-Tied'),
            ('full_backup', 'Full Backup'),
            ('no_battery', 'No Battery')
        ]

        utility_bill_holder = [
            ('customer', 'Customer'),
            ('cosigner_on_contract', 'Cosigner on contract'),
            ('other', 'Other')
        ]

        finance_type = [
            ('loan', 'Loan'),
            ('ppa', 'PPA'),
            ('cash','Cash')
            # ('cash', 'Cash'),
            # ('enfin_loan', 'Enfin Loan'),
            # ('everbright_loan', 'Everbright Loan'),
            # ('goodleap_ppa', 'GoodLeap PPA'),
            # ('goodleap_loan', 'GoodLeap Loan'),
            # ('lightreach_ppa', 'Lightreach PPA'),
            # ('mosaic_loan', 'Mosaic Loan'),
            # ('pace', 'PACE'),
            # ('sunlight_loan', 'Sunlight Loan'),
            # ('sunrun_ppa', 'Sunrun PPA'),
            # ('thrive_ppa', 'Thrive PPA')
        ]

        loanProduct = [
            'Sungage', 'Sunlight', 'Mosaic', 'Goodleap', 'Enfin'
        ]

        ppaProduct = [
            'Enfin', 'Everbright', 'Sunrun', 'Goodleap', 'Thrive'
        ]

        installer = [
            ('lytegen', 'Lytegen'),
            ('brightops', 'Bright Ops'),
            ('thrive', 'Thrive')
        ]

        lead_origin = [
            ('company_lead', 'Company Lead'),
            ('company_referral', 'Company Referral'),
            ('selfgen', 'Selfgen')
        ]

        sales_consultants = request.env['hr.employee'].sudo().search([
            ('job_id.name', '=', 'Sales Consultant'),
            ('active', '=', True)
        ])

        gated_access = [
            ('yes', 'Yes'),
            ('no', 'No')
        ]

        addons = [
            ('yes', 'Yes'),
            ('no', 'No')
        ]

        displacement_reasons = [
            ('forced_displacement', 'تهجير قسري'),
            ('house_demolition', 'هدم بيت'),
            ('house_damage', 'تضرر بيت'),
            ('lack_of_services', 'انعدام الخدمات')
        ]

        displacement_residences = [
            ('shelter', 'مركز إيواء'),
            ('relatives', 'لدى أقارب'),
            ('rented', 'شقة مستأجرة'),
            ('partial_return', 'عائد للمنزل لكن جزء من الأسرة ما زال نازحًا'),
            ('other', 'موقع آخر'),
        ]
        multiple_displacement_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]
        is_currently_displaced = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]
        housing_type_options = [
            ('inside_camp', 'بيت داخل المخيم'),
            ('outside_camp', 'بيت خارج المخيم'),
            ('with_relatives', 'عند أقارب'),
            ('shelter_center', 'مركز إيواء (مدرسة أو مسجد…)'),
            ('no_fixed_housing', 'بدون سكن ثابت'),
        ]

        housing_damage_level_options = [
            ('none', 'لا'),
            ('minor', 'بسيط'),
            ('moderate', 'متوسط'),
            ('destroyed', 'دمار كلي'),
        ]

        damage_documented_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        economic_status_options = [
            ('pension', 'راتب تقاعدي'),
            ('no_income', 'لا دخل'),
            ('aid_only', 'مساعدات فقط'),
            ('one_working', 'شخص واحد يعمل'),
            ('multiple_working', 'أكثر من شخص يعمل'),
        ]

        worked_inside_palestine_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        workers_count_options = [
            ('1', '1'),
            ('2', '2'),
            ('3_plus', '3+'),
        ]

        unemployed_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]
        school_students_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        school_attendance_options = [
            ('all_continuing', 'مستمرون'),
            ('some_stopped', 'بعضهم توقف'),
        ]

        university_students_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        university_attendance_options = [
            ('continuing', 'التعليم مستمر'),
            ('stopped', 'توقف'),
        ]

        disability_type_options = [
            ('visual', 'الإعاقة البصرية'),
            ('hearing', 'الإعاقة السمعية'),
            ('speech', 'الإعاقة النطقية'),
            ('mental', 'الإعاقة العقلية'),
            ('physical', 'الإعاقة الجسمية والحركية'),
            ('chronic', 'مرض مزمن'),
        ]

        receiving_care_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        has_disabled_members_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        care_affected_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        basic_needs_options = [
            ('shelter', 'مسكن'),
            ('food', 'غذاء'),
            ('treatment', 'علاج'),
            ('clothing', 'ملابس'),
            ('financial_aid', 'مساعدات مالية'),
            ('baby_supplies', 'مستلزمات أطفال'),
            ('support', 'دعم تعليمي/نفسي/لذوي الإعاقة'),
            ('other', 'أخرى'),
        ]

        family_skills_options = [
            ('construction', 'بناء'),
            ('electricity', 'كهرباء'),
            ('education', 'تعليم'),
            ('maintenance', 'صيانة'),
            ('other', 'آخر'),
        ]

        data_sharing_consent_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]
        pre_displacement_house_type_options = [
            ('independent', 'بيت مستقل'),
            ('apartment', 'شقة'),
            ('shared_building', 'بناية مشتركة'),
        ]

        house_ownership_status_options = [
            ('owned', 'ملك'),
            ('rented', 'مستأجر'),
        ]

        other_families_on_floor_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        support_type_options = [
            ('support', 'دعم تعليمي/نفسي/لذوي الإعاقة'),
            ('other', 'أخرى'),
        ]

        family_skills_options = [
            ('construction', 'بناء'),
            ('electricity', 'كهرباء'),
            ('education', 'تعليم'),
            ('maintenance', 'صيانة'),
            ('other', 'آخر'),
        ]

        data_sharing_consent_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        pre_displacement_house_type_options = [
            ('independent', 'بيت مستقل'),
            ('apartment', 'شقة'),
            ('shared_building', 'بناية مشتركة'),
        ]

        house_ownership_status_options = [
            ('owned', 'ملك'),
            ('rented', 'مستأجر'),
        ]

        other_families_on_floor_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        support_type_options = [
            ('support', 'دعم تعليمي/نفسي/لذوي الإعاقة'),
            ('other', 'أخرى'),
        ]

        family_skills_options = [
            ('construction', 'بناء'),
            ('electricity', 'كهرباء'),
            ('education', 'تعليم'),
            ('maintenance', 'صيانة'),
            ('other', 'آخر'),
        ]

        data_sharing_consent_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        pre_displacement_house_type_options = [
            ('independent', 'بيت مستقل'),
            ('apartment', 'شقة'),
            ('shared_building', 'بناية مشتركة'),
        ]

        house_ownership_status_options = [
            ('owned', 'ملك'),
            ('rented', 'مستأجر'),
        ]

        other_families_on_floor_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        support_type_options = [
            ('support', 'دعم تعليمي/نفسي/لذوي الإعاقة'),
            ('other', 'أخرى'),
        ]

        family_skills_options = [
            ('construction', 'بناء'),
            ('electricity', 'كهرباء'),
            ('education', 'تعليم'),
            ('maintenance', 'صيانة'),
            ('other', 'آخر'),
        ]

        data_sharing_consent_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        pre_displacement_house_type_options = [
            ('independent', 'بيت مستقل'),
            ('apartment', 'شقة'),
            ('shared_building', 'بناية مشتركة'),
        ]

        house_ownership_status_options = [
            ('owned', 'ملك'),
            ('rented', 'مستأجر'),
        ]

        other_families_on_floor_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        housing_condition_options = [('habitable', 'صالح للسكن'), ('uninhabitable', 'غير صالح')]
        employment_type_options = [('gov', 'موظف حكومي'), ('agency', 'موظف وكالة'), ('private', 'قطاع خاص'),
                                   ('interior_worker', 'عامل في الداخل')]
        stable_income_options = [('yes', 'نعم'), ('no', 'لا')]
        interior_workers_options = [('yes', 'نعم'), ('no', 'لا')]
        can_still_work_options = [('yes', 'نعم'), ('no', 'لا')]
        lost_shop_options = [('yes', 'نعم'), ('no', 'لا')]
        shop_ownership_options = [('owned', 'ملك'), ('rented', 'مستأجر')]
        main_income_source_options = [('yes', 'نعم'), ('no', 'لا')]
        special_equipment_options = [('yes', 'نعم'), ('no', 'لا')]
        self_employment_options = [('yes', 'نعم'), ('no', 'لا')]
        has_family_martyr_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        has_family_prisoner_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        has_family_injured_options = [
            ('yes', 'نعم'),
            ('no', 'لا'),
        ]

        sp1s = [(emp.id, emp.name) for emp in sales_consultants]

        return request.render("lytegen_contact_details.project_onboarding_form", {
            'sp1s': sp1s,
            'reroof': reroof,
            'mounts': mounts,
            'mpu': mpu,
            'question_answer': question_answer,
            'battery': battery,
            'utility_bill_holder': utility_bill_holder,
            'finance_type': finance_type,
            'installer': installer,
            'lead_origin': lead_origin,
            'loanProduct': loanProduct,
            'ppaProduct': ppaProduct,
            'gated_access': gated_access,
            'addons': addons,
            'displacement_reasons': displacement_reasons,
            'displacement_residences': displacement_residences,
            'multiple_displacement_options': multiple_displacement_options,
            'is_currently_displaced': is_currently_displaced,
            'housing_type_options': housing_type_options,
            'housing_damage_level_options': housing_damage_level_options,
            'damage_documented_options': damage_documented_options,
            'economic_status_options': economic_status_options,
            'worked_inside_palestine_options': worked_inside_palestine_options,
            'workers_count_options': workers_count_options,
            'unemployed_options': unemployed_options,
            'school_students_options': school_students_options,
            'school_attendance_options': school_attendance_options,
            'university_students_options': university_students_options,
            'university_attendance_options': university_attendance_options,
            'disability_type_options': disability_type_options,
            'receiving_care_options': receiving_care_options,
            'care_affected_options': care_affected_options,
            'basic_needs_options': basic_needs_options,
            'data_sharing_consent_options': data_sharing_consent_options,
            'family_skills_options': family_skills_options,
            'pre_displacement_house_type_options': pre_displacement_house_type_options,
            'house_ownership_status_options': house_ownership_status_options,
            'other_families_on_floor_options': other_families_on_floor_options,
            'support_type_options': support_type_options,
            # 'support_type_options': support_type_options,
            # 'family_skills_options': family_skills_options,
            'housing_condition_options': housing_condition_options,
            'employment_type_options': employment_type_options,
            'stable_income_options': stable_income_options,
            'interior_workers_options': interior_workers_options,
            'can_still_work_options': can_still_work_options,
            'lost_shop_options': lost_shop_options,
            'shop_ownership_options': shop_ownership_options,
            'main_income_source_options': main_income_source_options,
            'special_equipment_options': special_equipment_options,
            'self_employment_options': self_employment_options,
            'has_family_martyr_options': has_family_martyr_options,
            'has_family_prisoner_options': has_family_prisoner_options,
            'has_family_injured_options': has_family_injured_options,
            'has_disabled_members_options': has_disabled_members_options,


        })

    @http.route('/submit/project_onboarding', type='http', auth='public', website=True, csrf=False)
    def submit_project_onboarding(self, **post):
        try:
            full_name = f"{post.get('customer_first_name', '')} {post.get('customer_middle_name', '')} {post.get('customer_grandfather_name', '')} {post.get('customer_last_name', '')}".strip()
            phone = post.get('customer_phone_number', '')
            email = post.get('customer_email', '')
            secondary_phone = post.get('secondary_contact_phone', '')
            secondary_country_code = post.get('secondary_country_code', '')
            product_type = ''
            if post.get('finance_type', '').lower() == 'ppa':
                product_type = post.get('ppa_type', '')
            elif post.get('finance_type', '').lower() == 'loan':
                product_type = post.get('loantype', '')

            existing_project = request.env['project.project'].sudo().search([
                ('id_number', '=', post.get('id_number'))
            ], limit=1)

            # Parse relational field safely
            consultant_id = int(post['sp2']) if post.get('sp2') and post['sp2'].isdigit() else False

            # Clean optional phone field
            secondary_full_phone = f"+{secondary_country_code}{secondary_phone}" if secondary_phone else False

            # Build values
            project_vals = {
                'name': full_name,
                'customer_name': full_name,
                'phone': phone,
                'email': email,
                'secondary_customer_name': post.get('secondary_contact_name') or '',
                'secondary_phone': secondary_full_phone,
                'secondary_email': post.get('secondary_contact_email') or '',
                'id_number': post.get('id_number'),
                'unrwa_card_number': post.get('unrwa_card_number') or '',
                'sales_consultant_employee_id': consultant_id,
                'street_address': post.get('street_address') or '',
                'pre_displacement_area': post.get('pre_displacement_area') or '',
                'pre_displacement_address': post.get('pre_displacement_address') or '',
                'shared_with': post.get('shared_with') or '',
                'pre_displacement_description': post.get('pre_displacement_description') or '',
                'post_displacement_area': post.get('post_displacement_area') or '',
                'displacement_date': post.get('displacement_date'),
                'is_currently_displaced': post.get('is_currently_displaced'),
                'multiple_displacements': post.get('multiple_displacement_options'),
                'displacement_residence_type': post.get('displacement_residences'),
                'displacement_reasons': post.get('displacement_reasons'),
                'pre_displacement_house_type': post.get('pre_displacement_house_type'),
                'house_ownership_status': post.get('house_ownership_status'),
                'other_families_on_floor': post.get('other_families_on_floor'),
                'family_member_count': post.get('family_member_count'),
                'has_unemployed': post.get('has_unemployed'),
                'has_school_students': post.get('has_school_students'),
                'school_attendance_status': post.get('school_attendance_status'),
                'has_university_students': post.get('has_university_students'),
                'university_attendance_status': post.get('university_attendance_status'),
                'has_disabled_members': post.get('has_disabled_members'),
                'disabled_count': post.get('disabled_count'),
                'disability_type': post.get('disability_type'),
                'receiving_care': post.get('receiving_care'),
                'care_affected_by_displacement': post.get('care_affected_by_displacement'),
                'housing_type': post.get('housing_type'),
                'housing_damage_level': post.get('housing_damage_level'),
                'damage_documented': post.get('damage_documented'),
                'housing_condition': post.get('housing_condition'),
                'economic_status': post.get('economic_status'),
                'employment_type': post.get('employment_type'),
                'stable_income': post.get('stable_income'),
                'interior_workers': post.get('interior_workers'),
                'can_still_work': post.get('can_still_work'),
                'worked_inside_palestine_before': post.get('worked_inside_palestine_before'),
                'lost_shop': post.get('lost_shop'),
                'shop_name': post.get('shop_name'),
                'shop_location': post.get('shop_location'),
                'shop_business_type': post.get('shop_business_type'),
                'shop_ownership': post.get('shop_ownership'),
                'shop_main_income_source': post.get('shop_main_income_source'),
                'workers_count_before_displacement': post.get('workers_count_before_displacement'),
                'workers_count': post.get('workers_count'),
                'has_family_martyr': post.get('has_family_martyr'),
                'has_family_prisoner': post.get('has_family_prisoner'),
                'has_family_injured': post.get('has_family_injured'),
                'martyr_name': post.get('martyr_name'),
                'relation_to_head': post.get('relation_to_head'),
                'event_date': post.get('event_date'),
                'event_details': post.get('event_details'),
                'family_skills': post.get('family_skills'),
                'has_special_equipment': post.get('has_special_equipment'),
                'interested_in_self_employment': post.get('interested_in_self_employment'),
                'finance_type': post.get('finance_type'),
                'loantype': product_type,
                'custom_ss_times': post.get('call_window'),
                'notes': post.get('notes'),
                'special_request': post.get('special_request'),
                'additional_notes': post.get('additional_notes'),
                'basic_needs': post.get('basic_needs'),
                'data_sharing_consent': post.get('data_sharing_consent'),
                'wife_full_name': post.get('wife_full_name'),
                'wife_id_number': post.get('wife_id_number'),
                'skill_construction': post.get('skill_construction'),
                'skill_electricity': post.get('skill_electricity'),
                'skill_education': post.get('skill_education'),
                'skill_maintenance': post.get('skill_maintenance'),
                'skill_other': post.get('skill_other'),
                'date_of_birth': post.get('date_of_birth'),
                'date_start': date.today(),
            }

            # Update or create project safely
            project = existing_project.write(project_vals) and existing_project or \
                      request.env['project.project'].sudo().create(project_vals)

            # ✅ Write attachments safely
            attachment_vals = {}

            def add_attachments(field_name, file_list):
                ids = []
                for f in file_list:
                    if f:
                        content = f.read()
                        att = request.env['ir.attachment'].sudo().create({
                            'name': f.filename,
                            'datas': base64.b64encode(content),
                            'res_model': 'project.project',
                            'res_id': project.id,
                            'type': 'binary',
                            'mimetype': f.mimetype,
                            'public': True,
                        })
                        ids.append(att.id)
                if ids:
                    attachment_vals[field_name] = [(6, 0, ids)]

            add_attachments('usage_files', request.httprequest.files.getlist('utility_bill[]'))
            add_attachments('additional_files', request.httprequest.files.getlist('additional_files[]'))
            add_attachments('unrwa_document', [request.httprequest.files.get('unrwa_document')])
            add_attachments('house_damage_photos', request.httprequest.files.getlist('house_damage_photos[]'))
            add_attachments('report_documents', request.httprequest.files.getlist('report_documents[]'))

            if attachment_vals:
                project.write(attachment_vals)

            return request.render("lytegen_contact_details.project_onboarding_success", {'project': project})

        except Exception as e:
            import traceback
            _logger.error("Project onboarding submission error: %s\n%s", str(e), traceback.format_exc())
            return f"<pre>Error: {str(e)}</pre>"

    def getEnv(self):
        db_name = request.env.cr.dbname
        return 'prod' if 'main' in db_name else 'dev'

    def create_update_entry_in_ghl(self, images=None, **kwargs):
        if images is None:
            images = {}
        try:
            baseurl = 'https://rest.gohighlevel.com/v1/contacts/'
            params = kwargs
            phone = kwargs.get("phone")
            contact_lookup = f'{baseurl}lookup?phone={phone}'
            apiKeys = {
                'dev': {
                    'key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IjJYaENOY0VaQU1YN2VJbEVtdTBXIiwiY29tcGFueV9pZCI6ImQ1ZWNRdFVGeUxvWjVxS0xhQUlzIiwidmVyc2lvbiI6MSwiaWF0IjoxNzAzNTU2NjA3MzQ5LCJzdWIiOiJ1c2VyX2lkIn0.GpW1PP15wJdaIf8NzClAxwgz4cYgZ0MiSMVdvh8g_ZA',
                    'host': 'https://lytegen-odoo-v12112024-staging-bugs-19310422.dev.odoo.com'
                },
                'prod': {
                    'key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IjVRNUlGQW5tTFRYWWw4c0psNFFBIiwidmVyc2lvbiI6MSwiaWF0IjoxNzEwMTM2MTg2Mzg0LCJzdWIiOiI4TXF6Rk5XaWFoU20xRXM3S05haCJ9.nfm1wdjCYRFwUlfAG1R6ozQR_73rhE67N1DTCXCVwQU',
                    'host': 'https://odoo.lytegen.com'
                }
            }

            envData = apiKeys[self.getEnv()]

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {envData['key']}"
            }
            response = requests.request('GET', url=contact_lookup, headers=headers)
            json_data = json.loads(response.text)
            if 200 <= response.status_code <= 299:
                contacts = json_data['contacts']
                if len(contacts) > 0:
                    contacts = contacts[0]
                    contact_id = contacts['id']
                    url = f"{baseurl}{contact_id}"
                    response = requests.request('PUT', url=url, headers=headers, data=json.dumps(params))
                else:
                    response = requests.request('POST', url=baseurl, headers=headers, data=json.dumps(params))
            else:
                response = requests.request('POST', url=baseurl, headers=headers, data=json.dumps(params))
            # print(response.text)
            if 200 <= response.status_code <= 299:
                resp = json.loads(response.text)
                contact_id = resp['contact']['id']
                url = f'{baseurl}{contact_id}'

                if images:
                    for key, value in images.items():
                        for image_path in value:
                            params = {
                                'customField': {
                                    key: f"{envData['host']}/web/content/{image_path}"
                                }
                            }
                            response = requests.request('PUT', url=url, headers=headers, data=json.dumps(params))

                _logger.info("✅ Successfully created entry in GHL.",response.text)
                return True
            else:
                _logger.info("✅ Failed to create entry in GHL.",response.text)
                return False
        except Exception as e:
            _logger.error("❌ Error creating the entry in GHL: %s", str(e))
            return False

    @http.route('/site_survey', type='http', auth='public', website=True)
    def site_survey_form(self, **kwargs):
        return request.render("lytegen_contact_details.site_survey_form", {'questionAnswers': ['Yes','No'], 'house_type': ['Single family','Duplex','Triplex'], 'electrical_overhead': ['Yes','No','I don\'t know']})

    @http.route('/credit-check/success', type='http', auth="public", website=True)
    def credit_check_success(self):
        """ Renders the success page after form submission """
        return request.render("lytegen_contact_details.credit_check_success_page", {})

    # @http.route('/ach', type='http', auth='public', website=True)
    # def ach_appointment_form(self, **kwargs):
    #     return request.render("lytegen_contact_details.ach_appointment_form", {})
    # @http.route('/ach', type='http', auth='user', website=True)
    # def ach_appointment_form(self, **kwargs):
    #     user = request.env.user
    #     if not user.has_group('base.group_portal'):
    #         return request.redirect('/ach/error')  # You can customize this error route/page
    #     return request.render("lytegen_contact_details.ach_appointment_form", {})
    @http.route('/ach', type='http', auth='public', website=True)
    def ach_appointment_form(self, **kwargs):
        return request.render("lytegen_contact_details.ach_appointment_form", {})

    @http.route('/proposalrequest', type='http', auth='public', website=True)
    def proposal_form(self, **kwargs):
        rate_types = [
            ('care', 'Care'),
            ('no_care', 'No Care')
        ]
        discount_options = [
            ('senior_citizen', 'Senior citizen'),
            ('veteran', 'Veteran'),
            ('active_military', 'Active military'),
            ('law_enforcement', 'Law enforcement'),
            ('healthcare_worker', 'Healthcare Worker'),
            ('not_applicable', 'Not applicable')
        ]

        sales_consultants = request.env['hr.employee'].sudo().search([
            ('job_id.name', '=', 'Sales Consultant'),
            ('active', '=', True)
        ])

        sp1s = [(emp.id, emp.name) for emp in sales_consultants]
        return request.render("lytegen_contact_details.proposal_request_form", {
            'rate_types': rate_types,
            'discount_options': discount_options,
            'sp1s': sp1s
        })


    @http.route('/submit/proposalrequest', type='http', auth='public', website=True, csrf=False)
    def submit_proposal_request(self, **post):
        country_code = post.get('country_code')
        phone = f"+{country_code}{post.get('customer_phone_number')}"
        sp1 = int(post.get('sp1')) if post.get('sp1') else False

        vals = {
            'first_name': post.get('customer_first_name'),
            'last_name': post.get('customer_last_name'),
            'street_address': post.get('street_address'),
            'city': post.get('city'),
            'state': post.get('state'),
            'zip_code': post.get('zipcode'),
            'phone_number': phone,
            'sales_consultant_employee_id': sp1,
            'email': post.get('customer_email'),
            'utility_provider': post.get('utility_company'),
            'rate_type': post.get('rate_type'),
            'discounts': post.get('discounts'),
            'average_bill': post.get('average_bill'),
            'proposal_notes': post.get('notes'),
            'design_name': f"{post.get('customer_first_name')} {post.get('customer_last_name')}",
        }

        design = request.env['design'].sudo().search([('phone_number', 'ilike', phone[-10:])], limit=1)
        if design:
            design.sudo().write(vals)
        else:
            design = request.env['design'].sudo().create(vals)

        # Handle uploaded utility_bill files
        files = request.httprequest.files.getlist('utility_bill[]')
        attached_files = {}
        field_id = '2nvUQ4BJTvoGvoQc8DG4' if self.getEnv() == 'prod' else 'eG2AcvDmorpR5oa0vqY4'
        if files:
            attachment_ids = []
            for file in files:
                file_content = file.read()
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': file.filename,
                    'type': 'binary',
                    'datas': base64.b64encode(file_content),
                    'res_model': 'design',
                    'res_id': design.id,
                    'mimetype': file.content_type,
                    'public': True,
                })
                attachment_ids.append(attachment.id)
                if field_id not in attached_files.keys():
                    attached_files[field_id] = [f'{attachment.id}/{file.filename}']
                else:
                    attached_files[field_id].append(f'{attachment.id}/{file.filename}')

            design.sudo().write({'usage_files': [(6, 0, attachment_ids)]})

        # Link design to calendar event
        calendar_event = request.env['calendar.event'].sudo().search([('phone_number', 'ilike', phone[-10:])], limit=1)
        if calendar_event:
            calendar_event.write({'design_ids': [(4, design.id)]})

        existing_contact = request.env['res.partner'].sudo().search([('phone', 'ilike', phone[-10:])], limit=1)
        if existing_contact:
            existing_contact.write({'proposal_requested_date': datetime.now().date(),'date_sit': datetime.now().date()})
        else:
            request.env['res.partner'].sudo().create({
                'phone': phone,
                'address_2':  post.get('street_address'),
                'state_2': post.get('state'),
                'city_2': post.get('city'),
                'postal_code_2': post.get('zipcode'),
                'average_bill_2': post.get('average_bill'),
                'first_name': post.get('customer_first_name'),
                'last_name': post.get('customer_last_name'),
                'name': f"{post.get('customer_first_name','')} {post.get('customer_last_name','')}",
                'sales_consultant_id': sp1,
                'date_booked':  datetime.now().date(),
                'proposal_requested_date':  datetime.now().date(),
                'date_sit':  datetime.now().date()
            })

        # ✅ Create/Update entry in GHL
        custom_params = {
            'firstName': post.get('customer_first_name', '').strip(),
            'lastName': post.get('customer_last_name', '').strip(),
            'name': f"{ post.get('customer_first_name', '').strip()} {post.get('customer_last_name', '').strip()}",
            'email': post.get('customer_email'),
            'phone': phone,
            'address1': post.get('street_address'),
            'city': post.get('city'),
            'state': post.get('state'),
            'postalCode': post.get('zipcode')
        }
        if self.getEnv() == 'prod':
            selected_sales_consultants = request.env['hr.employee'].sudo().search([('id', '=', sp1)], limit=1)
            custom_params['customField'] = {
                'od4v2UaeiLHUtxZM3pXe': str(datetime.now().date()),
                'VSIRcO5vfkXTegzm0OgC': selected_sales_consultants.name if selected_sales_consultants else '',
                'KUrF30suYuw29WXT7Jmy': post.get('utility_company').strip(),
                's7WCQrqBrkLLRQlmyEbx': str(post.get('rate_type')).strip().replace('_',' ').title(),
                'hlvM7DNdjhWI9lJJ8pKR': 'Healthcare Worker' if post.get('discounts') == 'healthcare_worker' else str(post.get('discounts')).strip().replace('_',' ').capitalize(),
                'wyGNfjeE8j9P7avVFRvu': post.get('average_bill'),
                'U8eYNXsZMKvDsCuiAtM0': post.get('notes'),
            }

        self.create_update_entry_in_ghl(attached_files,**custom_params)

        # ✅ Log to Google Sheets
        self._log_proposal_to_sheet(design, sp1)
        # Send Slack message
        design._send_slack_message()

        return request.render('lytegen_contact_details.thankyou_template', {
            'design': design,
        })

    def _log_proposal_to_sheet(self, design, sp1_value=''):
        try:
            _logger.info("Logging proposal request to Google Sheet...")

            scope = ['https://www.googleapis.com/auth/spreadsheets']
            config = request.env['ir.config_parameter'].sudo()
            creds_path = config.get_param('json_file_path')
            sheet_id = config.get_param('proposal_request_sheet_id')
            worksheet_name = config.get_param('proposal_request_sheet_name')

            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.worksheet(worksheet_name)

            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                design.first_name or '',
                design.last_name or '',
                design.street_address or '',
                design.city or '',
                design.state or '',
                design.zip_code or '',
                design.email or '',
                design.phone_number or '',
                design.utility_provider or '',
                dict(design._fields['rate_type'].selection).get(design.rate_type, ''),
                sp1_value or '',
                str(design.average_bill or ''),
                dict(design._fields['discounts'].selection).get(design.discounts, ''),
                design.proposal_notes or '',
            ]

            worksheet.append_row(row)
            _logger.info("✅ Successfully logged proposal request to sheet.")

        except Exception as e:
            _logger.error("❌ Google Sheets Logging Failed: %s", str(e))
            _logger.error(traceback.format_exc())

        ### New ACH Success Route
    @http.route('/ach/success', type='http', auth='public', website=True)
    def ach_success(self, **kwargs):
        """ Renders the success page after ACH form submission """
        return request.render("lytegen_contact_details.ach_success_page", {})


    @route('/submit/ach', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def submit_ach_form(self, **post):
        full_name = post.get('full_name', '').strip()
        country_code = post.get('country_code','')
        phone = f"+{country_code}{post.get('phone', 'N/A').strip()}"
        account_number = post.get('account_number', 'N/A').strip()
        routing_number = post.get('routing_number', 'N/A').strip()
        bank_name = post.get('bank_name', 'N/A').strip()
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        def mask_number(number):
            return f"****{number[-4:]}" if len(number) > 4 else "Invalid"

        def column_letter_to_index(letter):
            letter = letter.upper()
            result = 0
            for char in letter:
                result *= 26
                result += ord(char) - ord('A') + 1
            return result - 1

        account_number_masked = mask_number(account_number)
        routing_number_masked = mask_number(routing_number)

        if not full_name or not account_number or not routing_number:
            _logger.warning("Missing essential ACH data.")
            return request.redirect('/ach/error')

        message = f"""
    *New ACH Submission Received*
    *Full Name:* {full_name}
    *Phone:* {phone}
    *Bank Name:* {bank_name}
    *Account Number:* {account_number_masked}
    *Routing Number:* {routing_number_masked}
    *Create Time:* {create_time}
    """

        try:
            self._send_slack_message_ach(message)
            _logger.info("ACH submission sent to Slack successfully")
        except Exception as e:
            _logger.error("Failed to send ACH to Slack: %s", e)

        try:
            # ✅ Step 1: Log to summary Google Sheet
            self._log_to_google_sheets2([
                create_time, full_name, phone, account_number_masked, routing_number_masked, bank_name
            ])
            _logger.info("Logged to summary Google Sheet successfully")

            # ✅ Step 2: Find calendar event by phone
            calendar_event = request.env['calendar.event'].sudo().search([('phone_number', 'ilike', phone[-10:])], limit=1)
            if not calendar_event or not calendar_event.access_token:
                _logger.warning("No calendar event found for phone: %s", phone)
                return request.redirect('/ach/error')

            access_token = calendar_event.access_token
            _logger.info("Found access token: %s", access_token)

            # ✅ Step 3: Find row in the target sheet
            row_index = self._find_row_by_token_in_sheet(access_token)
            if row_index is None:
                _logger.error("Access token not found in sheet")
                return request.redirect('/ach/error')

            # ✅ Step 4: Read the existing row data
            sheet = self._get_google_sheet_4()
            existing_row = sheet.row_values(row_index)

            # ✅ Step 5: Ensure the row has enough columns
            required_columns = ['BL']  # Last column to be updated
            while len(existing_row) <= column_letter_to_index(required_columns[0]):
                existing_row.append("")

            # ✅ Step 6: Update relevant columns using letter mapping
            existing_row[column_letter_to_index('BH')] = create_time  # Time stamp
            existing_row[column_letter_to_index('BI')] = create_time  # ACH submit date
            existing_row[column_letter_to_index('BJ')] = account_number_masked  # Account Number
            existing_row[column_letter_to_index('BK')] = routing_number_masked  # Routing Number
            existing_row[column_letter_to_index('BL')] = bank_name  # Bank Name

            # ✅ Step 7: Write only the updated range (BH to BL)
            sheet.update(f"BH{row_index}:BL{row_index}", [
                existing_row[column_letter_to_index('BH'):column_letter_to_index('BL') + 1]
            ])
            _logger.info("ACH data updated in row %s", row_index)

        except Exception as e:
            _logger.error("Error while processing Google Sheet logging: %s", e)
            return request.redirect('/ach/error')

        return request.redirect('/ach/success')

    # ✅ Google Sheets helper methods

    def _get_google_sheet_4(self):
        """Returns the worksheet object for CRM Google Sheet"""
        try:
            _logger.info("Starting Google Sheets connection process...")

            scope = ['https://www.googleapis.com/auth/spreadsheets']
            _logger.info("Scope defined: %s", scope)

            env = request.env()

            json_keyfile_path = env['ir.config_parameter'].sudo().get_param('json_file_path')
            _logger.info("Using credentials file: %s", json_keyfile_path)

            creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
            _logger.info("Successfully authenticated with Google API")

            client = gspread.authorize(creds)
            _logger.info("Google Sheets API authorized")

            sheet_id = env['ir.config_parameter'].sudo().get_param('google_keys_sheet_id4')
            _logger.info("Using Google Sheet ID: %s", sheet_id)

            sheet = client.open_by_key(sheet_id)
            _logger.info("Successfully opened Google Sheet")

            worksheet_name = env['ir.config_parameter'].sudo().get_param('worksheet_name_crm')
            worksheet = sheet.worksheet(worksheet_name)
            _logger.info("Opened worksheet: %s", worksheet_name)

            return worksheet

        except FileNotFoundError as e:
            _logger.error("JSON credentials file not found: %s", str(e))
        except gspread.SpreadsheetNotFound:
            _logger.error("Spreadsheet not found for ID.")
        except gspread.WorksheetNotFound:
            _logger.error("Worksheet not found.")
        except Exception as e:
            _logger.error("Failed to retrieve worksheet: %s", str(e))
            _logger.error(traceback.format_exc())
        return None

    def _find_row_by_token_in_sheet(self, token):
        """Searches for a row by access token in column A"""
        try:
            sheet = self._get_google_sheet_4()
            if not sheet:
                _logger.warning("Google Sheet not available")
                return None

            column_b = sheet.col_values(2)  # Column A
            for idx, value in enumerate(column_b, start=1):
                if value.strip() == token:
                    _logger.info("Token matched at row: %s", idx)
                    return idx

            _logger.warning("Access token not found in the sheet")
            return None
        except Exception as e:
            _logger.error("Error while searching for token in Google Sheet: %s", str(e))
            _logger.error(traceback.format_exc())
            return None

    def _log_to_google_sheets4_update_row(self, row_index, values):
        sheet = self._get_google_sheet_4()
        sheet.update(f"A{row_index}", [values])

    # ✅ Dummy Slack function – replace with your actual logic
    def _send_slack_message_ach(self, message):
        _logger.info("Pretending to send Slack message:\n%s", message)

    # ✅ Dummy log-to-summary-sheet function – replace with your actual logic
    def _log_to_google_sheets2(self, values):
        _logger.info("Pretending to log summary ACH to Google Sheet: %s", values)

    def _send_slack_message_ach(self, message):
        """Sends the given message to Slack using the configured webhook"""

        slack_channel = request.env['slack.webhook.configuration'].sudo().search([
            ('category', '=', 'ach_submission'),
            ('status', '=', 'active')
        ], limit=1)

        if not slack_channel:
            _logger.warning("No active default Slack channel found for ACH submissions.")
            return

        payload = {'text': message.strip()}
        try:
            response = requests.post(
                slack_channel.webhook,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                _logger.info("ACH Slack notification sent successfully.")
            else:
                _logger.error(f"Failed to send Slack message: {response.text}")
        except Exception as e:
            _logger.error(f"Slack message sending failed: {str(e)}")

    @http.route('/credentials', type='http', auth='public', website=True)
    def credentials_form(self, **kwargs):
        _logger.info("Accessed credentials form.")
        return request.render("lytegen_contact_details.credentials_request_form", {})

    @http.route('/credentials/success', type='http', auth='public', website=True)
    def credentials_success(self, **kwargs):
        _logger.info("Redirected to credentials success page.")
        return request.render("lytegen_contact_details.credentials_success_page", {})

    @http.route('/submit/credentials', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def submit_credentials_form(self, **post):
        _logger.info("🚀 Credentials form submission started.")
        _logger.debug("Raw POST data received: %s", post)

        try:
            # Step 1: Extract form data
            applied_position = post.get('applied_position', '').strip()
            first_name = post.get('first_name', '').strip()
            last_name = post.get('last_name', '').strip()
            phone = post.get('phone', '').strip()
            email = post.get('email', '').strip()
            create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            _logger.info("Parsed fields - Position: %s | First Name: %s | Last Name: %s | Phone: %s | Email: %s",
                         applied_position, first_name, last_name, phone, email)

            # Step 2: Compose Slack message
            message = f"""
                *New Credentials Request* 🧾
                *Position:* {applied_position}
                *Name:* {first_name} {last_name}
                *Phone:* {phone}
                *Email:* {email}
                *Time:* {create_time}
            """

            try:
                self._send_slack_message(message)
                _logger.info("✅ Slack message sent successfully.")
            except Exception as slack_error:
                _logger.error("❌ Failed to send Slack message: %s", slack_error)

            # Step 3: Create or fetch Job Position
            try:
                job = request.env['hr.job'].sudo().search([('name', '=', applied_position)], limit=1)
                if job:
                    _logger.info("🧩 Existing job found: %s (ID: %s)", job.name, job.id)
                else:
                    _logger.info("➕ No job found with name '%s'. Creating new job...", applied_position)
                    job = request.env['hr.job'].sudo().create({'name': applied_position})
                    _logger.info("✅ New job created: %s (ID: %s)", job.name, job.id)
            except Exception as job_error:
                _logger.error("❌ Failed to fetch or create job position: %s", job_error)
                job = None  # Fallback

            # Step 4: Create Employee
            try:
                full_name = f"{first_name} {last_name}".strip()
                employee_data = {
                    'name': full_name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'work_email': email,
                    'work_phone': phone,
                    'job_id': job.id if job else False,
                }

                _logger.info("📇 Creating employee with data: %s", employee_data)
                employee = request.env['hr.employee'].sudo().create(employee_data)
                _logger.info("✅ Employee created: ID %s | Name: %s", employee.id, employee.name)

            except Exception as employee_error:
                _logger.error("❌ Employee creation failed: %s", employee_error)

        except Exception as e:
            _logger.exception("🔥 Unexpected error during credentials form processing: %s", e)

        _logger.info("➡️ Redirecting user to success page.")
        return request.redirect('/credentials/success')

    def _send_slack_message(self, message):
        # Add your Slack integration here if needed
        _logger.debug("Preparing to send Slack message: %s", message)
        pass

    @http.route(['/appointment/<int:appointment_type_id>/submit'],
                type='http', auth="public", website=True, methods=["POST"])
    def appointment_form_submit(self, appointment_type_id, datetime_str, duration_str, name, phone, email,
                                staff_user_id=None, available_resource_ids=None, asked_capacity=1,
                                guest_emails_str=None, **kwargs):

        # # 🔐 Validate 2FA code before continuing
        # two_fa_code = kwargs.get('two_fa_code', '').strip()
        # auth_record = request.env['email.auth.code'].sudo().search([('code', '=', two_fa_code)], limit=1)
        #
        # if not auth_record or not auth_record.employee_id:
        #     return request.render('lytegen_contact_details.template_not_authorized', {
        #         'message': 'Unauthorized: Invalid or missing 2FA code.'
        #     })

        form_data = self._extract_form_data(kwargs)
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        """
        Handles appointment form submission, creates the appointment event, and updates related data.
        """
        # Fetch and validate the appointment type
        domain = self._appointments_base_domain(
            filter_appointment_type_ids=kwargs.get('filter_appointment_type_ids'),
            search=kwargs.get('search'),
            invite_token=kwargs.get('invite_token')
        )
        available_appointments = self._fetch_and_check_private_appointment_types(
            kwargs.get('filter_appointment_type_ids'),
            kwargs.get('filter_staff_user_ids'),
            kwargs.get('filter_resource_ids'),
            kwargs.get('invite_token'),
            domain=domain,
        )
        appointment_type = available_appointments.filtered(lambda appt: appt.id == int(appointment_type_id))
        if not appointment_type:
            raise NotFound()

        # Timezone and datetime handling
        timezone = request.session.get('timezone') or appointment_type.appointment_tz
        tz_session = pytz.timezone(timezone)
        datetime_str = unquote_plus(datetime_str)
        date_start = tz_session.localize(fields.Datetime.from_string(datetime_str)).astimezone(pytz.utc).replace(
            tzinfo=None)
        duration = float(duration_str)
        date_end = date_start + relativedelta(hours=duration)
        invite_token = kwargs.get('invite_token')
        phone = f"+{form_data['country_code']}{phone}"
        # Skip resource and staff availability checks
        staff_user = request.env['res.users'].sudo().search(
            [('id', '=', int(staff_user_id))]) if staff_user_id else None
        resources = request.env['appointment.resource'].sudo().browse(
            json.loads(unquote_plus(available_resource_ids or '[]')))

        # Handle guests if allowed
        guests = None
        if appointment_type.allow_guests and guest_emails_str:
            guests = request.env['calendar.event'].sudo()._find_or_create_partners(guest_emails_str)

        # Handle customer
        customer = request.env['res.partner'].sudo().search([('phone', 'ilike', phone[-10:])], limit=1)
        event = request.env['calendar.event'].sudo().search(
            [('phone_number', 'ilike', customer.phone)],
            order='create_date desc',
            limit=1
        )
        if customer:


            _logger.info("Updating existing customer with ID: %s", customer.id)
            customer.sudo().write({
                'name': name,
                'email': email,
                'lang': request.lang.code,
                'website': form_data['test_field'],
                'language_2': form_data['language'],
                'average_bill_2': form_data['average_bill'],
                'address_2': form_data['street_address'],
                'state_2': form_data['state'],
                'city_2': form_data['city'],
                'postal_code_2': form_data['zip_code'],
                # 'opener_2': form_data['opener'],
                # 'setter_2': form_data['setter'],
                'sales_consultant_2': form_data['sales_consultant'],
                'date_booked': datetime.now().date(),
                'date_appointment': event.date_appointment,
                'time_appointment': event.time_appointment,
                'qa_outcome': form_data['qa_outcome'],
                'first_name': form_data['name'],
                'last_name': form_data['last_name'],
                'phone': phone,
            })
        else:
            _logger.info("Creating a new customer with phone: %s", phone)
            customer = request.env['res.partner'].sudo().create({
                'name': name,
                'phone': phone,
                'email': email,
                'lang': request.lang.code,
                'website': form_data['test_field'],
                'language_2': form_data['language'],
                'average_bill_2': form_data['average_bill'],
                'address_2': form_data['street_address'],
                'state_2': form_data['state'],
                'city_2': form_data['city'],
                'postal_code_2': form_data['zip_code'],
                # 'opener_2': form_data['opener'],
                # 'setter_2': form_data['setter'],
                'sales_consultant_2': form_data['sales_consultant'],
                'date_booked': datetime.now().date(),
                'date_appointment': event.date_appointment,
                'time_appointment': event.time_appointment,
                'qa_outcome': form_data['qa_outcome'],
                'first_name': form_data['name'],
                'last_name': form_data['last_name'],

                })

        # Handle form answers
        partner_inputs = {}
        answer_input_values = []
        base_answer_input_vals = {
            'appointment_type_ids': [(6, 0, [appointment_type.id])],
        }

        for question in appointment_type.question_ids.filtered(lambda q: q.id in partner_inputs.keys()):
            if question.question_type in ['checkbox', 'radio', 'select', 'char', 'text']:
                answer_input_values.append(dict(base_answer_input_vals, question_id=question.id))

        # Prepare booking line values for resources
        booking_line_values = [
            {'appointment_resource_id': resource.id, 'capacity_reserved': asked_capacity,
             'capacity_used': asked_capacity}
            for resource in resources
        ]

        # Create or retrieve appointment invite
        if invite_token:
            appointment_invite = request.env['appointment.invite'].sudo().search([('access_token', '=', invite_token)],
                                                                                 limit=1)
        else:
            appointment_invite = request.env['appointment.invite'].sudo().create({
                'access_token': request.env['ir.sequence'].sudo().next_by_code('appointment.invite') or '',
                'appointment_type_ids': [(6, 0, [appointment_type.id])],
            })


        # Pass all processed data to the submission handler
        result = self._handle_appointment_form_submission(
            appointment_type, date_start, date_end, duration, answer_input_values, name,
            customer, appointment_invite, guests, staff_user, asked_capacity, booking_line_values
        )

        # ✅ Attach the validated employee to the calendar event
        calendar_event = request.env['calendar.event'].sudo().search([], order='create_date desc', limit=1)
        if calendar_event:
            calendar_event.write({
                'source_creation_employee_id': auth_record.employee_id.id
            })
        # Handling language conversion
        language_mapping = {
            'en': 'English',
            'es': 'Spanish'
        }
        event_language = language_mapping.get(form_data.get('language', ''),
                                              'Other Language')  # Default to 'Other Language'

        # Fetch the calendar event created
        calendar_event = request.env['calendar.event'].sudo().search([], order='create_date desc', limit=1)
        if calendar_event:
            event_name = calendar_event.name or ''
            event_phone = calendar_event.phone_number or ''
            event_email = calendar_event.email or ''
            event_street = form_data['street_address'] or ''
            event_state = form_data['state'] or ''
            event_city = form_data['city'] or ''
            event_zip = form_data['zip_code'] or ''
            event_date_appointment = calendar_event.date_appointment or ''
            # event_time_appointment = calendar_event.time_appointment or ''  # Using start time of the event
            event_time_appointment = calendar_event.formatted_time_appointment or ''  # Using start time of the event
            event_date_booked = calendar_event.date_booked or ''  # Assuming the event creation date is the booking date
            event_access_token = calendar_event.access_token or ''
            # event_name = calendar_event.full_name or ''
            event_name = f"{name} {form_data.get('last_name', '')}".strip()
            event_appointment_type = calendar_event.appointment_type_id.name or ''
            event_id = calendar_event.id or ''
            # event_language = form_data['language'] or ''
            event_language = event_language or ''

            event_submission_time = datetime.now().strftime('%H:%M:%S')
            create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


            event_date_appointment_str = event_date_appointment.strftime("%m/%d/%Y") if isinstance(event_date_appointment, date) else event_date_appointment
            event_date_booked_str = event_date_booked.strftime("%m/%d/%Y") if isinstance(event_date_booked, date) else event_date_booked
            # partner = request.env['res.partner'].sudo().search([('phone', '=', calendar_event.phone_number)], limit=1)

            # Search for partner based on phone number
            _logger.info("Searching for partner with phone number: %s", phone)
            partner = request.env['res.partner'].sudo().search([('phone', 'ilike', phone[-10:])], limit=1)


            if partner:
                _logger.info(
                    "Checking if setter_2, opener_2, appointment_status, auditor_notes, source_file, map_link, and qa_outcome exist for partner ID: %s",
                    partner.id)
                setter_2 = getattr(partner, 'setter_2', '') or ''
                opener_2 = getattr(partner, 'opener_2', '') or ''
                source_file = getattr(partner, 'origin_file', '') or ''
                appointment_status = getattr(partner, 'appointment_status', '') or ''
                auditor_notes = getattr(partner, 'auditor_notes', '') or ''
                map_link = getattr(partner, 'map_link', '') or ''
                qa_outcome = getattr(partner, 'qa_outcome', '') or ''
                first_name = getattr(partner, 'first_name', '') or ''
                last_name = getattr(partner, 'last_name', '') or ''
            else:
                setter_2 = ''
                opener_2 = ''
                appointment_status = ''
                auditor_notes = ''
                source_file = ''
                map_link = ''
                qa_outcome = ''
                first_name = ''
                last_name = ''

            # Log final values
            _logger.info(
                "Final values after validation: setter_2=%s, opener_2=%s, appointment_status=%s, auditor_notes=%s, source_file=%s, map_link=%s, qa_outcome=%s, first_name=%s, last_name=%s",
                setter_2, opener_2, appointment_status, auditor_notes, source_file, map_link, qa_outcome, first_name, last_name)

            # Warn if fields are still empty
            if not setter_2:
                _logger.warning("setter_2 is still empty or False after assignment!")

            if not opener_2:
                _logger.warning("opener_2 is still empty or False after assignment!")

            if not appointment_status:
                _logger.warning("appointment_status is still empty or False after assignment!")

            if not auditor_notes:
                _logger.warning("auditor_notes is still empty or False after assignment!")

            if not source_file:
                _logger.warning("source_file is still empty or False after assignment!")

            if not map_link:
                _logger.warning("map_link is still empty or False after assignment!")

            if not qa_outcome:
                _logger.warning("qa_outcome is still empty or False after assignment!")

            if not first_name:
                _logger.warning("first_name is still empty or False after assignment!")

            if not last_name:
                _logger.warning("last_name is still empty or False after assignment!")

            # event_date_appointment_str = event_date_appointment.strftime("%Y-%m-%d") if isinstance(
            #     event_date_appointment, (datetime, datetime.date)) else event_date_appointment
            # event_date_booked_str = event_date_booked.strftime("%Y-%m-%d") if isinstance(event_date_booked, (
            # datetime, datetime.date)) else event_date_booked
            # event_time_appointment_str = str(event_time_appointment)  # Ensure this is a string
            _logger.info("Updating the calendar event with ID: %s", calendar_event.id)
            self._update_calendar_event(calendar_event, kwargs, phone, email, name)

            self._update_appointment_resources(calendar_event, appointment_type_id)

            try:
                # Log data to Google Sheets (without raw account/routing numbers)
                # self._log_to_google_sheets2([
                #     full_name, phone, bank_name, account_number_masked, routing_number_masked
                # ])
                self._log_to_google_sheets3([
                    event_access_token, '', event_name, name, last_name, phone, email, event_street, event_city, event_state, event_zip, event_date_appointment_str, event_time_appointment, event_date_booked_str, event_submission_time, event_language, opener_2, setter_2, appointment_status, "", "", map_link, qa_outcome, source_file, auditor_notes
                ])
                self._log_to_google_sheets4([
                    create_time, event_access_token, event_id, name, name, last_name, phone, email, event_street, event_city,
                    event_state, event_zip, event_date_appointment_str, event_time_appointment, event_date_booked_str,
                    event_submission_time, event_language, opener_2, setter_2, appointment_status, "", "", map_link,
                    qa_outcome, source_file, auditor_notes
                ])
                _logger.info("SP1 Auditing logged to Google Sheets successfully")
            except Exception as e:
                _logger.error("Failed to log SP1 Auditing to Google Sheets: %s", e)

            timezone = request.session.get('timezone', 'UTC')
            tz = pytz.timezone(timezone)

            # Convert calendar_event.start (assumed in UTC) to local time
            local_time = calendar_event.start.astimezone(tz)
            start_hour_float = local_time.hour + (local_time.minute / 60.0)

            weekday = local_time.weekday() + 1

            _logger.info(
                "Looking for slot with start_hour: %s, weekday: %s, appointment_type_id: %s",
                start_hour_float, weekday, appointment_type_id
            )

            slot = request.env['appointment.slot'].sudo().search([
                ('start_hour', '=', start_hour_float),
                ('appointment_type_id', '=', appointment_type_id),
                ('weekday', '=', str(weekday)),
            ], limit=1)

            if not slot:
                _logger.warning("No slot found for start_hour: %s, weekday: %s, appointment_type_id: %s",
                                start_hour_float, weekday, appointment_type_id)

            # if slot.resource_ids:
            #     resource_to_remove = slot.resource_ids[0]
            #     slot.write({'resource_ids': [(3, resource_to_remove.id)]})
            #     _logger.info("Removed resource %s from slot ID: %s", resource_to_remove.name, slot.id)
            # else:
            #     _logger.warning("No resources available to remove from slot ID: %s", slot.id)
        else:
            _logger.warning("No calendar event found after submission.")

        # Ensure no duplicate partners exist for the given phone number
        # self._remove_duplicate_partners(phone)

        # ✅ Now send the Slack message
        if calendar_event:
            calendar_event._send_slack_message()
        return result

    def _update_appointment_resources(self, calendar_event, appointment_type_id):
        """
        Updates the resources for the given calendar event based on its schedule and weekday.
        """
        if not calendar_event.start:
            _logger.warning("Calendar event has no start date; skipping resource update.")
            return

        try:
            # Convert the start datetime to the user's timezone
            user_tz = request.env.user.tz or 'UTC'
            tz = pytz.timezone(user_tz)
            local_start = pytz.utc.localize(calendar_event.start).astimezone(tz)

            # Adjust time dynamically based on appointment type or specific logic
            adjustment_hours = 2  # Replace with logic to calculate if dynamic adjustment is needed
            adjusted_time = local_start + relativedelta(hours=adjustment_hours)

            # Determine weekday and adjusted start time
            weekday = adjusted_time.weekday() + 1  # Monday=0 in Python, adjust to Odoo's weekday convention
            start_time = adjusted_time.hour + (adjusted_time.minute / 60.0)

            _logger.info(
                "Searching for slot with weekday: %s, appointment_type_id: %s, adjusted start_hour: %s",
                weekday, appointment_type_id, start_time
            )

            # Search for appointment slots with the same weekday and appointment type
            slot = request.env['appointment.slot'].sudo().search([
                ('appointment_type_id', '=', appointment_type_id),
                ('weekday', '=', weekday),
                ('start_hour', '=', start_time),
            ], limit=1)

            if slot:
                # Use the resource IDs from the slot directly for validation
                valid_resource_ids = slot.resource_ids.ids

                if valid_resource_ids:
                    # Assign the resources from the slot to the calendar event
                    calendar_event.sudo().write({
                        'appointment_resource_ids': [(6, 0, valid_resource_ids)]
                    })
                    _logger.info(
                        "Assigned resources %s to calendar event ID: %s",
                        ', '.join(str(res_id) for res_id in valid_resource_ids), calendar_event.id
                    )
                else:
                    _logger.error("No valid resources found for slot ID: %s", slot.id)
            else:
                _logger.warning(
                    "No slot found for weekday: %s, appointment_type_id: %s, adjusted start_hour: %s",
                    weekday, appointment_type_id, start_time
                )

        except Exception as e:
            _logger.error("Error updating appointment resources: %s", str(e))






    def _handle_appointment_form_submission(
            self, appointment_type,
            date_start, date_end, duration,  # appointment boundaries
            answer_input_values, name, customer, appointment_invite, guests=None,  # customer info
            staff_user=None, asked_capacity=1, booking_line_values=None  # appointment staff / resources
    ):
        """
        Handles the creation of the appointment event and redirects to the confirmation page.
        """
        event = request.env['calendar.event'].with_context(
            mail_notify_author=True,
            mail_create_nolog=True,
            mail_create_nosubscribe=True,
            allowed_company_ids=self._get_allowed_companies(staff_user or appointment_type.create_uid).ids,
        ).sudo().create({
            'appointment_answer_input_ids': [Command.create(vals) for vals in answer_input_values],
            **appointment_type._prepare_calendar_event_values(
                asked_capacity, booking_line_values, duration,
                appointment_invite, guests, name, customer, staff_user, date_start, date_end
            )
        })
        return request.redirect(
            f"/calendar/view/{event.access_token}?partner_id={customer.id}&{keep_query('*', state='new')}")



    def _extract_form_data(self, kwargs):
        """
        Extract and return form data from the submission.
        """
        # fields = [
        #     'phone', 'name', 'email', 'test_field', 'language', 'average_bill', 'street_address',
        #     'state', 'city', 'zip_code', 'opener', 'setter', 'sales_consultant',
        #     'date_booked', 'date_appointment', 'time_appointment', 'qa_outcome', 'event_id'
        # ]
        fields = [
            'phone', 'name', 'email', 'test_field', 'language', 'average_bill',
            'street_address', 'state', 'city', 'zip_code', 'opener', 'setter',
            'sales_consultant', 'date_booked', 'date_appointment', 'time_appointment',
            'qa_outcome', 'event_id', 'property_not_shaded', 'high_bill', 'low_bill', 'average_bill_checkbox',
            'homeowner', 'spanish_speaker_requested', 'ground_mount_requested',
            'one_hour_arrival', 'customer_engagement_score', 'additional_notes_section', 'appointment_notes', 'first_name', 'last_name','country_code'
        ]
        return {field: kwargs.get(field) for field in fields}

    def _find_or_create_partner(self, form_data):
        """
        Find the most recent partner by phone who is associated with a calendar event,
        or create a new one if no such partner exists.
        """
        phone = form_data.get('phone')
        if not phone:
            _logger.warning("Phone number is required but not provided.")
            return None

        # Search for the most recent partner associated with a calendar event
        calendar_event = request.env['calendar.event'].sudo().search(
            [('partner_ids.phone', '=', phone)], order='create_date desc', limit=1
        )

        # Exclude Administrator from the partner_ids
        partner = None
        if calendar_event and calendar_event.partner_ids:
            partners = calendar_event.partner_ids.filtered(lambda p: p.name != 'Administrator')
            partner = partners[-1] if partners else None

        if partner:
            _logger.info("Updating existing partner with ID: %s", partner.id)
            partner.write({
                'name': form_data['name'],
                'email': form_data['email'],
                'website': form_data['test_field'],
                'language_2': form_data['language'],
                'average_bill_2': form_data['average_bill'],
                'address_2': form_data['street_address'],
                'state_2': form_data['state'],
                'city_2': form_data['city'],
                'postal_code_2': form_data['zip_code'],
                'opener_2': form_data['opener'],
                'setter_2': form_data['setter'],
                'sales_consultant_2': form_data['sales_consultant'],
                'date_booked': form_data['date_booked'],
                'date_appointment': form_data['date_appointment'],
                'time_appointment': form_data['time_appointment'],
                'qa_outcome': form_data['qa_outcome'],
            })
        else:
            _logger.info("No partner with calendar events found for phone: %s. Creating a new partner.", phone)
            partner = request.env['res.partner'].sudo().create({
                'name': form_data['name'],
                'phone': phone,
                'email': form_data['email'],
                'website': form_data['test_field'],
                'language_2': form_data['language'],
                'average_bill_2': form_data['average_bill'],
                'address_2': form_data['street_address'],
                'state_2': form_data['state'],
                'city_2': form_data['city'],
                'postal_code_2': form_data['zip_code'],
                'opener_2': form_data['opener'],
                'setter_2': form_data['setter'],
                'sales_consultant_2': form_data['sales_consultant'],
                'date_booked': form_data['date_booked'],
                'date_appointment': form_data['date_appointment'],
                'time_appointment': form_data['time_appointment'],
                'qa_outcome': form_data['qa_outcome'],
            })

        return partner


    def _update_calendar_event(self, calendar_event, form_data, phone, email, name):
        """
        Update the specified calendar event with the provided data and update region and city after the initial write.
        """
        if not calendar_event:
            _logger.warning("No calendar event provided to update.")
            return

        # Convert boolean fields from "on" to True and handle None as False
        boolean_fields = [
            'property_not_shaded', 'high_bill', 'low_bill', 'average_bill_checkbox',
            'homeowner', 'spanish_speaker_requested', 'ground_mount_requested',
            'one_hour_arrival', 'additional_notes_section'
        ]
        for field in boolean_fields:
            form_data[field] = form_data.get(field) == "on"

        _logger.info("Updating the calendar event with ID: %s", calendar_event.id)
        customer = request.env['res.partner'].sudo().search([('phone', '=', phone)], limit=1)


        # Write the processed data to the calendar event
        calendar_event.write({
            'full_name': name,
            'phone_number': phone,
            'email': email,
            'language': form_data.get('language'),
            'average_bill': form_data.get('average_bill'),
            'street_address': form_data.get('street_address'),
            'state': form_data.get('state'),
            'city': form_data.get('city'),
            'zip_code': form_data.get('zip_code'),
            # Processed Boolean Fields
            'property_not_shaded': form_data.get('property_not_shaded'),
            'high_bill': form_data.get('high_bill'),
            'low_bill': form_data.get('low_bill'),
            'average_bill_checkbox': form_data.get('average_bill_checkbox'),
            'homeowner': form_data.get('homeowner'),
            'spanish_speaker_requested': form_data.get('spanish_speaker_requested'),
            'ground_mount_requested': form_data.get('ground_mount_requested'),
            'one_hour_arrival': form_data.get('one_hour_arrival'),
            'additional_notes_section': form_data.get('additional_notes_section'),
            # Additional fields can be added here
            'qa_notes': form_data.get('qa_notes'),
            'appointment_setter_notes': form_data.get('appointment_notes'),
            'opener_2': customer.opener_2,
            'setter_2': customer.setter_2,
            'source_file': customer.origin_file,
        })

        # Update city and region_name based on the zip_code after the initial write
        zip_code = form_data.get('zip_code')
        if zip_code:
            region = self._match_region_by_zip(zip_code)
            if region:
                calendar_event.write({
                    # 'city': region.city,  # Auto-fill city based on region
                    'region_name': region.id,  # Auto-fill region_name (Many2one field)
                })
                _logger.info("Updated city and region_name for event ID %s based on zip_code %s.", calendar_event.id,
                             zip_code)
            else:
                calendar_event.write({
                    # 'city': None,
                    'region_name': None,
                })
                _logger.warning(
                    "No matching region found for zip_code %s. Cleared city and region_name for event ID %s.", zip_code,
                    calendar_event.id)

    def _match_region_by_zip(self, zip_code):
        """Match the ZIP Code to the region and return the region."""
        Region = request.env['res.region']  # Use request.env instead of self.env
        # return Region.search([('zip_codes_ids.name', '=', zip_code)], limit=1)
        return Region.search([('zip_codes', '=', zip_code)], limit=1)

    def _remove_duplicate_partners(self, phone):
        """
        Remove duplicate partners with the same phone number, keeping the most recent one.
        """
        if not phone:
            return

        partners = request.env['res.partner'].sudo().search(
            [('phone', '=', phone)], order='create_date desc'
        )
        if len(partners) > 1:
            _logger.info("Found %d duplicate partners for phone: %s. Removing the oldest ones.", len(partners), phone)
            partners[1:].unlink()

    def _send_slack_message_credit(self, message):
        """Sends the given message to Slack using the configured webhook"""

        slack_channel = request.env['slack.webhook.configuration'].sudo().search([
            ('category', '=', 'credit_check_submission'),
            ('status', '=', 'active')
        ], limit=1)

        if not slack_channel:
            _logger.warning("No active default Slack channel found for ACH submissions.")
            return

        payload = {'text': message.strip()}
        try:
            response = requests.post(
                slack_channel.webhook,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                _logger.info("ACH Slack notification sent successfully.")
            else:
                _logger.error(f"Failed to send Slack message: {response.text}")
        except Exception as e:
            _logger.error(f"Slack message sending failed: {str(e)}")



