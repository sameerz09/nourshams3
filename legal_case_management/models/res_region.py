from odoo import models, fields, api
import logging

class ResRegion(models.Model):
    _name = 'res.region'
    _description = "Sales Regions"

    name = fields.Char(string="Region Name", required=False)
    city_id = fields.Many2one('res.city.zip', string='city', required=False)
    city = fields.Char(string='City', required=True)
    zip_codes = fields.Char(string="ZIP Codes", help="Comma-separated ZIP codes")


