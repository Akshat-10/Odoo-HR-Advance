# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.fields import Datetime


class HrEmployeeActivity(models.Model):
    _name = 'hr.employee.activity'
    _description = 'Employee Attendance & Time Off Unified'
    _auto = False  # SQL view
    _order = 'start_datetime desc'

    name = fields.Char(string='Description')
    activity_type = fields.Selection([
        ('attendance', 'Attendance'),
        ('time_off', 'Time Off'),
    ], string='Type', index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', index=True)
    start_datetime = fields.Datetime(string='Start')
    end_datetime = fields.Datetime(string='End')
    duration_hours = fields.Float(string='Duration (h)')
    check_in = fields.Datetime(string='Check In')
    check_out = fields.Datetime(string='Check Out')
    leave_type_id = fields.Many2one('hr.leave.type', string='Time Off Type')
    # Alias for compatibility with hr_holidays calendar filters/tests (same relation)
    holiday_status_id = fields.Many2one(
        'hr.leave.type',
        string='Time Off Type',
        related='leave_type_id',
        store=False,
    )
    leave_id = fields.Many2one('hr.leave', string='Time Off')
    attendance_id = fields.Many2one('hr.attendance', string='Attendance')
    state = fields.Char(string='State')

    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        """Expose unusual days for the dashboard calendar.
        Delegates to hr.leave implementation to keep behavior consistent with Time Off dashboard.
        """
        return self.env['hr.leave'].get_unusual_days(date_from, date_to)

    def _select(self):
        return """
            -- Attendance lines
            SELECT
                a.id AS id,
                (
                    'Attendance: ' || to_char(a.check_in, 'YYYY-MM-DD HH24:MI') ||
                    COALESCE(' - ' || to_char(a.check_out, 'YYYY-MM-DD HH24:MI'), ' - ...')
                ) AS name,
                'attendance' AS activity_type,
                a.employee_id AS employee_id,
                a.check_in AS start_datetime,
                a.check_out AS end_datetime,
                EXTRACT(EPOCH FROM (COALESCE(a.check_out, a.check_in) - a.check_in))/3600.0 AS duration_hours,
                a.check_in AS check_in,
                a.check_out AS check_out,
                NULL::int AS leave_type_id,
                NULL::int AS leave_id,
                CASE WHEN a.check_out IS NULL THEN 'open' ELSE 'done' END AS state,
                a.id AS attendance_id
            FROM hr_attendance a
            WHERE a.check_in IS NOT NULL
            UNION ALL
            -- Time off leaves (ALL statuses)
            SELECT
                -l.id AS id,
                COALESCE(
                    NULLIF(l.private_name, ''),
                    'Time Off: ' || COALESCE(t.name->> 'en_US', t.name->> 'en', t.name::text)
                ) AS name,
                'time_off' AS activity_type,
                l.employee_id AS employee_id,
                l.date_from AS start_datetime,
                l.date_to AS end_datetime,
                EXTRACT(EPOCH FROM (l.date_to - l.date_from))/3600.0 AS duration_hours,
                NULL::timestamp AS check_in,
                NULL::timestamp AS check_out,
                l.holiday_status_id AS leave_type_id,
                l.id AS leave_id,
                l.state AS state,
                NULL::int AS attendance_id
            FROM hr_leave l
            LEFT JOIN hr_leave_type t ON t.id = l.holiday_status_id
            WHERE l.date_from IS NOT NULL AND l.date_to IS NOT NULL
        """

    def _from(self):
        return """( %s ) AS x""" % self._select()

    def _where(self):
        return """TRUE"""

    @api.model
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            "CREATE OR REPLACE VIEW %s AS (SELECT * FROM %s WHERE %s)" % (
                self._table,
                self._from(),
                self._where(),
            )
        )
