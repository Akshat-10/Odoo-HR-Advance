# -*- coding: utf-8 -*-
{
    
    "name": "Human Resources Forms Reporting",
    "version": "18.0.0.0",
    "category": "Human Resources",
    'sequence': -5,
    "author": "Akshat Gupta",
    'license': 'LGPL-3',    
    'website': 'https://github.com/Akshat-10',
    "installable": True,
    "application": True,
    "summary": "Human Resources Forms Reporting",
    "depends": [ "hr_custom_forms" , "hr_recruitment_extended"],
    "data": [
        'views/resignation_letter_views.xml',
        'report/resignation_action.xml',
        'report/resignation_report.xml',
        'views/leave_application_views.xml',
        'views/form15G_views.xml',
        'views/form_11_newsept_17_views.xml',
        'views/recruitment_views.xml',

        "views/covering_letter_views.xml",
        'report/covering_letter_action.xml',
        'report/covering_letter_report.xml',

        "views/mw_notice_views.xml",
        "views/formd_excel_views.xml",
        "views/form2_word_views.xml",
        "views/er1_word_views.xml",


        ],
}