from odoo import models, fields

class ResCityZip(models.Model):
    _name = 'res.city.zip'
    _description = "City Name"

    name = fields.Char(string="City Name")
    code = fields.Char(string="Code")
