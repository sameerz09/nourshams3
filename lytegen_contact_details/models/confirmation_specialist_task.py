# models/confirmation_specialist_task.py
from odoo import models, fields

class ConfirmationSpecialistTask(models.Model):
    _name = 'confirmation.specialist.task'
    _description = 'Confirmation Specialist Task'

    name = fields.Char(required=True)
    calendar_event_id = fields.Many2one('calendar.event', string='Related Calendar Event', required=True)
