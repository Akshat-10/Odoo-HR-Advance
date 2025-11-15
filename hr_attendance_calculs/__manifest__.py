# -*- coding: utf-8 -*-
{
    'name': 'Attendance Infractions Automation',
    'version': '1.0.0',
    'category': 'Human Resources',
    'summary': 'Auto generate time off penalties from attendance infractions',
    'author': 'Custom Development',
    'depends': [
        'hr_attendance',
        'hr_holidays',
        'hr_work_entry_holidays',
        'hr_payroll',
        'hr_payroll_attendance',  # Must load after to override overtime calculation
    ],
    'data': [
        'data/hr_attendance_calculs_data.xml',
        'views/res_config_settings_views.xml',
        'views/hr_work_entry_type_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_payslip_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
