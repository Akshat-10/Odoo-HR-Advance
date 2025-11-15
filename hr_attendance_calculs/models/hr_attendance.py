# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
import pytz

from odoo import api, fields, models, _


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model_create_multi
    def create(self, vals_list):
        attendances = super().create(vals_list)
        if attendances:
            attendances._process_attendance_penalties(check_create=True)
            # Also ensure work entries are split per calendar right away for closed attendances
            to_align = attendances.filtered(lambda a: a.check_in and a.check_out)
            if to_align:
                to_align._ensure_attendance_work_entries_alignment()
        return attendances

    def write(self, vals):
        process_check_in = 'check_in' in vals and vals.get('check_in')
        process_check_out = 'check_out' in vals and vals.get('check_out')
        result = super().write(vals)
        if process_check_in or process_check_out:
            self._process_attendance_penalties(
                check_in=process_check_in,
                check_out=process_check_out,
            )
            # After penalties, align attendance WE segments with calendar for records having both bounds
            to_align = self.filtered(lambda a: a.check_in and a.check_out)
            if to_align:
                to_align._ensure_attendance_work_entries_alignment()
        return result

    def _create_work_entries(self):
        res = super()._create_work_entries()
        attendances_with_bounds = self.filtered(lambda att: att.check_in and att.check_out)
        if attendances_with_bounds:
            attendances_with_bounds._ensure_attendance_work_entries_alignment()
        return res

    # ---------------------------------------------------------------------
    # Core processing
    # ---------------------------------------------------------------------

    def _process_attendance_penalties(self, check_create=False, check_in=False, check_out=False):
        if not self:
            return
        config = self._get_penalty_configuration()
        leave_type = config.get('leave_type')
        if not leave_type:
            return

        for attendance in self:
            employee = attendance.employee_id
            if not employee or not employee.resource_calendar_id or not employee.resource_id:
                continue

            tz = attendance._get_employee_timezone(employee)
            if (check_create or check_in) and attendance.check_in:
                attendance._handle_late_check_in(employee, leave_type, tz, config)
            if (check_create or check_out) and attendance.check_out:
                attendance._handle_early_check_out(employee, leave_type, tz, config)

    # ---------------------------------------------------------------------
    # Handlers
    # ---------------------------------------------------------------------

    def _handle_late_check_in(self, employee, leave_type, tz, config):
        self.ensure_one()
        local_check_in = self._to_employee_datetime(self.check_in, tz)
        if not local_check_in:
            return

        day_intervals = self._get_day_intervals(employee, local_check_in.date(), tz)
        if not day_intervals:
            return

        interval = self._get_interval_for_datetime(day_intervals, local_check_in)
        if not interval:
            # take next interval the employee is supposed to work in the future of that day
            interval = self._get_next_interval(day_intervals, local_check_in)
        if not interval:
            return

        expected_start, expected_end, attendance_line = interval
        delay_minutes = (local_check_in - expected_start).total_seconds() / 60.0
        portion = self._map_day_period_to_portion(attendance_line.day_period)
        if portion not in {'am', 'pm'}:
            # default morning when period unknown
            portion = 'am'

        self._apply_missing_prior_shift_penalties(
            employee=employee,
            leave_type=leave_type,
            day_intervals=day_intervals,
            local_check_in=local_check_in,
        )

        if delay_minutes <= config['late_grace']:
            self._clear_existing_penalties(
                employee=employee,
                target_date=local_check_in.date(),
                portion=portion,
                infraction_types={'late_in'},
            )
            return

        missing_start = expected_start
        missing_end = local_check_in
        if self._has_regular_leave_covering(employee, leave_type, missing_start, missing_end):
            self._clear_existing_penalties(
                employee=employee,
                target_date=local_check_in.date(),
                portion=portion,
                infraction_types={'late_in'},
            )
            return

        description = _(
            "Auto penalty: Late check-in at %(actual)s (expected %(expected)s).",
            actual=local_check_in.strftime('%H:%M'),
            expected=expected_start.strftime('%H:%M'),
        )
        self._ensure_half_day_penalty(
            employee=employee,
            leave_type=leave_type,
            target_date=local_check_in.date(),
            portion=portion,
            infraction_type='late_in',
            description=description,
        )

    def _handle_early_check_out(self, employee, leave_type, tz, config):
        self.ensure_one()
        local_check_out = self._to_employee_datetime(self.check_out, tz)
        if not local_check_out:
            return

        local_check_in = self._to_employee_datetime(self.check_in, tz) if self.check_in else None

        day_intervals = self._get_day_intervals(employee, local_check_out.date(), tz)
        if not day_intervals:
            return

        interval = self._get_interval_for_datetime(day_intervals, local_check_out)
        if not interval:
            interval = self._get_previous_interval(day_intervals, local_check_out)
        if not interval:
            return

        expected_start, expected_end, attendance_line = interval
        early_minutes = (expected_end - local_check_out).total_seconds() / 60.0

        portion = self._map_day_period_to_portion(attendance_line.day_period)
        if portion not in {'am', 'pm'}:
            portion = 'pm'

        base_description = _(
            "Auto penalty: Early check-out at %(actual)s (expected %(expected)s).",
            actual=local_check_out.strftime('%H:%M'),
            expected=expected_end.strftime('%H:%M'),
        )

        full_day_penalty = False
        full_day_context = {}
        if local_check_in:
            full_day_penalty, full_day_context = self._should_apply_full_day_penalty(
                employee=employee,
                day_intervals=day_intervals,
                local_check_in=local_check_in,
                local_check_out=local_check_out,
                config=config,
            )

        if full_day_penalty:
            description_parts = [base_description]
            reason = full_day_context.get('reason')
            if reason == 'morning':
                cutoff = full_day_context.get('morning_cutoff')
                cutoff_str = cutoff.astimezone(tz).strftime('%H:%M') if cutoff else False
                description_parts.append(_(
                    "Full-day penalty applied: departure occurred before completing the morning shift (ended at %(cutoff)s).",
                    cutoff=cutoff_str or '--:--',
                ))
            elif reason == 'half':
                worked_hours = full_day_context.get('worked_hours')
                minimum_hours = full_day_context.get('minimum_hours')
                if worked_hours is not None and minimum_hours is not None:
                    description_parts.append(_(
                        "Full-day penalty applied: worked %(worked)s h (< %(minimum)s h required).",
                        worked=f"{worked_hours:.2f}",
                        minimum=f"{minimum_hours:.2f}",
                    ))
                else:
                    description_parts.append(_("Full-day penalty applied due to insufficient worked hours."))
            description = " ".join(description_parts)
            self._ensure_full_day_penalty(
                employee=employee,
                leave_type=leave_type,
                target_date=local_check_out.date(),
                infraction_type='early_out',
                description=description,
            )
            return

        self._apply_missing_following_shift_penalties(
            employee=employee,
            leave_type=leave_type,
            day_intervals=day_intervals,
            local_check_out=local_check_out,
        )

        if early_minutes <= 0:
            return

        if early_minutes <= config['early_grace']:
            self._clear_existing_penalties(
                employee=employee,
                target_date=local_check_out.date(),
                portion=portion,
                infraction_types={'early_out'},
            )
            return

        # Clear legacy full-day penalties generated for lunch departures so a half-day can be applied instead.
        self._clear_existing_penalties(
            employee=employee,
            target_date=local_check_out.date(),
            portion='full',
            infraction_types={'lunch_early_out'},
        )

        missing_start = local_check_out
        missing_end = expected_end
        if self._has_regular_leave_covering(employee, leave_type, missing_start, missing_end):
            self._clear_existing_penalties(
                employee=employee,
                target_date=local_check_out.date(),
                portion=portion,
                infraction_types={'early_out'},
            )
            return

        self._ensure_half_day_penalty(
            employee=employee,
            leave_type=leave_type,
            target_date=local_check_out.date(),
            portion=portion,
            infraction_type='early_out',
            description=base_description,
        )

    # ---------------------------------------------------------------------
    # Leave creation helpers
    # ---------------------------------------------------------------------

    def _ensure_half_day_penalty(self, employee, leave_type, target_date, portion, infraction_type, description):
        leave_model = self.env['hr.leave']
        existing = leave_model.find_attendance_penalties(employee, target_date)
        if existing.filtered(lambda leave: leave.attendance_infraction_portion == 'full'):
            return
        half_existing = existing.filtered(lambda leave: leave.attendance_infraction_portion == portion)
        if half_existing:
            half_existing.sudo().with_context(
                leave_skip_date_check=True,
                leave_skip_state_check=True,
            ).write({
                'name': description,
                'attendance_infraction_type': infraction_type,
                'attendance_trigger_attendance_id': self.id,
            })
            self._refresh_leave_work_entries(half_existing)
            return

        new_leave = leave_model.sudo().create({
            'name': description,
            'employee_id': employee.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': target_date,
            'request_date_to': target_date,
            'request_unit_half': True,
            'request_date_from_period': portion,
            'attendance_auto_generated': True,
            'attendance_infraction_date': target_date,
            'attendance_infraction_type': infraction_type,
            'attendance_infraction_portion': portion,
            'attendance_trigger_attendance_id': self.id,
        })
        self._refresh_leave_work_entries(new_leave)
        return new_leave

    def _ensure_full_day_penalty(self, employee, leave_type, target_date, infraction_type, description):
        leave_model = self.env['hr.leave']
        existing = leave_model.find_attendance_penalties(employee, target_date)
        if existing:
            primary = existing[0]
            extra = existing - primary
            if extra:
                extra.sudo().with_context(
                    leave_skip_date_check=True,
                    leave_skip_state_check=True,
                ).action_refuse()
            primary.sudo().with_context(
                leave_skip_date_check=True,
                leave_skip_state_check=True,
            ).write({
                'name': description,
                'attendance_auto_generated': True,
                'attendance_infraction_date': target_date,
                'attendance_infraction_type': infraction_type,
                'attendance_infraction_portion': 'full',
                'attendance_trigger_attendance_id': self.id,
                'request_date_from': target_date,
                'request_date_to': target_date,
                'request_unit_half': False,
                'request_date_from_period': False,
            })
            self._refresh_leave_work_entries(primary)
            return primary

        new_leave = leave_model.sudo().create({
            'name': description,
            'employee_id': employee.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': target_date,
            'request_date_to': target_date,
            'attendance_auto_generated': True,
            'attendance_infraction_date': target_date,
            'attendance_infraction_type': infraction_type,
            'attendance_infraction_portion': 'full',
            'attendance_trigger_attendance_id': self.id,
            'request_unit_half': False,
            'request_date_from_period': False,
        })
        self._refresh_leave_work_entries(new_leave)
        return new_leave

    def _clear_existing_penalties(self, employee, target_date, portion=None, infraction_types=None):
        leave_model = self.env['hr.leave']
        leaves = leave_model.find_attendance_penalties(employee, target_date)
        if not leaves:
            return
        leaves = leaves.filtered(lambda l: l.attendance_trigger_attendance_id == self.id)
        if portion:
            if portion == 'full':
                leaves = leaves.filtered(lambda l: l.attendance_infraction_portion == 'full')
            else:
                leaves = leaves.filtered(lambda l: l.attendance_infraction_portion == portion)
        if infraction_types:
            leaves = leaves.filtered(lambda l: l.attendance_infraction_type in infraction_types)
        if leaves:
            leaves.sudo().with_context(
                leave_skip_date_check=True,
                leave_skip_state_check=True,
            ).action_refuse()

    # ---------------------------------------------------------------------
    # Attendance work entry helpers
    # ---------------------------------------------------------------------

    def _ensure_attendance_work_entries_alignment(self):
        WorkEntry = self.env['hr.work.entry'].sudo()
        WorkEntryCtx = WorkEntry.with_context(skip_penalty_compliance=True)
        for attendance in self:
            if not attendance.check_in or not attendance.check_out:
                continue
            employee = attendance.employee_id
            if not employee or not employee.resource_calendar_id or not employee.resource_id:
                continue
            tz = attendance._get_employee_timezone(employee)
            local_check_in = attendance._to_employee_datetime(attendance.check_in, tz)
            local_check_out = attendance._to_employee_datetime(attendance.check_out, tz)
            if not local_check_in or not local_check_out or local_check_out <= local_check_in:
                continue

            # Compute regular attendance segments (within planned hours, excluding lunch)
            segments = attendance._compute_attendance_segments(employee, local_check_in, local_check_out, tz)
            
            # Find all leaves (penalties and unpaid) that affect this attendance period
            check_in_utc = local_check_in.astimezone(pytz.UTC).replace(tzinfo=None)
            check_out_utc = local_check_out.astimezone(pytz.UTC).replace(tzinfo=None)
            
            # Get penalty leave intervals
            penalty_leaves = attendance.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', 'not in', ['cancel', 'refuse']),
                ('date_from', '<', check_out_utc),
                ('date_to', '>', check_in_utc),
                ('holiday_status_id.work_entry_type_id.code', '=', 'LEAVE_PENALTY'),
            ])
            
            penalty_intervals = []
            for leave in penalty_leaves:
                penalty_intervals.extend(attendance._get_penalty_intervals(leave))
            
            # Get unpaid leave work entries that overlap with this attendance
            unpaid_work_entries = WorkEntry.search([
                ('employee_id', '=', employee.id),
                ('state', '!=', 'cancelled'),
                ('date_start', '<', check_out_utc),
                ('date_stop', '>', check_in_utc),
                '|',
                ('work_entry_type_id.code', '=', 'LEAVE110'),  # Unpaid leave
                ('leave_id.holiday_status_id.unpaid', '=', True),  # Any unpaid leave type
            ])
            
            # Get intervals from unpaid work entries
            unpaid_intervals = [(entry.date_start, entry.date_stop) for entry in unpaid_work_entries]
            
            # Combine all intervals to exclude from attendance
            all_excluded_intervals = penalty_intervals + unpaid_intervals
            
            if all_excluded_intervals:
                segments = attendance._subtract_intervals_from_segments(segments, all_excluded_intervals)
            segments = [segment for segment in segments if (segment[1] - segment[0]).total_seconds() > 0]

            # Compute overtime segments (outside planned hours)
            # Also exclude unpaid leave intervals from overtime
            overtime_segments = attendance._compute_overtime_segments(employee, local_check_in, local_check_out, tz)
            if unpaid_intervals and overtime_segments:
                overtime_segments = attendance._subtract_intervals_from_segments(overtime_segments, unpaid_intervals)
                overtime_segments = [segment for segment in overtime_segments if (segment[1] - segment[0]).total_seconds() > 0]

            entries = WorkEntry.search([
                ('attendance_id', '=', attendance.id),
                ('active', 'in', [True, False]),
            ], order='date_start')

            if not segments and not overtime_segments:
                residual = entries.filtered(lambda entry: entry.state != 'validated')
                if residual:
                    residual.with_context(skip_penalty_compliance=True).write({'active': False})
                continue

            if entries.filtered(lambda entry: entry.state == 'validated'):
                # Avoid altering validated work entries.
                continue

            # Get work entry types
            attendance_type = attendance._get_attendance_work_entry_type(entries)
            overtime_type = attendance._get_overtime_work_entry_type()

            base_contract = entries[:1].contract_id if entries else False
            reusable_entries = list(entries)
            updated_entries = attendance.env['hr.work.entry']
            entry_idx = 0

            # Create/update regular attendance work entries
            for segment_start, segment_stop, segment_portion in segments:
                if not attendance_type:
                    continue
                contract = base_contract
                if not contract:
                    contract = employee._get_contracts(segment_start, segment_stop, states=['open', 'close'])[:1]
                if not contract:
                    continue
                portion_label = segment_portion.upper() if segment_portion in {'am', 'pm'} else 'FULL'
                entry_name = _('Attendance (%s): %s') % (portion_label, employee.name or attendance.id)
                vals = {
                    'attendance_id': attendance.id,
                    'employee_id': employee.id,
                    'contract_id': contract.id,
                    'company_id': contract.company_id.id or employee.company_id.id,
                    'date_start': segment_start,
                    'date_stop': segment_stop,
                    'work_entry_type_id': attendance_type.id,
                    'leave_id': False,
                    'active': True,
                    'name': entry_name,
                }
                if entry_idx < len(reusable_entries):
                    entry = reusable_entries[entry_idx].with_context(skip_penalty_compliance=True)
                    entry.write(vals)
                    updated_entries |= entry
                    entry_idx += 1
                else:
                    new_entry = WorkEntryCtx.create(vals)
                    updated_entries |= new_entry

            # Create/update overtime work entries
            for segment_start, segment_stop, segment_portion in overtime_segments:
                if not overtime_type:
                    continue
                contract = base_contract
                if not contract:
                    contract = employee._get_contracts(segment_start, segment_stop, states=['open', 'close'])[:1]
                if not contract:
                    continue
                entry_name = _('Overtime: %s') % (employee.name or attendance.id)
                vals = {
                    'attendance_id': attendance.id,
                    'employee_id': employee.id,
                    'contract_id': contract.id,
                    'company_id': contract.company_id.id or employee.company_id.id,
                    'date_start': segment_start,
                    'date_stop': segment_stop,
                    'work_entry_type_id': overtime_type.id,
                    'leave_id': False,
                    'active': True,
                    'name': entry_name,
                }
                if entry_idx < len(reusable_entries):
                    entry = reusable_entries[entry_idx].with_context(skip_penalty_compliance=True)
                    entry.write(vals)
                    updated_entries |= entry
                    entry_idx += 1
                else:
                    new_entry = WorkEntryCtx.create(vals)
                    updated_entries |= new_entry

            residual = (entries - updated_entries).filtered(lambda entry: entry.state != 'validated')
            if residual:
                residual.with_context(skip_penalty_compliance=True).write({'active': False})

            employee._prune_calendar_work_entries(attendance.check_in, attendance.check_out)
            employee._deduplicate_attendance_entries_for_range(attendance.check_in, attendance.check_out)

    def _compute_attendance_segments(self, employee, local_check_in, local_check_out, tz):
        self.ensure_one()
        segments = []
        calendar = employee.resource_calendar_id
        calendar_has_attendances = bool(calendar and calendar.attendance_ids)
        current_date = local_check_in.date()
        end_date = local_check_out.date()
        while current_date <= end_date:
            day_intervals = self._get_day_intervals(employee, current_date, tz)
            for interval_start, interval_stop, attendance_line in day_intervals:
                raw_period = getattr(attendance_line, 'day_period', False)
                # Skip lunch/break intervals entirely; we only want working periods.
                if raw_period == 'lunch':
                    continue
                portion = self._map_day_period_to_portion(raw_period) or 'am'
                effective_start = max(interval_start, local_check_in)
                effective_stop = min(interval_stop, local_check_out)
                if effective_stop <= effective_start:
                    continue
                segments.append((
                    effective_start.astimezone(pytz.UTC).replace(tzinfo=None),
                    effective_stop.astimezone(pytz.UTC).replace(tzinfo=None),
                    portion,
                ))
            current_date += timedelta(days=1)

        if not segments:
            # Only fall back to attendance if the employee has no planned schedule at all.
            if not calendar_has_attendances:
                segments.append((
                    local_check_in.astimezone(pytz.UTC).replace(tzinfo=None),
                    local_check_out.astimezone(pytz.UTC).replace(tzinfo=None),
                    'am',
                ))
            else:
                return []
        return self._merge_segments(segments)

    def _compute_overtime_segments(self, employee, local_check_in, local_check_out, tz):
        """
        Compute overtime segments - periods where employee worked outside planned hours.
        Returns list of tuples: (start_utc, stop_utc, 'overtime')
        """
        self.ensure_one()
        overtime_segments = []
        
        # Get company thresholds
        company = employee.company_id
        post_min_threshold_minutes = company.attendance_overtime_post_min_minutes or 0
        calendar = employee.resource_calendar_id
        calendar_has_attendances = bool(calendar and calendar.attendance_ids)
        
        current_date = local_check_in.date()
        end_date = local_check_out.date()
        
        while current_date <= end_date:
            day_intervals = self._get_day_intervals(employee, current_date, tz)
            day_start_local = tz.localize(datetime.combine(current_date, time.min))
            day_end_local = tz.localize(datetime.combine(current_date, time.max))
            day_check_in = max(local_check_in, day_start_local)
            day_check_out = min(local_check_out, day_end_local)
            if day_check_out <= day_check_in:
                current_date += timedelta(days=1)
                continue

            if not day_intervals:
                # No planned work on this day: treat any attendance as pure overtime
                if calendar_has_attendances:
                    overtime_segments.append((
                        day_check_in.astimezone(pytz.UTC).replace(tzinfo=None),
                        day_check_out.astimezone(pytz.UTC).replace(tzinfo=None),
                        'overtime',
                    ))
                else:
                    # Fully flexible calendar, fallback handled by attendance segments
                    pass
                current_date += timedelta(days=1)
                continue
            
            # Find planned working periods for the day (excluding lunch)
            working_intervals = []
            for interval_start, interval_stop, attendance_line in day_intervals:
                raw_period = getattr(attendance_line, 'day_period', False)
                if raw_period == 'lunch':
                    continue
                working_intervals.append((interval_start, interval_stop))
            
            if not working_intervals:
                current_date += timedelta(days=1)
                continue
            
            # Determine the last planned working time for the day
            last_planned_end = max(interval_stop for interval_start, interval_stop in working_intervals)
            first_planned_start = min(interval_start for interval_start, interval_stop in working_intervals)
            
            # Check if attendance extends beyond planned hours
            # Post-work overtime (after last planned end)
            if day_check_out > last_planned_end:
                overtime_start = max(last_planned_end, day_check_in)
                overtime_duration_minutes = (day_check_out - overtime_start).total_seconds() / 60.0
                
                if overtime_duration_minutes >= post_min_threshold_minutes:
                    overtime_segments.append((
                        overtime_start.astimezone(pytz.UTC).replace(tzinfo=None),
                        day_check_out.astimezone(pytz.UTC).replace(tzinfo=None),
                        'overtime',
                    ))
            
            current_date += timedelta(days=1)
        
        return overtime_segments

    @staticmethod
    def _merge_segments(segments):
        if not segments:
            return []
        ordered = sorted(segments, key=lambda segment: (segment[2], segment[0], segment[1]))
        merged = []
        for start, stop, portion in ordered:
            if not merged:
                merged.append([start, stop, portion])
                continue
            last_start, last_stop, last_portion = merged[-1]
            # Merge only if same portion (am/pm) and overlapping/contiguous
            if portion == last_portion and start <= last_stop:
                merged[-1][1] = max(last_stop, stop)
            else:
                merged.append([start, stop, portion])
        return [(s[0], s[1], s[2]) for s in merged]

    @staticmethod
    def _subtract_intervals_from_segments(segments, intervals):
        if not segments or not intervals:
            return segments
        remaining = []
        for seg_start, seg_stop, portion in segments:
            parts = [(seg_start, seg_stop)]
            for interval_start, interval_stop in intervals:
                updated_parts = []
                for part_start, part_stop in parts:
                    if interval_stop <= part_start or interval_start >= part_stop:
                        updated_parts.append((part_start, part_stop))
                        continue
                    if interval_start > part_start:
                        updated_parts.append((part_start, interval_start))
                    if interval_stop < part_stop:
                        updated_parts.append((interval_stop, part_stop))
                parts = updated_parts
            remaining.extend([(start, stop, portion) for start, stop in parts if start < stop])
        return remaining

    def _get_attendance_work_entry_type(self, existing_entries):
        self.ensure_one()
        # Always return the standard Attendance work entry type
        attendance_type = self.env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)
        if attendance_type:
            return attendance_type
        fallback = self.env['hr.work.entry.type'].search([('code', '=', 'WORK100')], limit=1)
        return fallback

    def _get_overtime_work_entry_type(self):
        self.ensure_one()
        # Return the Overtime Hours work entry type
        overtime_type = self.env.ref('hr_work_entry.overtime_work_entry_type', raise_if_not_found=False)
        if overtime_type:
            return overtime_type
        fallback = self.env['hr.work.entry.type'].search([('code', '=', 'OVERTIME')], limit=1)
        return fallback

    def _has_regular_leave_covering(self, employee, penalty_leave_type, start_dt, end_dt):
        if not employee or not start_dt or not end_dt or start_dt >= end_dt:
            return False
        leave_model = self.env['hr.leave'].sudo()
        start_utc = start_dt.astimezone(pytz.UTC).replace(tzinfo=None)
        end_utc = end_dt.astimezone(pytz.UTC).replace(tzinfo=None)
        domain = [
            ('employee_id', '=', employee.id),
            ('attendance_auto_generated', '=', False),
            ('state', 'not in', ['cancel', 'refuse']),
            ('date_from', '<', end_utc),
            ('date_to', '>', start_utc),
        ]
        if penalty_leave_type:
            domain.append(('holiday_status_id', '!=', penalty_leave_type.id))
        return bool(leave_model.search(domain, limit=1))

    def _has_unpaid_leave_covering(self, employee, start_dt, end_dt):
        """Check if there is any unpaid leave covering the given time period."""
        if not employee or not start_dt or not end_dt or start_dt >= end_dt:
            return False
        
        start_utc = start_dt.astimezone(pytz.UTC).replace(tzinfo=None)
        end_utc = end_dt.astimezone(pytz.UTC).replace(tzinfo=None)
        
        # Check for unpaid leave work entries
        unpaid_work_entries = self.env['hr.work.entry'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '!=', 'cancelled'),
            ('date_start', '<', end_utc),
            ('date_stop', '>', start_utc),
            '|',
            ('work_entry_type_id.code', '=', 'LEAVE110'),  # Unpaid leave
            ('leave_id.holiday_status_id.unpaid', '=', True),  # Any unpaid leave type
        ], limit=1)
        
        return bool(unpaid_work_entries)

    def _apply_missing_prior_shift_penalties(self, employee, leave_type, day_intervals, local_check_in):
        if not employee or not leave_type or not day_intervals or not local_check_in:
            return
        processed_portions = set()
        for interval_start, interval_stop, attendance_line in sorted(day_intervals, key=lambda x: x[0]):
            portion = self._map_day_period_to_portion(getattr(attendance_line, 'day_period', False))
            if portion not in {'am', 'pm'} or portion in processed_portions:
                continue
            if interval_start <= local_check_in <= interval_stop:
                self._clear_existing_penalties(
                    employee=employee,
                    target_date=local_check_in.date(),
                    portion=portion,
                    infraction_types={'missing_shift'},
                )
                processed_portions.add(portion)
                break
            if local_check_in <= interval_start:
                # Employee arrived before the start of this shift; clear any pending penalty for it.
                self._clear_existing_penalties(
                    employee=employee,
                    target_date=local_check_in.date(),
                    portion=portion,
                    infraction_types={'missing_shift'},
                )
                processed_portions.add(portion)
                break
            if interval_stop > local_check_in:
                break
            if self._has_regular_leave_covering(employee, leave_type, interval_start, interval_stop):
                self._clear_existing_penalties(
                    employee=employee,
                    target_date=local_check_in.date(),
                    portion=portion,
                    infraction_types={'missing_shift'},
                )
                processed_portions.add(portion)
                continue
            if self._attendance_interval_is_covered(employee, interval_start, interval_stop):
                self._clear_existing_penalties(
                    employee=employee,
                    target_date=local_check_in.date(),
                    portion=portion,
                    infraction_types={'missing_shift'},
                )
                processed_portions.add(portion)
                continue
            start_local_str = interval_start.strftime('%H:%M')
            stop_local_str = interval_stop.strftime('%H:%M')
            portion_label = _('Morning') if portion == 'am' else _('Afternoon')
            description = _(
                "Auto penalty: Missing attendance for %(portion)s shift (%(start)s - %(stop)s).",
                portion=portion_label,
                start=start_local_str,
                stop=stop_local_str,
            )
            self._ensure_half_day_penalty(
                employee=employee,
                leave_type=leave_type,
                target_date=local_check_in.date(),
                portion=portion,
                infraction_type='missing_shift',
                description=description,
            )
            processed_portions.add(portion)

    def _apply_missing_following_shift_penalties(self, employee, leave_type, day_intervals, local_check_out):
        if not employee or not leave_type or not day_intervals or not local_check_out:
            return

        processed_portions = set()
        for interval_start, interval_stop, attendance_line in sorted(day_intervals, key=lambda x: x[0]):
            portion = self._map_day_period_to_portion(getattr(attendance_line, 'day_period', False))
            if portion not in {'am', 'pm'} or portion in processed_portions:
                continue
            if interval_start <= local_check_out:
                continue

            if self._has_regular_leave_covering(employee, leave_type, interval_start, interval_stop):
                self._clear_existing_penalties(
                    employee=employee,
                    target_date=local_check_out.date(),
                    portion=portion,
                    infraction_types={'missing_shift'},
                )
                processed_portions.add(portion)
                continue

            if self._attendance_interval_is_covered(employee, interval_start, interval_stop):
                self._clear_existing_penalties(
                    employee=employee,
                    target_date=local_check_out.date(),
                    portion=portion,
                    infraction_types={'missing_shift'},
                )
                processed_portions.add(portion)
                continue

            portion_label = _('Morning') if portion == 'am' else _('Afternoon')
            description = _(
                "Auto penalty: Missing attendance for %(portion)s shift (%(start)s - %(stop)s).",
                portion=portion_label,
                start=interval_start.strftime('%H:%M'),
                stop=interval_stop.strftime('%H:%M'),
            )
            self._ensure_half_day_penalty(
                employee=employee,
                leave_type=leave_type,
                target_date=local_check_out.date(),
                portion=portion,
                infraction_type='missing_shift',
                description=description,
            )
            processed_portions.add(portion)
            break

    def _attendance_interval_is_covered(self, employee, interval_start, interval_stop):
        if not employee or not interval_start or not interval_stop:
            return False
        domain_start = interval_start.astimezone(pytz.UTC).replace(tzinfo=None)
        domain_stop = interval_stop.astimezone(pytz.UTC).replace(tzinfo=None)
        attendances = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '<', domain_stop),
            ('check_out', '>', domain_start),
            ('id', '!=', self.id),
        ], limit=1)
        return bool(attendances)

    def _should_apply_full_day_penalty(self, employee, day_intervals, local_check_in, local_check_out, config):
        self.ensure_one()
        if not employee or not day_intervals or not local_check_in or not local_check_out:
            return False, {}

        working_intervals = []
        for interval_start, interval_stop, attendance_line in day_intervals:
            period = self._map_day_period_to_portion(getattr(attendance_line, 'day_period', False))
            if period in {'am', 'pm'}:
                working_intervals.append((interval_start, interval_stop, period))

        if not working_intervals:
            return False, {}

        working_intervals.sort(key=lambda interval: interval[0])
        first_interval_start = working_intervals[0][0]

        if local_check_in.date() != first_interval_start.date() or local_check_out.date() != first_interval_start.date():
            return False, {}

        late_grace = config.get('late_grace', 0) or 0
        diff_minutes = (local_check_in - first_interval_start).total_seconds() / 60.0
        if diff_minutes > late_grace:
            return False, {}

        if local_check_out <= local_check_in:
            return False, {}

        worked_seconds = (local_check_out - local_check_in).total_seconds()
        if worked_seconds <= 0:
            return False, {}

        calendar = employee.resource_calendar_id
        calendar_hours = float(calendar.hours_per_day) if calendar and calendar.hours_per_day else 0.0
        calendar_half_seconds = (calendar_hours * 3600.0 / 2.0) if calendar_hours else 0.0

        total_expected_seconds = 0.0
        morning_cutoff = None
        has_afternoon = False
        for start, stop, period in working_intervals:
            total_expected_seconds += max(0.0, (stop - start).total_seconds())
            if period == 'am':
                if not morning_cutoff or stop > morning_cutoff:
                    morning_cutoff = stop
            if period == 'pm':
                has_afternoon = True

        expected_half_seconds = (total_expected_seconds / 2.0) if total_expected_seconds else 0.0
        half_threshold_seconds = calendar_half_seconds or expected_half_seconds

        below_half = bool(half_threshold_seconds and (worked_seconds + 60.0) < half_threshold_seconds)
        left_before_morning = bool(morning_cutoff and local_check_out < morning_cutoff)
        completed_morning = bool(morning_cutoff and local_check_out >= morning_cutoff)

        if below_half and completed_morning and has_afternoon:
            # Employee completed the entire morning portion but left before the afternoon began.
            # Treat this as a missing shift rather than a full-day infraction.
            below_half = False

        if not (left_before_morning or below_half):
            return False, {}

        info = {
            'reason': 'morning' if left_before_morning else 'half',
            'worked_hours': worked_seconds / 3600.0,
            'minimum_hours': (half_threshold_seconds / 3600.0) if half_threshold_seconds else None,
        }
        if morning_cutoff:
            info['morning_cutoff'] = morning_cutoff
        if calendar_hours:
            info['calendar_hours'] = calendar_hours
        if total_expected_seconds:
            info['expected_hours'] = total_expected_seconds / 3600.0

        return True, info

    def _get_pre_post_work_time(self, employee, working_times, attendance_date):
        planned_slots = working_times.get(attendance_date)
        if not planned_slots:
            return super()._get_pre_post_work_time(employee, working_times, attendance_date)

        company = employee.company_id
        company_threshold = company.overtime_company_threshold / 60.0
        employee_threshold = company.overtime_employee_threshold / 60.0
        post_min_threshold = (company.attendance_overtime_post_min_minutes or 0) / 60.0

        planned_start_dt = False
        planned_end_dt = False
        planned_work_duration = 0.0

        for interval_start, interval_stop, *_rest in planned_slots:
            planned_start_dt = min(planned_start_dt, interval_start) if planned_start_dt else interval_start
            planned_end_dt = max(planned_end_dt, interval_stop) if planned_end_dt else interval_stop
            planned_work_duration += (interval_stop - interval_start).total_seconds() / 3600.0

        if not planned_start_dt or not planned_end_dt:
            return super()._get_pre_post_work_time(employee, working_times, attendance_date)

        lunch_intervals = []
        if not employee.is_flexible:
            # Fetch calendar slots flagged as lunch/break so they never inflate overtime.
            lunch_intervals = employee._employee_attendance_intervals(planned_start_dt, planned_end_dt, lunch=True)

        def _lunch_overlap_hours(window_start, window_stop):
            if not lunch_intervals:
                return 0.0
            overlap_seconds = 0.0
            for lunch_start, lunch_stop, *_unused in lunch_intervals:
                overlap_start = max(window_start, lunch_start)
                overlap_stop = min(window_stop, lunch_stop)
                if overlap_stop > overlap_start:
                    overlap_seconds += (overlap_stop - overlap_start).total_seconds()
            return overlap_seconds / 3600.0

        work_duration = 0.0
        post_work_time = 0.0

        for attendance in self:
            if not attendance.check_in or not attendance.check_out:
                continue

            local_check_in = pytz.utc.localize(attendance.check_in)
            local_check_out = pytz.utc.localize(attendance.check_out)

            delta_in = (planned_start_dt - local_check_in).total_seconds() / 3600.0
            if (delta_in > 0 and delta_in <= company_threshold) or (delta_in < 0 and abs(delta_in) <= employee_threshold):
                local_check_in = planned_start_dt

            delta_out = (local_check_out - planned_end_dt).total_seconds() / 3600.0
            if (delta_out > 0 and delta_out <= company_threshold) or (delta_out < 0 and abs(delta_out) <= employee_threshold):
                local_check_out = planned_end_dt

            if local_check_in <= planned_end_dt and local_check_out >= planned_start_dt:
                start_dt = max(planned_start_dt, local_check_in)
                stop_dt = min(planned_end_dt, local_check_out)
                duration_hours = max((stop_dt - start_dt).total_seconds() / 3600.0, 0.0)
                if duration_hours and lunch_intervals:
                    duration_hours -= _lunch_overlap_hours(start_dt, stop_dt)
                work_duration += max(duration_hours, 0.0)

            if local_check_out > planned_end_dt:
                post_work_time += (local_check_out - max(planned_end_dt, local_check_in)).total_seconds() / 3600.0

        if post_work_time < post_min_threshold:
            post_work_time = 0.0

        return 0.0, work_duration, post_work_time, planned_work_duration

    # ---------------------------------------------------------------------
    # Calendar helpers
    # ---------------------------------------------------------------------

    @api.model
    def _get_penalty_configuration(self):
        params = self.env['ir.config_parameter'].sudo()
        default_leave_type = self.env.ref('hr_attendance_calculs.leave_type_attendance_penalty', raise_if_not_found=False)

        def _safe_int(value, default=0):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        leave_type_id = params.get_param('hr_attendance_calculs.leave_type_id')
        leave_type_id = _safe_int(leave_type_id) if leave_type_id else (default_leave_type.id if default_leave_type else False)
        leave_type = self.env['hr.leave.type'].browse(leave_type_id) if leave_type_id else self.env['hr.leave.type']
        return {
            'leave_type': leave_type if leave_type and leave_type.exists() else (default_leave_type or self.env['hr.leave.type']),
            'late_grace': _safe_int(params.get_param('hr_attendance_calculs.late_grace_minutes'), 0),
            'early_grace': _safe_int(params.get_param('hr_attendance_calculs.early_checkout_grace_minutes'), 0),
        }

    @staticmethod
    def _to_employee_datetime(value, tz):
        if not value:
            return None
        if isinstance(value, str):
            value = fields.Datetime.from_string(value)
        if not value:
            return None
        if value.tzinfo:
            return value.astimezone(tz)
        return pytz.UTC.localize(value).astimezone(tz)

    def _get_employee_timezone(self, employee):
        tz_name = employee.tz or employee.resource_calendar_id.tz or employee.company_id.resource_calendar_id.tz or self.env.user.tz or 'UTC'
        return pytz.timezone(tz_name)

    def _get_day_intervals(self, employee, target_date, tz):
        calendar = employee.resource_calendar_id
        if not calendar:
            return []
        start_dt = tz.localize(datetime.combine(target_date, time.min))
        end_dt = tz.localize(datetime.combine(target_date, time.max))
        intervals_map = calendar._attendance_intervals_batch(
            start_dt,
            end_dt,
            resources=employee.resource_id,
            tz=tz,
        )
        intervals = intervals_map.get(employee.resource_id.id) or []
        return list(intervals)

    @staticmethod
    def _get_interval_for_datetime(intervals, target_dt):
        for start, end, attendance_line in intervals:
            if start <= target_dt <= end:
                return start, end, attendance_line
        return None

    @staticmethod
    def _get_next_interval(intervals, reference_dt):
        future_intervals = [interval for interval in intervals if interval[0] >= reference_dt]
        return future_intervals[0] if future_intervals else None

    @staticmethod
    def _get_previous_interval(intervals, reference_dt):
        past_intervals = [interval for interval in intervals if interval[1] <= reference_dt]
        return past_intervals[-1] if past_intervals else None

    @staticmethod
    def _map_day_period_to_portion(day_period):
        mapping = {
            'morning': 'am',
            'am': 'am',
            'afternoon': 'pm',
            'pm': 'pm',
            'evening': 'pm',
            'night': 'pm',
        }
        return mapping.get(day_period, False)

    @staticmethod
    def _refresh_leave_work_entries(leaves):
        if not leaves:
            return
        try:
            leaves = leaves.sudo()
            leaves._cancel_work_entry_conflict()
        except AttributeError:
            # hr_work_entry_holidays not installed or method unavailable.
            pass
        else:
            self = leaves.env['hr.attendance']
            penalty_leaves = leaves.filtered(lambda l: l.holiday_status_id.work_entry_type_id.code == 'LEAVE_PENALTY')
            if penalty_leaves:
                self._adjust_attendance_work_entries(penalty_leaves)
                self._align_penalty_work_entries(penalty_leaves)
                attendance_records = penalty_leaves.attendance_trigger_attendance_id
                if attendance_records:
                    attendance_records.with_context(skip_penalty_compliance=True)._ensure_attendance_work_entries_alignment()
                employees = penalty_leaves.mapped('employee_id')
                date_from_values = [leave.date_from for leave in penalty_leaves if leave.date_from]
                date_to_values = [leave.date_to for leave in penalty_leaves if leave.date_to]
                if employees and date_from_values and date_to_values:
                    employees._deduplicate_penalty_entries_for_range(
                        min(date_from_values),
                        max(date_to_values),
                    )

    @api.model
    def _adjust_attendance_work_entries(self, leaves):
        WorkEntry = self.env['hr.work.entry'].sudo()
        WorkEntryCtx = WorkEntry.with_context(skip_penalty_compliance=True)
        for leave in leaves:
            start = leave.date_from
            stop = leave.date_to
            employee = leave.employee_id
            if not start or not stop or not employee:
                continue
            
            # Check if this is an unpaid leave - if so, we need to archive ALL overlapping attendance entries
            # because unpaid time should never count as worked time in payroll
            is_unpaid = leave.holiday_status_id.unpaid or leave.work_entry_type_id.code == 'LEAVE110'
            
            attendance_entries = WorkEntry.search([
                ('employee_id', '=', employee.id),
                ('attendance_id', '!=', False),
                ('active', '=', True),
                ('date_start', '<', stop),
                ('date_stop', '>', start),
            ])
            if not attendance_entries:
                continue
            base_entries = attendance_entries
            updated_entries = self.env['hr.work.entry']
            with base_entries._error_checking(start=start, stop=stop, employee_ids=[employee.id]):
                for entry in base_entries.sorted('date_start'):
                    if entry.state == 'validated':
                        continue
                    original_start = entry.date_start
                    original_stop = entry.date_stop
                    if original_start >= stop or original_stop <= start:
                        continue
                    # Full overlap: attendance entry is completely within leave period
                    if original_start >= start and original_stop <= stop:
                        # For both paid and unpaid leaves, archive fully overlapping entries
                        entry.with_context(skip_penalty_compliance=True).write({'active': False})
                        continue
                    
                    # Partial overlaps - handle differently for unpaid vs paid leaves
                    if is_unpaid:
                        # For unpaid leaves, we must split/trim attendance to exclude ALL unpaid time
                        if original_start < start <= original_stop <= stop:
                            # Attendance starts before leave, ends during/at leave end
                            entry.with_context(skip_penalty_compliance=True).write({'date_stop': start})
                            updated_entries |= entry
                            continue
                        if start <= original_start < stop < original_stop:
                            # Attendance starts during leave, ends after leave
                            entry.with_context(skip_penalty_compliance=True).write({'date_start': stop})
                            updated_entries |= entry
                            continue
                        if original_start < start and original_stop > stop:
                            # Leave is in the middle of attendance - split into two entries
                            entry.with_context(skip_penalty_compliance=True).write({'date_stop': start})
                            updated_entries |= entry
                            new_entry = WorkEntryCtx.create({
                                'employee_id': entry.employee_id.id,
                                'contract_id': entry.contract_id.id,
                                'work_entry_type_id': entry.work_entry_type_id.id,
                                'date_start': stop,
                                'date_stop': original_stop,
                                'company_id': entry.company_id.id,
                                'attendance_id': entry.attendance_id.id,
                                'state': entry.state,
                            })
                            base_entries |= new_entry
                            updated_entries |= new_entry
                    else:
                        # For paid penalty leaves, trim attendance entries
                        if original_start < start <= original_stop <= stop:
                            entry.with_context(skip_penalty_compliance=True).write({'date_stop': start})
                            updated_entries |= entry
                            continue
                        if start <= original_start < stop < original_stop:
                            entry.with_context(skip_penalty_compliance=True).write({'date_start': stop})
                            updated_entries |= entry
                            continue
                        if original_start < start and original_stop > stop:
                            entry.with_context(skip_penalty_compliance=True).write({'date_stop': start})
                            updated_entries |= entry
                            new_entry = WorkEntryCtx.create({
                                'employee_id': entry.employee_id.id,
                                'contract_id': entry.contract_id.id,
                                'work_entry_type_id': entry.work_entry_type_id.id,
                                'date_start': stop,
                                'date_stop': original_stop,
                                'company_id': entry.company_id.id,
                                'attendance_id': entry.attendance_id.id,
                                'state': entry.state,
                            })
                            base_entries |= new_entry
                            updated_entries |= new_entry
            if updated_entries:
                updated_entries.sudo()._reset_conflicting_state()

    @api.model
    def _align_penalty_work_entries(self, leaves):
        if not leaves:
            return
        penalty_type = self.env.ref('hr_attendance_calculs.work_entry_type_attendance_penalty', raise_if_not_found=False)
        WorkEntry = self.env['hr.work.entry'].sudo()
        WorkEntryCtx = WorkEntry.with_context(skip_penalty_compliance=True)
        for leave in leaves:
            intervals = self._get_penalty_intervals(leave)
            if not intervals:
                continue
            intervals = self._normalize_penalty_intervals(intervals)
            if not intervals:
                continue
            entries = WorkEntry.search([
                ('leave_id', '=', leave.id),
                ('active', 'in', [True, False]),
            ], order='date_start, id')
            penalty_type_record = penalty_type or leave.holiday_status_id.work_entry_type_id
            desired_type_id = penalty_type_record.id if penalty_type_record else False
            if not desired_type_id:
                continue
            reusable_entries = list(entries)
            updated_entries = self.env['hr.work.entry']
            for idx, (interval_start, interval_stop) in enumerate(intervals):
                vals = {
                    'date_start': interval_start,
                    'date_stop': interval_stop,
                    'active': True,
                    'work_entry_type_id': desired_type_id,
                    'leave_id': leave.id,
                }
                if idx < len(reusable_entries):
                    entry = reusable_entries[idx].with_context(skip_penalty_compliance=True)
                    entry.write(vals)
                    updated_entries |= entry
                else:
                    contract = leave.employee_id._get_contracts(interval_start, interval_stop, states=['open', 'close'])[:1]
                    if not contract:
                        continue
                    create_vals = {
                        'name': leave.name,
                        'employee_id': leave.employee_id.id,
                        'contract_id': contract.id,
                        'date_start': interval_start,
                        'date_stop': interval_stop,
                        'company_id': leave.company_id.id or contract.company_id.id or leave.employee_id.company_id.id,
                        'leave_id': leave.id,
                        'work_entry_type_id': desired_type_id,
                    }
                    new_entry = WorkEntryCtx.create(create_vals)
                    updated_entries |= new_entry
            residual_entries = entries - updated_entries
            if residual_entries:
                residual_entries.with_context(skip_penalty_compliance=True).write({'active': False})
            self._deduplicate_penalty_work_entries(leave)
            active_entries = WorkEntry.search([
                ('leave_id', '=', leave.id),
                ('active', '=', True),
            ])
            if active_entries:
                active_entries.sudo()._reset_conflicting_state()

    @api.model
    def _get_penalty_intervals(self, leave):
        employee = leave.employee_id
        if not employee:
            return []
        target_date = leave.attendance_infraction_date or (leave.date_from and leave.date_from.date())
        if not target_date:
            return []
        portion = leave.attendance_infraction_portion
        if not portion:
            if leave.request_unit_half:
                portion = leave.request_date_from_period or 'am'
            else:
                portion = 'full'
        tz = self._get_employee_timezone(employee)
        day_intervals = self._get_day_intervals(employee, target_date, tz)
        if not day_intervals:
            if leave.date_from and leave.date_to and leave.date_from < leave.date_to:
                return [(leave.date_from, leave.date_to)]
            return []
        if portion == 'full':
            relevant_intervals = day_intervals
        else:
            relevant_intervals = [interval for interval in day_intervals if self._map_day_period_to_portion(interval[2].day_period) == portion]
            if not relevant_intervals:
                if portion == 'am' and day_intervals:
                    relevant_intervals = [day_intervals[0]]
                elif portion == 'pm' and day_intervals:
                    relevant_intervals = [day_intervals[-1]]
        if not relevant_intervals:
            if leave.date_from and leave.date_to and leave.date_from < leave.date_to:
                return [(leave.date_from, leave.date_to)]
            return []

        intervals = []
        for local_start, local_stop, _attendance_line in relevant_intervals:
            if not isinstance(local_start, datetime) or not isinstance(local_stop, datetime):
                continue
            start_utc = local_start.astimezone(pytz.UTC).replace(tzinfo=None)
            stop_utc = local_stop.astimezone(pytz.UTC).replace(tzinfo=None)
            if leave.date_from:
                start_utc = max(leave.date_from, start_utc)
            if leave.date_to:
                stop_utc = min(leave.date_to, stop_utc)
            if start_utc >= stop_utc:
                continue
            intervals.append((start_utc, stop_utc))
        return intervals

    def _deduplicate_penalty_work_entries(self, leave):
        if not leave:
            return
        WorkEntry = self.env['hr.work.entry'].sudo()
        penalty_entries = WorkEntry.search([
            ('leave_id', '=', leave.id),
        ], order='date_start, id')
        if not penalty_entries:
            return
        groups = {}
        duplicates_to_archive = WorkEntry
        for entry in penalty_entries:
            key = (
                entry.employee_id.id,
                entry.contract_id.id,
                entry.work_entry_type_id.id,
                entry.date_start,
                entry.date_stop,
            )
            chosen = groups.get(key)
            if not chosen:
                groups[key] = entry
                continue
            # Prefer keeping the active entry if the stored one was inactive
            if chosen.active is False and entry.active:
                groups[key] = entry
                duplicates_to_archive |= chosen
            else:
                duplicates_to_archive |= entry
        if duplicates_to_archive:
            removable = duplicates_to_archive.filtered(lambda rec: rec.state != 'validated')
            if removable:
                removable.with_context(skip_penalty_compliance=True).unlink()
            still_conflicting = (duplicates_to_archive - removable).filtered(lambda rec: rec.active)
            if still_conflicting:
                still_conflicting.with_context(skip_penalty_compliance=True).write({'active': False})

    def _normalize_penalty_intervals(self, intervals):
        unique = []
        seen = set()
        for interval_start, interval_stop in sorted(intervals, key=lambda value: (value[0], value[1])):
            key = (
                interval_start.replace(microsecond=0) if isinstance(interval_start, datetime) else interval_start,
                interval_stop.replace(microsecond=0) if isinstance(interval_stop, datetime) else interval_stop,
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append((interval_start, interval_stop))
        return unique
