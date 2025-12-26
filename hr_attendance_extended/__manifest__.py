# -*- coding: utf-8 -*-
{
    "name": "HR Attendance Extended - Bulk Attendance Entry",
    "version": "18.0.1.0.0",
    "category": "Human Resources/Attendances",
    "sequence": 10,
    "author": "Akshat Gupta",
    "license": "LGPL-3",
    "website": "https://github.com/Akshat-10",
    "installable": True,
    "application": False,
    "summary": "Bulk attendance entry for multiple employees with date range",
    "description": """
HR Attendance Extended - Bulk Attendance Entry
===============================================

This module extends the HR Attendance functionality to allow bulk attendance entry:

Features:
---------
* Add attendance for multiple employees at once
* Select date range (from date to end date)
* Specify check-in and check-out times
* Automatically creates attendance records for all selected employees
* Option to skip weekends
* Option to skip existing attendance records
* Preview of records to be created before confirmation

This saves significant time when entering attendance data for multiple employees
with the same schedule.
    """,
    "depends": [
        "hr_attendance",
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/hr_attendance_bulk_wizard_views.xml",
        "views/hr_attendance_menu.xml",
    ],
}
