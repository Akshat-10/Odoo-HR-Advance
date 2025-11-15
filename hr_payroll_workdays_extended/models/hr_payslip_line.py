# -*- coding: utf-8 -*-
from odoo import api, models
import math


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        """Override to round total to whole numbers (no decimals)"""
        for line in self:
            if line.amount_select == 'code':
                # Let the code compute the value, then round it
                super(HrPayslipLine, line)._compute_total()
                # Round to nearest whole number
                line.total = self._round_to_whole(line.total)
            else:
                # Calculate total
                total = float(line.quantity) * line.amount * line.rate / 100
                # Round to nearest whole number
                line.total = self._round_to_whole(total)

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
