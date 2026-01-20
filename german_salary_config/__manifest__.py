# -*- coding: utf-8 -*-
{
    'name': 'German TMT Salary Configuration',
    'version': '1.0.0',
    'summary': 'German TMT Salary Structure for Contracts',
    'description': """
        This module provides the German TMT Salary Structure configuration.
        
        Salary Components:
        - Basic (50% of monthly CTC - bonus)
        - HRA (40% of Basic)
        - Conveyance (10% of Basic)
        - LTA (10% of Basic)
        - Other Allowance (balance amount)
        - TOTAL (sum of all allowances)
        - Bonus (fixed 1200)
        - Payable (Total + Bonus)
        - PF Salary (conditional based on is_pf_deduct)
        - In Hand (Payable - PF Salary)
        
        Note: is_pf_deduct field is provided by contract_salary_config module.
    """,
    'category': 'Human Resources/Contracts',
    'license': 'LGPL-3',
    'author': 'Akshat Gupta',
    'sequence': 1,
    'depends': [
        'contract_salary_config',  # Inherits salary structure on contracts
    ],
    'data': [
        'data/german_salary_structure_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
