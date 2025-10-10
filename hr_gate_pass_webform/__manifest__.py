# -*- coding: utf-8 -*-
{
    'name': 'HR Gate Pass Web Form',
    'version': '18.0.1.0',
    'summary': 'Public website form to request Gate Pass (visitor/material/vehicle/contractor)',
    'description': '''Allow public (not logged-in) users to submit gate pass requests.
Creates hr.gate.pass records in Draft and auto-submits for approval.
''',
    'author': 'Akshat Gupta',
    'website': '',
    'category': 'Human Resources',
    'license': 'LGPL-3',
    'depends': ['website', 'hr_gate_pass'],
    'data': [
        'data/mail_template.xml',
        # 'security/ir.model.access.csv',
        'views/gate_pass_templates.xml',
        'views/website_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'hr_gate_pass_webform/static/src/js/gate_pass_form.js',
            'hr_gate_pass_webform/static/src/css/gate_pass_form.css',
        ],
    },
    'installable': True,
    'application': False,
    'sequence': -1,
}