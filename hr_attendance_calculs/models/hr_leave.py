# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    attendance_auto_generated = fields.Boolean(default=False, copy=False)
    attendance_infraction_date = fields.Date(index=True, copy=False)
    attendance_infraction_type = fields.Selection(
        selection=[
            ('late_in', 'Late Check-In'),
            ('early_out', 'Early Check-Out'),
            ('lunch_early_out', 'Early Lunch Break Check-Out'),
            ('missing_shift', 'Missing Shift Attendance'),
        ],
        string='Attendance Infraction Type',
        copy=False,
    )
    attendance_infraction_portion = fields.Selection(
        selection=[
            ('am', 'Morning Half'),
            ('pm', 'Afternoon Half'),
            ('full', 'Full Day'),
        ],
        string='Attendance Penalty Portion',
        copy=False,
    )
    attendance_trigger_attendance_id = fields.Many2one(
        'hr.attendance',
        string='Trigger Attendance',
        copy=False,
        ondelete='set null',
    )

    @api.model
    def find_attendance_penalties(self, employee, target_date):
        """Convenience search helper for attendance penalties on a given date."""
        if not employee or not target_date:
            return self.env['hr.leave']
        return self.sudo().search([
            ('attendance_auto_generated', '=', True),
            ('employee_id', '=', employee.id),
            ('attendance_infraction_date', '=', target_date),
            ('state', '!=', 'cancel'),
        ])
