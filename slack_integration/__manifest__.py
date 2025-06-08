{
    'name': 'Slack Integration',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Integrates Slack with Odoo for message sending.',
    'images': ['static/description/icon.png'],
    'depends': ['base','calendar','crm','custom_google_integration'],
    # 'depends': ['base', 'calendar', 'project', 'crm'],

    'data': [
        'views/slack_configuration_views.xml',
        'views/slack_message_views.xml',
        'views/request_log.xml',
        'views/slack_integration_menu.xml',
        'views/crm_extend.xml',
        'views/calendar_event_views.xml',
        'views/hr_employee_view.xml',
        'security/ir.model.access.csv',

    ],
    'assets': {
        'web.assets_backend': [
            'slack_integration/static/src/address_autocomplete.js',  # Load your JS
            'slack_integration/static/src/style.css',  # Load your JS
        ],
    },
    'installable': True,
}
