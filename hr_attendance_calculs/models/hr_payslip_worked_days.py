# -*- coding: utf-8 -*-
from odoo import api, models


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    @api.depends(
        'is_paid',
        'is_credit_time',
        'number_of_hours',
        'payslip_id',
        'contract_id.wage',
        'contract_id.ot_hourly_rate',
        'contract_id.currency_id',
        'payslip_id.sum_worked_hours',
        'work_entry_type_id',
    )
    def _compute_amount(self):
        """
        Override to calculate overtime using the contract's ot_hourly_rate.
        For overtime work entry types, use: ot_hourly_rate × number_of_hours
        This runs AFTER hr_payroll_attendance and completely replaces overtime logic.
        """
        overtime_work_entry_type = self.env.ref('hr_work_entry.overtime_work_entry_type', raise_if_not_found=False)
        
        if not overtime_work_entry_type:
            super()._compute_amount()
            return
        print("Custom overtime calculation using ot_hourly_rate --", overtime_work_entry_type)
        overtime_lines = self.filtered(lambda line: line.work_entry_type_id == overtime_work_entry_type)
        regular_lines = self - overtime_lines
        print("Overtime lines:", overtime_lines)
        print("Regular lines:", regular_lines)
        # Let parent modules handle non-overtime lines
        if regular_lines:
            super(HrPayslipWorkedDays, regular_lines)._compute_amount()

        # Custom overtime calculation using ot_hourly_rate
        for worked_days in overtime_lines:
            if worked_days.payslip_id.edited or worked_days.payslip_id.state not in ['draft', 'verify']:
                continue

            if not worked_days.contract_id or worked_days.code == 'OUT' or worked_days.is_credit_time:
                worked_days.amount = 0
                continue

            if not worked_days.is_paid:
                worked_days.amount = 0
                continue
            print("Calculating OT for worked days:", worked_days.id)
            # Use the contract's configured OT hourly rate directly
            ot_rate = worked_days.contract_id.ot_hourly_rate or 0.0
            amount = ot_rate * worked_days.number_of_hours
            print("Calculating OT amount:", ot_rate, "*", worked_days.number_of_hours, "=", amount)
            # Apply currency rounding
            currency = worked_days.currency_id or worked_days.contract_id.currency_id
            worked_days.amount = currency.round(amount) if currency else amount
            print("Final OT amount after rounding:", worked_days.amount)