# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class HrMultiContract(models.Model):
    _name = 'hr.multi.contract'
    _description = 'HR Multi Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        default='New',
        copy=False,
        tracking=True
    )
    
    employee_ids = fields.Many2many(
        'hr.employee',
        'hr_multi_contract_employee_rel',
        'contract_id',
        'employee_id',
        string='Employees',
        required=True,
        tracking=True
    )
    
    employee_count = fields.Integer(
        string='Employee Count',
        compute='_compute_employee_count',
        store=True
    )
    
    structure_type_id = fields.Many2one(
        'hr.payroll.structure.type',
        string='Salary Structure Type',
        tracking=True
    )
    
    date_start = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Start date of the contracts"
    )
    
    date_end = fields.Date(
        string='End Date',
        tracking=True,
        help="End date of the contracts (if applicable)"
    )
    
    wage = fields.Monetary(
        string='Wage',
        required=True,
        tracking=True,
        help="Basic Wage of the employee"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        tracking=True
    )
    
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        tracking=True
    )
    
    contract_type_id = fields.Many2one(
        'hr.contract.type',
        string='Contract Type',
        tracking=True
    )
    
    resource_calendar_id = fields.Many2one(
        'resource.calendar',
        string='Working Schedule',
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Contracts Created'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)
    
    contract_ids = fields.One2many(
        'hr.contract',
        'multi_contract_id',
        string='Created Contracts',
        readonly=True
    )
    
    contract_count = fields.Integer(
        string='Contracts Created',
        compute='_compute_contract_count',
        store=True
    )
    
    notes = fields.Text(string='Notes')
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    
    use_employee_specific_dates = fields.Boolean(
        string='Use Employee Joining Dates',
        default=True,
        help="If checked, will use each employee's joining date as contract start date"
    )
    
    auto_fetch_custom_fields = fields.Boolean(
        string='Auto-fetch Custom Fields',
        default=True,
        help="Automatically fetch employee code, father name, and other custom fields"
    )

    @api.depends('employee_ids')
    def _compute_employee_count(self):
        for record in self:
            record.employee_count = len(record.employee_ids)

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        for record in self:
            record.contract_count = len(record.contract_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.multi.contract') or 'New'
        return super(HrMultiContract, self).create(vals_list)

    @api.onchange('employee_ids')
    def _onchange_employee_ids(self):
        """Set default department and job if all selected employees have same values"""
        if self.employee_ids and len(self.employee_ids) > 0:
            departments = self.employee_ids.mapped('department_id')
            jobs = self.employee_ids.mapped('job_id')
            
            if len(departments) == 1:
                self.department_id = departments[0]
            
            if len(jobs) == 1:
                self.job_id = jobs[0]

    def action_confirm(self):
        """Confirm the multi-contract record"""
        self.ensure_one()
        if not self.employee_ids:
            raise UserError(_('Please select at least one employee.'))
        
        self.state = 'confirmed'
        return True

    def action_create_contracts(self):
        """Create individual contracts for all selected employees"""
        self.ensure_one()
        
        if self.state != 'confirmed':
            raise UserError(_('Please confirm the multi-contract before creating contracts.'))
        
        if not self.employee_ids:
            raise UserError(_('No employees selected to create contracts.'))
        
        created_contracts = self.env['hr.contract']
        errors = []
        
        for employee in self.employee_ids:
            try:
                contract_vals = self._prepare_contract_values(employee)
                contract = self.env['hr.contract'].create(contract_vals)
                created_contracts |= contract
            except Exception as e:
                errors.append(_('Error creating contract for %s: %s') % (employee.name, str(e)))
        
        if errors:
            raise UserError('\n'.join(errors))
        
        self.state = 'done'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%d contracts created successfully!') % len(created_contracts),
                'type': 'success',
                'sticky': False,
            }
        }

    def _prepare_contract_values(self, employee):
        """Prepare contract values for a single employee"""
        self.ensure_one()
        
        # Determine contract start date
        if self.use_employee_specific_dates and employee.joining_date:
            contract_start_date = employee.joining_date
        else:
            contract_start_date = self.date_start
        
        # Generate contract name/reference
        contract_name = _('Contract - %s - %s') % (
            employee.name,
            fields.Date.to_string(contract_start_date)
        )
        
        vals = {
            'name': contract_name,
            'employee_id': employee.id,
            'date_start': contract_start_date,
            'date_end': self.date_end,
            'wage': self.wage,
            'structure_type_id': self.structure_type_id.id if self.structure_type_id else False,
            'department_id': self.department_id.id if self.department_id else employee.department_id.id,
            'job_id': self.job_id.id if self.job_id else employee.job_id.id,
            'contract_type_id': self.contract_type_id.id if self.contract_type_id else False,
            'resource_calendar_id': self.resource_calendar_id.id if self.resource_calendar_id else employee.resource_calendar_id.id,
            'company_id': self.company_id.id,
            'multi_contract_id': self.id,
        }
        
        # Auto-fetch custom fields if enabled
        if self.auto_fetch_custom_fields:
            if hasattr(employee, 'employee_code') and employee.employee_code:
                vals['employee_code'] = employee.employee_code
            if hasattr(employee, 'father_name') and employee.father_name:
                vals['father_name'] = employee.father_name
        
        return vals

    def action_view_contracts(self):
        """Open created contracts"""
        self.ensure_one()
        return {
            'name': _('Created Contracts'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.contract',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.contract_ids.ids)],
            'context': {'default_multi_contract_id': self.id},
        }

    def action_draft(self):
        """Reset to draft"""
        self.state = 'draft'
        return True

    def action_cancel(self):
        """Cancel the multi-contract"""
        self.state = 'cancel'
        return True

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """Validate date range"""
        for record in self:
            if record.date_end and record.date_end < record.date_start:
                raise ValidationError(_('End date must be after start date.'))

    def unlink(self):
        """Prevent deletion if contracts are created"""
        for record in self:
            if record.state == 'done' and record.contract_ids:
                raise UserError(_('Cannot delete a multi-contract that has created contracts. Cancel it instead.'))
        return super(HrMultiContract, self).unlink()
