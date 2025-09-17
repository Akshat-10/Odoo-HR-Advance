# -*- coding: utf-8 -*-
from odoo import models, fields


class HrGateIdNo(models.Model):
    _name = 'hr.gate.idno'
    _description = 'Gate ID Number'

    name = fields.Char(string='ID No.', required=True)
    description = fields.Char(string='Description')
