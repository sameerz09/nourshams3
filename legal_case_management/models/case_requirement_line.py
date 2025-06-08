from odoo import models, fields, api

class CaseRequirementLine(models.Model):
    _name = 'case.requirement.line'
    _description = 'Case Requirement Line'
    _order = 'sequence'

    case_id = fields.Many2one(
        'case.registration',
        string='Case',
        required=True,
        ondelete='cascade'
    )

    requirement_name = fields.Char(
        string='Requirement Name',
        readonly=True
    )

    requirements_code = fields.Char(
        string='Requirement Code',
        readonly=True
    )

    req_vio_id = fields.Many2one(
        'violations.types',
        string='Violation',
        readonly=True
    )

    is_yes = fields.Boolean(
        string='Submitted'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10
    )

    files = fields.Many2many(
        'ir.attachment',
        relation="rep_attachment_rel",
        string="المرفقات",
    )

    @api.model
    def create(self, vals):
        if vals.get('files'):
            vals['is_yes'] = True
        return super().create(vals)

    def write(self, vals):
        if 'files' in vals:
            for rec in self:
                if vals.get('files') and not rec.is_yes:
                    vals['is_yes'] = True
        return super().write(vals)

