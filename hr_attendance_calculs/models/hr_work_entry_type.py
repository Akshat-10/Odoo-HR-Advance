# -*- coding: utf-8 -*-
from odoo import fields, models


class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    include_lunch_in_overtime = fields.Boolean(
        string='Include Lunch In Overtime',
        default=False,
        help=(
            'When enabled on an overtime work entry type, worked time that falls inside the '
            'scheduled lunch or break interval counts towards overtime instead of being '
            'excluded. Disable to keep lunch breaks out of overtime computations.'
        ),
    )
    
    # Overtime calculation parameters
    ot_calculation_days_per_month = fields.Float(
        string='OT Calculation Days Per Month',
        default=26.0,
        help='Number of days to use for calculating overtime hourly rate (typically 26-30 days).'
    )
    ot_calculation_hours_per_day = fields.Float(
        string='OT Calculation Working Hours Per Day',
        default=8.0,
        help='Number of working hours per day to use for overtime calculation.'
    )
