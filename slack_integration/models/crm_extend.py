from importlib.metadata import requires

from odoo import models, api, exceptions, _ ,fields
from odoo.exceptions import ValidationError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Define new fields with tracking enabled
    first_name = fields.Char(string="Customer First Name", tracking=True, )
    last_name = fields.Char(string="Customer Last Name", tracking=True)
    email_2 = fields.Char(string="Email", tracking=True)
    sold_design_link = fields.Char(string="Sold Design Link", tracking=True)
    street2 = fields.Char(string="Street Address", tracking=True)
    state = fields.Char(string="State", tracking=True)
    city = fields.Char(string="City", tracking=True)
    postal_code = fields.Char(string="Postal Code", tracking=True)
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
        tracking=True,

    )
    average_bill = fields.Char(string="Average Bill", tracking=True)
    readymode_disposition = fields.Char(string="Readymode Disposition", tracking=True,)
    opener = fields.Char(string="Opener", tracking=True ,)
    closer = fields.Char(string="Closer", tracking=True ,)
    map_link = fields.Char(string="Map Link", tracking=True ,)
    date_transferred = fields.Datetime(string="Date Transferred", tracking=True,)
    additional_contacts = fields.Many2many(
        'res.partner',  # Related model
        'crm_lead_res_partner_rel',  # Relation table name
        'lead_id',  # Column for this model in the relation table
        'partner_id',  # Column for the related model in the relation table
        string='Additional Contacts',
        tracking=True
    )

    test = fields.Char(string="Test", required=False, tracking=True)
    setter = fields.Char(string="Setter", tracking=True ,)
    sales_consultant = fields.Char(string="Sales Consultant", tracking=True ,)
    bps_number = fields.Char(string="BPS Number", tracking=True,)
    sales_rep_email = fields.Char(string="Sales Rep Email", tracking=True,)
    financer = fields.Selection(
        string="Financer",
        selection=[
            ('everbright', 'Everbright'),
            ('enfin', 'Enfin')
        ],
        help="Select the financer",
        tracking=True,
    )
    pipeline_stage = fields.Selection(
        string="Pipeline Stage",
        selection=[
            ('welcome_call', 'Welcome call'),
            ('site_survey', 'Site survey'),
            ('missing_ntp', 'Missing NTP'),
            ('updates', 'Updates'),
            ('install_ready', 'Install ready'),
            ('installed', 'Installed'),
            ('post_install_work', 'Post install work'),
            ('pto', 'PTO'),
            ('change_order', 'Change order'),
            ('retention', 'Retention'),
            ('scalation', 'Scalation')
        ],
        help="Select the pipeline stage",
        tracking=True,
        default='welcome_call',
    )

    @api.model
    def web_search_read(self, domain, offset=0, limit=None, order=None, **kwargs):
        current_user = self.env.user

        # Print current user and groups (debug)
        print(f"🔍 Current User: {current_user.name}")
        print("🔐 Current User Groups:")
        for group in current_user.groups_id:
            print(f"   - {group.name} ({group.full_name})")

        # If user is Full Admin, allow all
        if current_user.has_group('lytegen_contact_details.group_user_hide_menu'):
            return super().web_search_read(domain, offset=offset, limit=limit, order=order, **kwargs)

        # Stage-to-groups mapping
        stage_access = {
            'welcome_call': [
                'lytegen_contact_details.group_ntp_coordinators',
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
            'site_survey': [
                'lytegen_contact_details.group_ntp_coordinators',
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
            'missing_ntp': [
                'lytegen_contact_details.group_ntp_coordinators',
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
            'updates': [
                'lytegen_contact_details.group_account_coordinators',
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
            'install_ready': [
                'lytegen_contact_details.group_account_coordinators',
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
            'installed': [
                'lytegen_contact_details.group_account_coordinators',
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
            'post_install_work': [
                'lytegen_contact_details.group_account_coordinators',
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
            'pto': [
                'lytegen_contact_details.group_account_coordinators',
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
            'change_order': [
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
            'retention': [
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
            'scalation': [
                'lytegen_contact_details.group_change_coordinators',
                'lytegen_contact_details.group_sales_consultant',
            ],
        }

        # Collect allowed stages for the user
        allowed_stages = []
        for stage, groups in stage_access.items():
            if any(current_user.has_group(group) for group in groups):
                allowed_stages.append(stage)

        print(f"✅ Allowed pipeline stages: {allowed_stages}")

        # Apply filtering
        domain += [('pipeline_stage', 'in', allowed_stages)]

        return super().web_search_read(domain, offset=offset, limit=limit, order=order, **kwargs)

    def default_domin_sale_consultant(self):
        user_id = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('lytegen_contact_details.group_sales_consultant') and not user.has_group(
                    'lytegen_contact_details.group_user_role_dispatch_manager') and not user.has_group(
                    'lytegen_contact_details.group_user_role_admin'):
                user_id.append(user.id)
        return [('id', 'in', user_id)]

    sales_consultant_employee_id = fields.Many2one(
        'hr.employee',
        string="Sales Consultant (Employee)",
        domain=lambda self: self._default_domain_sales_consultant_employee(),
        help="Sales Consultant assigned to this event (Employee)."
    )

    @api.model
    def _default_domain_sales_consultant_employee(self):
        """Return only employees with the job position 'Sales Consultant'."""
        return [('job_id.name', '=', 'Sales Consultant')]
    average_bill = fields.Float(string="Average Bill", tracking=True)
    date_sit = fields.Date(string="Date Sit", tracking=True,required = False)
    date_design_requested = fields.Date(string="Date Design Requested", tracking=True ,required = True)
    date_signed = fields.Date(string="Date Signed", tracking=True ,required = True)
    date_booked = fields.Date(string="Date Booked", tracking=True ,required = True)
    date_appointment = fields.Date(string="Date Appointment", tracking=True ,required = True)
    phone = fields.Char(required=False)
    time_appointment = fields.Float(
        string="Time Appointment",
        help="Time in hours (e.g., 14.5 for 2:30 PM)",
        tracking=True,required = True
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

        # Mapping: stage name <-> pipeline_stage

    STAGE_TO_PIPELINE = {
        'Welcome call': 'welcome_call',
        'Site survey': 'site_survey',
        'Missing NTP': 'missing_ntp',
        'Updates': 'updates',
        'Install ready': 'install_ready',
        'Installed': 'installed',
        'Post install work': 'post_install_work',
        'PTO': 'pto',
        'Change order': 'change_order',
        'Retention': 'retention',
        'Scalation': 'scalation',
    }
    PIPELINE_TO_STAGE = {v: k for k, v in STAGE_TO_PIPELINE.items()}

    def write(self, vals):
        if self.env.context.get('from_partner_sync'):
            # Bypass any special logic if context is set
            return super().create(vals)
        # Sync between stage_id and pipeline_stage
        if 'stage_id' in vals:
            stage = self.env['crm.stage'].browse(vals['stage_id'])
            mapped_pipeline = self.STAGE_TO_PIPELINE.get(stage.name)
            if mapped_pipeline:
                vals['pipeline_stage'] = mapped_pipeline

        elif 'pipeline_stage' in vals:
            stage_name = self.PIPELINE_TO_STAGE.get(vals['pipeline_stage'])
            if stage_name:
                stage = self.env['crm.stage'].search([('name', '=', stage_name)], limit=1)
                if stage:
                    vals['stage_id'] = stage.id

        current_user = self.env.user

        # Full Admins skip all checks
        if current_user.has_group('lytegen_contact_details.group_user_hide_menu'):
            return super().write(vals)

        # Mapping: pipeline_stage → allowed editor groups
        STAGE_EDIT_GROUPS = {
            'welcome_call': ['lytegen_contact_details.group_change_coordinators',
                             'lytegen_contact_details.group_ntp_coordinators'],
            'site_survey': ['lytegen_contact_details.group_change_coordinators',
                            'lytegen_contact_details.group_ntp_coordinators'],
            'missing_ntp': ['lytegen_contact_details.group_change_coordinators',
                            'lytegen_contact_details.group_ntp_coordinators'],
            'updates': ['lytegen_contact_details.group_change_coordinators',
                        'lytegen_contact_details.group_account_coordinators'],
            'install_ready': ['lytegen_contact_details.group_change_coordinators',
                              'lytegen_contact_details.group_account_coordinators'],
            'installed': ['lytegen_contact_details.group_change_coordinators',
                          'lytegen_contact_details.group_account_coordinators'],
            'post_install_work': ['lytegen_contact_details.group_change_coordinators',
                                  'lytegen_contact_details.group_account_coordinators'],
            'pto': ['lytegen_contact_details.group_change_coordinators',
                    'lytegen_contact_details.group_account_coordinators'],
            'change_order': ['lytegen_contact_details.group_change_coordinators','lytegen_contact_details.group_ntp_coordinators','lytegen_contact_details.group_account_coordinators'],
            'retention': ['lytegen_contact_details.group_change_coordinators','lytegen_contact_details.group_ntp_coordinators','lytegen_contact_details.group_account_coordinators'],
            'scalation': ['lytegen_contact_details.group_change_coordinators','lytegen_contact_details.group_ntp_coordinators','lytegen_contact_details.group_account_coordinators'],
        }

        NTP_STAGES = ['welcome_call', 'site_survey', 'missing_ntp', 'updates','change_order','retention','scalation']
        CHANGE_COORDINATOR_STAGES = ['welcome_call', 'site_survey', 'missing_ntp', 'updates', 'install_ready',
                                     'installed', 'post_install_work', 'pto', 'change_order', 'retention', 'scalation']
        ACCOUNT_COORDINATOR_STAGES = ['pto', 'post_install_work', 'installed', 'install_ready', 'updates','change_order','retention','scalation']

        selection_dict = dict(self.fields_get(allfields=['pipeline_stage'])['pipeline_stage']['selection'])

        for record in self:
            current_stage = record.pipeline_stage
            new_stage = vals.get('pipeline_stage', current_stage)

            allowed_groups = STAGE_EDIT_GROUPS.get(current_stage, [])
            # if not any(current_user.has_group(group) for group in allowed_groups):
            #     stage_name = selection_dict.get(current_stage, 'Unknown')
            #     raise ValidationError(_(
            #         "You do not have permission to edit this record in the '%s' stage."
            #     ) % stage_name)

            if current_stage != new_stage:
                if current_user.has_group('lytegen_contact_details.group_ntp_coordinators'):
                    if current_stage not in NTP_STAGES or new_stage not in NTP_STAGES:
                        raise ValidationError(
                            _("You can only move the record between 'Welcome call', 'Site survey', 'Missing NTP', and 'Updates'."))

                elif current_user.has_group('lytegen_contact_details.group_account_coordinators'):
                    if current_stage not in ACCOUNT_COORDINATOR_STAGES:
                        raise ValidationError(_("Account Coordinators can only move records from stages 4 to 9."))

                elif current_user.has_group('lytegen_contact_details.group_change_coordinators'):
                    if current_stage not in CHANGE_COORDINATOR_STAGES:
                        raise ValidationError(_("Account Coordinators can only move records from stages 9 to 11."))

        return super().write(vals)

    @api.onchange('mobile')
    def _onchange_mobile_copy_to_phone(self):
        if self.mobile:
            self.phone = self.mobile

    @api.onchange('phone')
    def _onchange_phone_copy_to_mobile(self):
        if self.phone and (not self.mobile or self.mobile != self.phone):
            self.mobile = self.phone

    def create(self, vals_list):
        if self.env.context.get('from_partner_sync'):
            # Bypass any special logic if context is set
            return super().create(vals_list)
        # Ensure we always work with a list of dictionaries
        vals_list = vals_list if isinstance(vals_list, list) else [vals_list]

        for vals in vals_list:
            # Case: pipeline_stage is provided → set matching stage_id
            if 'pipeline_stage' in vals:
                stage_name = self.PIPELINE_TO_STAGE.get(vals['pipeline_stage'])
                if stage_name:
                    stage = self.env['crm.stage'].search([('name', '=', stage_name)], limit=1)
                    if stage:
                        vals['stage_id'] = stage.id

            # Case: stage_id is provided → set matching pipeline_stage
            elif 'stage_id' in vals:
                stage = self.env['crm.stage'].browse(vals['stage_id'])
                mapped_pipeline = self.STAGE_TO_PIPELINE.get(stage.name)
                if mapped_pipeline:
                    vals['pipeline_stage'] = mapped_pipeline

        return super().create(vals_list)

    def action_open_email_wizard(self):
        """Open the email wizard."""
        return {
            'name': 'Send Email',
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'view_id': self.env.ref('mail.email_compose_message_wizard_form').id,
            'target': 'new',
            'context': {
                'default_composition_mode': 'comment',
                'default_model': 'crm.lead',
                'default_res_ids': [self.id],
                'search_default_has_email': True,  # Filters contacts with emails
                'domain_partner_ids': [('email', '!=', False)],  # Domain for partner_ids
            },
        }
class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    partner_ids = fields.Many2many(
        'res.partner',
        string="To (Contacts)",
        domain=[('email', '!=', False)]  # Only show contacts with an email
    )
