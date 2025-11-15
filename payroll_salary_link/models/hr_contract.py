# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.tools.float_utils import float_compare


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def _get_monthly_hour_volume(self):
        """
        Calculate the average working hours per month based on calendar.
        Uses the calendar's computed hours_per_week which is dynamically calculated
        from attendance records, respecting hours_per_day, working days, and two_weeks_calendar.
        
        Formula: (hours_per_week × 52 weeks) / 12 months
        This gives the actual monthly working hours based on the calendar configuration.
        
        Note: hours_per_week from resource.calendar is computed from attendance_ids,
        so it already reflects the actual working schedule including part-time adjustments.
        """
        self.ensure_one()
        calendar = self.resource_calendar_id
        if not calendar:
            return 0.0
        
        # Use calendar's hours_per_week (computed from attendance_ids)
        # This is the most accurate as it reflects the actual calendar setup
        hours_per_week = calendar.hours_per_week or 0.0
        
        # If hours_per_week not computed/available, fallback to manual calculation
        if not hours_per_week:
            hours_per_day = calendar.hours_per_day or 0.0
            if hours_per_day:
                days_per_week = 0.0
                if hasattr(calendar, '_get_days_per_week'):
                    days_per_week = calendar._get_days_per_week() or 0.0
                hours_per_week = hours_per_day * days_per_week
        
        if not hours_per_week:
            return 0.0
        
        # Calculate monthly hours: (weekly hours × 52 weeks) / 12 months
        # This standard formula gives average monthly working hours
        # For a 40-hour week: (40 × 52) / 12 = 173.33 hours/month
        monthly_hours = (hours_per_week * 52.0) / 12.0
        
        return monthly_hours

    def _get_hourly_wage_amount(self):
        """
        Calculate hourly wage from monthly wage.
        For a monthly wage, divide by the average monthly working hours.
        """
        self.ensure_one()
        if self.wage_type != 'hourly':
            return 0.0
        monthly_hours = self._get_monthly_hour_volume()
        if not monthly_hours:
            return 0.0
        wage = self.wage or 0.0
        return wage / monthly_hours if wage else 0.0

    def _apply_hourly_wage_autoset(self):
        precision = self.env.company.currency_id.rounding
        to_update = {}
        for contract in self:
            if contract.wage_type != 'hourly':
                continue
            hourly_amount = contract._get_hourly_wage_amount()
            currency = contract.currency_id or contract.company_id.currency_id
            rounding = currency.rounding if currency else precision
            if float_compare(contract.hourly_wage or 0.0, hourly_amount or 0.0, precision_rounding=rounding):
                to_update[contract.id] = hourly_amount
        if to_update:
            for contract in self.browse(to_update.keys()):
                contract.with_context(payroll_salary_link_skip_hourly_auto=True).write({'hourly_wage': to_update[contract.id]})

    @api.onchange('wage', 'resource_calendar_id', 'wage_type')
    def _onchange_hourly_wage_autoset(self):
        for contract in self:
            if contract.wage_type != 'hourly':
                continue
            contract.hourly_wage = contract._get_hourly_wage_amount()

    @api.model_create_multi
    def create(self, vals_list):
        contracts = super().create(vals_list)
        if not self.env.context.get('payroll_salary_link_skip_hourly_auto'):
            contracts._apply_hourly_wage_autoset()
        return contracts

    def write(self, vals):
        if self.env.context.get('payroll_salary_link_skip_hourly_auto'):
            return super().write(vals)
        res = super().write(vals)
        tracked = {'wage', 'resource_calendar_id', 'structure_type_id', 'wage_type'}
        if tracked.intersection(vals):
            self._apply_hourly_wage_autoset()
        return res
