from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.addons.resource.models.utils import Intervals
from pytz import timezone, UTC
import datetime
from collections import defaultdict

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_attendance_metrics(self, start_date, end_date):
        self.ensure_one()
        metrics = {}
        start = fields.Datetime.from_string(start_date).replace(hour=0, minute=0, second=0)
        stop = fields.Datetime.from_string(end_date).replace(hour=23, minute=59, second=59)

        calendar = self.resource_calendar_id or self.company_id.resource_calendar_id
        tz = timezone(calendar.tz) if calendar.tz else UTC
        start = tz.localize(start)
        stop = tz.localize(stop)

        # Existing calculations
        expected_days, expected_hours = self._get_expected_work_days_hours(calendar, start, stop)
        metrics['expected_work_days'] = expected_days
        metrics['expected_working_hours'] = expected_hours

        attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', self.id),
            ('check_in', '>=', start),
            ('check_out', '<=', stop),
        ])
        present_days = len(set(att.check_in.date() for att in attendances))
        actual_hours = sum(att.worked_hours for att in attendances)
        metrics['present'] = present_days
        metrics['actual_working_hours'] = actual_hours

        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', self.id),
            ('state', '=', 'validate'),
            ('date_from', '<', stop),
            ('date_to', '>', start),
        ])
        leave_days_by_type = {}
        paid_leave_days = 0
        unpaid_leave_days = 0
        for leave in leaves:
            leave_type = leave.holiday_status_id.name
            days = leave.number_of_days
            leave_days_by_type[leave_type] = leave_days_by_type.get(leave_type, 0) + days
            if leave.holiday_status_id.unpaid:
                unpaid_leave_days += days
            else:
                paid_leave_days += days
        metrics.update(leave_days_by_type)
        metrics['no_of_leaves_paid'] = paid_leave_days
        metrics['no_of_leaves_unpaid'] = unpaid_leave_days

        holiday_days = self._get_holiday_days(start, stop)
        weekoff_days = self._get_weekoff_days(calendar, start, stop)
        metrics['weekoff'] = weekoff_days
        metrics['holiday'] = len(holiday_days)

        leave_days = sum(leave_days_by_type.values())
        absent_days = expected_days - present_days - leave_days
        metrics['absent'] = max(absent_days, 0)
        metrics['pay_days'] = present_days + paid_leave_days
        metrics['total'] = (stop - start).days + 1

        # Additional existing metrics
        metrics['count_of_ar'] = len(attendances)
        overtime_days = len(set(att.check_in.date() for att in attendances if att.worked_hours > calendar.hours_per_day))
        metrics['count_of_od'] = overtime_days
        short_leaves = len([leave for leave in leaves if leave.number_of_days < 1])
        metrics['count_of_short_leave'] = short_leaves

        early_late_count = 0
        for att in attendances:
            check_in = att.check_in.astimezone(tz)
            check_out = att.check_out.astimezone(tz) if att.check_out else None
            attendance_date = check_in.date()
            day_start = datetime.datetime.combine(attendance_date, datetime.time.min, tzinfo=tz)
            day_end = datetime.datetime.combine(attendance_date, datetime.time.max, tzinfo=tz)
            day_intervals = calendar._attendance_intervals_batch(day_start, day_end, self.resource_id)[self.resource_id.id]
            if day_intervals:
                intervals_list = list(day_intervals)
                if intervals_list:
                    expected_start = intervals_list[0][0]
                    expected_end = intervals_list[-1][1]
                    if check_in < expected_start or (check_out and check_out > expected_end):
                        early_late_count += 1
        metrics['count_of_early_late'] = early_late_count

        metrics['last_attendance_worked_hours'] = self.last_attendance_worked_hours if self.last_attendance_id else 0
        metrics['attendance_state'] = self.attendance_state
        metrics['total_overtime'] = sum(att.worked_hours - calendar.hours_per_day for att in attendances if att.worked_hours > calendar.hours_per_day)
        metrics['remaining_leaves'] = self.remaining_leaves
        metrics['leaves_count'] = self.leaves_count
        metrics['hours_previously_today'] = self.hours_previously_today
        metrics['hours_last_month'] = self.hours_last_month
        metrics['allocation_count'] = self.allocation_count
        metrics['allocations_count'] = self.allocations_count
        metrics['contracts_count'] = self.contracts_count
        metrics['resource_calendar_id'] = self.resource_calendar_id.name if self.resource_calendar_id else ''
        metrics['leave_manager_id'] = self.leave_manager_id.name if self.leave_manager_id else ''

        # New daily status calculation
        leave_days = set()
        for leave in leaves:
            leave_start = leave.date_from.astimezone(tz).date()
            leave_end = leave.date_to.astimezone(tz).date()
            current = leave_start
            while current <= leave_end:
                leave_days.add(current)
                current += datetime.timedelta(days=1)

        attendances_by_day = defaultdict(list)
        for att in attendances:
            day = att.check_in.astimezone(tz).date()
            attendances_by_day[day].append(att)

        date_range = [start.date() + datetime.timedelta(days=x) for x in range((stop.date() - start.date()).days + 1)]
        daily_status = {}
        for day in date_range:
            if day in leave_days:
                status = "Leave"
            elif day in holiday_days:
                status = "Holiday"
            else:
                day_start = tz.localize(datetime.datetime.combine(day, datetime.time.min))
                day_end = tz.localize(datetime.datetime.combine(day, datetime.time.max))
                attendance_intervals = calendar._attendance_intervals_batch(day_start, day_end, resources=self.resource_id)[self.resource_id.id]
                if not attendance_intervals:
                    status = "Weekoff"
                else:
                    morning_intervals = [interval for interval in attendance_intervals if interval[2].day_period == 'morning']
                    afternoon_intervals = [interval for interval in attendance_intervals if interval[2].day_period == 'afternoon']
                    day_attendances = attendances_by_day.get(day, [])

                    present_morning = any(
                        any(
                            att.check_in.astimezone(tz) < interval[1] and (att.check_out.astimezone(tz) if att.check_out else day_end) > interval[0]
                            for interval in morning_intervals
                        )
                        for att in day_attendances
                    ) if morning_intervals else False
                    present_afternoon = any(
                        any(
                            att.check_in.astimezone(tz) < interval[1] and (att.check_out.astimezone(tz) if att.check_out else day_end) > interval[0]
                            for interval in afternoon_intervals
                        )
                        for att in day_attendances
                    ) if afternoon_intervals else False

                    if morning_intervals and afternoon_intervals:
                        status = f"{'P' if present_morning else 'A'} | {'P' if present_afternoon else 'A'}"
                    elif morning_intervals:
                        status = f"{'P' if present_morning else 'A'} | N/A"
                    elif afternoon_intervals:
                        status = f"N/A | {'P' if present_afternoon else 'A'}"
                    else:
                        status = "N/A"
            daily_status[day] = status
        metrics['daily_status'] = {str(day): status for day, status in daily_status.items()}

        # Existing shift status counts (optional, retained for compatibility)
        pp = 0  # Present in both shifts
        pa = 0  # Present in morning only
        ap = 0  # Present in afternoon only
        aa = 0  # Absent in both shifts
        # Iterate over actual date objects, not the original string params
        current_date = start.date()
        end_date_date = stop.date()
        # Do NOT count future days in transition metrics (esp. A|A)
        # Use the employee/calendar timezone to determine "today"
        today_local = datetime.datetime.now(tz).date()
        if end_date_date > today_local:
            end_date_date = today_local
        while current_date <= end_date_date:
            day_start = tz.localize(datetime.datetime.combine(current_date, datetime.time.min))
            day_end = tz.localize(datetime.datetime.combine(current_date, datetime.time.max))
            attendance_intervals = calendar._attendance_intervals_batch(day_start, day_end, resources=self.resource_id)[self.resource_id.id]
            leave_intervals = calendar._leave_intervals_batch(day_start, day_end, resources=self.resource_id)[self.resource_id.id]
            if attendance_intervals and not leave_intervals:
                morning_intervals = [interval for interval in attendance_intervals if interval[2].day_period == 'morning']
                afternoon_intervals = [interval for interval in attendance_intervals if interval[2].day_period == 'afternoon']
                if morning_intervals and afternoon_intervals:
                    day_attendances = self.env['hr.attendance'].search([
                        ('employee_id', '=', self.id),
                        ('check_in', '<', day_end.astimezone(UTC)),
                        ('check_out', '>', day_start.astimezone(UTC)),
                        ('check_out', '!=', False),
                    ])
                    present_morning = any(
                        any(
                            att.check_in.astimezone(tz) < interval[1] and att.check_out.astimezone(tz) > interval[0]
                            for interval in morning_intervals
                        )
                        for att in day_attendances
                    )
                    present_afternoon = any(
                        any(
                            att.check_in.astimezone(tz) < interval[1] and att.check_out.astimezone(tz) > interval[0]
                            for interval in afternoon_intervals
                        )
                        for att in day_attendances
                    )
                    if present_morning and present_afternoon:
                        pp += 1
                    elif present_morning:
                        pa += 1
                    elif present_afternoon:
                        ap += 1
                    else:
                        aa += 1
            current_date += datetime.timedelta(days=1)
        metrics['days_p|p'] = pp
        metrics['days_p|a'] = pa
        metrics['days_a|p'] = ap
        metrics['days_a|a'] = aa

        return metrics

    def _get_expected_work_days_hours(self, calendar, start, stop):
        if not self.resource_id:
            return 0, 0
        attendance_intervals = calendar._attendance_intervals_batch(start, stop, self.resource_id)
        days = set()
        total_hours = 0
        for interval in attendance_intervals[self.resource_id.id]:
            days.add(interval[0].date())
            total_hours += (interval[1] - interval[0]).total_seconds() / 3600
        return len(days), total_hours

    def _get_weekoff_days(self, calendar, start, stop):
        """Return number of days in [start, stop] that have NO attendance slots.

        Previous implementation subtracted work intervals from the full span,
        which included partial non-working gaps within working days and
        overcounted week-off days. Here we simply check, per day, whether
        there are any attendance intervals configured for the resource.
        """
        if not self.resource_id:
            return 0

        tz = timezone(calendar.tz) if calendar.tz else UTC
        # Iterate day by day and consider a day week-off if there is no attendance interval
        day = start.date()
        end_day = stop.date()
        weekoff_count = 0
        while day <= end_day:
            day_start = tz.localize(datetime.datetime.combine(day, datetime.time.min))
            day_end = tz.localize(datetime.datetime.combine(day, datetime.time.max))
            intervals = calendar._attendance_intervals_batch(day_start, day_end, resources=self.resource_id)[self.resource_id.id]
            if not intervals:
                weekoff_count += 1
            day += datetime.timedelta(days=1)
        return weekoff_count

    def _get_holiday_days(self, start, stop):
        tz = timezone(self.resource_calendar_id.tz) if self.resource_calendar_id.tz else UTC
        holidays = self.env['resource.calendar.leaves'].search([
            ('resource_id', '=', False),
            ('date_from', '<', stop),
            ('date_to', '>', start),
        ])
        holiday_days = set()
        for holiday in holidays:
            holiday_start_local = holiday.date_from.astimezone(tz)
            holiday_stop_local = holiday.date_to.astimezone(tz)
            effective_start = max(holiday_start_local, start)
            effective_stop = min(holiday_stop_local, stop)
            current = effective_start.date()
            end_date = effective_stop.date()
            while current <= end_date:
                holiday_days.add(current)
                current += datetime.timedelta(days=1)
        return holiday_days