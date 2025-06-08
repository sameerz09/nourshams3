from odoo import models, api

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def get_user_roots(self):
        # Get the current user
        user = self.env.user

        # Reference the restricted menu ID
        restricted_menu_id = 104  # Replace with the menu ID you want to restrict

        # Reference the relevant groups
        admin_group = self.env.ref('lytegen_contact_details.group_user_role_admin', raise_if_not_found=False)
        dispatch_manager_group = self.env.ref('lytegen_contact_details.group_user_role_dispatch_manager', raise_if_not_found=False)
        confirmation_specialist_group = self.env.ref('lytegen_contact_details.group_user_role_confirmation_specialist', raise_if_not_found=False)

        # If the user is in the admin group, skip hiding the menu
        if admin_group and admin_group in user.groups_id:
            return super(IrUiMenu, self).get_user_roots()

        # Collect the restricted groups
        restricted_groups = [dispatch_manager_group, confirmation_specialist_group]
        restricted_groups = [group for group in restricted_groups if group]

        # Check if the user belongs to any of the restricted groups
        if any(group in user.groups_id for group in restricted_groups):
            # Get all root menus
            all_roots = super(IrUiMenu, self).get_user_roots()

            # Exclude the restricted menu
            restricted_menu = self.env['ir.ui.menu'].browse(restricted_menu_id)
            return all_roots - restricted_menu

        # Default behavior for other users
        return super(IrUiMenu, self).get_user_roots()
