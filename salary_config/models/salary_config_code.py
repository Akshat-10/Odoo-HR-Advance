# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SalaryConfigCode(models.Model):
    _name = 'salary.config.code'
    _description = 'Salary Structure Code Master'
    _order = 'name'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The technical code must be unique.'),
    ]

    name = fields.Char(required=True, help='Label / Description of the code usage.')
    code = fields.Char(required=True, help='Technical code referenced in formulas.')
    active = fields.Boolean(default=True)

    def name_get(self):
        return [(rec.id, f"{rec.code} - {rec.name}") for rec in self]
