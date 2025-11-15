# -*- coding: utf-8 -*-
from datetime import datetime, time
from pytz import timezone, UTC

from odoo import api, fields, models
from odoo.addons.resource.models.utils import Intervals


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    expected_working_hours = fields.Float(
        string='Expected Working Hours',
        compute='_compute_expected_working_hours',
        store=True,
        help='Total expected working hours based on the working schedule from contract for the payslip period'
    )

    @api.depends('date_from', 'date_to', 'contract_id', 'contract_id.resource_calendar_id', 'employee_id')
    def _compute_expected_working_hours(self):
        for payslip in self:
            if not payslip.contract_id or not payslip.contract_id.resource_calendar_id:
                payslip.expected_working_hours = 0.0
                continue

            # Get contract calendar
            calendar = payslip.contract_id.resource_calendar_id
            employee = payslip.employee_id
            
            # Convert dates to datetime with timezone
            tz = timezone(calendar.tz or 'UTC')
            start_dt = tz.localize(datetime.combine(payslip.date_from, time.min))
            end_dt = tz.localize(datetime.combine(payslip.date_to, time.max))

            # Check if employee has flexible hours
            if employee.resource_id._is_fully_flexible():
                # For fully flexible employees, calculate expected hours differently
                # Using the full time required hours per week
                num_days = (payslip.date_to - payslip.date_from).days + 1
                if calendar.full_time_required_hours:
                    expected_hours = round(calendar.full_time_required_hours * (num_days / 7))
                else:
                    expected_hours = calendar.hours_per_day * num_days
                payslip.expected_working_hours = expected_hours
            else:
                # For non-flexible employees, calculate based on work intervals
                work_intervals = calendar._work_intervals_batch(
                    start_dt,
                    end_dt,
                    resources=employee.resource_id,
                    tz=tz
                )
                
                # Get the intervals for this employee's resource
                employee_intervals = work_intervals.get(employee.resource_id.id, Intervals([]))
                
                # Calculate total hours from intervals
                total_hours = 0.0
                for start, stop, meta in employee_intervals:
                    # Calculate duration in hours
                    duration = (stop - start).total_seconds() / 3600.0
                    total_hours += duration
                
                payslip.expected_working_hours = total_hours
