# -*- coding: utf-8 -*-
{
    
    "name": "Human Resources - KPI",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    'sequence': 1,
    "author": "Akshat Gupta",
    'license': 'LGPL-3',    
    'website': 'https://github.com/Akshat-10',
    "installable": True,
    "application": True,
    "summary": "Human Resources - Key Performance Index Management System",
    "depends": ["hr", "mail", 'web' ],
    "data": [
        "security/ir.model.access.csv",
        "data/kpi_sequence.xml",
        "views/kpi_views.xml",
        "views/category_views.xml",
    ],

    'assets': {
        'web.assets_backend': [
            'kpi/static/src/js/kpi_employee_list.js',
            'kpi/static/src/xml/kpi_employee_list.xml',
        ],
    },
    
}
