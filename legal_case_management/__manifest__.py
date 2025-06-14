# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
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
###############################################################################
{
    'name': "Legal Case Management",
    'version': '18.0.1.0.0',
    'category': 'Services',
    'summary': 'Legal Case Management for odoo 17. This module will helps '
               'to manage a legal case management firm. This will allows to '
               'manage all details of case sucha as evidence, trial and overall'
               ' payment of a case',
    'description': 'This module helps to manage all process of a legal case'
                   ' management firm.In this way we can register a case and add'
                   'their evidence, trial and payment also. Assign the lawyers'
                   ' based on the wages and per case ',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'hr', 'contacts', 'account', 'mail'],
    'data': [
        'security/legal_case_management_groups.xml',
        'security/legal_case_management_security.xml',
        'security/ir.model.access.csv',
        # 'data/case_register_menu.xml',
        'data/ir_sequence_data.xml',
        'wizard/invoice_payment_views.xml',
        'wizard/full_settlement_views.xml',
        'wizard/legal_case_report_views.xml',
        'views/legal_case_management_menus.xml',
        'report/case_registration_reports.xml',
        'report/legal_case_reports.xml',
        'report/legal_evidence_reports.xml',
        'report/legal_evidence_templates.xml',
        'report/legal_trial_reports.xml',
        'report/report_legal_case_management_report_legal_case_details_templates.xml',
        'report/report_legal_case_management_report_case_register_document_templates.xml',
        'report/legal_evidence_templates.xml',
        'report/report_legal_case_management_report_case_trial_document_templates.xml',
        'views/case_registration_views.xml',
        'views/hr_employee_views.xml',
        'views/res_partner_views.xml',
        'views/legal_evidence_views.xml',
        'views/legal_trial_views.xml',
        'views/legal_court_views.xml',
        'views/case_category_views.xml',
        'views/case_register_portal_template.xml',
        'views/case_register_template.xml',
        'views/account_move_views.xml',
        'views/thanks_template.xml',
        'views/legal_case_page_template.xml',
        'views/res_city_zip_view.xml',
        'views/res_region_menu.xml',
        'views/violations_types_views.xml',
        'views/hide_menus_views.xml',
        'views/requirements_types_view.xml',
        'views/cancel_reason_wizard_view.xml',
        'views/reforward_wizard_views.xml',
        # 'views/clean_login_page_view.xml',
        # 'views/invoice_payment_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True
}
