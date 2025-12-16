# -*- coding: utf-8 -*-

from odoo import fields, models


class HrSalaryAttachment(models.Model):
    _inherit = 'hr.salary.attachment'

    attachment_line_ids = fields.One2many(
        'hr.salary.attachment.line',
        'salary_attachment_id',
        string='Attachment Lines'
    )
