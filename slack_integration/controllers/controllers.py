import json

import requests

from odoo import http
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

def convert_to_odoo_date(date_str):
    """Converts a date string like '12/v20/v2024 8:23am' to Odoo's date format (YYYY-MM-DD). Handles unusual separators."""
    try:
        # Normalize the date format by replacing '\v' with '/'
        normalized_date_str = date_str.replace('\\v', '/')
        date_obj = datetime.strptime(normalized_date_str, '%m/%d/%Y %I:%M%p')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError as e:
        _logger.error("Date conversion error: %s", str(e))
        return None

def _send_slack_message(phone_number):
    """Send Slack message for calendar events linked to the contact."""
    # Fetch the contact using the phone number
    contact = http.request.env['res.partner'].sudo().search([('phone', '=', phone_number)], limit=1)

    if not contact:
        _logger.warning(f"No contact found with phone number: {phone_number}")
        return

    # Fetch calendar events where slack_sent is False and linked to the contact
    calendar_events = http.request.env['calendar.event'].sudo().search([
        ('phone_number', '=', phone_number),  # Adjust this field as per your setup
        ('slack_sent', '=', False)
    ])

    slack_channel =http.request.env['slack.webhook.configuration'].sudo().search([
        ('category', '=', 'calendar_event'),
        ('is_default', '=', True),
        ('status', '=', 'active')
    ], limit=1)

    if not slack_channel:
        # Fallback to the original logic if no 'project' category is found
        slack_channel = http.request.env['slack.webhook.configuration'].sudo().search([
            ('category', '=', True),
            ('status', '=', 'active')
        ], limit=1)

    if not slack_channel:
        _logger.warning("No active default Slack channel found.")
        return
    # Get the base URL from system parameters
    base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    for event in calendar_events:
        calendar_event_link = f"{base_url}/web#id={event.id}&model=calendar.event&view_type=form"
        # Construct the message using event and contact data
        message = f"""
        {getattr(contact, 'setter_2', 'N/A')} booked {contact.name} for {event.start.strftime('%Y-%m-%d %H:%M:%S')}
        Calendar: {getattr(event.appointment_type_id, 'name', 'N/A')}
        Full Address: {event.street_address}, {event.city}, {event.state}, {event.zip_code}
        Language: {getattr(contact, 'language_2', 'N/A')}
        Readymode Disposition: {getattr(contact, 'readymode_disposition', 'N/A')}
        Opener: {getattr(contact, 'opener_2', 'N/A')}
        Map Link: {event.map_link or 'N/A'}
        Calendar Event Link: {calendar_event_link}
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
            else:
                _logger.error(f"Failed to send Slack message for event {event.id}: {response.text}")
        except Exception as e:
            _logger.error(f"Slack message sending failed for event {event.id}: {str(e)}")


class OpenerWebhookController(http.Controller):
    @http.route('/opener_webhook', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def opener_webhook(self, **kwargs):
        """Logs the request and processes the contact information."""
        try:
            # Log request headers, query parameters, and body
            headers = {key: value for key, value in http.request.httprequest.headers.items()}
            query_params = http.request.params
            body = http.request.httprequest.data
            body_decoded = body.decode('utf-8') if body else "{}"

            # Log the request into a custom model
            http.request.env['request.log'].sudo().create({
                'name': 'Incoming Request',
                'headers': str(headers),
                'query_params': str(query_params),
                'body': body_decoded,
            })

            # Parse the body as JSON
            payload = json.loads(body_decoded)

            # If not "Opener", return early
            if payload.get("AgentUserGroup") != "Opener":
                return http.Response(
                    "Request ignored. AgentUserGroup is not 'Opener'.",
                    status=200
                )

            # Field mapping
            field_mapping = {
                'firstName': 'first_name',
                'lastName': 'last_name',
                'phone': 'phone',
                'address': 'address_2',
                'city': 'city_2',
                'state': 'state_2',
                'zip': 'postal_code_2',
                'AssignedUser_Name': 'opener_2',
                'Notes': 'log_note',
                'CallResult': 'readymode_disposition',
                'CallLog_last_time': 'date_transferred',
                'OriginFile': 'origin_file',
            }

            # Normalize the payload
            normalized_payload = {}
            for key, value in payload.items():
                normalized_key = field_mapping.get(key, key)  # Map key if available
                if normalized_key == 'date_transferred':
                    normalized_payload[normalized_key] = convert_to_odoo_date(value)
                else:
                    normalized_payload[normalized_key] = value

            # Combine first name and last name for the contact name
            normalized_payload[
                'name'] = f"{normalized_payload.get('first_name', '')} {normalized_payload.get('last_name', '')}".strip()

            # Extract phone number for searching
            phone_number = normalized_payload.get('phone')

            # Search for existing contact using the phone number
            contact_model = http.request.env['res.partner']
            existing_contact = contact_model.sudo().search([('phone', '=', phone_number)], limit=1)

            # Filter valid fields for res.partner
            allowed_fields = ['name', 'phone', 'address_2', 'city_2', 'state_2', 'postal_code_2', 'opener_2',
                              'readymode_disposition', 'date_transferred','origin_file']
            updates = {key: value for key, value in normalized_payload.items() if key in allowed_fields and value}

            # Add notes if available
            if 'log_note' in normalized_payload:
                if existing_contact:
                    existing_contact.message_post(body=normalized_payload['log_note'])
                else:
                    new_contact = contact_model.sudo().create(updates)
                    if new_contact:
                        new_contact.message_post(body=normalized_payload['log_note'])

            # Update or create the contact
            if existing_contact:
                existing_contact.sudo().write(updates)



            return http.Response(
                "Request processed successfully. Contact updated or created.",
                status=200
            )

        except Exception as e:
            _logger.error("Error processing request: %s", str(e))
            return http.Response(
                "An error occurred while processing the request.",
                status=500
            )


class CloserWebhookController(http.Controller):

    @http.route('/closer_webhook', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def closer_webhook(self, **kwargs):
        """Logs the request and processes the contact information."""
        try:
            # Log request headers, query parameters, and body
            headers = {key: value for key, value in http.request.httprequest.headers.items()}
            query_params = http.request.params
            body = http.request.httprequest.data
            body_decoded = body.decode('utf-8') if body else "{}"



            # Parse the body as JSON
            payload = json.loads(body_decoded)

            # Log the request into a custom model
            http.request.env['request.log'].sudo().create({
                'name': 'Incoming Request',
                'headers': str(headers),
                'query_params': str(query_params),
                'body': body_decoded,
            })

            # Field mapping
            field_mapping = {
                'firstName': 'first_name',
                'lastName': 'last_name',
                'phone': 'phone',
                'address': 'address_2',
                'city': 'city_2',
                'state': 'state_2',
                'zip': 'postal_code_2',
                'AssignedUser_Name': 'setter_2',
                'Notes': 'log_note',
                'CallResult': 'readymode_disposition',
                'CallLog_last_time': 'date_transferred',
                'OriginFile': 'origin_file',
            }

            # Normalize the payload
            normalized_payload = {}
            for key, value in payload.items():
                normalized_key = field_mapping.get(key, key)  # Map key if available
                if normalized_key == 'date_transferred':
                    normalized_payload[normalized_key] = convert_to_odoo_date(value)
                else:
                    normalized_payload[normalized_key] = value

            # Combine first name and last name for the contact name
            normalized_payload[
                'name'] = f"{normalized_payload.get('first_name', '')} {normalized_payload.get('last_name', '')}".strip()

            # Extract phone number for searching
            phone_number = normalized_payload.get('phone')

            # Search for existing contact using the phone number
            contact_model = http.request.env['res.partner']
            existing_contact = contact_model.sudo().search([('phone', '=', phone_number)], limit=1)

            # Filter valid fields for res.partner
            allowed_fields = ['name', 'phone', 'address_2', 'city_2', 'state_2', 'postal_code_2', 'setter_2',
                              'readymode_disposition', 'date_transferred','origin_file']
            updates = {key: value for key, value in normalized_payload.items() if key in allowed_fields and value}

            # Add notes if available
            if 'log_note' in normalized_payload:
                if existing_contact:
                    existing_contact.message_post(body=normalized_payload['log_note'])
                else:
                    new_contact = contact_model.sudo().create(updates)
                    if new_contact:
                        new_contact.message_post(body=normalized_payload['log_note'])

            # Update or create the contact
            if existing_contact:
                existing_contact.sudo().write(updates)


            return http.Response(
                "Request processed successfully. Contact updated or created.",
                status=200
            )

        except Exception as e:
            _logger.error("Error processing request: %s", str(e))
            return http.Response(
                "An error occurred while processing the request.",
                status=500
            )


class EventWebhookController(http.Controller):

    @http.route('/event_webhook', type='http', auth='public', methods=['POST', 'GET'], csrf=False)
    def event_webhook(self, **kwargs):
        """Updates the map_link field for a given event_id."""
        try:
            # Log request headers and body
            headers = {key: value for key, value in http.request.httprequest.headers.items()}
            body = http.request.httprequest.data
            body_decoded = body.decode('utf-8') if body else "{}"

            # Log the initial request into the custom model
            log_entry = http.request.env['request.log'].sudo().create({
                'name': 'Event Webhook Request',
                'headers': str(headers),
                'body': body_decoded,
            })

            # Parse the body as JSON
            payload = json.loads(body_decoded)

            # Validate required fields
            event_id = payload.get('event_id')
            map_link = payload.get('map_link')

            if not event_id or not map_link:
                log_entry.sudo().write({
                    'body': f"Error: Missing 'event_id' or 'map_link'. Payload received: {body_decoded}"
                })
                return http.Response(
                    "Error: 'event_id' and 'map_link' are required fields.",
                    status=400
                )

            # Search for the event record
            event_model = http.request.env['calendar.event']
            event_record = event_model.sudo().search([('id', '=', event_id)], limit=1)

            if not event_record:
                log_entry.sudo().write({
                    'body': f"Error: Event with ID {event_id} not found. Payload received: {body_decoded}"
                })
                return http.Response(
                    f"Error: Event with ID {event_id} not found.",
                    status=404
                )

            # Update the map_link field
            event_record.sudo().write({'map_link': map_link})

            # Update log entry to indicate success
            log_entry.sudo().write({
                'body': f"Success: Event with ID {event_id} updated with map_link {map_link}."
            })

            return http.Response(
                f"Event with ID {event_id} updated successfully.",
                status=200
            )

        except Exception as e:
            # Log error details in the request log
            http.request.env['request.log'].sudo().create({
                'name': 'Event Webhook Error',
                'headers': str(headers),
                'body': f"Error processing request: {str(e)}. Raw body: {body_decoded}"
            })
            return http.Response(
                "An error occurred while processing the request.",
                status=500
            )

class TestWebhookController(http.Controller):

    @http.route('/test_webhook', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def test_webhook(self, **kwargs):
        """Logs the request data for testing purposes."""
        try:
            # Log request headers, query parameters, and body
            headers = {key: value for key, value in http.request.httprequest.headers.items()}
            query_params = http.request.params
            body = http.request.httprequest.data
            body_decoded = body.decode('utf-8') if body else "{}"

            # Create a unique name for the log entry
            log_name = f"Test Webhook Request - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Log the request into the custom model
            http.request.env['request.log'].sudo().create({
                'name': log_name,
                'headers': str(headers),
                'query_params': str(query_params),
                'body': body_decoded,
            })

            return http.Response(
                f"Test Webhook logged successfully with name '{log_name}'.",
                status=200
            )

        except Exception as e:
            _logger.error("Error in test_webhook: %s", str(e))
            return http.Response(
                "An error occurred while processing the test webhook request.",
                status=500
            )
