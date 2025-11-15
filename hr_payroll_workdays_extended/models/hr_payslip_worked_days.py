# -*- coding: utf-8 -*-
from odoo import api, models


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    @api.depends(
        'is_paid',
        'is_credit_time',
        'number_of_hours',
        'payslip_id',
        'payslip_id.date_from',
        'payslip_id.date_to',
        'payslip_id.sum_worked_hours',
        'payslip_id.contract_id.wage_type',
        'contract_id.wage',
        'contract_id.hourly_wage',
        'contract_id.resource_calendar_id',
        'contract_id.employee_id',
        'work_entry_type_id',
    )
    def _compute_amount(self):
        # Get week-off type reference
        weekoff_type = self.env.ref('hr_payroll_workdays_extended.hr_work_entry_type_weekoff', raise_if_not_found=False)
        
        # Call super for base computation
        super()._compute_amount()

        # Apply enhanced hourly wage calculation for hourly contracts (including week-offs)
        overtime_type = self.env.ref('hr_work_entry.overtime_work_entry_type', raise_if_not_found=False)

        for worked_days in self:
                
            payslip = worked_days.payslip_id
            contract = worked_days.contract_id

            if not payslip or not contract:
                continue
            if payslip.edited or payslip.state not in ['draft', 'verify']:
                continue
            if contract.wage_type != 'hourly':
                continue
            # For week-offs: Calculate amount even if not marked as "is_paid"
            # For others: Skip if not paid, credit time, or OUT
            if worked_days.work_entry_type_id != weekoff_type:
                if not worked_days.is_paid or worked_days.is_credit_time or worked_days.code == 'OUT':
                    continue
            if overtime_type and worked_days.work_entry_type_id == overtime_type:
                continue
            if not payslip.date_from or not payslip.date_to:
                continue

            # Get hourly rate calculated WITH week-off hours included in divisor
            # This gives: Monthly Wage / (Working Hours + Week-off Hours)
            hourly_rate = contract.with_context(
                hourly_wage_date_from=payslip.date_from,
                hourly_wage_date_to=payslip.date_to,
            )._get_hourly_wage_amount()
            if not hourly_rate:
                hourly_rate = contract.hourly_wage or 0.0

            # Calculate amount: Hourly Rate × Hours (including week-off hours)
            # Week-off hours NOW GET PAID at the adjusted hourly rate
            amount = hourly_rate * worked_days.number_of_hours
            currency = worked_days.currency_id or contract.currency_id
            worked_days.amount = currency.round(amount) if currency else amount
