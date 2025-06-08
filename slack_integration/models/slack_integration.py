from odoo import models, fields, api
import json
import requests


class WebhookConfiguration(models.Model):
    _name = 'slack.webhook.configuration'
    _description = 'Slack Webhook Configuration'

    name = fields.Char(string='Title', required=True)
    webhook = fields.Char(string='Webhook URL', required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Not Active')
    ], string='Status', default='active')
    is_default = fields.Boolean(string='Is Default')
    category = fields.Selection([
        ('project', 'Project'),
        ('design', 'Design'),
        ('calendar_event', 'Calendar Event'),
        ('ach_submission', 'ACH Submission'),
        ('credit_check_submission', 'Credit Check Submission')
    ], string='Category', required=True)


class SlackMessages(models.Model):
    _name = 'slack.messages'
    _description = 'Slack Messages'

    message = fields.Text(string='Message', required=True)
    channel_id = fields.Many2one(
        'slack.webhook.configuration',
        string='Channel',
        domain=[('status', '=', 'active')],
        required=True
    )
    stats_sent = fields.Boolean(string='Sent?', default=False)

    @api.model
    def create(self, vals):
        # Call the super to create the record
        new_record = super(SlackMessages, self).create(vals)

        # Get the webhook URL from the configuration
        webhook_config = new_record.channel_id
        webhook_url = webhook_config.webhook

        # Prepare the message payload
        payload = {
            'text': new_record.message
        }

        # Sending the message to Slack
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )

        # Check the response and update the stats_sent field
        if response.status_code == 200:
            new_record.stats_sent = True
        return new_record
