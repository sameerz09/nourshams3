# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
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
###############################################################################

from odoo import api, fields, models, _, exceptions
from odoo.exceptions import UserError, ValidationError
import re
import logging
import traceback
import gspread
from google.oauth2.service_account import Credentials
from odoo.service.security import check


class CaseRegistration(models.Model):
    """Case registration and invoice for trials and case"""
    _name = 'case.registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Case Register'

    _rec_name = 'identity_no'

    _order = 'create_date desc'

    completion_status = fields.Selection([
        ('complete', 'Complete'),
        ('not_complete', 'Not Complete')
    ], string='Completion Status', compute='_compute_completion_status', store=True)



    documents_requirement = fields.Boolean(
        string='Documents Requirement',
        tracking=True,
        help='Indicates whether document requirements are completed for this case.'
    )

    city_id = fields.Many2one('res.city.zip', string='City', required=False)

    region_id = fields.Many2one('res.region', string='Region', required=False)
    # city = fields.Char(string='City', required=False, store=True)
    city = fields.Char(compute='_compute_city', store=True)


    # violation_id = fields.Many2one('violations.types', string='Violation Name', required=True)

    violation_id = fields.Many2one('violations.types', string='Violation Name', required=True, tracking=True)

    name = fields.Char(
        string='Case No',
        readonly=True,
        # default=lambda self: _('New'),
        copy=False,
        help='Case number',
        tracking=True
    )

    # client_id = fields.Many2one('res.partner', string='Client', required=False, help='', tracking=True)
    name = fields.Char(string='Case No', readonly=True,
                       default=lambda self: _('جديد'),
                       copy=False,
                       help='Case number')
    client_id = fields.Many2one('res.partner', string='client', required=False,
                                help='')

    job = fields.Char(string='Job', readonly=True,
                       copy=False,
                       help='Title')

    applicant=fields.Char(required=False,
                                  string='applicant name',
                                  help='applicant Name', readonly=False)
    affected_person_id= fields.Many2one('res.partner', string='The Affected Person', required=False,
                                help='')
    representative_name = fields.Char(required=False,
                                  string='Representative name',
                                  help='The Representative Name', readonly=False)
    personal_name = fields.Char(required=False,
                                      string='Personal name',
                                      help='The Personal Name', readonly=False)
    family_name = fields.Char(required=False,
                                string='Family name',
                                help='The Family Name', readonly=False)
    # city = fields.Char(required=True,
    #                           string='City',
    #                           help='City Name', readonly=False)
    # community = fields.Char(required=True,
    #                           string='Community name',
    #                           help='The Community Name', readonly=False)
    identity_no= fields.Char(required=False,
                            string='Identity Number',
                            help='The Identity Number', readonly=False)

    contact_no = fields.Char(string='Contact Number', compute='_compute_contact_no', store=True)

    applicant = fields.Char(
        required=False,
        string='Applicant Name',
        help='Applicant Name',
        readonly=False,
        tracking=True
    )

    affected_person_id = fields.Many2one('res.partner', string='The Affected Person', required=True, help='',
                                         tracking=True)

    representative_name = fields.Char(
        required=False,
        string='Representative Name',
        help='The Representative Name',
        readonly=False,
        tracking=True
    )

    personal_name = fields.Char(
        required=False,
        string='Personal Name',
        help='The Personal Name',
        readonly=False,
        tracking=True
    )

    family_name = fields.Char(
        required=False,
        string='Family Name',
        help='The Family Name',
        readonly=False,
        tracking=True
    )

    identity_no = fields.Char(
        required=False,
        string='Identity Number',
        help='The Identity Number',
        readonly=False,
        tracking=True
    )

    contact_no = fields.Char(string='Contact Number', compute='_compute_contact_no', store=True, tracking=True)

    payment_method = fields.Selection(
        selection=[
            ('trial', "Per Trial"),
            ('case', "Per Case"),
            ('out_of_court', "Out of Court")
        ],
        string='Payment Method',
        states={'draft': [('invisible', True)]},
        help="Payment method to select one method",
        tracking=True
    )
    amount_value = fields.Monetary(
        string='Amount Value',
        required=False,
        readonly=False,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=False,
        default=lambda self: self.env.company.currency_id.id,
    )

    lawyer_wage = fields.Char(string="Lawyer Wage", help="Wage of the lawyers", invisible=True, tracking=True)

    lawyer_id = fields.Many2one(
        'hr.employee',
        string='Lawyer',
        domain=[('is_lawyer', '=', True), ('parent_id', '=', False)],
        help="Lawyers in the law firm",
        tracking=True
    )

    lawyer_unavailable = fields.Boolean(
        string="Is Unavailable",
        help="Used to identify available lawyers",
        default=False,
        tracking=True
    )

    junior_lawyer_id = fields.Many2one(
        'hr.employee',
        string='Junior Lawyer',
        help='Junior lawyers in the law firm',
        tracking=True
    )

    court_id = fields.Many2one(
        'legal.court',
        string='Court',
        help="Name of courts",
        tracking=True
    )

    court_no_required = fields.Boolean(
        string="Is Court Number Required",
        help='Makes court number as not required field',
        default=True,
        tracking=True
    )

    judge_id = fields.Many2one(
        related='court_id.judge_id',
        string='Judge',
        store=True,
        help="Available judges",
        tracking=True
    )

    register_date = fields.Date(
        string='Registration Date',
        required=True,
        default=fields.Date.today,
        help='Case registration date',
        tracking=True
    )

    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today,
        tracking=True
    )

    end_date = fields.Date(
        string='End Date',
        tracking=True
    )

    case_category_id = fields.Many2one(
        'case.category',
        string='Case Category',
        required=False,
        help="Category of case",
        tracking=True
    )

    description = fields.Html(
        string='Description',
        required=False,
        help="Case Details",
    )

    opposition_name = fields.Char(
        string='Name',
        help="Name of Opposite Party",
        tracking=True
    )

    opposite_lawyer = fields.Char(
        string='Lawyer',
        help="Name of opposite lawyer",
        tracking=True
    )

    opp_party_contact = fields.Char(
        string='Contact No',
        help='Contact No for opposite party',
        tracking=True
    )

    victim_ids = fields.One2many(
        'case.victim',
        'registration_id',
        help="List of Victims",
        tracking=True
    )

    sitting_detail_ids = fields.One2many(
        'case.sitting',
        'case_id',
        tracking=True
    )

    evidence_count = fields.Integer(
        string="Evidence Count",
        compute='_compute_evidence_count',
        help="Count of evidence",
        tracking=True
    )

    case_attachment_count = fields.Integer(
        string="Case Attachment Count",
        compute='_compute_case_attachment_count',
        help="Count of attachments",
        tracking=True
    )

    trial_count = fields.Integer(
        string="Trial Count",
        compute='_compute_trial_count',
        help="Count of trials",
        tracking=True
    )

    invoice_count = fields.Integer(
        string="Invoice Count",
        compute='_compute_invoice_count',
        help="Count of invoices",
        tracking=True
    )


    requirement_ids = fields.One2many(
        'case.requirement.line',
        'case_id',
        string='Requirements'
    )

    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []

        if name:
            domain = ['|', '|',
                      ('name', operator, name),
                      ('affected_person_id.name', operator, name),
                      ('identity_no', operator, name)]
            records = self.search(domain + args, limit=limit)
        else:
            records = self.search(args, limit=limit)

        return records.name_get()

    # @api.onchange('region_id')
    # def _onchange_region_id(self):
    #     if self.region_id and self.region_id.city_id:
    #         self.city_id = self.region_id.city_id

    # @api.onchange('region_id')
    # def _onchange_region_id_set_city(self):
    #     for rec in self:
    #         if rec.region_id:
    #             rec.city = rec.region_id.city
    #         else:
    #             rec.city = False

    # @api.onchange('region_id')
    # def _onchange_region_id(self):
    #     self.city = self.region_id.city or ''

    city = fields.Char(compute='_compute_city', store=True)

    # def action_open_reforward_wizard(self):
    #     for record in self:
    #         if record.completion_status != 'complete':
    #             raise UserError("يجب رفع جميع المستندات")
    #     return {
    #         'name': _('Re-forward Case'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'reforward.wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {'active_ids': self.ids},
    #     }

    @api.depends('region_id')
    def _compute_city(self):
        for record in self:
            record.city = record.region_id.city or ''

    def _generate_requirement_lines(self):
        for rec in self:
            # Clear existing lines
            rec.requirement_ids = [(5, 0, 0)]

            if not rec.violation_id:
                continue

            # Fetch templates based on selected violation
            templates = self.env['requirements.types'].search([
                ('req_vio_id', '=', rec.violation_id.id)
            ])

            # Create new requirement lines
            rec.requirement_ids = [
                (0, 0, {
                    'requirement_name': tmpl.requirement_name or tmpl.name,
                    'requirements_code': tmpl.requirements_code,
                    'req_vio_id': tmpl.req_vio_id.id,
                    'is_yes': False,
                }) for tmpl in templates
            ]

    @api.onchange('violation_id')
    def _onchange_violation_id(self):
        self._generate_requirement_lines()

    # @api.onchange('violation_id')
    # def _onchange_violation_id(self):
    #     if not self.violation_id:
    #         self.requirement_ids = [(5, 0, 0)]  # Clear all lines
    #         return
    #
    #     # Clear existing lines to prevent duplicates
    #     self.requirement_ids = [(5, 0, 0)]
    #
    #     # Fetch and assign new lines based on selected violation
    #     templates = self.env['requirements.types'].search([
    #         ('req_vio_id', '=', self.violation_id.id)
    #     ])
    #
    #     self.requirement_ids = [(0, 0, {
    #         'requirement_name': tmpl.requirement_name or tmpl.name,
    #         'requirements_code': tmpl.requirements_code,
    #         'req_vio_id': tmpl.req_vio_id.id,
    #         'is_yes': False,
    #     }) for tmpl in templates]

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('auditing_attachment', 'Auditing Attachment'),
            ('field_committee', 'Field Committee'),
            ('north_directory', 'North Directory'),
            ('south_directory', 'South Directory'),
            ('middle_directory', 'Middle Directory'),
            ('director_general_of_directorates', 'Director General of Directorates'),
            ('somood_directory', 'Somoud Directory'),
            ('the_highest_committee', 'The Highest Committee'),  # ✅ Added here
            ('misinstry_office', 'Ministry Office'),
            ('financial_directory', 'Financial Directory'),
            ('accepted', 'Accepted'),
            ('invoiced', 'Invoiced'),
            ('reject', 'Reject'),
            ('cancel', 'Cancel'),
        ],
        string='State',
        default='draft',
        help="State of the case",
        tracking=True
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        readonly=True,
        help="Company in which the case is handled",
        tracking=True
    )
    card_id_req = fields.Boolean(
        string="Card ID Req",
        help='Makes court number as not required field',
        default=True,
        tracking=True
    )
    bank_account_number = fields.Boolean(
        string="Bank Account Number",
        help='Makes court number as not required field',
        default=True,
        tracking=True
    )


    # Filtered one2many (only for selected violation_id)
    filtered_requirements_ids = fields.One2many(
        'requirements.types', 'req_vio_id',
        string='Filtered Requirements',
        compute="_compute_filtered_requirements",
        store=False  # Dynamic field (not stored)
    )

    directory = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('middle', 'Middle'),
        ('somoud', 'Somoud'),
    ], string='Directory')

    # 🔥 New Related Field for `requirements_code`
    requirements_code = fields.Char(related='filtered_requirements_ids.requirements_code', string="Requirement Code")

    is_north_directory = fields.Boolean(
        compute="_compute_user_roles",
        string="North Directory",
        store=False,
    )
    is_north_department = fields.Boolean(
        compute="_compute_user_roles",
        string="North Department",
        store=False,
    )
    is_north_employees = fields.Boolean(
        compute="_compute_user_roles",
        string="North Employees",
        store=False,
    )
    is_south_directory = fields.Boolean(
        compute="_compute_user_roles",
        string="South Directory",
        store=False,
    )
    is_south_department = fields.Boolean(
        compute="_compute_user_roles",
        string="South Department",
        store=False,
    )
    is_south_employees = fields.Boolean(
        compute="_compute_user_roles",
        string="South Employees",
        store=False,
    )
    is_financial_department = fields.Boolean(
        compute="_compute_user_roles",
        string="Financial Department",
        store=False,
    )
    is_middle_directory = fields.Boolean(
        compute="_compute_user_roles",
        string="Middle Directory",
        store=False,
    )
    is_middle_department = fields.Boolean(
        compute="_compute_user_roles",
        string="Middle Department",
        store=False,
    )
    is_middle_employees = fields.Boolean(
        compute="_compute_user_roles",
        string="Middle Employees",
        store=False,
    )
    is_somood_directory = fields.Boolean(
        compute="_compute_user_roles",
        string="Somood Directory",
        store=False,
    )
    is_somood_department = fields.Boolean(
        compute="_compute_user_roles",
        string="Somood Department",
        store=False,
    )
    is_somood_employees = fields.Boolean(
        compute="_compute_user_roles",
        string="Somood Employees",
        store=False,
    )
    is_ministry_office = fields.Boolean(
        compute="_compute_user_roles",
        string="Misinstry Office",
        store=False,
    )

    directory = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('middle', 'Middle'),
        ('somoud', 'Somoud'),
    ], string='Directory', compute='_compute_directory', store=True)

    files = fields.Many2many(
        'ir.attachment',
        relation="design_attachment_rel",
        string="Files",
    )

    report = fields.Many2many(
        'ir.attachment',
        relation="report_attachment_rel",
        string="Report",
    )

    field_report = fields.Many2many(
        'ir.attachment',
        relation="field_report_attachment_rel",
        string="تقرير اللجنة الميدانية",
    )

    forward_to = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('middle', 'Middle'),
        # ('somoud', 'Somoud'),
        ], string='Forward To', required=False)

    cancel_reason = fields.Text(string='سبب الرفض')

    @api.depends('requirement_ids.is_yes')
    def _compute_completion_status(self):
        for rec in self:
            if rec.requirement_ids and all(line.is_yes for line in rec.requirement_ids):
                rec.completion_status = 'complete'
            else:
                rec.completion_status = 'not_complete'

    @api.constrains('amount_value', 'state')
    def _check_amount_value_required(self):
        for record in self:
            if record.state == 'accepted' and not record.amount_value:
                raise ValidationError("يجب ادخال المبلغ")


    @api.model
    def create(self, vals):
        user = self.env.user

        # Allowed employee groups
        allowed_groups = [
            'legal_case_management.legal_case_management_north_employees',
            'legal_case_management.legal_case_management_south_employees',
            'legal_case_management.legal_case_management_middle_employees',
        ]

        # Block creation if user not in group
        if not any(user.has_group(group) for group in allowed_groups):
            raise exceptions.AccessError(_("Only employees can create a case registration."))

        record = super(CaseRegistration, self).create(vals)

        # Directory assignment
        if record.is_north_directory or record.is_north_department or record.is_north_employees:
            record.directory = 'north'
        elif record.is_south_directory or record.is_south_department or record.is_south_employees:
            record.directory = 'south'
        elif record.is_middle_directory or record.is_middle_department or record.is_middle_employees:
            record.directory = 'middle'
        elif record.is_somood_directory or record.is_somood_department or record.is_somood_employees:
            record.directory = 'somoud'

        # Auto-create requirement lines
        record._create_requirement_lines()

        return record

    def write(self, vals):
        res = super(CaseRegistration, self).write(vals)
        if 'violation_id' in vals:
            self._create_requirement_lines()
        return res

    def _create_requirement_lines(self):
        for rec in self:
            if not rec.violation_id:
                continue

            # Remove old lines to avoid duplicates
            rec.requirement_ids.unlink()

            templates = self.env['requirements.types'].search([
                ('req_vio_id', '=', rec.violation_id.id)
            ])
            lines = []
            for tmpl in templates:
                lines.append((0, 0, {
                    'requirement_name': tmpl.requirement_name or tmpl.name,
                    'requirements_code': tmpl.requirements_code,
                    'req_vio_id': tmpl.req_vio_id.id,
                    'is_yes': False,
                }))
            rec.requirement_ids = lines

    # def _compute_directory(self):
    #     for rec in self:
    #         if rec.is_north_directory or rec.is_north_department or rec.is_north_employees:
    #             rec.directory = 'north'
    #         elif rec.is_south_directory or rec.is_south_department or rec.is_south_employees:
    #             rec.directory = 'south'
    #         elif rec.is_middle_directory or rec.is_middle_department or rec.is_middle_employees:
    #             rec.directory = 'middle'
    #         elif rec.is_somood_directory or rec.is_somood_department or rec.is_somood_employees:
    #             rec.directory = 'somoud'
    #         else:
    #             rec.directory = False

    # def action_mark_field_committee(self):
    #     """Move case to the appropriate directory state after Field Committee check"""
    #     for rec in self:
    #         if not rec.field_report:
    #             raise UserError(_("You must fill in the field report before confirming."))
    #         if rec.is_north_directory or rec.is_north_department or rec.is_north_employees:
    #             rec.state = 'north_directory'
    #         elif rec.is_south_directory or rec.is_south_department or rec.is_south_employees:
    #             rec.state = 'south_directory'
    #         elif rec.is_middle_directory or rec.is_middle_department or rec.is_middle_employees:
    #             rec.state = 'middle_directory'
    #         elif rec.is_somood_directory or rec.is_somood_department or rec.is_somood_employees:
    #             rec.state = 'somood_directory'
    #         else:
    #             rec.state = 'field_committee'  # fallback if no match

    def action_mark_field_committee(self):
        """Move case to the appropriate directory state after Field Committee check"""
        for rec in self:
            if not rec.field_report:
                raise UserError(_("You must fill in the field report before confirming."))

            if rec.forward_to:
                # Apply based on forward_to value
                if rec.forward_to == 'north':
                    rec.state = 'north_directory'
                elif rec.forward_to == 'south':
                    rec.state = 'south_directory'
                elif rec.forward_to == 'middle':
                    rec.state = 'middle_directory'
                elif rec.forward_to == 'somoud':
                    rec.state = 'somood_directory'
                else:
                    rec.state = 'field_committee'  # fallback if unknown value
            else:
                # Apply based on directory/department/employee flags
                if rec.is_north_directory or rec.is_north_department or rec.is_north_employees:
                    rec.state = 'north_directory'
                elif rec.is_south_directory or rec.is_south_department or rec.is_south_employees:
                    rec.state = 'south_directory'
                elif rec.is_middle_directory or rec.is_middle_department or rec.is_middle_employees:
                    rec.state = 'middle_directory'
                elif rec.is_somood_directory or rec.is_somood_department or rec.is_somood_employees:
                    rec.state = 'somood_directory'
                else:
                    rec.state = 'field_committee'  # fallback if no match

    @api.depends()
    def _compute_user_roles(self):
        user = self.env.user

        check_north_directory = user.has_group('legal_case_management.legal_case_management_north_directory')
        check_north_department = user.has_group('legal_case_management.legal_case_management_north_department')
        check_north_employees = user.has_group('legal_case_management.legal_case_management_north_employees')
        check_south_directory = user.has_group('legal_case_management.legal_case_management_south_directory')
        check_south_department = user.has_group('legal_case_management.legal_case_management_south_department')
        check_south_employees = user.has_group('legal_case_management.legal_case_management_south_employees')
        check_financial_department = user.has_group('legal_case_management.legal_case_management_financial_department')
        check_middle_directory = user.has_group('legal_case_management.legal_case_management_middle_directory')
        check_middle_department = user.has_group('legal_case_management.legal_case_management_middle_department')
        check_middle_employees = user.has_group('legal_case_management.legal_case_management_middle_employees')
        check_somood_directory = user.has_group('legal_case_management.legal_case_management_somood_directory')
        check_somood_department = user.has_group('legal_case_management.legal_case_management_somood_department')
        check_somood_employees = user.has_group('legal_case_management.legal_case_management_somood_employees')
        check_ministry_office = user.has_group('legal_case_management.legal_case_management_misinstry_office')

        for record in self:
            record.is_north_directory = check_north_directory
            record.is_north_department = check_north_department
            record.is_north_employees = check_north_employees
            record.is_south_directory = check_south_directory
            record.is_south_department = check_south_department
            record.is_south_employees = check_south_employees
            record.is_financial_department = check_financial_department
            record.is_middle_directory = check_middle_directory
            record.is_middle_department = check_middle_department
            record.is_middle_employees = check_middle_employees
            record.is_somood_directory = check_somood_directory
            record.is_somood_department = check_somood_department
            record.is_somood_employees = check_somood_employees
            record.is_ministry_office=check_ministry_office


    @api.depends('violation_id')
    def _compute_filtered_requirements(self):
        """Fetch only related requirements for the selected violation type."""
        for record in self:
            if record.violation_id:
                record.filtered_requirements_ids = self.env['requirements.types'].search([
                    ('req_vio_id', '=', record.violation_id.id)
                ])
            else:
                record.filtered_requirements_ids = False

    # @api.depends('affected_person_id')
    # def _compute_contact_no(self):
    #     for record in self:
    #         phone = record.affected_person_id.phone_sanitized or ''
    #         # Clean unwanted characters like spaces or dashes
    #         cleaned = re.sub(r'[^\d+]', '', phone)
    #
    #         # Convert +972 or +970 to 0
    #         if cleaned.startswith('+972') or cleaned.startswith('+970'):
    #             local_mobile = '0' + cleaned[4:]
    #         else:
    #             local_mobile = cleaned
    #
    #         record.contact_no = local_mobile
    #         record.personal_name = record.affected_person_id.name or ''

    @api.depends('affected_person_id')
    def _compute_contact_no(self):
        for record in self:
            partner = record.affected_person_id
            record.contact_no = partner.mobile2 or ''
            # record.personal_name = partner.name or ''
            record.personal_name = partner.full_name or ''
            record.family_name = partner.family_name or ''
            record.identity_no = partner.card_id or ''
            record.representative_name = partner.representative_name or ''
            record.job = partner.function or ''

    @api.onchange('payment_method')
    def _onchange_payment_method(self):
        """Court not required based on,
         - if payment method = out of court
         - if invoice through full settlement"""
        if self.payment_method == 'out_of_court':
            self.court_no_required = False
        else:
            self.court_no_required = True

    @api.onchange('lawyer_id')
    def _onchange_lawyer_id(self):
        """Lawyer unavailable warning and lists his juniors"""
        cases = self.sudo().search(
            [('lawyer_id', '=', self.lawyer_id.id), ('state', '!=', 'draft'),
             ('id', '!=', self._origin.id)])
        self.lawyer_id.not_available = False
        self.lawyer_unavailable = False
        if self.lawyer_id:
            for case in cases:
                if case.end_date and case.end_date <= fields.Date.today():
                    self.lawyer_id.not_available = False
                    self.lawyer_unavailable = False
                else:
                    self.lawyer_id.not_available = True
                    self.lawyer_unavailable = True
                    break
            if self.lawyer_unavailable:
                return {
                    'warning': {
                        'title': 'Lawyer Unavailable',
                        'message': 'The selected lawyer is unavailable '
                                   'at this time.'
                                   'You can choose his juniors.',
                    },
                    'domain': {
                        'junior_lawyer_id': [('parent_id', '=',
                                              self.lawyer_id.id),
                                             ('is_lawyer', '=', True)],
                    },
                }

    # @api.ondelete(at_uninstall=False)
    # def _unlink_except_draft_or_cancel(self):
    #     """ Records can be deleted only draft and cancel state"""
    #     case_records = self.filtered(
    #         lambda x: x.state not in ['draft', 'cancel'])
    #     if case_records:
    #         raise UserError(_(
    #             "You can not delete a Approved Case."
    #             " You must first cancel it."))

    def action_full_settlement(self):
        """Returns the full settlement view"""
        self.court_no_required = False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'full.settlement',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_case_id': self.id}
        }

    # def action_cancel(self):
    #     """State changed to cancel"""
    #     self.write({'state': 'cancel'})
    #     self.lawyer_id.not_available = False
    #     self.end_date = fields.Date.today()

    def action_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Case',
            'res_model': 'cancel.reason.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('legal_case_management.view_cancel_reason_wizard_form').id,
            'target': 'new',
            'context': {
                'default_case_id': self.id,
            }
        }


    def action_reset_to_draft(self):
        """ Stage reset to draft"""
        self.write({'state': 'draft'})

    # def action_confirm(self):
    #     """Confirmation of Cases"""
    #     if self.name == 'New':
    #         self.name = self.env['ir.sequence']. \
    #                         next_by_code('case_registration') or 'New'
    #     self.state = 'somood_directory'

    # def action_confirm(self):
    #     """Confirmation of Cases"""
    #     for rec in self:
    #         # if rec.completion_status != 'complete':
    #         #     raise UserError(_("You cannot confirm the case because the requirements are not complete."))
    #
    #         if rec.name == 'جديد':
    #             rec.name = self.env['ir.sequence'].next_by_code('case_registration') or 'New'
    #
    #         if rec.is_north_employees:
    #             rec.state = 'north_directory'
    #         elif rec.is_south_employees:
    #             rec.state = 'south_directory'
    #         elif rec.is_middle_employees:
    #             rec.state = 'middle_directory'
    #         else:
    #             rec.state = 'somood_directory'

    def action_mark_auditing_attachment(self):
        """Mark case as moved to Field Committee after auditing attachment"""
        for rec in self:
            if rec.completion_status != 'complete':
                raise UserError(_("يجب اكمال المستندات"))
            rec.state = 'field_committee'

    # def action_mark_auditing_attachment(self):
    #     """Route case based on employee region after auditing attachment"""
    #     for rec in self:
    #         if rec.completion_status != 'complete':
    #             raise UserError(_("يجب اكمال المستندات"))
    #         if rec.is_north_employees:
    #             rec.state = 'north_directory'
    #         elif rec.is_south_employees:
    #             rec.state = 'south_directory'
    #         elif rec.is_middle_employees:
    #             rec.state = 'middle_directory'
    #         else:
    #             rec.state = 'somood_directory'


    def action_confirm(self):
        """Confirmation of Cases"""
        for rec in self:
            # Optional: block confirmation if requirements aren't complete
            # if rec.completion_status != 'complete':
            #     raise UserError(_("You cannot confirm the case because the requirements are not complete."))

            # Assign sequence if still default
            if rec.name == 'جديد':
                rec.name = self.env['ir.sequence'].next_by_code('case_registration') or 'New'

            # Move to 'auditing_attachment' state as the first step after draft
            rec.state = 'auditing_attachment'

    def action_confirm_directories(self):
        """Confirmation of Cases"""
        for rec in self:
            # if not rec.field_report:
            #     raise UserError(_("You must fill in the field report before confirming."))
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('case_registration') or 'New'
            rec.state = 'director_general_of_directorates'

    def action_confirm_somood(self):
        """Confirmation of Cases"""
        if self.name == 'New':
            self.name = self.env['ir.sequence'].next_by_code('case_registration') or 'New'

        self.state = 'the_highest_committee'

    def action_ministry_office(self):
            """Confirmation of Cases"""
            if self.name == 'New':
                self.name = self.env['ir.sequence'].next_by_code('case_registration') or 'New'

            self.state = 'financial_directory'

    def action_financial_department(self):
        """Move the case to 'Accepted' state."""
        if self.name == 'New':
            self.name = self.env['ir.sequence'].next_by_code('case_registration') or 'New'
        self.write({'state': 'accepted'})

        #self.state = 'financial_directory'
       # self.write({'state': 'won'})

    def action_reject(self):
        """Rejection of Cases"""
        self.write({'state': 'reject'})


    def validation_case_registration(self):
        """Show Validation Until The Lawyer Details are Filled"""
        if not self.lawyer_id:
            raise ValidationError(_(
                """Please assign a lawyer for the case"""
            ))

    # def action_invoice(self):
    #     """Open invoice creation form with pre-filled context."""
    #     # Determine lawyer wage based on payment method
    #     self.lawyer_wage = (
    #         self.lawyer_id.wage_per_case if self.payment_method == 'case'
    #         else self.lawyer_id.wage_per_trial if self.payment_method == 'trial'
    #         else ''
    #     )
    #
    #     # Find the default bank journal
    #     default_bank = self.env['account.journal'].search([
    #         ('type', '=', 'bank'),
    #         ('company_id', '=', self.company_id.id)
    #     ], limit=1)
    #
    #     return {
    #         'name': _('Create Invoice'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'invoice.payment',
    #         'view_mode': 'list,form',  # <-- tree first, form second
    #         'target': 'current',  # <-- open in full page
    #         'context': {
    #             'default_case_id': self.id,
    #             'default_cost': self.lawyer_wage,
    #             'default_bank_id': default_bank.id if default_bank else False
    #         }
    #     }
    def action_open_reforward_wizard(self):
        for record in self:
            if record.completion_status != 'complete':
                raise UserError("يجب رفع جميع المستندات")
        return {
            'name': _('Re-forward Case'),
            'type': 'ir.actions.act_window',
            'res_model': 'reforward.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_ids': self.ids},
        }

    def action_invoice(self):
        """Create a customer invoice for the affected person, mark case as invoiced, and refresh the view."""
        # # Search or create 'Compensation' product
        # product = self.env['product.product'].search([('name', '=', 'Compensation')], limit=1)
        # if not product:
        #     product = self.env['product.product'].create({
        #         'name': 'Compensation',
        #         'type': 'service',
        #         'list_price': 0.0,
        #     })
        #
        # # Create the invoice
        # invoice = self.env['account.move'].create({
        #     'move_type': 'out_invoice',
        #     'partner_id': self.affected_person_id.id,
        #     'invoice_date': fields.Date.today(),
        #     'invoice_line_ids': [(0, 0, {
        #         'product_id': product.id,
        #         'name': product.name,
        #         'quantity': 1,
        #         'price_unit': 0.0,
        #         'tax_ids': [(5, 0, 0)],  # Remove any tax
        #     })],
        #     'case_ref': self.name,  # ✅ Set case_ref at creation
        # })

        # Update case state to 'invoiced'
        self.write({'state': 'invoiced'})

        # Show notification and refresh the form view
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invoice Created'),
                'message': _('Customer invoice created and case marked as invoiced.'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            }
        }

    def action_evidence(self):
        """Button to add evidence"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Evidence',
            'view_mode': 'form',
            'res_model': 'legal.evidence',
            'context': {'default_case_id': self.id,
                        'default_client_id': self.client_id.id}
        }

    def get_attachments(self):
        """Show attachments in smart tab which added in chatter"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachment',
            'view_mode': 'kanban,form',
            'res_model': 'ir.attachment',
            'domain': [('res_id', '=', self.id),
                       ('res_model', '=', self._name)],
            'context': {'create': False}
        }

    def _compute_case_attachment_count(self):
        """Compute the count of attachments"""
        for attachment in self:
            attachment.case_attachment_count = self.env['ir.attachment']. \
                sudo().search_count([('res_id', '=', self.id),
                                     ('res_model', '=', self._name)])

    def action_won(self):
        """Changed to won state"""
        self.state = 'won'
        self.end_date = fields.Date.today()
        self.lawyer_id.not_available = False

    def action_lost(self):
        """Changed to lost state"""
        self.state = 'lost'
        self.end_date = fields.Date.today()
        self.lawyer_id.not_available = False

    def _compute_evidence_count(self):
        """Computes the count of evidence"""
        for case in self:
            case.evidence_count = case.env['legal.evidence'].search_count(
                [('client_id', '=', self.client_id.id),
                 ('case_id', '=', self.id)])

    def _compute_trial_count(self):
        """Compute the count of trials"""
        for case in self:
            case.trial_count = case.env['legal.trial']. \
                search_count([('client_id', '=', self.client_id.id),
                              ('case_id', '=', self.id)])

    def action_trial(self):
        """Button to add trial"""
        self.validation_case_registration()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trial',
            'view_mode': 'form',
            'res_model': 'legal.trial',
            'context': {'default_case_id': self.id,
                        'default_client_id': self.client_id.id}
        }

    def _compute_invoice_count(self):
        """Calculate the count of invoices"""
        for inv in self:
            inv.invoice_count = self.env['account.move'].search_count(
                [('case_ref', '=', self.name)])

    def get_invoice(self):
        """Get the corresponding invoices"""
        return {
            'name': 'Case Invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('case_ref', '=', self.name)],
        }

    def get_evidence(self):
        """Returns the evidences"""
        evidence_ids_list = self.env['legal.evidence']. \
            search([('client_id', '=', self.client_id.id),
                    ('case_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Evidence',
            'view_mode': 'list,form',
            'res_model': 'legal.evidence',
            'domain': [('id', 'in', evidence_ids_list)],
            'context': "{'create': False}"
        }

    def get_trial(self):
        """Returns the Trials"""
        trial_ids_list = self.env['legal.trial']. \
            search([('client_id', '=', self.client_id.id),
                    ('case_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trial',
            'view_mode': 'list,form',
            'res_model': 'legal.trial',
            'domain': [('id', 'in', trial_ids_list)],
            'context': "{'create': False}"
        }

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = ['|', '|',
                  ('card_id_req', operator, name),
                  ('identity_no', operator, name),
                  ('affected_person_id.name', operator, name)]  # M2O field
        return self.search(domain + args, limit=limit).name_get()

    def action_director_general_of_directorates(self):
        """Move case to Somoud Directory after Director General of Directorates approval"""
        for rec in self:
            rec.state = 'somood_directory'

    def action_the_highest_committee(self):
        """Move case to Ministry Office after The Highest Committee approval"""
        for rec in self:
            rec.state = 'misinstry_office'

