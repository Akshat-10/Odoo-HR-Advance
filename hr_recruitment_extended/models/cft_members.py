from odoo import api, fields, models, tools


class CFTMember(models.Model):
    _name = 'cft.member'
    _description = 'CFT Member'

    user_id = fields.Many2one('res.users', string='User', required=True)


class CFTApproval(models.Model):
    _name = 'cft.approval'
    _description = 'CFT Approval'

    job_id = fields.Many2one('hr.job', string='Job', required=True)
    cft_member_id = fields.Many2one('res.users', string='CFT Member', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending')