# -*- coding: utf-8 -*-
from odoo import models, fields


class HrGateRepresenting(models.Model):
    _name = 'hr.gate.representing'
    _description = 'Representing From Entity'

    name = fields.Char(string='Name', required=True)
    contact = fields.Char(string='Contact')
    notes = fields.Char(string='Notes')
