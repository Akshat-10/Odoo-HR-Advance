# -*- coding: utf-8 -*-

from odoo import fields, models


class HrSalaryAttachmentLine(models.Model):
    _name = 'hr.salary.attachment.line'
    _description = 'Salary Attachment Line'
    _order = 'sequence, id'

    salary_attachment_id = fields.Many2one(
        'hr.salary.attachment',
        string='Salary Attachment',
        required=True,
        ondelete='cascade',
        index=True
    )
    attachment_type_id = fields.Many2one(
        'hr.salary.attachment.type',
        string='Type',
        required=True,
        ondelete='restrict'
    )
    amount = fields.Monetary(string='Amount', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='salary_attachment_id.currency_id',
        store=True,
        readonly=True
    )
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='salary_attachment_id.company_id',
        store=True,
        readonly=True
    )
