from odoo import models, api

class CalendarAttendee(models.Model):
    _inherit = 'calendar.attendee'

    def _send_invitation_emails(self):
        # Completely disable appointment invitation emails
        return True

    @api.depends('alarm_type', 'mail_template_id')
    def _compute_mail_template_id(self):
        for alarm in self:
            # Do nothing to disable default template assignment
            alarm.mail_template_id = False



class AlarmManager(models.AbstractModel):
    _inherit = 'calendar.alarm_manager'

    def _send_reminder(self):
        # Prevent sending email reminders entirely
        return True
