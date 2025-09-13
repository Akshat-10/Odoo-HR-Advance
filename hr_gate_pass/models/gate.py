# -*- coding: utf-8 -*-
from odoo import models, fields

class HrGate(models.Model):
    _name = 'hr.gate'
    _description = 'Security Gate'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    location = fields.Char(string='Location')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    default_security_user_id = fields.Many2one('res.users', string='Default Security User')
