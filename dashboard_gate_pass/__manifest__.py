{
    'name': 'Gate Pass Dashboard',
    'version': '18.0.1.0',
    'summary': 'Gate Pass ',
    'description': '',
    'author': 'Balaji',
    'website': '',
    'license': 'LGPL-3',
    'sequence': -1,

    'depends': ['base', 'web', 'mail', 'EHS', 'monitoring_areas','hr_gate_pass','ehs_monitoring_areas_link','hr_gate_pass_ehs_link'],
    'data': [
        'views/gate_pass_action.xml',

    ],
    'assets': {
        'web.assets_backend': [
            "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js",

            'dashboard_gate_pass/static/css/gate_pass.css',
            'dashboard_gate_pass/static/js/gate_pass_dashboard.esm.js',
            'dashboard_gate_pass/static/xml/gate_pass_templates.xml',

        ],
    },
    'installable': True,
    'application': True,
}
