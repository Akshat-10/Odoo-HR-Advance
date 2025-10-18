# -*- coding: utf-8 -*-
{
    'name': 'Safety Training Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Employees',
    'summary': 'Manage employee safety training programs and certifications',
    'description': """
        Safety Training Management System for Odoo HR
        - Track employee safety training sessions
        - Manage training certifications
        - Schedule training programs
        - Monitor compliance and expiration dates
        - Generate training reports
    """,
    'sequence': '0',
    'author': 'Balaji Bathini',
    'website': '',
    'depends': [
        'base',
        'hr',
        'mail',
        'web',
        'hr_gate_pass'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/safety_training_view.xml',
        'views/safety_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'safety_training/static/src/css/safety_training.css',
            'safety_training/static/src/js/safety_training.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}