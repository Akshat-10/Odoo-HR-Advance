# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    multi_contract_id = fields.Many2one(
        'hr.multi.contract',
        string='Multi Contract',
        readonly=True,
        help="Reference to the multi-contract that created this contract"
    )

    def action_view_multi_contract(self):
        """Open the related multi-contract"""
        self.ensure_one()
        if not self.multi_contract_id:
            return {}
        
        return {
            'name': _('Multi Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.multi.contract',
            'view_mode': 'form',
            'res_id': self.multi_contract_id.id,
        }
