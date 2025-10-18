# -*- coding: utf-8 -*-
{
    'name': 'HR GatePass',
    'summary': 'Gate Pass management for Employees, Visitors, Materials, Vehicles, Contractors with approvals, QR, and audit logs.',
    'description': """Comprehensive Gate Pass module
        - Employee/Visitor/Material/Vehicle/Contractor passes
        - Multi-level approvals and dynamic approvers
        - QR token issuance & scan verification
        - PDF printouts
        - Integrations: HR, Inventory, Fleet
        - Audit logs and dashboards
    """,
    'version': '18.0.1.0',
    'author': 'Akshat Gupta',
    'website': '',
    'category': 'Human Resources',
    'license': 'LGPL-3',
    'sequence': -1,
    'depends': ['base', 'mail', 'hr', 'stock', 'product', 'web'],
    'data': [
        'security/hr_gate_pass_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    'data/approval_profile_data.xml',
        'data/sequence_data.xml',
        'data/mail_templates.xml',
        'data/cron_data.xml',
        'report/gate_pass_reports.xml',
        'views/gate_pass_views.xml',
        'views/approval_profile_views.xml',
        'views/gate_views.xml',
        'views/incident_views.xml',
        'views/security_views.xml',
    'views/gate_log_views.xml',
        'views/menu.xml',
        'views/gate_pass_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [

            ('include', 'web._assets_helpers'),
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js',

            'hr_gate_pass/static/src/css/gate_pass_buttons.css',
            'hr_gate_pass/static/src/css/gate_pass_dashboard.css',
            'hr_gate_pass/static/src/js/gate_pass_dashboard.js',
            'hr_gate_pass/static/src/js/plant_layout.js',
            'hr_gate_pass/static/src/xml/gate_pass_dashboard.xml',
            'hr_gate_pass/static/src/xml/plant_layout_template.xml',
        ],
    },
    # 'assets': {
    #     'web.assets_backend': [
    #         # Add JS/CSS if needed later
    #     ],
    #     'web.assets_qweb': [
    #         # QWeb templates if any
    #     ],
    # },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}
