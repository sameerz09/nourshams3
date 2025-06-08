from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError, AccessError, UserError



class ProjectTask(models.Model):
    _inherit = 'project.task'

    calendar_event_id = fields.Many2one('calendar.event', string='Calendar Event')
