# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    attendance_penalty_leave_type_id = fields.Many2one(
        'hr.leave.type',
        string='Attendance Penalty Time Off Type',
        domain="[('request_unit', '=', 'half_day')]",
        help='Time off type used when the system generates penalties from attendance infractions.',
    )
    attendance_late_grace_minutes = fields.Integer(
        string='Late Check-In Tolerance (minutes)',
        help='Minutes tolerated after the expected check-in time before creating a half-day penalty.',
    )
    attendance_early_checkout_grace_minutes = fields.Integer(
        string='Early Check-Out Tolerance (minutes)',
        help='Minutes tolerated before the expected check-out time (excluding lunch) before creating a half-day penalty.',
    )
    attendance_overtime_post_min_minutes = fields.Integer(
        related='company_id.attendance_overtime_post_min_minutes',
        readonly=False,
        string='Minimum Post-Shift Overtime (minutes)',
        help='Overtime is only counted when work exceeds this many minutes past the afternoon period end.',
    )

    @api.model
    def _get_default_penalty_leave_type(self):
        return self.env.ref('hr_attendance_calculs.leave_type_attendance_penalty', raise_if_not_found=False)

    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        default_leave_type = self._get_default_penalty_leave_type()

        def _get_int_param(key, default=0):
            value = params.get_param(key, default)
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        leave_type_id = params.get_param('hr_attendance_calculs.leave_type_id', default_leave_type.id if default_leave_type else False)
        res.update({
            'attendance_penalty_leave_type_id': int(leave_type_id) if leave_type_id else (default_leave_type.id if default_leave_type else False),
            'attendance_late_grace_minutes': _get_int_param('hr_attendance_calculs.late_grace_minutes', 0),
            'attendance_early_checkout_grace_minutes': _get_int_param('hr_attendance_calculs.early_checkout_grace_minutes', 0),
            'attendance_overtime_post_min_minutes': self.env.company.attendance_overtime_post_min_minutes,
        })
        return res

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('hr_attendance_calculs.leave_type_id', self.attendance_penalty_leave_type_id.id or False)
        params.set_param('hr_attendance_calculs.late_grace_minutes', self.attendance_late_grace_minutes or 0)
        params.set_param('hr_attendance_calculs.early_checkout_grace_minutes', self.attendance_early_checkout_grace_minutes or 0)
        company = self.env.company
        if self.attendance_overtime_post_min_minutes != company.attendance_overtime_post_min_minutes:
            company.attendance_overtime_post_min_minutes = self.attendance_overtime_post_min_minutes or 0
