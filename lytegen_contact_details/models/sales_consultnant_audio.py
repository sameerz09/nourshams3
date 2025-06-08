import requests
from odoo import models, fields, api,_
from odoo.exceptions import UserError, AccessError

class SalesConsultantAudio(models.Model):
    _name = 'sales.consultant.audio'
    _description = 'Sales Consultant Audio Files'

    file = fields.Binary("Audio File", required=True, attachment=True)
    file_url = fields.Char("Audio")
    duration = fields.Char("Duration")
    creation_date = fields.Datetime("Creation Date", default=fields.Datetime.now)
    appointment_id = fields.Many2one('calendar.event', string="Appointment")
    is_sent_fireflies = fields.Boolean("Sent to Fireflies", default=False)
    is_transcript_generated = fields.Boolean("Transcript Generated", default=False)

    is_sales_consultant = fields.Boolean(
        compute="_compute_user_roles",
        string="Sales Consultant",
        store=False
    )
    is_sales_manager = fields.Boolean(
        compute="_compute_user_roles",
        string="Sales Manager",
        store=False,
    )
    is_designer = fields.Boolean(
        compute="_compute_user_roles",
        string="Designer",
        store=False,
    )
    is_dispatch_manager = fields.Boolean(
        compute="_compute_user_roles",
        string="Dispatch Manager",
        store=False,
    )
    is_confirmation_specialist = fields.Boolean(
        compute="_compute_user_roles",
        string="Confirmation Specialist",
        store=False,
    )

    def _compute_user_roles(self):
        user = self.env.user
        check_sales_consultant_group = user.has_group('lytegen_contact_details.group_sales_consultant')
        check_sales_manager_group = user.has_group('lytegen_contact_details.group_sales_manager')
        check_designer_group = user.has_group('lytegen_contact_details.group_designer')
        check_dispatch_manager_group = user.has_group('lytegen_contact_details.group_user_role_dispatch_manager')
        check_confirmation_specialist_group = user.has_group(
            'lytegen_contact_details.group_user_role_confirmation_specialist')

        for record in self:
            record.is_sales_consultant = check_sales_consultant_group
            record.is_sales_manager = check_sales_manager_group
            record.is_designer = check_designer_group
            record.is_dispatch_manager = check_dispatch_manager_group
            record.is_confirmation_specialist = check_confirmation_specialist_group



    def action_view_transcript(self):
        print(self.id)
        """
        Button handler for 'View Transcript':
         - If is_transcript_generated is True, open existing transcript.
         - Else, fetch transcript (placeholder), create record, mark as generated, open it.
        """
        self.ensure_one()


        # Check if transcript is already generated
        if self.is_transcript_generated:
            # If so, try to find the transcript record
            transcript = self.env['calendar.transcript'].search([
                ('audio_id', '=', self.id)
            ], limit=1)
            if not transcript:
                raise UserError(_("Transcript is marked as generated but no record found."))
        else:
            # Step 1: Query Fireflies to get the transcript ID using the title
            fireflies_url = 'https://api.fireflies.ai/graphql'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer c2bd7ace-a4b9-4691-95ed-0322be6107d3'
            }
            query_data = {
                "query": "query Transcripts($title: String) { transcripts(title: $title) { title id } }",
                "variables": {"title": f"odoo-{self.id}"}
            }
            response = requests.post(fireflies_url, headers=headers, json=query_data)
            resp_json = response.json()
            transcripts_list = resp_json.get('data', {}).get('transcripts', [])
            expected_title = f"odoo-{self.id}"
            transcript_id = None
            for transcript_item in transcripts_list:
                if transcript_item.get('title') == expected_title:
                    transcript_id = transcript_item.get('id')
                    break

            # Step 2: If transcript_id is found, fetch its content
            transcript_text = ""
            if transcript_id:
                GRAPHQL_URL = "https://api.fireflies.ai/graphql"
                API_KEY = "c2bd7ace-a4b9-4691-95ed-0322be6107d3"
                HEADERS = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
                query = """
                query Transcript($transcriptId: String!) {
                  transcript(id: $transcriptId) {
                    sentences {
                      speaker_name
                      text
                    }
                  }
                }
                """
                variables = {"transcriptId": transcript_id}
                resp = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": query, "variables": variables})
                data = resp.json()
                if "data" in data and "transcript" in data["data"]:
                    sentences = data["data"]["transcript"]["sentences"]
                    # Build HTML string from sentences
                    for sentence in sentences:
                        speaker = sentence.get("speaker_name", "Unknown")
                        text = sentence.get("text", "")
                        transcript_text += f"<p><strong>{speaker}:</strong> {text}</p>"
                else:
                    transcript_text = "<p>Transcript is under processing or not available yet.</p>"
            else:
                transcript_text = "<p>Transcript is under processing or not available yet.</p>"

            if transcript_text == "<p>Transcript is under processing or not available yet.</p>":
                raise UserError(_("Transcript is under processing or not available yet."))

            # Create the transcript record
            transcript = self.env['calendar.transcript'].create({
                'name': f"odoo-{self.id}",  # same naming style used in Fireflies
                'audio_id': self.id,
                'content': transcript_text,
            })
            # Mark as generated
            self.is_transcript_generated = True

        # Return action to open the transcript form view
        # Build the URL for the transcript form view.
        # This URL format opens the form view in a new browser tab.
        url = f"/web#id={transcript.id}&model=calendar.transcript&view_type=form"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',  # Opens in a new browser tab
        }


    def _generate_file_url(self):
        """Generate a public URL for the uploaded file and push it to Fireflies."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.file and record.id:
                # Look up the attachment for this record and field
                domain = [
                    ('res_model', '=', self._name),
                    ('res_id', '=', record.id),
                    ('res_field', '=', 'file')
                ]
                attachment = self.env['ir.attachment'].sudo().search(domain, limit=1)
                if attachment:
                    # Mark the attachment as public
                    attachment.sudo().write({'public': True})
                    # Generate the URL with download parameter
                    record.file_url = f"{base_url}/web/content/{attachment.id}?download=true"
                else:
                    # Fallback URL if the attachment is not found
                    record.file_url = f"{base_url}/web/content/{record.id}?model={self._name}&field=file"
                print("Generated file URL:", record.file_url)

                # Prepare the payload to push the file URL to Fireflies
                fireflies_url = 'https://api.fireflies.ai/graphql'
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer c2bd7ace-a4b9-4691-95ed-0322be6107d3'
                }
                input_data = {
                    "url": record.file_url,
                    "title": f"odoo-{record.id}",
                    "attendees": [
                        {
                            "displayName": "Fireflies Notetaker",
                            "email": "notetaker@fireflies.ai",
                            "phoneNumber": "xxxxxxxxxxxxxxxx"
                        },
                        {
                            "displayName": "Fireflies Notetaker 2",
                            "email": "notetaker2@fireflies.ai",
                            "phoneNumber": "xxxxxxxxxxxxxxxx"
                        }
                    ]
                }
                data = {
                    'query': '''
                        mutation($input: AudioUploadInput) {
                            uploadAudio(input: $input) {
                                success
                                title
                                message
                            }
                        }
                    ''',
                    'variables': {'input': input_data}
                }

                try:
                    response = requests.post(fireflies_url, headers=headers, json=data)
                    if response.status_code == 200:
                        result = response.json()
                        # Check for a successful API response
                        if result.get("data", {}).get("uploadAudio", {}).get("success"):
                            record.is_sent_fireflies = True
                        else:
                            record.is_sent_fireflies = False
                    else:
                        record.is_sent_fireflies = False
                    print("Fireflies API response:", response.json())
                except Exception as e:
                    record.is_sent_fireflies = False
                    print("Error sending file to Fireflies:", e)
            else:
                record.file_url = False
    # @api.model
    # def create(self, vals):
    #     if self.env.user.has_group('lytegen_contact_details.group_sales_consultant'):
    #         raise AccessError(_("You are not allowed to create audio files."))
    #     """Override create to generate the file URL."""
    #     record = super(SalesConsultantAudio, self).create(vals)
    #     if record.file:
    #         record._generate_file_url()
    #     return record
    # @api.model
    # def create(self, vals):
    #     """ Prevent Sales Consultants and Sales Managers from creating audio files. """
    #     if self.env.user.has_group('lytegen_contact_details.group_sales_consultant') or \
    #             self.env.user.has_group('lytegen_contact_details.group_sales_manager'):
    #         raise AccessError(_("You are not allowed to create audio files."))
    #
    #     """Override create to generate the file URL."""
    #     record = super(SalesConsultantAudio, self).create(vals)
    #     if record.file:
    #         record._generate_file_url()
    #     return record
    #
    # def write(self, vals):
    #     """Override write to generate the file URL on update."""
    #     result = super(SalesConsultantAudio, self).write(vals)
    #     if 'file' in vals:
    #         self._generate_file_url()
    #     return result
    @api.model
    def create(self, vals):
        """ Prevent Sales Consultants and Sales Managers from creating audio files. """
        if self.env.user.has_group('lytegen_contact_details.group_sales_consultant') or \
                self.env.user.has_group('lytegen_contact_details.group_sales_manager'):
            raise AccessError(_("You are not allowed to create audio files."))

        """Override create to generate the file URL."""
        record = super(SalesConsultantAudio, self).create(vals)
        if record.file:
            record._generate_file_url()
        return record

    def write(self, vals):
        """ Prevent Sales Consultants and Sales Managers from modifying audio files. """
        if self.env.user.has_group('lytegen_contact_details.group_sales_consultant') or \
                self.env.user.has_group('lytegen_contact_details.group_sales_manager'):
            raise AccessError(_("You are not allowed to modify audio files."))

        """Override write to generate the file URL on update."""
        result = super(SalesConsultantAudio, self).write(vals)
        if 'file' in vals:
            self._generate_file_url()
        return result

    # def unlink(self):
    #     """ Prevent Sales Consultants and Sales Managers from deleting audio files. """
    #     if self.env.user.has_group('lytegen_contact_details.group_sales_consultant') or \
    #             self.env.user.has_group('lytegen_contact_details.group_sales_manager'):
    #         raise AccessError(_("You are not allowed to delete audio files."))
    #
    #     return super(SalesConsultantAudio, self).unlink()

    def unlink(self):
        """Prevent specific groups from deleting audio files."""
        restricted_groups = [
            'lytegen_contact_details.group_user_role_confirmation_specialist',
            'lytegen_contact_details.group_user_role_auditor',
            'lytegen_contact_details.group_sales_manager',
            'lytegen_contact_details.group_sales_consultant',
            'lytegen_contact_details.group_designer',
            'lytegen_contact_details.group_user_role_dispatch_manager',
        ]
        if any(self.env.user.has_group(group) for group in restricted_groups):
            raise AccessError(_("You are not allowed to delete audio files."))

        return super(SalesConsultantAudio, self).unlink()


class CalendarTranscript(models.Model):
    """New model to store transcript information."""
    _name = 'calendar.transcript'
    _description = 'Calendar Transcript'

    name = fields.Char("Title")
    audio_id = fields.Many2one('sales.consultant.audio', string="Related Audio")
    content = fields.Html("Transcript Content")

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    sales_audio_ids = fields.One2many(
        'sales.consultant.audio', 'appointment_id', string="Sales Consultant Audio Files"
    )

