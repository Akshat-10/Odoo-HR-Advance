# -*- coding: utf-8 -*-
{
    'name': 'Payroll Workdays Extended',
    'version': '1.4.9',
    'category': 'Human Resources',
    'description': 'Dynamic hourly wage including week-off hours and week-off days calculation',
    'license': 'LGPL-3',
    'author': 'Akshat Gupta',
    'category': 'Human Resources',
    'sequence': -1,
    'depends': [
        'hr_payroll',
        'payroll_salary_link',
        'hr_attendance_calculs',
    ],
    'data': [
        'data/hr_work_entry_type_data.xml',
        'views/report_payslip_templates.xml',
    ],
    'installable': True,
    'application': False,
}
