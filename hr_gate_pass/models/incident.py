# -*- coding: utf-8 -*-
from odoo import models, fields

class HrGateIncident(models.Model):
    _name = 'hr.gate.incident'
    _description = 'Gate Incident'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Incident No', required=True, copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('hr.gate.incident'))
    gate_pass_id = fields.Many2one('hr.gate.pass', string='Gate Pass', ondelete='set null')
    description = fields.Text(string='Description')
    severity = fields.Selection([('low','Low'),('medium','Medium'),('high','High'),('critical','Critical')], string='Severity', default='low')
    responsible_department_id = fields.Many2one('hr.department', string='Responsible Department')
    actions_taken = fields.Text(string='Actions Taken')
    status = fields.Selection([('open','Open'),('in_progress','In Progress'),('resolved','Resolved'),('closed','Closed')], string='Status', default='open', tracking=True)
