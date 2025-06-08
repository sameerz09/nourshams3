from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ResRegion(models.Model):
    _name = 'res.region'
    _description = "Sales Regions"
    _rec_name = 'name'  # Ensures the correct name is displayed in relational fields

    name = fields.Char(string="Region Name", required=True)
    zip_codes = fields.Text(string="ZIP Code", help="Comma-separated ZIP codes for reference")
    state = fields.Char(string="State")
    city = fields.Char(string="City")
    county = fields.Char(string="County")
    dialer_status = fields.Char(string="Dialer Status")
    utility = fields.Char(string="Utility")

    zip_codes_ids = fields.Many2many(
        comodel_name='res.city.zip',
        string="ZIP Codes",
        help="Select related ZIP codes for this region",
        relation="res_region_zip_rel",
        column1="region_id",
        column2="zip_id",
    )

    @api.model
    def create(self, vals):
        """Logs new region creation"""
        _logger.info(f"Creating new region: {vals.get('name')}")
        return super(ResRegion, self).create(vals)

    def write(self, vals):
        """Logs when a region is updated"""
        _logger.info(f"Updating region {self.id} with values: {vals}")
        return super(ResRegion, self).write(vals)
