# -*- coding: utf-8 -*-
from odoo import models, fields

class HrGatePassApprovalProfile(models.Model):
    _name = 'hr.gate.pass.approval.profile'
    _description = 'Gate Pass Approval Profile'

    name = fields.Char(string='Name', required=True)
    pass_type = fields.Selection([
        ('employee_out','Employee Out'),
        ('visitor','Visitor'),
        ('material','Material'),
        ('vehicle','Vehicle'),
        ('contractor','Contractor')
    ], string='Pass Type', required=True)
    approver_user_ids = fields.Many2many('res.users', string='Approver Users')
    approver_group_ids = fields.Many2many('res.groups', string='Approver Groups')
    conditional_rules = fields.Json(string='Conditional Rules')
    auto_approve_conditions = fields.Json(string='Auto Approve Conditions')
    allow_override = fields.Boolean(string='Allow Override', default=False)
    notify_on_action = fields.Boolean(string='Notify On Action', default=True)
