# -*- coding: utf-8 -*-
{
    'name': 'Payroll Salary Link',
    'version': '1.1.0',
    'category': 'Human Resources',
    'summary': 'Tie salary configuration lines to payroll salary rules',
    'license': 'LGPL-3',
    'depends': [
        'salary_config',
        'hr_payroll_community',
        'hr_contract_salary',
    ],
    'data': [
        'data/salary_rule_sync_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
