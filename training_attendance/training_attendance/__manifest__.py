
{
    "name": "Training Attendance",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "Training Attendance Register",
    'author': 'Balaji',
    'sequence': -4,
    "depends": ['base', "hr"],
    "data": [
        "security/ir.model.access.csv",
        "views/training_attendance_views.xml",
    ],
    "installable": True,
    "application": True,
    'auto_install': False,
    'license': 'LGPL-3',
}
