from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class Employee(models.Model):
    _inherit = 'hr.employee'

    
    joining_date = fields.Date(compute='_compute_joining_date',
                              string='Joining Date', store=True,
                              help="Employee joining date")

    @api.depends('create_date')
    def _compute_joining_date(self):
        """Compute the joining date based on when the employee record was created."""
        for employee in self:
            if employee.create_date:
                employee.joining_date = employee.create_date.date()
            else:
                employee.joining_date = False

    def write(self, vals):
        """Override write to handle resource calendar updates and contract synchronization."""
        # Check if we're already in the middle of a contract-employee update loop
        if self.env.context.get('skip_contract_calendar_sync'):
            return super(Employee, self).write(vals)
            
        # Store old contract_id for leave transfer processing
        old_contract_ids = {employee.id: employee.contract_id for employee in self}
        
        # Call the parent write method to apply the changes to the employee
        res = super(Employee, self).write(vals)
        
        # Check if resource_calendar_id is being updated
        if 'resource_calendar_id' in vals and not self.env.context.get('calendar_sync_from_contract'):
            # Iterate over each employee record being updated
            for employee in self:
                # Find all contracts with state='open' in contract_ids
                open_contracts = employee.contract_ids.filtered(lambda c: c.state == 'open')
                if open_contracts:
                    # Update resource_calendar_id for all open contracts - with context flag to prevent loops
                    open_contracts.with_context(calendar_sync_from_employee=True).sudo().write({
                        'resource_calendar_id': vals['resource_calendar_id']
                    })
                    # Ensure contract_id is set to one of the open contracts (if not already)
                    if employee.contract_id not in open_contracts:
                        employee.with_context(skip_contract_calendar_sync=True).contract_id = open_contracts[0]
                # If no open contracts exist but contract_id is set, update it as well
                elif employee.contract_id:
                    employee.contract_id.with_context(calendar_sync_from_employee=True).sudo().write({
                        'resource_calendar_id': vals['resource_calendar_id']
                    })
        
        # Handle contract_id changes for leave transfers
        if vals.get('contract_id') and not self.env.context.get('skip_contract_calendar_sync'):
            for employee in self:
                # Only transfer leaves if the contract actually changed
                old_contract = old_contract_ids.get(employee.id)
                if old_contract and old_contract.id != employee.contract_id.id:
                    old_calendar = old_contract.resource_calendar_id
                    new_calendar = employee.contract_id.resource_calendar_id
                    old_calendar.transfer_leaves_to(new_calendar, employee.resource_id)
                
                # Update employee's resource calendar to match the contract
                if employee.resource_calendar_id.id != employee.contract_id.resource_calendar_id.id:
                    employee.with_context(calendar_sync_from_contract=True, skip_contract_calendar_sync=True).resource_calendar_id = employee.contract_id.resource_calendar_id
        
        return res
    

class Contract(models.Model):
    _inherit = 'hr.contract'
    
    def write(self, vals):
        """Override write to update employee's resource_calendar_id when contract's is updated."""
        # Call the parent write method to apply the changes to the contract
        res = super(Contract, self).write(vals)
        
        # Check if resource_calendar_id is being updated and we're not already in a sync loop
        if 'resource_calendar_id' in vals and not self.env.context.get('calendar_sync_from_employee'):
            # Only sync calendar to employees for open contracts
            open_contracts = self.filtered(lambda c: c.state == 'open')
            for contract in open_contracts:
                # If this contract is the employee's current contract, update employee's calendar too
                if contract == contract.employee_id.contract_id and contract.employee_id.resource_calendar_id.id != vals['resource_calendar_id']:
                    contract.employee_id.with_context(calendar_sync_from_contract=True).sudo().write({
                        'resource_calendar_id': vals['resource_calendar_id']
                    })
        
        return res