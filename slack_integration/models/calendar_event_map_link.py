from odoo import models, api, fields

class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    map_link = fields.Char(string="Google Map Link")

    @api.model
    def create(self, vals):
        """
        Override create to generate a Google Maps link for the event location.
        """
        if 'street_address' in vals:  # Check if location field is provided
            address = vals.get('street_address')
            if address:
                map_link = self._generate_google_maps_link(address)
                vals.update({'map_link': map_link})

        return super(CalendarEvent, self).create(vals)

    def write(self, vals):
        """
        Override write to update the Google Maps link when the location is changed.
        """
        if 'street_address' in vals:  # Check if location is being updated
            for record in self:
                address = vals.get('street_address') or record.location
                if address:
                    map_link = self._generate_google_maps_link(address)
                    vals.update({'map_link': map_link})

        return super(CalendarEvent, self).write(vals)

    def _generate_google_maps_link(self, address):
        """
        Generate a Google Maps link for the given address.
        """
        base_url = "https://www.google.com/maps/search/?api=1&query="
        formatted_address = address.replace(" ", "+")  # Replace spaces with '+'
        return f"{base_url}{formatted_address}"
