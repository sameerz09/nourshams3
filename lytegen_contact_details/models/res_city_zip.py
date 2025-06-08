from odoo import models, fields

class ResCityZip(models.Model):
    _name = 'res.city.zip'
    _description = "City ZIP Codes"

    name = fields.Char(string="ZIP Code")
    code = fields.Char(string="Code")
    city_id = fields.Many2one('res.city', string="City")
    country_id = fields.Many2one('res.country', string="Country")
    dialer_code = fields.Char(string="Dialer Code")
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string="Status", default='active')
    utility = fields.Char(string="Utility")
