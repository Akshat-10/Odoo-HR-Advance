# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    multi_contract_ids = fields.Many2many(
        'hr.multi.contract',
        'hr_multi_contract_employee_rel',
        'employee_id',
        'contract_id',
        string='Multi Contracts',
        help="Multi-contract records this employee is part of"
    )
    
    multi_contract_count = fields.Integer(
        string='Multi Contracts',
        compute='_compute_multi_contract_count'
    )

    def _compute_multi_contract_count(self):
        for employee in self:
            employee.multi_contract_count = len(employee.multi_contract_ids)

    def action_view_multi_contracts(self):
        """Open multi-contracts related to this employee"""
        self.ensure_one()
        return {
            'name': _('Multi Contracts'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.multi.contract',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.multi_contract_ids.ids)],
            'context': {'default_employee_ids': [(6, 0, [self.id])]},
        }

    def action_create_mass_contracts(self):
        """Open wizard to create mass contracts for selected employees"""
        if not self:
            raise UserError(_('Please select at least one employee.'))
        
        return {
            'name': _('Create Mass Contracts'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.mass.contract.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_ids': [(6, 0, self.ids)],
            },
        }
