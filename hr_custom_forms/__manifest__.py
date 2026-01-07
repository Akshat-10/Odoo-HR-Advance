# -*- coding: utf-8 -*-
{
    
    "name": "Human Resources Forms",
    "version": "18.0.0.1",
    "category": "Human Resources",
    'sequence': -5,
    "author": "Akshat Gupta",
    'license': 'LGPL-3',    
    'website': 'https://github.com/Akshat-10',
    "installable": True,
    "application": False,
    "summary": "Human Resources Forms",
    "depends": [ "hr_employee_entended", "hr", "mail" ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/hr_custom_form_views.xml",
    ],
    
    
}
