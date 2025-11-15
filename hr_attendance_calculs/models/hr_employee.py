# -*- coding: utf-8 -*-
from datetime import date, datetime, time

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _align_attendance_entries_for_range(self, date_start, date_stop):
        """Utility to split attendance work entries for a given date span."""
        if not self:
            return

        start_dt = None
        stop_dt = None
        if date_start:
            start_date = fields.Date.to_date(date_start)
            if start_date:
                start_dt = datetime.combine(start_date, time.min)
        if date_stop:
            stop_date = fields.Date.to_date(date_stop)
            if stop_date:
                stop_dt = datetime.combine(stop_date, time.max)

        domain = [
            ('employee_id', 'in', self.ids),
            ('check_in', '!=', False),
            ('check_out', '!=', False),
        ]
        if start_dt:
            domain.append(('check_out', '>=', start_dt))
        if stop_dt:
            domain.append(('check_in', '<=', stop_dt))

        attendances = self.env['hr.attendance'].with_context(skip_penalty_compliance=True).search(domain)
        if attendances:
            attendances._ensure_attendance_work_entries_alignment()

    def _deduplicate_penalty_entries_for_range(self, date_start, date_stop):
        if not self:
            return
        if not date_start or not date_stop:
            return

        WorkEntry = self.env['hr.work.entry'].sudo()
        penalty_type = self.env.ref('hr_attendance_calculs.work_entry_type_attendance_penalty', raise_if_not_found=False)
        type_domain = [('work_entry_type_id', '=', penalty_type.id)] if penalty_type else [('work_entry_type_id.code', '=', 'LEAVE_PENALTY')]
        domain = [
            ('employee_id', 'in', self.ids),
            ('date_start', '<', date_stop),
            ('date_stop', '>', date_start),
        ] + type_domain

        penalty_entries = WorkEntry.search(domain, order='active desc, leave_id desc, id asc')
        if not penalty_entries:
            return

        duplicates = WorkEntry
        keepers = {}

        def _rank(entry):
            return (
                0 if entry.leave_id else 1,
                0 if entry.active else 1,
                0 if entry.state != 'validated' else 1,
                entry.id or 0,
            )

        for entry in penalty_entries:
            key = (
                entry.employee_id.id,
                entry.contract_id.id or 0,
                entry.work_entry_type_id.id or 0,
                entry.date_start,
                entry.date_stop,
            )
            chosen = keepers.get(key)
            if not chosen:
                keepers[key] = entry
                continue
            preferred = entry if _rank(entry) < _rank(chosen) else chosen
            discarded = chosen if preferred is entry else entry
            keepers[key] = preferred
            duplicates |= discarded

        if not duplicates:
            return

        removable = duplicates.filtered(lambda rec: rec.state != 'validated')
        if removable:
            removable.with_context(skip_penalty_compliance=True, hr_work_entry_no_check=True).unlink()

        remaining = (duplicates - removable).filtered(lambda rec: rec.active)
        if remaining:
            remaining.with_context(skip_penalty_compliance=True).write({'active': False})

    def _prune_calendar_work_entries(self, date_start, date_stop):
        if not self:
            return

        def _to_datetime(value, default_time):
            if not value:
                return None
            if isinstance(value, datetime):
                return value
            if isinstance(value, date):
                return datetime.combine(value, default_time)
            converted = fields.Datetime.to_datetime(value)
            if converted:
                return converted
            return None

        start_dt = _to_datetime(date_start, time.min)
        stop_dt = _to_datetime(date_stop, time.max)

        if start_dt and stop_dt and stop_dt <= start_dt:
            return

        WorkEntry = self.env['hr.work.entry'].sudo()
        attendance_type = self.env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)
        type_domain = [('work_entry_type_id', '=', attendance_type.id)] if attendance_type else [('work_entry_type_id.code', '=', 'WORK100')]

        domain = [
            ('employee_id', 'in', self.ids),
            ('attendance_id', '=', False),
            ('leave_id', '=', False),
            ('active', 'in', [True, False]),
        ] + type_domain

        if start_dt:
            domain.append(('date_stop', '>', start_dt))
        if stop_dt:
            domain.append(('date_start', '<', stop_dt))

        stale_entries = WorkEntry.search(domain)
        if not stale_entries:
            return

        removable = stale_entries.filtered(lambda entry: entry.state != 'validated')
        if removable:
            removable.with_context(skip_penalty_compliance=True, hr_work_entry_no_check=True).unlink()

        remaining = (stale_entries - removable).filtered(lambda entry: entry.active)
        if remaining:
            remaining.with_context(skip_penalty_compliance=True).write({'active': False})

    def _deduplicate_attendance_entries_for_range(self, date_start, date_stop):
        if not self:
            return

        def _to_datetime(value, default_time):
            if not value:
                return None
            if isinstance(value, datetime):
                return value
            if isinstance(value, date):
                return datetime.combine(value, default_time)
            converted = fields.Datetime.to_datetime(value)
            if converted:
                return converted
            return None

        start_dt = _to_datetime(date_start, time.min)
        stop_dt = _to_datetime(date_stop, time.max)

        if start_dt and stop_dt and stop_dt <= start_dt:
            return

        WorkEntry = self.env['hr.work.entry'].sudo()
        domain = [
            ('employee_id', 'in', self.ids),
            ('attendance_id', '!=', False),
            ('active', 'in', [True, False]),
        ]
        if start_dt:
            domain.append(('date_stop', '>', start_dt))
        if stop_dt:
            domain.append(('date_start', '<', stop_dt))

        attendance_entries = WorkEntry.search(domain, order='attendance_id asc, date_start asc, id asc')
        if not attendance_entries:
            return

        duplicates = WorkEntry
        keepers = {}

        def _rank(entry):
            return (
                0 if entry.state == 'validated' else 1,
                0 if entry.active else 1,
                entry.id or 0,
            )

        for entry in attendance_entries:
            key = (
                entry.attendance_id.id,
                entry.work_entry_type_id.id or 0,
                entry.date_start,
                entry.date_stop,
            )
            chosen = keepers.get(key)
            if not chosen:
                keepers[key] = entry
                continue
            preferred = entry if _rank(entry) < _rank(chosen) else chosen
            discarded = chosen if preferred is entry else entry
            keepers[key] = preferred
            duplicates |= discarded

        if not duplicates:
            return

        removable = duplicates.filtered(lambda rec: rec.state != 'validated')
        if removable:
            removable.with_context(skip_penalty_compliance=True, hr_work_entry_no_check=True).unlink()

        remaining = (duplicates - removable).filtered(lambda rec: rec.active)
        if remaining:
            remaining.with_context(skip_penalty_compliance=True).write({'active': False})
