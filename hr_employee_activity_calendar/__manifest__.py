# -*- coding: utf-8 -*-
{
    'name': 'Employee Activity Calendar & Gantt',
    'version': '18.0.1.0',
    'summary': 'Unified calendar & gantt for Attendance and Time Off per employee',
    'category': 'Human Resources',
    'author': 'Akshat Gupta',
    'license': 'LGPL-3',
    'website': 'https://github.com/Akshat-10',
    'depends': ['hr', 'hr_attendance', 'hr_holidays', 'web_gantt', 'hr_attendance_gantt_enhanced'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_activity_views.xml',
        'views/employees_kanban.xml',
        'views/hr_employee_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_employee_activity_calendar/static/src/dashboard/employee_activity_dashboard.js',
            'hr_employee_activity_calendar/static/src/dashboard/employee_activity_dashboard.xml',
            'hr_employee_activity_calendar/static/src/dashboard/calendar_renderer_patch.js',
            'hr_employee_activity_calendar/static/src/dashboard/calendar_renderer_patch.xml',
            'hr_employee_activity_calendar/static/src/dashboard/time_off_dashboard_patch.js',
            'hr_employee_activity_calendar/static/src/dashboard/time_off_dashboard_patch.xml',
        ],
    },
    'installable': True,
    'application': True,
}
