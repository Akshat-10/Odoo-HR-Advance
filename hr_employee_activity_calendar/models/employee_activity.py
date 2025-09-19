# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class HrEmployeeActivity(models.Model):
    _name = 'hr.employee.activity'
    _description = 'Employee Attendance & Time Off Unified'
    _auto = False  # SQL view
    _order = 'start_datetime desc'

    # keep SQL-provided label in base_name; compute name for UI
    base_name = fields.Char(string='Base Description')
    name = fields.Char(string='Description', compute='_compute_name', store=False)
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
    # Visual flags for base calendar hatch/strike styles
    is_hatched = fields.Boolean('Hatched', readonly=True)
    is_striked = fields.Boolean('Striked', readonly=True)

    # @api.depends('base_name', 'activity_type', 'leave_id')
    # def _compute_name(self):
    #     for rec in self:
    #         label = rec.base_name or ''
    #         if rec.activity_type == 'time_off' and rec.leave_id:
    #             # Append base-like friendly duration to label
    #             duration_txt = rec.leave_id.sudo().duration_display or ''
    #             if duration_txt:
    #                 label = f"{label}: {duration_txt}"
    #         rec.name = label

    @api.depends('base_name', 'activity_type', 'leave_id')
    def _compute_name(self):
        """Compute a clean display name for calendar items.
        - Attendance: use the SQL-provided base_name (e.g., "Attendance: 2025-09-19 09:00 - 17:00").
        - Time Off: use base_name (private_name or type label) and append duration if available.
        Never include employee name and never render falsy values like "False: False".
        """
        for rec in self:
            label = rec.base_name or ''
            if rec.activity_type == 'time_off' and rec.leave_id:
                # Append friendly duration only when available
                duration_txt = rec.leave_id.sudo().duration_display or ''
                if duration_txt:
                    label = f"{label}: {duration_txt}"
            rec.name = label
            
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
                ) AS base_name,
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
                a.id AS attendance_id,
                FALSE AS is_hatched,
                FALSE AS is_striked
            FROM hr_attendance a
            WHERE a.check_in IS NOT NULL
            UNION ALL
            -- Time off leaves (ALL statuses)
            SELECT
                -l.id AS id,
                COALESCE(
                    NULLIF(l.private_name, ''),
                    'Time Off: ' || COALESCE(t.name->> 'en_US', t.name->> 'en', t.name::text)
                ) AS base_name,
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
                NULL::int AS attendance_id,
                CASE WHEN l.state IN ('confirm', 'validate1') THEN TRUE ELSE FALSE END AS is_hatched,
                CASE WHEN l.state IN ('refuse', 'cancel') THEN TRUE ELSE FALSE END AS is_striked
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
