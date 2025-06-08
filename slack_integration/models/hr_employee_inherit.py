from odoo import models, fields,api

class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    usercode = fields.Char(string="User id")
    # Work Information Custom Fields
    custom_work_location = fields.Selection([
        ('remote', 'Remote'),
        ('office', 'Office'),
        ('on_field', 'On Field')
    ], string="Work Location", tracking=True)

    custom_shortname = fields.Char(string="Shortname (Dialer)", compute="_compute_custom_shortname", store=True)

    custom_ai_transcriber_api_key = fields.Char(string="AI Transcriber API Key")
    custom_schedule = fields.Char(string="Schedule")
    custom_base_pay = fields.Float(string="Base Pay")
    custom_commissions = fields.Boolean(string="Commissions?")
    custom_commission_details = fields.Char(string="Explain the Commissions")

    custom_hired_date = fields.Date(string="Hired Date")
    custom_terminated_date = fields.Date(string="Terminated Date")
    custom_rehireable = fields.Boolean(string="Rehireable?")

    # Private Information Custom Fields
    custom_street_address = fields.Char(string="Street Address")
    custom_city = fields.Char(string="City")
    custom_state = fields.Char(string="State")
    custom_country = fields.Many2one('res.country', string="Country")
    custom_personal_phone = fields.Char(string="Personal Phone")
    custom_personal_email = fields.Char(string="Personal Email")

    @api.depends('name')
    def _compute_custom_shortname(self):
        """Compute Shortname as First Name + Last Name"""
        for employee in self:
            if employee.name:
                employee.custom_shortname = employee.name.replace(" ", "_")
            else:
                employee.custom_shortname = ''