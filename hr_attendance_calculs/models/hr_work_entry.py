# -*- coding: utf-8 -*-
from odoo import api, models


class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    @api.model_create_multi
    def create(self, vals_list):
        work_entries = super().create(vals_list)
        if not self.env.context.get('skip_penalty_compliance'):
            work_entries._ensure_penalty_alignment()
        return work_entries

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('skip_penalty_compliance') and {
            'date_start',
            'date_stop',
            'employee_id',
            'attendance_id',
            'work_entry_type_id',
            'active',
        } & set(vals.keys()):
            self._ensure_penalty_alignment()
        return res

    def _ensure_penalty_alignment(self):
        if not self:
            return
        if self.env.context.get('skip_penalty_compliance'):
            return

        attendance_type = self.env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)
        attendance_entries = self.filtered(lambda entry: entry.active and entry.attendance_id and (
            (attendance_type and entry.work_entry_type_id == attendance_type) or
            (entry.work_entry_type_id and entry.work_entry_type_id.code == 'WORK100')
        ))
        if not attendance_entries:
            return

        employees = attendance_entries.employee_id
        if not employees:
            return

        start = min(attendance_entries.mapped('date_start'))
        stop = max(attendance_entries.mapped('date_stop'))
        if not start or not stop:
            return

        penalty_leaves = self.env['hr.leave'].sudo().search([
            ('employee_id', 'in', employees.ids),
            ('state', 'not in', ['cancel', 'refuse']),
            ('date_from', '<', stop),
            ('date_to', '>', start),
            ('holiday_status_id.work_entry_type_id.code', '=', 'LEAVE_PENALTY'),
        ])
        if not penalty_leaves:
            return
        attendance_model = self.env['hr.attendance'].with_context(skip_penalty_compliance=True)
        attendance_model._adjust_attendance_work_entries(penalty_leaves)
        attendance_model._align_penalty_work_entries(penalty_leaves)
        for employee in employees:
            employee._deduplicate_penalty_entries_for_range(start, stop)
