# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
from odoo import api, models, fields
import pytz
import math


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # Override employee_id to show only active employees
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        domain="[('active', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )

    def _get_paid_amount(self):
        """Override to round paid amount to whole numbers"""
        amount = super()._get_paid_amount()
        # Round to nearest whole number
        return self._round_to_whole(amount)

    def _get_payslip_line_total(self, amount, quantity, rate, rule):
        """Override to round line total to whole numbers"""
        total = super()._get_payslip_line_total(amount, quantity, rate, rule)
        # Round to nearest whole number
        return self._round_to_whole(total)

    def _round_to_whole(self, amount):
        """
        Round amount to nearest whole number.
        Examples:
        - 32424.43 -> 32424.00
        - 32424.67 -> 32425.00
        - -4423.67 -> -4424.00
        """
        if amount >= 0:
            return math.floor(amount + 0.5)  # Round to nearest
        else:
            return math.ceil(amount - 0.5)  # Round to nearest for negative

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        """
        Override to add Week-Off Days calculation based on resource calendar.
        """
        res = super()._get_worked_day_lines(domain=domain, check_out_of_contract=check_out_of_contract)
        
        # Add week-off days calculation
        weekoff_line = self._compute_weekoff_days()
        if weekoff_line:
            res.append(weekoff_line)
        
        return res

    def _compute_weekoff_days(self):
        """
        Calculate week-off days (non-working days) based on the employee's 
        working schedule (resource.calendar) for the payslip period.
        
        Logic:
        1. Get total calendar days in the payslip period
        2. Calculate working days from resource.calendar
        3. Week-off days = Total days - Working days - Public holidays
        
        Returns a dict with week-off worked days line data.
        """
        self.ensure_one()
        
        if not self.contract_id or not self.contract_id.resource_calendar_id:
            return None
        
        if not self.date_from or not self.date_to:
            return None
        
        contract = self.contract_id
        calendar = contract.resource_calendar_id
        employee = self.employee_id
        
        # Get week-off work entry type
        weekoff_type = self.env.ref(
            'hr_payroll_workdays_extended.hr_work_entry_type_weekoff', 
            raise_if_not_found=False
        )
        if not weekoff_type:
            return None
        
        # Calculate total calendar days in the period
        total_days = (self.date_to - self.date_from).days + 1
        
        # Calculate working days from calendar
        working_days = self._calculate_working_days_from_calendar()
        
        # Calculate public holidays in the period
        public_holiday_days = self._calculate_public_holidays()
        
        # Week-off days = Total days - Working days - Public holidays
        weekoff_days = total_days - working_days - public_holiday_days
        
        # Ensure week-off days is not negative
        weekoff_days = max(0, weekoff_days)
        
        # Calculate week-off hours
        # Assuming 8 hours per day as standard, or use calendar's hours_per_day
        hours_per_day = calendar.hours_per_day or 8.0
        weekoff_hours = weekoff_days * hours_per_day
        
        return {
            'sequence': weekoff_type.sequence,
            'work_entry_type_id': weekoff_type.id,
            'number_of_days': weekoff_days,
            'number_of_hours': weekoff_hours,
            # Amount will be calculated by _compute_amount() in hr_payslip_worked_days
        }

    def _calculate_working_days_from_calendar(self):
        """
        Calculate the actual working days based on resource.calendar attendance records.
        This considers the specific weekdays configured in the calendar.
        
        Returns: float - number of working days
        """
        self.ensure_one()
        
        if not self.contract_id or not self.contract_id.resource_calendar_id:
            return 0.0
        
        calendar = self.contract_id.resource_calendar_id
        employee = self.employee_id
        
        # Get timezone
        tz = pytz.timezone(calendar.tz or 'UTC')
        
        # Convert dates to datetime
        start_dt = tz.localize(datetime.combine(self.date_from, time.min))
        end_dt = tz.localize(datetime.combine(self.date_to, time.max))
        
        # Get work intervals from calendar
        if employee and employee.resource_id:
            # Use employee-specific intervals (respects leaves)
            work_data = employee._get_work_days_data_batch(
                start_dt,
                end_dt,
                compute_leaves=False,  # Don't include leaves in working days count
                calendar=calendar,
            ).get(employee.id, {})
            working_days = work_data.get('days', 0.0)
        else:
            # Fallback: calculate from calendar directly
            intervals = calendar._work_intervals_batch(
                start_dt,
                end_dt,
                compute_leaves=False,
            )
            
            # Count unique working days from intervals
            working_dates = set()
            resource_intervals = intervals.get(False, [])
            
            for interval in resource_intervals:
                interval_start = interval[0]
                interval_date = interval_start.date()
                working_dates.add(interval_date)
            
            working_days = len(working_dates)
        
        return working_days

    def _calculate_public_holidays(self):
        """
        Calculate the number of public holidays in the payslip period.
        Public holidays are resource.calendar.leaves with no specific resource.
        
        Returns: float - number of public holiday days
        """
        self.ensure_one()
        
        if not self.contract_id or not self.contract_id.resource_calendar_id:
            return 0.0
        
        calendar = self.contract_id.resource_calendar_id
        company = self.company_id
        
        # Search for public holidays (global leaves)
        public_holidays = self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id),
            ('resource_id', '=', False),  # Global leaves only
            ('date_from', '<=', fields.Datetime.to_datetime(self.date_to).replace(hour=23, minute=59, second=59)),
            ('date_to', '>=', fields.Datetime.to_datetime(self.date_from).replace(hour=0, minute=0, second=0)),
            ('company_id', 'in', [False, company.id]),
        ])
        
        if not public_holidays:
            return 0.0
        
        # Calculate total holiday days
        total_holiday_days = 0.0
        
        for holiday in public_holidays:
            # Get overlap with payslip period
            holiday_start = max(
                holiday.date_from.date(),
                self.date_from
            )
            holiday_end = min(
                holiday.date_to.date(),
                self.date_to
            )
            
            if holiday_start <= holiday_end:
                # Calculate days (inclusive)
                days = (holiday_end - holiday_start).days + 1
                total_holiday_days += days
        
        return total_holiday_days

    def _get_weekoff_summary(self):
        """
        Get a summary of week-off days calculation for the payslip.
        Useful for debugging and reporting.
        
        Returns: dict with calculation breakdown
        """
        self.ensure_one()
        
        if not self.date_from or not self.date_to:
            return {}
        
        total_days = (self.date_to - self.date_from).days + 1
        working_days = self._calculate_working_days_from_calendar()
        public_holidays = self._calculate_public_holidays()
        weekoff_days = max(0, total_days - working_days - public_holidays)
        
        # Get working weekdays from calendar
        calendar = self.contract_id.resource_calendar_id if self.contract_id else None
        working_weekdays = []
        if calendar:
            # Get unique weekdays from attendance records
            weekdays_map = {
                '0': 'Monday',
                '1': 'Tuesday',
                '2': 'Wednesday',
                '3': 'Thursday',
                '4': 'Friday',
                '5': 'Saturday',
                '6': 'Sunday',
            }
            working_weekday_numbers = set(calendar.attendance_ids.mapped('dayofweek'))
            working_weekdays = [weekdays_map.get(day, day) for day in sorted(working_weekday_numbers)]
        
        return {
            'payslip_period': f"{self.date_from} to {self.date_to}",
            'total_calendar_days': total_days,
            'working_days': working_days,
            'public_holidays': public_holidays,
            'weekoff_days': weekoff_days,
            'working_weekdays': working_weekdays,
            'calendar_name': calendar.name if calendar else 'N/A',
        }
