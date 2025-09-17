# -*- coding: utf-8 -*-
{
    'name': 'EHS Monitoring Areas Link',
    'version': '18.0.1.0',
    'summary': 'Link EHS permits with Monitoring Areas and QR-based monitoring',
    'description': 'Adds a Monitoring page to EHS permits linking to monitoring areas with QR flow, monitoring lines, time limits, emails, and expirations.',
    'author': 'Akshat Gupta',
    'website': '',
    'license': 'LGPL-3',
    'sequence': -1,
    'category': 'Operations/Safety',
    'depends': ['base', 'web', 'mail', 'EHS', 'monitoring_areas'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'data/mail_template.xml',
        'views/res_config_settings_views.xml',
        'views/monitoring_line_views.xml',
        'views/inherit_work_heights_permit_views.xml',
        'views/inherit_daily_permit_work_views.xml',
        'views/inherit_hot_work_permit_views.xml',
        'views/inherit_energized_work_permit_views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ehs_monitoring_areas_link/static/src/css/ehs_monitoring_buttons.css',
        ],
    },
    'installable': True,
    'application': True,
}
