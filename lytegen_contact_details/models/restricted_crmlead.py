import logging
from odoo import models, api, _
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class RestrictedProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def create(self, vals):
        _logger.info("Creating a new project with values: %s", vals)
        return super(RestrictedProject, self).create(vals)

    def write(self, vals):
        _logger.info("Attempting to write on project with values: %s", vals)
        _logger.info("Current user: %s, Groups: %s", self.env.user.name, self.env.user.groups_id.mapped('name'))

        # Restrict updates for users in the specific group
        if self.env.user.has_group('lytegen_contact_details.group_sales_consultant'):
            for record in self:
                _logger.info("Checking project ID: %s, Created by: %s", record.id, record.create_uid.name)
                if record.id:  # If the project exists
                    raise AccessError(_("You are not allowed to update this project after it is created."))

        # Allow updates for other users/groups
        return super(RestrictedProject, self).write(vals)
