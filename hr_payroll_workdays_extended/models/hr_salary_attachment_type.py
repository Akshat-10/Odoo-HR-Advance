# -*- coding: utf-8 -*-

from odoo import fields, models


class HrSalaryAttachmentType(models.Model):
    _name = 'hr.salary.attachment.type'
    _description = 'Salary Attachment Type'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    description = fields.Text(string='Description')
