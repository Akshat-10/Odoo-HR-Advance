# -*- coding: utf-8 -*-
{
    'name': 'HR Gate Pass - EHS Link',
    'version': '18.0.1.0',
    'summary': 'Link HR Gate Pass with EHS Work Permit Records',
    'author': 'Akshat Gupta',
    # Added hr_attendance and fetch_employee_attendance_location to ensure attendance address fields are available
    'depends': ['hr_gate_pass', 'EHS', 'hr_attendance', 'fetch_employee_attendance_location'],
    'sequence': -4,
    'data': [
        'views/hr_gate_pass_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_gate_pass_ehs_link/static/src/css/ehs_buttons.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
