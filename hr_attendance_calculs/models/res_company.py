# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    attendance_overtime_post_min_minutes = fields.Integer(
        string='Minimum Post-Shift Overtime (minutes)',
        help=(
            'Overtime is only counted when an employee works at least this many minutes '
            'after the last scheduled work interval of the day.'
        ),
        default=0,
    )
