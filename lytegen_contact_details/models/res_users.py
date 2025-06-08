from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SalesConsultant(models.Model):
    _inherit = 'res.users'  # Assuming sales consultants are users

    region_ids = fields.Many2many(
        'res.region', string="Assigned Regions"
    )

    # def _remove_sales_groups(self):
    #     """ Removes all sales-related groups from users who have 'group_sales_manager'. """
    #     sales_manager_group = self.env.ref('lytegen_contact_details.group_sales_manager', raise_if_not_found=False)
    #     sales_groups = [
    #         'sales_team.group_sale_salesman',
    #         'sales_team.group_sale_salesman_all_leads',
    #         'sales_team.group_sale_manager'
    #     ]
    #
    #     group_ids = []
    #     for group in sales_groups:
    #         ref = self.env.ref(group, raise_if_not_found=False)
    #         if ref:
    #             group_ids.append(ref.id)
    #
    #     for user in self:
    #         if sales_manager_group and sales_manager_group.id in user.groups_id.ids:  # If user is in Sales Manager group
    #             _logger.info(f"Removing Sales Groups {group_ids} from Sales Manager {user.id}")
    #             user.write({'groups_id': [(3, gid) for gid in group_ids]})
    #
    # @api.model
    # def create(self, vals):
    #     """ Remove all sales-related groups when creating a user who is assigned to 'group_sales_manager'. """
    #     user = super(SalesConsultant, self).create(vals)
    #     user._remove_sales_groups()
    #     return user
    #
    # def write(self, vals):
    #     """ Remove all sales-related groups when updating a user who is assigned to 'group_sales_manager'. """
    #     res = super(SalesConsultant, self).write(vals)
    #     self._remove_sales_groups()
    #     return res

    # def write(self, vals):
    #     _logger.info("START: Entering write method in SalesConsultant")
    #
    #     if 'groups_id' in vals:
    #         _logger.info(f"Detected groups_id update in vals: {vals['groups_id']}")
    #
    #         admin_group = self.env.ref('lytegen_contact_details.group_user_role_admin', raise_if_not_found=False)
    #         if admin_group:
    #             _logger.info(f"Admin Group ID: {admin_group.id}")
    #
    #             for record in self:
    #                 _logger.info(f"Processing user: {record.name} (ID: {record.id})")
    #
    #                 current_groups = record.groups_id.ids  # Get current assigned groups
    #                 _logger.info(f"User's current groups: {current_groups}")
    #
    #                 removed_groups = [group[1] for group in vals['groups_id'] if group[0] == 3]
    #                 _logger.info(f"Groups being removed: {removed_groups}")
    #
    #                 if admin_group.id in removed_groups and admin_group.id in current_groups:
    #                     _logger.info(f"Admin group is being removed for user {record.name}")
    #
    #                     # Define the groups to be removed when Admin is deselected
    #                     groups_to_remove = [
    #                         'lytegen_contact_details.group_user_role_dispatch_manager',
    #                         'lytegen_contact_details.group_sales_consultant',
    #                         'lytegen_contact_details.group_designer',
    #                         'lytegen_contact_details.group_user_role_confirmation_specialist',
    #                         'lytegen_contact_details.group_user_role_auditor',
    #                         'lytegen_contact_details.group_user_hide_menu',
    #                         'base.group_system'
    #                     ]
    #
    #                     # Get actual group IDs
    #                     group_ids_to_remove = [
    #                         self.env.ref(group, raise_if_not_found=False).id
    #                         for group in groups_to_remove if self.env.ref(group, raise_if_not_found=False)
    #                     ]
    #                     _logger.info(f"Resolved group IDs to remove: {group_ids_to_remove}")
    #
    #                     if group_ids_to_remove:
    #                         _logger.info(f"Removing groups for user {record.name}: {group_ids_to_remove}")
    #                         record.with_context(group_update=1).write({
    #                             "groups_id": [(3, group_id) for group_id in group_ids_to_remove]
    #                         })
    #                     else:
    #                         _logger.warning(f"No valid groups found to remove for user {record.name}")
    #
    #     _logger.info("END: Exiting write method in SalesConsultant")
    #     return super(SalesConsultant, self).write(vals)
