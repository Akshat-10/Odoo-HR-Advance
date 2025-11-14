# -*- coding: utf-8 -*-
{
    'name': 'Salary Configuration Templates',
    'version': '1.0.0',
    'summary': 'Reusable salary structures applied to Offers',
    'category': 'Human Resources',
    'license': 'LGPL-3',
    "author": "Akshat Gupta",
    'sequence': 1,
    'depends': [
        'hr_contract_salary',
        'hr_contract_reports',
        'hr_recruitment',
        'hr_payroll_community',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/salary_config_code_data.xml',
        'data/salary_config_demo.xml',
        'views/salary_config_views.xml',
        'views/hr_contract_salary_offer_views_inherit.xml',
    ],
    'demo': [
        'data/salary_config_demo.xml',
        ],
    'installable': True,
    'application': False,
    'assets': {
        'web.assets_frontend': [
            'salary_config/static/src/xml/resume_sidebar_inherit.xml',
            'salary_config/static/src/xml/offer_modal.xml',
            'salary_config/static/src/js/hr_contract_salary_modal.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
}
