from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        """Force default timezone for all partners"""
        vals['tz'] = "America/Los_Angeles"
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        """Prevent changing timezone for all partners"""
        if 'tz' in vals:
            vals['tz'] = "America/Los_Angeles"
        return super(ResPartner, self).write(vals)


class ResUsers(models.Model):
    _inherit = "res.users"


    @api.model
    def create(self, vals):
        """Force default timezone for new users"""
        vals['tz'] = "America/Los_Angeles"
        return super(ResUsers, self).create(vals)

    def write(self, vals):
        """Prevent users from changing their timezone"""
        if 'tz' in vals:
            vals['tz'] = "America/Los_Angeles"
        return super(ResUsers, self).write(vals)
