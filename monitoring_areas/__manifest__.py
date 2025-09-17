# -*- coding: utf-8 -*-
{
    'name': 'Monitoring Areas with QR Codes',
    'version': '18.0.1.0',
    'summary': 'Monitor work permit areas with QR generation',
    'description': 'Simple module to manage Areas and generate QR codes for monitoring records.',
    'author': 'Akshat Gupta',
    'license': 'LGPL-3',
    'website': '',
    'sequence': -3,
    'category': 'Operations/Safety',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/monitoring_areas_views.xml',
    ],
    'assets': {},
    'installable': True,
    'application': True,
}
