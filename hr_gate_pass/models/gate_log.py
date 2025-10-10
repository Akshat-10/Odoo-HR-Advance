# -*- coding: utf-8 -*-
from odoo import models, fields

class HrGateLog(models.Model):
    _name = 'hr.gate.log'
    _description = 'Gate Log'
    _order = 'timestamp desc'

    gate_pass_id = fields.Many2one('hr.gate.pass', string='Gate Pass', required=True, ondelete='cascade', index=True)
    action = fields.Selection([
        ('submitted','Submitted'),
        ('approved','Approved'),
        ('printed','Printed'),
        ('qr_generated','QR Generated'),
        ('issued','Issued'),
        ('scanned_out','Scanned Out'),
        ('scanned_in','Scanned In'),
        ('checked_out','Checked Out'),
        ('checked_in','Checked In'),
        ('returned','Returned'),
        ('rejected','Rejected'),
        ('canceled','Canceled'),
        ('reverted','Reverted'),
        ('reset','Reset to Draft'),
        ('back_to_draft','Back to Draft'),
        ('closed','Closed'),
    ], string='Action', required=True)
    by_user_id = fields.Many2one('res.users', string='By User')
    timestamp = fields.Datetime(string='Time', default=lambda self: fields.Datetime.now())
    gate_id = fields.Many2one('hr.gate', string='Gate')
    remarks = fields.Char(string='Remarks')
