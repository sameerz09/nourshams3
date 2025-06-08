from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ReforwardWizard(models.TransientModel):
    _name = 'reforward.wizard'
    _description = 'Reforward Wizard'

    target_state = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('middle', 'Middle'),
        # ('somoud', 'Somoud'),
    ], string='Target State', required=True)

    def action_confirm_reforward(self):
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            return

        cases = self.env['case.registration'].browse(active_ids)
        for case in cases:
            case.forward_to = self.target_state
            case.state = 'field_committee'
