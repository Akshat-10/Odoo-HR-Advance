# -*- coding: utf-8 -*-
from datetime import datetime, time

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # Overtime calculation fields
    ot_basic_salary = fields.Monetary(
        string='Basic Salary',
        compute='_compute_ot_basic_salary',
        store=True,
        # readonly=False,
        currency_field='currency_id',
        help='Basic salary for overtime calculation (typically wage/2). Can be manually overridden.'
    )
    ot_calculation_base = fields.Selection(
        [('basic', 'Basic Salary'), ('gross', 'Gross Salary')],
        string='OT Calculation Base',
        default='basic',
        # required=True,
        help='Choose whether to calculate overtime based on Basic Salary or Gross Salary.'
    )
    ot_hourly_rate = fields.Monetary(
        string='Overtime Hourly Rate',
        compute='_compute_ot_hourly_rate',
        store=True,
        currency_field='currency_id',
        help='Calculated as: (Basic or Gross) / (Days per month × Hours per day). '
             'Days and hours are taken from the Overtime work entry type configuration.'
    )

    @api.depends('wage')
    def _compute_ot_basic_salary(self):
        """Compute basic salary as 50% of wage (default Indian payroll structure)."""
        for contract in self:
            if contract.wage:
                contract.ot_basic_salary = contract.wage / 2.0
            else:
                contract.ot_basic_salary = 0.0

    @api.depends('wage', 'ot_basic_salary', 'ot_calculation_base')
    def _compute_ot_hourly_rate(self):
        """
        Calculate overtime hourly rate based on:
        - Selected base (Basic or Gross)
        - Days per month and hours per day from overtime work entry type
        Formula: Base Amount / (Days per month × Hours per day)
        """
        overtime_type = self.env.ref('hr_work_entry.overtime_work_entry_type', raise_if_not_found=False)
        
        for contract in self:
            if not overtime_type:
                contract.ot_hourly_rate = 0.0
                continue
            
            # Get calculation parameters from overtime work entry type
            days_per_month = overtime_type.ot_calculation_days_per_month or 30.0
            hours_per_day = overtime_type.ot_calculation_hours_per_day or 8.0
            total_hours = days_per_month * hours_per_day
            
            if total_hours <= 0:
                contract.ot_hourly_rate = 0.0
                continue
            
            # Determine base amount
            if contract.ot_calculation_base == 'basic':
                base_amount = contract.ot_basic_salary or 0.0
            else:  # gross
                base_amount = contract.wage or 0.0
            
            # Calculate hourly rate
            contract.ot_hourly_rate = base_amount / total_hours if total_hours else 0.0

    def generate_work_entries(self, date_start, date_stop, force=False):
        res = super().generate_work_entries(date_start, date_stop, force=force)
        employees = self.employee_id
        if employees:
            employees._align_attendance_entries_for_range(date_start, date_stop)
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
            employees._prune_calendar_work_entries(start_dt, stop_dt)
            employees._deduplicate_attendance_entries_for_range(start_dt, stop_dt)
        return res
