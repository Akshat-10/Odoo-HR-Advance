{
    'name': 'Salary Structure Calculation',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Salary Structurefor Employees',
    'description': """
        Salary Structure Calculation Module
        ====================================
        This module allows you to:
        * Create salary structures linked to HR employees
        * Calculate salary components dynamically based on CTC, Basic, etc.
        * Manage deductions and compliances
        * Track gross salary and in-hand salary
    """,
    'author': 'Megha',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/salary_structure_calculation_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}