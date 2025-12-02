# -*- coding: utf-8 -*-
{
    'name': 'HR Multi Contract Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'sequence': 2,
    'author': 'Akshat Gupta',
    'license': 'LGPL-3',
    'website': 'https://github.com/Akshat-10',
    'summary': 'Create multiple employee contracts at once with custom field support',
    'description': """
HR Multi Contract Management
==============================
This module allows you to:
* Create multiple employee contracts at once
* Mass create contracts from employee list view
* Automatically fetch custom fields like Employee Code, Father Name
* Auto-populate contract start date from employee joining date
* Manage contracts efficiently through dedicated interface
    """,
    'depends': [
        'hr',
        'hr_contract',
        'hr_employee_entended',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/hr_mass_contract_wizard_views.xml',
        'views/hr_multi_contract_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
