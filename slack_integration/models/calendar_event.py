from odoo import models, fields, api,exceptions
import json
import requests
import logging
_logger = logging.getLogger(__name__)
class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    slack_sent = fields.Boolean(string='Slack Sent?', default=False)

    @api.model
    def web_search_read(self, domain, offset=0, limit=None, order=None, **kwargs):
        current_user = self.env.user
        current_partner_id = current_user.partner_id.id
        current_employee = current_user.employee_id

        # Remove domain filter on partner_ids for current user
        has_partner_ids = any(
            filter for filter in domain if
            filter[0] == 'partner_ids' and filter[1] == 'in' and current_partner_id in filter[2]
        )
        if has_partner_ids and len(domain) == 1:
            domain = []

        # # Dispatch Manager restrictions
        # if current_user.has_group('lytegen_contact_details.group_user_role_dispatch_manager'):
        #     domain += [('confirmation_status', 'not in', ['dq', 'requested_rescheduling'])]

        # Restrict access for Confirmation specialist, Auditors
        if current_user.has_group('lytegen_contact_details.group_user_role_confirmation_specialist') or \
                current_user.has_group('lytegen_contact_details.group_user_role_auditor'):
            domain += [('sales_consultant_employee_id', '=', False)]

        # Sales Consultants: can only see events assigned to them
        if current_user.has_group('lytegen_contact_details.group_sales_consultant'):
            domain += [('sales_consultant_employee_id', '=', current_employee.id)]

        # Sales Managers: can only see events assigned to their team members
        if current_user.has_group('lytegen_contact_details.group_sales_manager'):
            team_member_ids = self.env['hr.employee'].search([
                ('parent_id', '=', current_employee.id)
            ]).ids
            domain += [('sales_consultant_employee_id', 'in', team_member_ids)]

        return super(CalendarEvent, self).web_search_read(
            domain, offset=offset, limit=limit, order=order, **kwargs
        )
    def _send_slack_message(self):
        """Send Slack message when a new calendar event is created."""
        slack_channel = self.env['slack.webhook.configuration'].sudo().search([
            ('category', '=', 'calendar_event'),
            ('status', '=', 'active')
        ], limit=1)

        if not slack_channel:
            # Fallback to default Slack channel
            slack_channel = self.env['slack.webhook.configuration'].sudo().search([
                ('is_default', '=', True),
                ('status', '=', 'active')
            ], limit=1)

        if not slack_channel:
            _logger.warning("No active Slack channel found for calendar events.")
            return

        # Get base URL from system parameters
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        for event in self:
            event_link = f"{base_url}/web#id={event.id}&model=calendar.event&view_type=form"
            sold_design_link = event.sold_design_link_id.link if event.sold_design_link_id else "N/A"

            # Construct the Slack message
            message = f"""
                New Calendar Event Created!*
                -----------------------------------
                Appointment Name:* {event.name or ''}
                Email:* {event.email or ''}
                Phone Number:* {event.phone_number or ''}
                Address:* {event.street_address or ''}, {event.city or ''}, {event.state or ''}, {event.zip_code or ''}
                Map Link:* {event.map_link or ''}
                Notes:* {event.appointment_setter_notes or ''}
                Event Link:* {event_link}
                """

            payload = {'text': message.strip()}
            try:
                response = requests.post(
                    slack_channel.webhook,
                    data=json.dumps(payload),
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    event.slack_sent = True
                    _logger.info(f"Slack message sent successfully for event {event.id}")
                else:
                    _logger.error(f"Failed to send Slack message for event {event.id}: {response.text}")
            except Exception as e:
                _logger.error(f"Slack message sending failed for event {event.id}: {str(e)}")
