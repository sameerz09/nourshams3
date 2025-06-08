from odoo import models, api, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        """
        Override create to calculate latitude, longitude, and map link for the address.
        """
        if 'address_2' in vals:  # Check if address_2 field is provided
            address = vals.get('address_2')
            google_integration = self.env['google.integrations']

            # Get coordinates
            latitude, longitude = google_integration.get_coordinates(address)
            vals.update({
                'partner_latitude': latitude or 0.0,
                'partner_longitude': longitude or 0.0,
            })

            # Generate map image and upload it to Google Drive
            map_image_content = google_integration.get_google_map_image_with_marker(address)
            if map_image_content:
                map_link = google_integration.upload_file_to_drive(f"map_{address}.png", map_image_content)
                vals.update({'map_link': map_link})

        return super(ResPartner, self).create(vals)

    def write(self, vals):
        """
        Override write to calculate latitude, longitude, and map link for the address if updated.
        """
        if 'address_2' in vals:  # Check if address_2 field is being updated
            for record in self:
                address = vals.get('address_2') or record.address_2
                google_integration = self.env['google.integrations']

                # Get coordinates
                latitude, longitude = google_integration.get_coordinates(address)
                vals.update({
                    'partner_latitude': latitude or 0.0,
                    'partner_longitude': longitude or 0.0,
                })

                # Generate map image and upload it to Google Drive
                map_image_content = google_integration.get_google_map_image_with_marker(address)
                if map_image_content:
                    map_link = google_integration.upload_file_to_drive(f"map_{address}.png", map_image_content)
                    vals.update({'map_link': map_link})

        return super(ResPartner, self).write(vals)
