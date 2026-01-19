# -*- coding: utf-8 -*-
{
    'name': 'Contract Salary Configuration',
    'version': '1.0.0',
    'summary': 'Salary bifurcation/structure directly on Employee Contracts',
    'description': """
        This module adds salary structure configuration directly to hr.contract model.
        Users can configure salary breakdowns (Basic, HRA, PF, etc.) on the contract
        without needing to create separate salary offers.
        
        Features:
        - Salary structure lines on contracts with automatic calculation
        - Uses final_yearly_costs and monthly_yearly_costs from hr_contract_salary
        - Bonus field with configurable amount (default 1200)
        - Support for percentage, fixed amount, and formula-based computations
        - Integration with existing salary.config.structure templates
        - Automatic population from structure type defaults
        - Monthly and annual amount display
        
        Formula Variables:
        - final_yearly_costs: Annual CTC from contract
        - monthly_yearly_costs: Monthly CTC (final_yearly_costs / 12)
        - bonus: Bonus amount from contract
        - amount('CODE'): Get computed amount of another salary component by code
    """,
    'category': 'Human Resources/Contracts',
    'license': 'LGPL-3',
    'author': 'Akshat Gupta',
    'sequence': 1,
    'depends': [
        'hr_contract_salary',  # Provides final_yearly_costs, monthly_yearly_costs
        'hr_payroll',
        'salary_config',  # Reuses salary.config.structure templates
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
