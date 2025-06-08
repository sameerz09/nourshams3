# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
        'name': "Lytegen Contact Details",
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': "Updated code for mapping appointments with clients.",
    'description': """
        This module enhances the appointment functionality by enabling better
        mapping between appointments and client details.
    """,
    'author': 'Sameer Zuhairi',
    'company': 'Lytegen',
    'maintainer': 'Lytegen',
    'website': 'https://lytegen.com',
    'depends': [

        # 'base',
        # 'contacts',
        # 'website_appointment',
        # 'calendar',
        # 'mail',
        # 'hr_attendance',
        # 'web',
        # 'slack_integration',
        # 'spreadsheet_dashboard',
        'crm',
        # 'timesheet_grid',
        # 'industry_fsm',
    ],
    'data': [
        # 'security/sales_consultant_security.xml',
        # 'security/ir.model.access.csv',
        # 'views/res_config_settings_views.xml',
        # 'views/appointment_slots_list_template.xml',
        # 'views/appointment_template_inherit.xml',
        # 'views/res_partner_views.xml',
        # 'views/calendar_event_views.xml',
        # 'views/design_views.xml',
        # 'views/appointment_slot_view.xml',
        # 'views/appointment_info_template.xml',
        # 'views/hide_contact_address_views.xml',
        # 'views/crm_views_list.xml',
        # 'views/crm_lead_form_view_inherit.xml',
        # 'views/project_menu_inherit.xml',
        'views/ach_public_page.xml',
        'views/project_onboarding.xml',
        # 'views/site_survey.xml',
        # 'views/credit_check_request_form.xml',
        # 'views/credit_check_success.xml',
        # 'views/res_users_views.xml',
        # 'views/res_region_menu.xml',
        'views/ach_success_page.xml',
        # 'views/res_city_zip_view.xml',
        'views/project.xml',
        'views/clean_login_page_view.xml',
        # 'views/calendar_transcript_views.xml',
        # 'views/appointment_resource_view_inherit.xml',
        'views/credentials_request_template.xml',
        # 'views/appointment_cleanup_template.xml',
        'views/project_onboarding_success.xml',
        # 'views/proposal_request_page.xml',
        # 'views/proposal_thankyou.xml',
        # 'views/website_favicon.xml',
        # 'views/appointment_mail_template.xml',
        # 'views/unauthorized_template.xml',
        # 'security/menu_access.xml',

        # 'views/hide_menus.xml',

        # 'views/appointment_templates.xml',
        # 'views/calendar_hide_create.xml',
        # 'views/calendar_override.xml',
        # 'views/hr_employee_views.xml',
        # 'views/calendar_override.xml',
        # 'views/sales_consultant_audio.xml',
        # 'data/scheduled_action.xml',


        # 'views/assets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # 'lytegen_contact_details/static/src/xml/appointment_overrides.xml',
            # Core or public JS (optional, commented out)
            # 'web/static/src/js/core/utils/timing.js',
            # 'web/static/src/js/public/public_widget.js',

            # Appointment-related JS
            # 'appointment/static/src/js/appointment_form.js',

            # Custom contact detail logic

            'lytegen_contact_details/static/src/img/favicon.ico',
            'lytegen_contact_details/static/src/js/custom_appointment_validation.js',
            'lytegen_contact_details/static/src/js/appointment_slot_select_extended.js',
            'lytegen_contact_details/static/src/js/street_address_goole_maps.js',
            'lytegen_contact_details/static/src/js/credit_check_event_lookup_plain.js',
            # 'lytegen_contact_details/static/src/js/credentials_positions.js',

            # Optional JS overrides (commented out)
            # 'lytegen_contact_details/static/src/js/calendar_override.xml',
            # 'lytegen_contact_details/static/src/js/hide_calendar_sidebar.js',

            # Custom styles
            'lytegen_contact_details/static/src/css/credit_check_style.css',
            'lytegen_contact_details/static/src/js/appointment_slot_patch.js',
            # 'lytegen_contact_details/static/src/css/ach_style.css',
            # 'lytegen_contact_details/static/src/css/success_style.css',

        ],
        'web.assets_backend': [

            'lytegen_contact_details/static/src/img/favicon.ico',
            'lytegen_contact_details/static/src/css/calendar_hide.css',
            'lytegen_contact_details/static/src/css/hide_appointment_share.css',
            # 'lytegen_contact_details/static/src/js/hide_new_button.js',
            'lytegen_contact_details/static/src/css/form_disable.css',
            # 'lytegen_contact_details/static/src/xml/calendar_buttons.xml',
            # 'lytegen_contact_details/static/src/css/hide_new_button.css',
                    ],


    },



    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
