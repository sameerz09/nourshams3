from odoo import models, fields, api, exceptions, _
from pytz import timezone, UTC
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, AccessError
from odoo.exceptions import UserError

import re
import logging
import traceback
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import logging

_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    task_ids = fields.One2many('project.task', 'calendar_event_id', string='Related Tasks')

    region_name = fields.Many2one(
        'res.region',
        string='Region Name',
        help='Select the region associated with this calendar event.'
    )

    current_status = fields.Selection(
        selection=[
            ('yes', 'Yes'),
            ('no', 'No'),
            ('maybe', 'Maybe'),
            ('needs_action', 'Needs Action'),
        ],
        string='Attending',
        tracking=True,  # Track changes
    )


    appointment_status_2 = fields.Selection(
        selection=[
            ('booked', 'Booked'),
            ('follow_up_required', 'Follow up required'),
            ('closed', 'Closed'),
            ('invalid', 'Invalid'),
            ('cancelled', 'Cancelled'),
            ('no_consultant', 'No Consultant'),
        ],
        tracking=True,
        string='Appointment Status',
    )

    appointment_state = fields.Selection(
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

    appointment_resource_ids = fields.Many2many(
        comodel_name='resource.resource',
        relation='calendar_event_appointments_resource_rel',
        column1='event_id',
        column2='appointment_resource_id',
        string="Appointment Resources",
        help="Appointment resources associated with this calendar event.",
        tracking=True,  # Track changes
    )

    start_weekday = fields.Integer(
        string="Start Weekday",
        compute="_compute_start_weekday",
        store=True,
        help="Day of the week extracted from the start datetime field, where Monday is 0 and Sunday is 6.",
        tracking=True,  # Track changes
    )

    # Self Quality Check Fields
    property_not_shaded = fields.Boolean(
        string="Property is not heavily shaded?",
        help="Indicates whether the property is not heavily shaded.",
        tracking=True,  # Track changes
    )
    high_bill = fields.Boolean(
        string="High bill?",
        help="Indicates if the customer has a high bill.",
        tracking=True,  # Track changes
    )
    low_bill = fields.Boolean(
        string="Low bill?",
        help="Indicates if the customer has a low bill.",
        tracking=True,  # Track changes
    )
    average_bill_checkbox = fields.Boolean(
        string="Average bill?",
        help="Indicates if the customer has an average bill.",
        tracking=True,  # Track changes
    )
    homeowner = fields.Boolean(
        string="Homeowner",
        help="Indicates if the customer is a homeowner.",
        tracking=True,  # Track changes
    )
    spanish_speaker_requested = fields.Boolean(
        string="Spanish Speaker Requested",
        help="Indicates if a Spanish-speaking representative is requested.",
        tracking=True,  # Track changes
    )
    ground_mount_requested = fields.Boolean(
        string="Ground Mount Requested",
        help="Indicates if ground mount installation is requested.",
        tracking=True,  # Track changes
    )
    one_hour_arrival = fields.Boolean(
        string="One-hour arrival window for the appointment",
        help="Indicates if a one-hour arrival window is agreed upon.",
        tracking=True,  # Track changes
    )
    customer_engagement_score = fields.Integer(
        string="Customer Engagement Score (10 b)",
        help="Customer engagement score out of 10.",
        default=0,
        tracking=True,  # Track changes
    )
    additional_notes_section = fields.Boolean(
        string="Additional Notes Section",
        help="Indicates if there are additional notes.",
        tracking=True,  # Track changes
    )
    appointment_name = fields.Char(string="Appointment Name")
    design_ids = fields.Many2many(
        comodel_name='design',  # Related model
        relation='calendar_event_design_rel',  # New unique relation table name
        column1='calendar_event',  # Column for crm.lead IDs
        column2='design_id',  # Column for design IDs
        string='Designs'
    )

    project_ids = fields.Many2many(
        comodel_name='project.project',  # Related model
        relation='calendar_event_project_rel',  # New unique relation table name
        column1='calendar_event_id',  # Column for crm.lead IDs
        column2='project_id',  # Column for project.project IDs
        string='Projects'
    )
    sold_design_id = fields.Many2one(
        'design',
        string='Sold Design',
        tracking=True,
        ondelete='set null'  # Ensures if the design is deleted, the field is reset to null
    )

    sold_design_link_id = fields.Many2one(
        'design.link',
        string='Sold Design Link',
        tracking=True,
        ondelete='set null'  # Ensures if the design is deleted, the field is reset to null
    )
    formatted_time_appointment = fields.Char(string="Formatted Time", compute="_compute_formatted_time", store=True)

    appointment_type_id = fields.Many2one('appointment.type', 'Calendar', tracking=True)
    # Credit Check Firm Fields
    postal_code_credit_check = fields.Char(
        string="Postal Code", required=False
    )
    first_name_credit_check = fields.Char(
        string="First Name", required=False
    )
    last_name_credit_check = fields.Char(
        string="Last Name", required=False
    )
    phone_credit_check = fields.Char(
        string="Phone", required=False
    )
    email_credit_check = fields.Char(
        string="Email", required=False
    )
    annual_income_credit_check = fields.Float(
        string="Annual Income ($)", required=False
    )
    other_household_income_credit_check = fields.Float(
        string="Other Household Income"
    )
    ssn_tin_credit_check = fields.Char(
        string="SSN/TIN", required=False
    )
    date_of_birth_credit_check = fields.Date(
        string="Date of Birth", required=False
    )
    cosigner_needed_credit_check = fields.Boolean(
        string="Cosigner Needed?", required=False
    )
    cosigner_dob_credit_check = fields.Date(
        string="Cosigner DOB"
    )
    address_credit_check = fields.Char(
        string="Address", required=False
    )
    city_credit_check = fields.Char(
        string="City", required=False
    )
    state_credit_check = fields.Char(
        string="State", required=False
    )
    name = fields.Char(string="Name", compute="_compute_customer_name", store=False)

    # name = fields.Char(string="First Name", index=True, default_export_compatible=True)

    @api.depends('phone_number')
    def _compute_customer_name(self):
        for event in self:
            # event.first_name = ""
            # event.last_name = ""
            event.name = ""

            if event.phone_number:
                customer = self.env['res.partner'].sudo().search([('phone', '=', event.phone_number)], limit=1)
                if customer:
                    first_name = customer.name
                    last_name = customer.last_name

                    # event.first_name = first_name
                    # event.last_name = last_name
                    event.name = f"{first_name} {last_name}".strip()


    # @api.depends('time_appointment')
    # def _compute_formatted_time(self):
    #     for record in self:
    #         if record.time_appointment:
    #             hours = int(record.time_appointment)
    #             minutes = int((record.time_appointment - hours) * 60)
    #             record.formatted_time_appointment = f"{hours:02}:{minutes:02}:00"
    #         else:
    #             record.formatted_time_appointment = "00:00:00"
    @api.depends('time_appointment')
    def _compute_formatted_time(self):
        for record in self:
            if record.time_appointment:
                hours = int(record.time_appointment)
                minutes = int((record.time_appointment - hours) * 60)
                record.formatted_time_appointment = f"{hours:02}:{minutes:02}"
            else:
                record.formatted_time_appointment = "00:00"

    @api.onchange('sales_consultant_id')
    def _onchange_sales_consultant(self):
        """Update the Sales Consultant in the partner when it is changed in the event."""
        if self.phone_number and self.sales_consultant_id:
            partner = self.env['res.partner'].search([('phone', '=', self.phone_number)], limit=1)
            if partner:
                partner.sales_consultant_id = self.sales_consultant_id
                _logger.info("Updated sales_consultant_id for partner %s based on phone number %s", partner.name,
                             self.phone_number)

    def update_appointment_resources(self):
        for event in self:
            if event.start:
                # Convert the start datetime to the user's timezone
                user_tz = self.env.user.tz or 'UTC'
                start_date = fields.Datetime.context_timestamp(event, event.start)
                # Calculate the weekday (Monday=0, Sunday=6)
                weekday = start_date.weekday()
                _logger.info(f"Event '{event.name}' starts on weekday: {weekday}")

                # Search for appointment slots with the same weekday
                matching_slots = self.env['appointment.slot'].search([
                    ('weekday', '=', str(weekday))
                ])
                _logger.info(f"Found {len(matching_slots)} matching slots for event '{event.name}'")

                # Collect all unique appointment resources from matching slots
                appointment_resources = self.env['resource.resource'].browse()
                for slot in matching_slots:
                    appointment_resources |= slot.resource_ids
                    resource_names = ', '.join(slot.resource_ids.mapped('name'))
                    _logger.info(f"Slot ID {slot.id} has resources: {resource_names}")

                # Update the event's appointment_resource_ids field
                event.appointment_resource_ids = [(6, 0, appointment_resources.ids)]
                _logger.info(
                    f"Updated event '{event.name}' with resources: {', '.join(appointment_resources.mapped('name'))}")
            else:
                _logger.warning(f"Event '{event.name}' has no start date; skipping resource update.")

    @api.depends('start')
    def _compute_start_weekday(self):
        for event in self:
            if event.start:
                # Convert the start datetime to a date object
                start_date = fields.Datetime.from_string(event.start).date()
                # Get the day of the week as an integer (Monday=0, Sunday=6)
                event.start_weekday = start_date.weekday() + 1
            else:
                event.start_weekday = False

    @api.model
    def _slots_generate(self, start, stop, timezone):
        slots = super()._slots_generate(start, stop, timezone)
        _logger.info("Generated slots before modification: %s", slots)
        for slot in slots:
            slot['available_resources'] = []
        _logger.info("Slots after modification: %s", slots)
        return slots

    @api.depends('start', 'stop', 'resource_ids')
    def _compute_on_leave_resource_ids(self):
        for event in self:
            _logger.info(f"Marking resources as unavailable for event {event.name}")
            event.on_leave_resource_ids = event.resource_ids

    # =============================
    # Appointment Information Fields
    # =============================
    date_booked = fields.Date(
        string="Date Booked",
        default=fields.Date.context_today,  # Automatically set to today's date
        required=False,
        readonly=True,  # Make it readonly to prevent manual edits
        tracking=True  # Track changes
    )


    date_appointment = fields.Date(
        string="Appointment Date",
        compute="_compute_appointment_details",
        store=True,
        tracking=True  # Track changes
    )

    time_appointment = fields.Float(
        string="Appointment Time",
        compute="_compute_appointment_details",
        store=True,
        tracking=True  # Track changes
    )

    sales_consultant = fields.Char(
        string="Sales Consultant",
        required=False,
        tracking=True  # Track changes
    )

    map_link = fields.Char(
        string="Map Link",
        help="Hyperlink to the map location",
        tracking=True  # Track changes
    )

    sales_consultant_notes = fields.Text(
        string="Sales Consultant Notes",
        tracking=True  # Track changes
    )
    appointment_setter_notes = fields.Text(
        string="Appointment Setter Notes",
        tracking=True  # Track changes
    )

    confirmation_status = fields.Selection(
        [
            ('unconfirmed', 'Unconfirmed'),
            ('confirmed', 'Confirmed'),
            ('dq', 'DQ'),
            ('requested_rescheduling', 'Requested Rescheduling'),
            # ('dead_lead', 'Dead Lead'),
        ],
        string="Confirmation Status",
        required=False,
        tracking=True,  # Track changes in chatter
        default='unconfirmed'  # Set default value
    )


    appointment_outcome = fields.Selection(
        [
            ('no_show', 'No Show'),
            ('signed_deal', 'Signed Deal'),
            ('not_presented_follow_up', 'Not Presented Follow Up'),
            ('presented_follow_up', 'Presented Follow Up'),
            ('turned_away', 'Turned Away'),
            ('not_able_to_make_it', 'Not Able to Make It'),
            ('dq', 'DQ')
        ],
        string="Appointment Outcome",
        required=False,
        tracking=True  # Track changes
    )



    @api.constrains('appointment_outcome')
    def _check_mandatory_activity_log(self):
        for event in self:
            # Check if the outcome is updated from empty to any value
            if event.appointment_outcome and self.env.user.has_group('lytegen_contact_details.group_sales_consultant'):
                # Check if the notes field is empty
                if not event.sales_consultant_notes:
                    raise ValidationError(_(
                        "You must leave a note in the 'Sales Consultant Notes' field before updating the 'Appointment Outcome' field."
                    ))


    # full_name = fields.Char(
    #     string="Full Name",
    #     required=False,
    #     tracking=True  # Track changes
    # )
    full_name = fields.Char(
        string="Full Name",
        compute="_compute_full_name",
        store=True,
        tracking=True
    )

    phone_number = fields.Char(
        string='Phone Number',
        placeholder='Enter 10-digit phone number',
        tracking=True  # Track changes
    )

    email = fields.Char(
        string="Email",
        required=False,
        tracking=True  # Track changes
    )

    street_address = fields.Char(
        string="Street Address",
        tracking=True  # Track changes
    )

    street_address_visible = fields.Boolean(
        string="Is Street Address Visible",
        # compute='_compute_street_address_visible',
        default=False,
        store=True,
    )

    @api.depends('name')
    def _compute_full_name(self):
        for record in self:
            record.full_name = record.name or ''

    @api.model
    def update_street_address_visibility(self):
        """Scheduled action to update street_address_visible
        based on whether the event starts within the next 3 hours.
        """
        current_time = fields.Datetime.now()
        # Search for records where `street_address_visible` is False or True (i.e., all)
        events = self.search([])  # You can filter if needed

        for event in events:
            if event.start:
                if (event.start - current_time) <= timedelta(hours=2):
                    event.street_address_visible = True
                else:
                    event.street_address_visible = False

    city = fields.Char(
        string="City",
        tracking=True  # Track changes
    )

    state = fields.Char(
        string="State",
        tracking=True  # Track changes
    )

    zip_code = fields.Char(
        string="Zip Code",
        tracking=True  # Track changes
    )

    average_bill = fields.Float(
        string="Average Bill",
        tracking=True  # Track changes
    )

    language = fields.Selection(
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
        tracking=True  # Track changes
    )
    language_display = fields.Char(
        string="Language Display",
        # compute="_compute_language_display",
        store=True,
        help="Displays the selected language name."
    )

    # =============================
    # Design and QA Fields
    # =============================
    shading = fields.Boolean(string="Shading", tracking=True)
    high_bill = fields.Float(string="High Bill", tracking=True)
    low_bill = fields.Float(string="Low Bill", tracking=True)
    average_bill = fields.Float(string="Average Bill", tracking=True)
    homeowner = fields.Boolean(string="Homeowner", tracking=True)
    spanish_speaker_requested = fields.Boolean(string="Spanish Speaker Requested", tracking=True)
    indian = fields.Boolean(string="Indian", tracking=True)
    ground_mount_requested = fields.Boolean(string="Ground Mount Requested", tracking=True)
    one_hour_window_mentioned = fields.Boolean(string="One-hour Arrival Window Mentioned", tracking=True)
    program_explained = fields.Boolean(string="Program and Core Offer Explained", tracking=True)
    credit_score_650_plus = fields.Boolean(string="Credit Score 650+", tracking=True)
    no_bankruptcies = fields.Boolean(string="No Bankruptcies", tracking=True)
    no_foreclosures = fields.Boolean(string="No Foreclosures", tracking=True)
    minimum_market_set_rate_bill = fields.Boolean(string="Minimum Market Set Rate Bill", tracking=True)
    address_confirmed = fields.Boolean(string="Address Confirmed", tracking=True)
    homeowners_present_mentioned = fields.Boolean(string="Mentioned All Homeowners Must Be Present", tracking=True)
    customer_engagement_score = fields.Selection(
        [(str(i), str(i)) for i in range(1, 11)],
        string="Customer Engagement Score",
        tracking=True  # Track changes
    )
    additional_notes = fields.Text(string="Additional Notes", tracking=True)
    qa_outcome = fields.Selection(
        [
            ('approved', 'Approved'),
            ('dq', 'DQ - Invalid'),
            ('dq_viable', 'DQ - Viable'),
            ('duplicate', 'Duplicate')

        ],
        string="QA Outcome",
        required=False,
        tracking=True  # Track changes
    )
    is_qa_outcome = fields.Boolean(
        string="Is QA Outcome",
        default=True,
        tracking=True
    )

    qa_outcome_set_time = fields.Datetime(
        string="QA Outcome Set Time"
    )

    shading_2 = fields.Selection([
        ('no_shade', 'No Shade'),
        ('medium_shade', 'Medium Shade'),
        ('heavily_shaded', 'Heavily Shaded')
    ], string="Shading")

    homeowner_2 = fields.Selection([
        ('yes', 'Yes'),
        ('authorized_relative', 'Authorized Relative')
    ], string="Homeowner")

    qa_notes = fields.Text(
        string="QA Notes",
        tracking=True  # Track changes
    )
    # =============================
    # Onboard Project Disposition Lead Fields
    # =============================
    reroof = fields.Boolean(string="Reroof", tracking=True)
    mount = fields.Boolean(string="Mount", tracking=True)
    mpu = fields.Boolean(string="MPU", tracking=True)
    hoa = fields.Boolean(string="HOA", tracking=True)
    gated_access = fields.Boolean(string="Gated Access", tracking=True)
    battery = fields.Boolean(string="Battery", tracking=True)
    utility_bill_holder = fields.Char(string="Utility Bill Holder", tracking=True)
    provider = fields.Char(string="Provider", tracking=True)
    finance_type = fields.Char(string="Finance Type", tracking=True)
    installer = fields.Char(string="Installer", tracking=True)
    lead_origin = fields.Char(string="Lead Origin", tracking=True)
    requested_site_survey = fields.Boolean(string="Requested Site Survey", tracking=True)
    custom_ss_times = fields.Char(string="Custom SS Times", tracking=True)
    usage_upload = fields.Binary(string="Usage (Upload Picture)", tracking=True)
    bill_pics = fields.Binary(string="Bill Pics", tracking=True)
    additional_files = fields.Binary(string="Additional Files", tracking=True)
    notes = fields.Text(string="Notes", tracking=True)
    special_requests = fields.Text(string="Special Requests", tracking=True)
    system_size = fields.Float(string="System Size", tracking=True)
    announce_win = fields.Boolean(string="Announce Win", tracking=True)

    design_ids = fields.Many2many(
        'design',
        'calendar_event_design_rel',
        'event_id',
        'design_id',
        string='Designs',
        tracking=True  # Track changes
    )

    selected_design_id = fields.Many2one(
        'design',
        string="Selected Design",
        domain="[('id', 'in', design_ids)]",  # Restricts choices to those in design_ids
    )

    selected_design_name = fields.Char(
        help="Selected Design",
        string="Selected Design",
        tracking=True
        # domain="[('id', 'in', design_ids)]",  # Restricts choices to those in design_ids
    )

    is_show_appointment_qa = fields.Boolean(
        string="Show Appointment QA",
        default=False,
        compute="_show_tabs_calendar_event",
        store=False,
        tracking=True  # Track changes
    )

    is_show_onboarding_request = fields.Boolean(
        string="Show Onboarding Request",
        default=False,
        compute="_show_tabs_calendar_event",
        store=False,
        tracking=True  # Track changes
    )

    is_show_questions = fields.Boolean(
        string="Show Question",
        default=False,
        compute="_show_tabs_calendar_event",
        store=False,
        tracking=True  # Track changes
    )

    setter = fields.Char(
        string="Setter",
        help="Enter the name of the Setter for this contact.",
        tracking=True  # Track changes
    )

    date_sit = fields.Date(
        string="Date Sit",
        tracking=True  # Track changes
    )

    date_design_requested = fields.Date(
        string="Date Design Requested",
        tracking=True  # Track changes
    )

    date_signed = fields.Date(
        string="Date Signed",
        tracking=True  # Track changes
    )
    sales_consultant_employee_id = fields.Many2one(
        'hr.employee',
        string="Sales Consultant (Employee)",
        domain=lambda self: self._default_domain_sales_consultant_employee(),
        help="Sales Consultant assigned to this event (Employee)."
    )
    opener = fields.Many2one(
        'hr.employee',
        string="Opener",
        domain=lambda self: self._default_domain_opener(),
        help="Opener assigned to this event (Employee)."
    )

    setter = fields.Many2one(
        'hr.employee',
        string="SP1 Setter",
        domain=lambda self: self._default_domain_setter(),
        help="Setter assigned to this event (Employee)."
    )
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

    sales_consultant_employee_id = fields.Many2one(
        'hr.employee',
        string="Sales Consultant (Employee)",
        domain=lambda self: self._default_domain_sales_consultant_employee(),
        help="Sales Consultant assigned to this event (Employee)."
    )

    source_file = fields.Char(
        string="Source File",
        tracking=True
    )

    source_creation_employee_id = fields.Many2one(
        'hr.employee',
        string='Source Creation Employee',
        tracking=True,
    )

    @api.onchange('qa_outcome')
    def _onchange_qa_outcome(self):
        if self.qa_outcome:
            self.qa_outcome_set_time = fields.Datetime.now()
            self.is_qa_outcome = True

    def _cron_reset_is_qa_outcome(self):
        expiration_time = fields.Datetime.now() - timedelta(hours=36)
        outdated_events = self.search([
            ('qa_outcome_set_time', '<=', expiration_time),
            ('is_qa_outcome', '=', True),
        ])
        for event in outdated_events:
            event.is_qa_outcome = False


    @api.model
    def _ensure_job_position_exists(self, job_name):
        """
        Ensure a job position exists. If not, create it.
        :param job_name: Name of the job position (e.g., 'Opener', 'Setter', 'Sales Consultant')
        :return: The job position record.
        """
        JobPosition = self.env['hr.job']
        job_position = JobPosition.search([('name', '=', job_name)], limit=1)
        if not job_position:
            job_position = JobPosition.create({'name': job_name})
        return job_position

    @api.model
    def _default_domain_opener(self):
        """Return only employees with the job position 'Opener'."""
        self._ensure_job_position_exists('Opener')  # Ensure the job position exists
        return [('job_id.name', '=', 'Opener')]

    @api.model
    def _default_domain_setter(self):
        """Return only employees with the job position 'Setter'."""
        self._ensure_job_position_exists('Setter')  # Ensure the job position exists
        return [('job_id.name', '=', 'Setter')]

    @api.model
    def _default_domain_sales_consultant_employee(self):
        """Return only employees with the job position 'Sales Consultant'."""
        self._ensure_job_position_exists('Sales Consultant')  # Ensure the job position exists
        return [('job_id.name', '=', 'Sales Consultant')]



    def default_domin_sale_consultant(self):
        user_id = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('lytegen_contact_details.group_sales_consultant') and not user.has_group('lytegen_contact_details.group_user_role_dispatch_manager') and not user.has_group('lytegen_contact_details.group_user_role_admin'):
                user_id.append(user.id)
        return [('id', 'in', user_id)]



    # resource_ids = fields.Many2many(
    #     'resource.resource',  # Replace with the appropriate model for resources
    #
    #     string="Additional Resources",
    #     help="Resources allocated for this event"
    # )
    sales_consultant_id = fields.Many2one(
        'res.users',
        string="Sales Consultant",
        domain=default_domin_sale_consultant,
        help="Sales Consultant assigned to this event."
    )

    is_sales_consultant = fields.Boolean(
        compute="_compute_user_roles",
        string="Sales Consultant",
        store=False
    )
    is_sales_manager = fields.Boolean(
        compute="_compute_user_roles",
        string="Sales Manager",
        store=False,
    )
    is_designer = fields.Boolean(
        compute="_compute_user_roles",
        string="Designer",
        store=False,
    )
    is_dispatch_manager = fields.Boolean(
        compute="_compute_user_roles",
        string="Dispatch Manager",
        store=False,
    )
    is_confirmation_specialist = fields.Boolean(
        compute="_compute_user_roles",
        string="Confirmation Specialist",
        store=False,
    )
    is_not_admin = fields.Boolean(
        compute="_compute_user_roles",
        string="Not Admin",
        store=False
    )
    is_auditor = fields.Boolean(
        compute="_compute_user_roles",
        string="Auditor",
        store=False
    )

    def _compute_user_roles(self):
        user = self.env.user
        check_sales_consultant_group = user.has_group('lytegen_contact_details.group_sales_consultant')
        check_sales_manager_group = user.has_group('lytegen_contact_details.group_sales_manager')
        check_designer_group = user.has_group('lytegen_contact_details.group_designer')
        check_dispatch_manager_group = user.has_group('lytegen_contact_details.group_user_role_dispatch_manager')
        check_confirmation_specialist_group = user.has_group(
            'lytegen_contact_details.group_user_role_confirmation_specialist')
        check_admin_group = user.has_group('lytegen_contact_details.group_user_role_admin')
        check_full_admin_group = user.has_group('lytegen_contact_details.group_user_hide_menu')
        check_auditor_group = user.has_group('lytegen_contact_details.group_user_role_auditor')

        for record in self:
            record.is_sales_consultant = check_sales_consultant_group
            record.is_sales_manager = check_sales_manager_group
            record.is_designer = check_designer_group
            record.is_dispatch_manager = check_dispatch_manager_group
            record.is_confirmation_specialist = check_confirmation_specialist_group
            record.is_not_admin = not (check_admin_group or check_full_admin_group)
            record.is_auditor = check_auditor_group

    def _assign_sales_consultant(self):
        """Assign a sales consultant based on the event's ZIP Code."""
        for event in self:
            if event.zip_code:  # Changed from `zip` to `zip_code`
                _logger.info("Searching for region with ZIP Code: %s", event.zip_code)
                region = self.env['res.region'].sudo().search([('zip_codes', 'ilike', event.zip_code)], limit=1)
                if region:
                    _logger.info("Region found: %s. Searching for sales consultant...", region.name)
                    consultant = self.env['res.users'].sudo().search([
                        ('region_ids', 'in', region.ids)
                    ], limit=1)
                    if consultant:
                        _logger.info("Assigning Sales Consultant ID: %s to Event ID: %s", consultant.id, event.id)
                        event.sales_consultant_id = consultant
                    else:
                        _logger.warning("No sales consultant found for region: %s", region.name)
                else:
                    _logger.warning("No region found with ZIP Code: %s", event.zip_code)



    @api.model_create_multi
    def create(self, vals_list):
        """Assign a sales consultant automatically and set city based on ZIP code.
        Restrict users in the 'Confirmation Specialist' and 'Auditor' groups from creating events.
        Additionally, after creation, update CRM leads with the new sales consultant and, if
        appointment_outcome is 'presented_follow_up', create a new CRM lead.
        """
        # Check if the current user belongs to any restricted groups
        if self.env.user.has_group('lytegen_contact_details.group_user_role_confirmation_specialist') or \
                self.env.user.has_group('lytegen_contact_details.group_user_role_auditor') or \
                self.env.user.has_group('lytegen_contact_details.group_designer') or \
                self.env.user.has_group('lytegen_contact_details.group_sales_consultant') or \
                self.env.user.has_group('lytegen_contact_details.group_user_role_dispatch_manager') or \
                self.env.user.has_group('lytegen_contact_details.group_sales_manager'):
            raise exceptions.UserError(
                _("You do not have the permission to create calendar events.")
            )

        # Auto-fill city and region based on ZIP code
        for vals in vals_list:
            if vals.get('zip_code'):
                region = self._match_region_by_zip(vals['zip_code'])
                if region:
                    vals['city'] = region.city  # Auto-fill the city based on the region
                    vals['region_name'] = region.id

        # Create the events and assign a sales consultant
        events = super(CalendarEvent, self).create(vals_list)
        events._assign_sales_consultant()

        # Post-creation: update CRM leads and/or create a new CRM lead based on event values
        for event in events:
            # Update CRM leads with the new sales_consultant_id if provided
            if event.sales_consultant_id:
                new_sales_consultant_id = event.sales_consultant_id.id
                _logger.info("Detected sales_consultant_id for event ID %s: %s", event.id, new_sales_consultant_id)
                if event.phone_number:
                    _logger.info("Searching for CRM Leads with Phone Number: %s", event.phone_number)
                    leads = self.env['crm.lead'].search([('phone', '=', event.phone_number)])
                    _logger.info("Found %s leads with matching phone number: %s", len(leads), event.phone_number)
                    if leads:
                        _logger.info("Attempting to update 'sales_consultant_id' for Leads: %s", leads.ids)
                        try:
                            leads.write({'sales_consultant_id': new_sales_consultant_id})
                            _logger.info("Successfully updated leads for event ID: %s", event.id)
                        except Exception as e:
                            _logger.error("Error updating leads for event ID %s: %s", event.id, str(e))
                    else:
                        _logger.warning("No leads found with phone number: %s for event ID: %s", event.phone_number,
                                        event.id)
                else:
                    _logger.warning("Skipping CRM Lead update as no phone number is available for event ID: %s",
                                    event.id)
            else:
                _logger.debug("Skipping sales_consultant_id update for event ID: %s", event.id)

            # Check if appointment_outcome is set to 'presented_follow_up'
            if event.appointment_outcome == 'presented_follow_up':
                _logger.info("Appointment outcome set to 'presented_follow_up' for event ID: %s. Creating CRM lead.",
                             event.id)
                try:
                    # Wrap lead creation in a savepoint to prevent transaction abort on error
                    with self.env.cr.savepoint():
                        self._create_crm_lead_from_event(event)
                    _logger.info("Successfully created CRM lead for event ID: %s", event.id)
                except Exception as e:
                    _logger.error("Error creating CRM lead for event ID %s: %s", event.id, str(e))
            else:
                _logger.debug("No CRM lead creation required for event ID: %s", event.id)

        return events

        # Existing logic for auto-filling fields
        for vals in vals_list:
            if vals.get('zip_code'):
                region = self._match_region_by_zip(vals['zip_code'])
                if region:
                    vals['city'] = region.city  # Auto-fill the city based on the region
                    vals['region_name'] = region.id

        # Create the events and assign a sales consultant
        events = super(CalendarEvent, self).create(vals_list)
        events._assign_sales_consultant()
        return events



    def unlink(self):
        """Prevent users in specific groups from deleting events."""
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
                raise exceptions.UserError(
                    _("You do not have the permission to delete calendar events.")
                )
        return super(CalendarEvent, self).unlink()

    def _match_region_by_zip(self, zip_code):
        """Match the ZIP Code to the region and return the region."""
        Region = self.env['res.region']
        region = Region.search([
            ('zip_codes_ids.name', '=', zip_code)
        ], limit=1)
        return region



    project_ids = fields.Many2one('project.project', string="Assigned Project")

    def create_task_for_no_show(self):
        """Create a task in the selected project if the outcome is No Show."""
        for record in self:
            _logger.info(f"Checking project assignment for event: {record.name}")

            # Check if project_ids is set
            if not record.project_ids:
                _logger.warning(f"No project assigned for event: {record.name}. Showing a warning to the user.")
                raise UserError(_("No project is assigned to this meeting. Please assign a project before proceeding."))

            # Handle multiple projects assigned
            if len(record.project_ids) > 1:
                _logger.warning(
                    f"Multiple projects assigned to event: {record.name}. Using the first project: {record.project_ids[0].name}")
                project = record.project_ids[0]  # Use the first project
            else:
                project = record.project_ids[0]

            _logger.info(f"Selected project: {project.name} for event: {record.name}")

            # Search for the 'Confirmation Specialist' tag or create it if not found
            tag_name = "Confirmation Specialist"
            tag = self.env['project.tags'].search([('name', '=', tag_name)], limit=1)

            if not tag:
                _logger.info(f"Tag '{tag_name}' not found. Creating a new tag.")
                tag = self.env['project.tags'].create({'name': tag_name})
                _logger.info(f"Tag '{tag_name}' created with ID: {tag.id}")
            else:
                _logger.info(f"Tag '{tag_name}' found with ID: {tag.id}")

            # Task values
            task_vals = {
                'name': f'Task for No Show: {record.name}',
                'project_id': project.id,
                # Assign user using user_ids (many2many field)
                'user_ids': [(4, record.user_id.id)] if record.user_id else False,
                'description': f'Task created because the appointment outcome was set to No Show for meeting: {record.name}',
                # Add the Confirmation Specialist tag
                'tag_ids': [(4, tag.id)],  # Add the tag to the task
            }

            _logger.info(f"Task values to create: {task_vals}")
            try:
                task = self.env['project.task'].create(task_vals)
                _logger.info(f"Task created successfully in project '{project.name}' with ID: {task.id}")
            except Exception as e:
                _logger.error(f"Error while creating task for No Show: {str(e)}")
                raise UserError(_("Error while creating the task: %s") % str(e))

    def write(self, vals):
        """Override write to create a task if the outcome is No Show."""
        _logger.info(f"-----> Entering write() method in calendar.event for event IDs: {self.ids}")
        _logger.info(f"-----> Incoming values: {vals}")

        # Get the initial state of records before update
        previous_outcomes = {event.id: event.appointment_outcome for event in self}
        _logger.info(f"Previous outcomes before update: {previous_outcomes}")

        # Call super to update the records
        res = super(CalendarEvent, self).write(vals)

        # Check if appointment_outcome is updated and set to 'no_show'
        if 'appointment_outcome' in vals:
            for record in self:
                previous_outcome = previous_outcomes.get(record.id)
                new_outcome = vals['appointment_outcome']

                _logger.info(f"Previous outcome: {previous_outcome}, New outcome: {new_outcome} for event: {record.name}")

                # Create a task if the new outcome is 'no_show' and it was changed
                if new_outcome == 'no_show' and previous_outcome != 'no_show':
                    _logger.info(f"Appointment outcome set to 'No Show' for meeting: {record.name}")
                    record.create_task_for_no_show()
                else:
                    _logger.info(f"No task created because the outcome is not 'No Show' or it was already set.")

        _logger.info(f"Appointment update completed successfully for event: {self.mapped('name')}")
        return res

    @api.onchange(
        'qa_outcome',
        'qa_notes',
        'source_file',
        'map_link',
        'appointment_status',
        'opener_2',
        'setter_2',
        'appointment_setter_notes',
        'appointment_outcome',
        'sales_consultant_notes',
        'sales_consultant_id'
    )
    def _onchange_log_to_google_sheets(self):
        """Log changes to Google Sheets when specific fields are updated."""
        for event in self:
            if event.create_date and (datetime.now() - event.create_date) > timedelta(minutes=1):
                event._log_qa_details_to_google_sheets(event)
                event._update_master_sheet_log_qa_details_to_google_sheets(event)

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
            # worksheet = sheet.worksheet("Sheet1")

            access_token = event.access_token
            if not access_token:
                _logger.warning("Event access token is missing for Event ID: %s", event.id)
                return False

            cell_list = worksheet.col_values(1)
            if access_token in cell_list:
                row_index = cell_list.index(access_token) + 1
                columns = {
                    "W": dict(event._fields['qa_outcome'].selection).get(event.qa_outcome, ''),
                    "Y": event.qa_notes,
                    "X": event.source_file,
                    "V": event.map_link,
                    "Q": event.opener_2,
                    "R": event.setter_2,
                    "U": event.appointment_status
                }
                for col, value in columns.items():
                    cell_reference = f"{col}{row_index}"
                    worksheet.update(range_name=cell_reference, values=[[str(value)]])
            else:
                worksheet.append_row(
                    [access_token, '', '', '', '', str(event.qa_outcome), str(event.qa_notes), str(event.source_file),
                     str(event.map_link), str(event.appointment_status)]
                )

            _logger.info("Successfully logged fields to Google Sheets.")
            return True

        except Exception as e:
            _logger.error("Failed to log fields to Google Sheets: %s", str(e))
            _logger.error(traceback.format_exc())
            return False

    def _update_master_sheet_log_qa_details_to_google_sheets(self, event):
        """Update the master Google Sheet with QA and appointment details if 'event_access_token' exists in Column B."""
        try:
            _logger.info("Logging fields to Google Sheets for Event ID: %s", event.id)

            env = self.env
            json_keyfile_path = env['ir.config_parameter'].sudo().get_param('json_file_path')
            if not json_keyfile_path:
                _logger.error("Google Sheets JSON keyfile path is missing.")
                return False

            creds = ServiceAccountCredentials.from_json_keyfile_name(
                json_keyfile_path, ['https://www.googleapis.com/auth/spreadsheets']
            )
            client = gspread.authorize(creds)

            sheet_id = env['ir.config_parameter'].sudo().get_param('google_keys_sheet_id4')
            if not sheet_id:
                _logger.error("Google Sheet ID is missing.")
                return False

            worksheet_name = env['ir.config_parameter'].sudo().get_param('worksheet_name_crm')
            if not worksheet_name:
                _logger.error("Worksheet name is missing.")
                return False

            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.worksheet(worksheet_name)

            access_token = event.access_token
            if not access_token:
                _logger.warning("Event access token is missing for Event ID: %s", event.id)
                return False

            access_token = access_token.strip()
            col_b_values = [cell.strip() for cell in worksheet.col_values(2)]  # Column B (Appointment ID)

            if access_token in col_b_values:
                row_index = col_b_values.index(access_token) + 1
                update_columns = {
                    "R": event.opener_2,
                    "S": event.setter_2,
                    "T": event.sales_consultant_id.name if event.sales_consultant_id else event.sales_consultant,
                    "U": event.appointment_status,
                    "V": event.map_link,
                    "W": event.source_file,
                    "X": event.qa_outcome,
                    "Y": event.qa_notes,
                    "Z": event.appointment_status,
                    "AA": event.appointment_setter_notes,
                    "AB": event.appointment_outcome,
                    "AC": event.sales_consultant_notes,
                }

                for col_letter, value in update_columns.items():
                    cell_ref = f"{col_letter}{row_index}"
                    worksheet.update(range_name=cell_ref, values=[[str(value or '')]])
                _logger.info("Updated row %s for access_token (Column B): %s", row_index, access_token)
            else:
                # Fill columns A to Q (17 columns) before writing values starting from R to AC
                empty_padding = [''] * 16  # A to P (A is '', B is access_token)
                new_row = [''] + [access_token] + empty_padding + [
                    str(event.opener_2 or ''),
                    str(event.setter_2 or ''),
                    str(event.sales_consultant_id.name if event.sales_consultant_id else event.sales_consultant or ''),
                    str(event.appointment_status or ''),
                    str(event.map_link or ''),
                    str(event.source_file or ''),
                    str(event.qa_outcome or ''),
                    str(event.qa_notes or ''),
                    str(event.appointment_status or ''),
                    str(event.appointment_setter_notes or ''),
                    str(event.appointment_outcome or ''),
                    str(event.sales_consultant_notes or '')
                ]
                worksheet.append_row(new_row)
                _logger.info("Appended new row with access_token in Column B: %s", access_token)

            return True

        except Exception as e:
            _logger.error("Failed to log fields to Google Sheets: %s", str(e))
            _logger.error(traceback.format_exc())
            return False

    def _create_crm_lead_from_event(self, event):
        """Helper method to create a CRM lead from a calendar event."""
        # Search for any partner in the system (adjust domain as needed)
        partner = self.env['res.partner'].search([], limit=1)

        lead_vals = {
            'name': event.name or 'New Lead from Appointment',
            'partner_id': partner.id if partner else False,
            'phone': partner.phone if partner and partner.phone else '',
            # Optionally add additional fields, for example:
            # 'description': event.description,
        }

        # Find the CRM stage named "Appointments"
        new_stage = self.env['crm.stage'].search([('name', '=', 'Appointments')], limit=1)
        if new_stage:
            lead_vals['stage_id'] = new_stage.id

        # Create the new CRM lead record
        self.env['crm.lead'].sudo().create(lead_vals)




    def _show_tabs_calendar_event(self):
        user = self.env.user
        for record in self:
            # if user.has_group('lytegen_contact_details.group_sales_consultant') and not user.has_group('lytegen_contact_details.group_user_role_dispatch_manager'):
                record.is_show_appointment_qa = True
                record.is_show_onboarding_request = True
                record.is_show_questions = True
            # elif user.has_group('lytegen_contact_details.group_designer') and not user.has_group('lytegen_contact_details.group_sales_consultant') and not user.has_group('lytegen_contact_details.group_user_role_dispatch_manager'):
            #     record.is_show_onboarding_request = False
            #     record.is_show_appointment_qa = False
            #     record.is_show_questions = False
            # elif (user.has_group('lytegen_contact_details.group_user_role_confirmation_specialist') or user.has_group('lytegen_contact_details.group_user_role_auditor')) and not user.has_group('lytegen_contact_details.group_user_role_dispatch_manager'):
            #     record.is_show_onboarding_request = False
            #     record.is_show_appointment_qa = True
            #     record.is_show_questions = False
            # else:
            #     record.is_show_onboarding_request = True
            #     record.is_show_appointment_qa = True
            #     record.is_show_questions = True

    # @api.depends('start')
    # def _compute_appointment_details(self):
    #     for record in self:
    #         if record.start:
    #             # Extract date and time from the `start` field
    #             record.date_appointment = record.start.date()
    #             record.time_appointment = record.start.hour + record.start.minute / 60.0
    #         else:
    #             record.date_appointment = False
    #             record.time_appointment = 0.0

    @staticmethod
    def _get_timezone_selection():
        """Get all available timezone options."""
        return [(tz, tz) for tz in timezone.all_timezones]

    @api.depends('start', 'appointment_type_id')
    def _compute_appointment_details(self):
        for record in self:
            if record.start:
                # Get timezone from the related appointment type
                appointment_tz = record.appointment_type_id and record.appointment_type_id.appointment_tz or 'UTC'
                local_tz = timezone(appointment_tz)

                # Convert `start` from UTC to the appointment type's timezone
                utc_dt = fields.Datetime.from_string(record.start).replace(tzinfo=UTC)  # Parse and set as UTC
                local_dt = utc_dt.astimezone(local_tz)  # Convert to the appointment type's timezone

                # Extract date and time in the local timezone
                record.date_appointment = local_dt.date()
                record.time_appointment = local_dt.hour + local_dt.minute / 60.0
            else:
                record.date_appointment = False
                record.time_appointment = 0.0

    # def _compute_sales_consultant(self):
    #     for record in self:
    #         user = self.env.user
    #         check_sales_consultant_group = user.has_group('lytegen_contact_details.group_sales_consultant')
    #         self.is_sales_consultant = True if check_sales_consultant_group else False

    @api.model
    def web_search_read(self, domain, offset=0, limit=None, order=None, **kwargs):
        if not order or 'sequence' in order:
            order = 'id desc'
        return super(CalendarEvent, self).web_search_read(domain, offset=offset, limit=limit, order=order, **kwargs)
    
    @api.onchange('sales_consultant_id')
    def onchange_sales_consultant(self):
        if self.sales_consultant_id and self.sales_consultant_id.partner_id:
            if self.sales_consultant_id.partner_id not in self.partner_ids:
                self.partner_ids += self.sales_consultant_id.partner_id

    def action_create_design_onboarding_requests(self):
        """Retrieve and Return Data to the Web Interface."""
        self.ensure_one()  # Ensure the method runs only on one record

        # Collect the required data
        data = {
            'consultant_name': self.consultant_name,
            'customer_first_name': self.customer_first_name,
            'customer_last_name': self.customer_last_name,
            'customer_phone': self.customer_phone,
            'email': self.email,
            'street_address': self.street_address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'notes': self.notes,
            'special_requests': self.special_requests,
        }

        # Return the data as an alert popup
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Retrieved Data",
                'message': f"""
                    Consultant Name: {data['consultant_name']}<br/>
                    Customer Name: {data['customer_first_name']} {data['customer_last_name']}<br/>
                    Phone: {data['customer_phone']}<br/>
                    Email: {data['email']}<br/>
                    Address: {data['street_address']}, {data['city']}, {data['state']} {data['postal_code']}<br/>
                    Notes: {data['notes']}<br/>
                    Special Requests: {data['special_requests']}
                """,
                'sticky': False,  # The notification disappears automatically
            }
        }

    @api.model
    def create_confirmation_tasks(self):
        now = fields.Datetime.now()

        events = self.search([
            ('start', '<=', now),
            ('sales_consultant_employee_id', '=', False),
        ])

        project = self.env['project.project'].search([('name', '=', 'Field Service')], limit=1)

        # Get users in the confirmation specialist group
        group = self.env.ref('lytegen_contact_details.group_user_role_confirmation_specialist')
        users = group.users

        for event in events:
            # Find or create partner
            partner = self.env['res.partner'].search([('name', '=', event.name)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({'name': event.name})

            # Build calendar event link
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            calendar_link = f"{base_url}/web#id={event.id}&model=calendar.event&view_type=form"

            self.env['project.task'].create({
                'name': f'Reschedule task for {event.name}',
                'project_id': project.id,
                'user_ids': [(6, 0, users.ids)],
                'partner_id': partner.id,
                'calendar_event_id': event.id,
                'description': f"""<p>Reschedule appointment</p>
            <p>Access record: <a href="{calendar_link}" target="_blank">Click here</a></p>
            <p>Phone Number: {event.phone_number or 'N/A'}</p>""",
            })