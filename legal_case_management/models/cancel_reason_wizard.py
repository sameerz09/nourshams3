from odoo import models, fields

class CancelReasonWizard(models.TransientModel):
    _name = 'cancel.reason.wizard'
    _description = 'Cancel Reason Wizard'

    cancel_reason = fields.Text(string="سبب الرفض", required=True)
    case_id = fields.Many2one('case.registration', string="Case", required=True)

    def action_confirm_cancel(self):
        self.case_id.write({
            'cancel_reason': self.cancel_reason,
            'state': 'cancel'
        })
