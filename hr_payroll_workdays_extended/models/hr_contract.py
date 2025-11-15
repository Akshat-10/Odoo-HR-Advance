# -*- coding: utf-8 -*-
from datetime import datetime, time

from odoo import fields, models
import pytz


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def _get_monthly_hour_volume(self):
        """Return working hours INCLUDING week-off hours for hourly wage calculation.

        This ensures hourly rate is calculated as: Monthly Wage / (Working Hours + Week-Off Hours)
        Falls back to the standard average volume when the period is not known
        or when no data can be computed for the contract calendar.
        """
        self.ensure_one()
        date_from = self.env.context.get('hourly_wage_date_from')
        date_to = self.env.context.get('hourly_wage_date_to')
        if date_from and date_to:
            hours = self._get_period_work_hours(date_from, date_to, include_weekoff=True)
            if hours:
                return hours

        calendar = self.resource_calendar_id
        if not calendar:
            return 0.0

        hours_per_week = calendar.hours_per_week or 0.0
        if not hours_per_week:
            hours_per_day = calendar.hours_per_day or 0.0
            if hours_per_day:
                days_per_week = 0.0
                if hasattr(calendar, '_get_days_per_week'):
                    days_per_week = calendar._get_days_per_week() or 0.0
                hours_per_week = hours_per_day * days_per_week

        if not hours_per_week:
            return 0.0

        # Standard monthly average (working + week-off hours based on calendar)
        # This is approximate - actual period calculation is more accurate
        return (hours_per_week * 52.0) / 12.0

    def _get_period_work_hours(self, date_from, date_to, include_weekoff=False):
        """Compute the total working hours for the contract calendar.

        The computation honours the contract calendar (and therefore public
        holidays, two weeks schedule, etc.) so that hourly conversions reflect
        the actual payroll month instead of an average.
        
        Args:
            date_from: Start date of the period
            date_to: End date of the period
            include_weekoff: If True, adds week-off hours to the total
                           (for hourly wage calculation where week-offs affect the rate)
        
        Returns:
            float: Total hours (working hours + week-off hours if requested)
        """
        self.ensure_one()
        if not self.resource_calendar_id or not date_from or not date_to:
            return 0.0

        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        if not date_from or not date_to or date_from > date_to:
            return 0.0

        dt_from = datetime.combine(date_from, time.min)
        dt_to = datetime.combine(date_to, time.max)
        employee = self.employee_id
        calendar = self.resource_calendar_id

        # Calculate working hours
        working_hours = 0.0
        if employee:
            work_data = employee._get_work_days_data_batch(
                dt_from,
                dt_to,
                compute_leaves=False,
                calendar=calendar,
            ).get(employee.id)
            if work_data:
                working_hours = work_data.get('hours', 0.0)

        if not working_hours:
            # Fallback to calendar intervals
            intervals_map = calendar._work_intervals_batch(dt_from, dt_to, compute_leaves=False)
            intervals = intervals_map.get(False, []) if isinstance(intervals_map, dict) else intervals_map
            total_seconds = 0.0
            for interval in intervals:
                # interval is a tuple (start_datetime, end_datetime, data)
                start_dt, end_dt = interval[0], interval[1]
                total_seconds += (end_dt - start_dt).total_seconds()
            working_hours = total_seconds / 3600.0

        # If week-off hours should be included in the calculation
        if include_weekoff:
            weekoff_hours = self._calculate_weekoff_hours(date_from, date_to)
            return working_hours + weekoff_hours
        
        return working_hours

    def _calculate_weekoff_hours(self, date_from, date_to):
        """Calculate week-off hours for the period.
        
        Logic: Total Calendar Days - Working Days - Public Holidays = Week-off Days
        Week-off Hours = Week-off Days × Hours Per Day
        
        Args:
            date_from: Start date
            date_to: End date
            
        Returns:
            float: Week-off hours
        """
        self.ensure_one()
        
        if not self.resource_calendar_id or not date_from or not date_to:
            return 0.0
        
        calendar = self.resource_calendar_id
        employee = self.employee_id
        
        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        
        # Calculate total calendar days
        total_days = (date_to - date_from).days + 1
        
        # Calculate working days
        working_days = self._calculate_working_days(date_from, date_to)
        
        # Calculate public holidays
        public_holidays = self._calculate_public_holidays(date_from, date_to)
        
        # Week-off days = Total - Working - Holidays
        weekoff_days = max(0, total_days - working_days - public_holidays)
        
        # Convert to hours
        hours_per_day = calendar.hours_per_day or 8.0
        return weekoff_days * hours_per_day

    def _calculate_working_days(self, date_from, date_to):
        """Calculate actual working days from calendar for the period.
        
        Returns:
            float: Number of working days
        """
        self.ensure_one()
        
        if not self.resource_calendar_id or not self.employee_id:
            return 0.0
        
        calendar = self.resource_calendar_id
        employee = self.employee_id
        
        # Timezone handling
        tz = pytz.timezone(calendar.tz or 'UTC')
        
        dt_from = tz.localize(datetime.combine(date_from, time.min))
        dt_to = tz.localize(datetime.combine(date_to, time.max))
        
        # Get working days data
        work_data = employee._get_work_days_data_batch(
            dt_from,
            dt_to,
            compute_leaves=False,
            calendar=calendar,
        ).get(employee.id, {})
        
        return work_data.get('days', 0.0)

    def _calculate_public_holidays(self, date_from, date_to):
        """Calculate public holidays in the period.
        
        Returns:
            float: Number of public holiday days
        """
        self.ensure_one()
        
        if not self.resource_calendar_id:
            return 0.0
        
        calendar = self.resource_calendar_id
        company = self.company_id or self.env.company
        
        # Search for global public holidays
        public_holidays = self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id),
            ('resource_id', '=', False),  # Global leaves only
            ('date_from', '<=', fields.Datetime.to_datetime(date_to).replace(hour=23, minute=59, second=59)),
            ('date_to', '>=', fields.Datetime.to_datetime(date_from).replace(hour=0, minute=0, second=0)),
            ('company_id', 'in', [False, company.id]),
        ])
        
        if not public_holidays:
            return 0.0
        
        total_holiday_days = 0.0
        for holiday in public_holidays:
            # Calculate overlap with period
            holiday_start = max(holiday.date_from.date(), date_from)
            holiday_end = min(holiday.date_to.date(), date_to)
            
            if holiday_start <= holiday_end:
                days = (holiday_end - holiday_start).days + 1
                total_holiday_days += days
        
        return total_holiday_days
