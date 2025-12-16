# -*- coding: utf-8 -*-
{
    'name': 'Payroll Workdays Extended',
    'version': '1.5.0',
    'category': 'Human Resources',
    'description': 'Dynamic hourly wage including week-off hours and week-off days calculation',
    'license': 'LGPL-3',
    'author': 'Akshat Gupta',
    'category': 'Human Resources',
    'sequence': -1,
    'depends': [
        'hr_payroll',
        'payroll_salary_link',
        'l10n_in_hr_payroll',
        # 'hr_attendance_calculs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_work_entry_type_data.xml',
        'data/hr_payroll_report_data.xml',
        'views/hr_salary_attachment_type_views.xml',
        'views/hr_salary_attachment_views.xml',
        'views/report_payslip_templates.xml',
    ],
    'installable': True,
    'application': False,
}
