# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class HrMassContractWizard(models.TransientModel):
    _name = 'hr.mass.contract.wizard'
    _description = 'Mass Contract Creation Wizard'

    employee_ids = fields.Many2many(
        'hr.employee',
        'hr_mass_contract_wizard_employee_rel',
        'wizard_id',
        'employee_id',
        string='Employees',
        required=True,
        help="Select employees to create contracts for"
    )
    
    employee_count = fields.Integer(
        string='Selected Employees',
        compute='_compute_employee_count'
    )
    
    structure_type_id = fields.Many2one(
        'hr.payroll.structure.type',
        string='Salary Structure Type',
        help="Leave empty to use employee's default structure type"
    )
    
    date_start = fields.Date(
        string='Contract Start Date',
        required=True,
        default=fields.Date.today,
        help="Start date for all contracts. Will be overridden by joining date if 'Use Joining Date' is checked"
    )
    
    date_end = fields.Date(
        string='Contract End Date',
        help="End date for all contracts (leave empty for indefinite contracts)"
    )
    
    wage = fields.Monetary(
        string='Wage',
        required=True,
        help="Basic wage for all employees"
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
        help="Leave empty to use each employee's current department"
    )
    
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        help="Leave empty to use each employee's current job position"
    )
    
    contract_type_id = fields.Many2one(
        'hr.contract.type',
        string='Contract Type'
    )
    
    resource_calendar_id = fields.Many2one(
        'resource.calendar',
        string='Working Schedule',
        help="Leave empty to use each employee's default working schedule"
    )
    
    use_employee_joining_date = fields.Boolean(
        string='Use Employee Joining Date as Start Date',
        default=True,
        help="Use each employee's joining date as their contract start date"
    )
    
    auto_fetch_custom_fields = fields.Boolean(
        string='Auto-fetch Custom Fields',
        default=True,
        help="Automatically populate employee code, father name from employee record"
    )
    
    create_multi_contract_record = fields.Boolean(
        string='Create Multi-Contract Record',
        default=True,
        help="Create a multi-contract record to track this batch creation"
    )
    
    notes = fields.Text(string='Notes')
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.depends('employee_ids')
    def _compute_employee_count(self):
        for wizard in self:
            wizard.employee_count = len(wizard.employee_ids)

    @api.onchange('employee_ids')
    def _onchange_employee_ids(self):
        """Suggest common values if all employees share them"""
        if self.employee_ids:
            departments = self.employee_ids.mapped('department_id')
            jobs = self.employee_ids.mapped('job_id')
            calendars = self.employee_ids.mapped('resource_calendar_id')
            
            # Set default department if all employees are in same department
            if len(departments) == 1 and not self.department_id:
                self.department_id = departments[0]
            
            # Set default job if all employees have same job
            if len(jobs) == 1 and not self.job_id:
                self.job_id = jobs[0]
            
            # Set default calendar if all employees have same calendar
            if len(calendars) == 1 and not self.resource_calendar_id:
                self.resource_calendar_id = calendars[0]

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """Validate date range"""
        for wizard in self:
            if wizard.date_end and wizard.date_end < wizard.date_start:
                raise ValidationError(_('End date must be after start date.'))

    def action_create_contracts(self):
        """Create contracts for all selected employees"""
        self.ensure_one()
        
        if not self.employee_ids:
            raise UserError(_('Please select at least one employee.'))
        
        # Validate employees don't have overlapping contracts
        self._validate_no_overlapping_contracts()
        
        created_contracts = self.env['hr.contract']
        multi_contract = None
        errors = []
        
        # Create multi-contract record if requested
        if self.create_multi_contract_record:
            multi_contract = self._create_multi_contract_record()
        
        # Create individual contracts
        for employee in self.employee_ids:
            try:
                contract_vals = self._prepare_contract_values(employee, multi_contract)
                contract = self.env['hr.contract'].create(contract_vals)
                created_contracts |= contract
            except Exception as e:
                errors.append(_('Error creating contract for %s: %s') % (employee.name, str(e)))
        
        if errors:
            error_msg = '\n'.join(errors)
            if created_contracts:
                error_msg += _('\n\n%d contracts were created successfully before errors occurred.') % len(created_contracts)
            raise UserError(error_msg)
        
        # Return action to view created contracts
        return self._get_success_action(created_contracts, multi_contract)

    def _validate_no_overlapping_contracts(self):
        """Check if employees already have contracts in the date range"""
        for employee in self.employee_ids:
            # Determine the start date for this employee
            if self.use_employee_joining_date and employee.joining_date:
                start_date = employee.joining_date
            else:
                start_date = self.date_start
            
            # Build domain to check for overlapping contracts
            domain = [
                ('employee_id', '=', employee.id),
                ('date_start', '<=', self.date_end or '2099-12-31'),
            ]
            
            if self.date_end:
                domain.append('|')
                domain.append(('date_end', '>=', start_date))
                domain.append(('date_end', '=', False))
            else:
                domain.append('|')
                domain.append(('date_end', '>=', start_date))
                domain.append(('date_end', '=', False))
            
            existing_contracts = self.env['hr.contract'].search(domain, limit=1)
            
            if existing_contracts:
                raise ValidationError(
                    _('Employee %s already has an overlapping contract: %s (from %s to %s)') % (
                        employee.name,
                        existing_contracts[0].name,
                        existing_contracts[0].date_start,
                        existing_contracts[0].date_end or 'Indefinite'
                    )
                )

    def _create_multi_contract_record(self):
        """Create a multi-contract record"""
        vals = {
            'employee_ids': [(6, 0, self.employee_ids.ids)],
            'structure_type_id': self.structure_type_id.id if self.structure_type_id else False,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'wage': self.wage,
            'currency_id': self.currency_id.id,
            'department_id': self.department_id.id if self.department_id else False,
            'job_id': self.job_id.id if self.job_id else False,
            'contract_type_id': self.contract_type_id.id if self.contract_type_id else False,
            'resource_calendar_id': self.resource_calendar_id.id if self.resource_calendar_id else False,
            'state': 'done',
            'notes': self.notes,
            'company_id': self.company_id.id,
            'use_employee_specific_dates': self.use_employee_joining_date,
            'auto_fetch_custom_fields': self.auto_fetch_custom_fields,
        }
        
        return self.env['hr.multi.contract'].create(vals)

    def _prepare_contract_values(self, employee, multi_contract=None):
        """Prepare contract values for a single employee"""
        # Determine contract start date
        if self.use_employee_joining_date and employee.joining_date:
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
            'currency_id': self.currency_id.id,
            'structure_type_id': self.structure_type_id.id if self.structure_type_id else False,
            'department_id': self.department_id.id if self.department_id else employee.department_id.id,
            'job_id': self.job_id.id if self.job_id else employee.job_id.id,
            'contract_type_id': self.contract_type_id.id if self.contract_type_id else False,
            'resource_calendar_id': self.resource_calendar_id.id if self.resource_calendar_id else employee.resource_calendar_id.id,
            'company_id': self.company_id.id,
        }
        
        # Link to multi-contract if created
        if multi_contract:
            vals['multi_contract_id'] = multi_contract.id
        
        # Auto-fetch custom fields if enabled
        if self.auto_fetch_custom_fields:
            if hasattr(employee, 'employee_code') and employee.employee_code:
                vals['employee_code'] = employee.employee_code
            if hasattr(employee, 'father_name') and employee.father_name:
                vals['father_name'] = employee.father_name
        
        return vals

    def _get_success_action(self, contracts, multi_contract=None):
        """Return action to display after successful creation"""
        message = _('%d contract(s) created successfully!') % len(contracts)
        
        if multi_contract:
            # Return action to view multi-contract
            return {
                'type': 'ir.actions.act_window',
                'name': _('Multi Contract Created'),
                'res_model': 'hr.multi.contract',
                'res_id': multi_contract.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            # Return action to view created contracts
            return {
                'type': 'ir.actions.act_window',
                'name': _('Created Contracts'),
                'res_model': 'hr.contract',
                'view_mode': 'list,form',
                'domain': [('id', 'in', contracts.ids)],
                'target': 'current',
            }

    def action_preview_employees(self):
        """Preview selected employees"""
        self.ensure_one()
        return {
            'name': _('Selected Employees'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.employee_ids.ids)],
            'target': 'new',
        }
