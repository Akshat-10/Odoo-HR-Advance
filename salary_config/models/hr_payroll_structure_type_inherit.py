# -*- coding: utf-8 -*-
from odoo import fields, models


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    salary_config_structure_id = fields.Many2one(
        'salary.config.structure',
        string='Default Salary Structure',
        help='Structure used to auto-populate Salary Structure lines on offers for this Salary Structure Type.',
    )
