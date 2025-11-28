from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class Employee(models.Model):
    _inherit = 'hr.employee'

    joining_date = fields.Date(
        compute='_compute_joining_date',
        string='Joining Date',
        store=True,
        help="Employee joining date"
    )
    
    join_date = fields.Date(string='Join Date', store=True)
    father_name = fields.Char(string='Father Name')

    @api.depends('join_date', 'create_date')
    def _compute_joining_date(self):
        """Compute the joining date based on when the employee record was created."""
        for employee in self:
            if employee.join_date:
                employee.joining_date = employee.join_date
            elif employee.create_date:
                employee.joining_date = employee.create_date.date()
            else:
                employee.joining_date = False

    def write(self, vals):
        """Override write to synchronize resource_calendar_id with open contracts."""
        # Skip synchronization if already in a contract-employee update loop
        if self.env.context.get('skip_contract_calendar_sync'):
            return super(Employee, self).write(vals)

        # Store old contract_id for leave transfer processing
        old_contract_ids = {employee.id: employee.contract_id for employee in self}

        # Apply the changes to the employee
        res = super(Employee, self).write(vals)

        # Synchronize resource_calendar_id to open contracts
        if 'resource_calendar_id' in vals and not self.env.context.get('calendar_sync_from_contract'):
            new_calendar = vals['resource_calendar_id']
            for employee in self:
                # Check if the new calendar matches the current contract's calendar
                # If so, skip updating contracts to prevent loops from contract updates
                if employee.contract_id and employee.contract_id.resource_calendar_id.id == new_calendar:
                    continue

                # Find all open contracts for the employee
                open_contracts = employee.contract_ids.filtered(lambda c: c.state == 'open')
                if open_contracts:
                    # Update resource_calendar_id for all open contracts
                    open_contracts.with_context(calendar_sync_from_employee=True).sudo().write({
                        'resource_calendar_id': new_calendar
                    })
                    # Ensure contract_id is set to an open contract if not already
                    if employee.contract_id not in open_contracts:
                        employee.with_context(skip_contract_calendar_sync=True).contract_id = open_contracts[0]
                # Update contract_id's calendar if no open contracts exist but contract_id is set
                elif employee.contract_id:
                    employee.contract_id.with_context(calendar_sync_from_employee=True).sudo().write({
                        'resource_calendar_id': new_calendar
                    })

        # Handle contract_id changes for leave transfers
        if vals.get('contract_id') and not self.env.context.get('skip_contract_calendar_sync'):
            for employee in self:
                old_contract = old_contract_ids.get(employee.id)
                if old_contract and old_contract.id != employee.contract_id.id:
                    old_calendar = old_contract.resource_calendar_id
                    new_calendar = employee.contract_id.resource_calendar_id
                    old_calendar.transfer_leaves_to(new_calendar, employee.resource_id)

                # Sync employee's calendar with the new contract
                if employee.resource_calendar_id.id != employee.contract_id.resource_calendar_id.id:
                    employee.with_context(
                        calendar_sync_from_contract=True,
                        skip_contract_calendar_sync=True
                    ).resource_calendar_id = employee.contract_id.resource_calendar_id

        return res

class Contract(models.Model):
    _inherit = 'hr.contract'

    father_name = fields.Char(string='Father Name')

    def write(self, vals):
        """Override write to handle contract updates, relying on base behavior for employee sync."""
        # Apply changes via the parent method (includes base hr.contract logic)
        res = super(Contract, self).write(vals)

        # The base hr.contract write method already updates employee.resource_calendar_id
        # for open contracts or specific draft states. Additional sync logic can be minimal.
        # If custom employee sync beyond base behavior is needed, add it here with checks.
        if 'resource_calendar_id' in vals and not self.env.context.get('calendar_sync_from_employee'):
            open_contracts = self.filtered(lambda c: c.state == 'open')
            for contract in open_contracts:
                # Only update employee if this is the current contract and values differ
                if (contract == contract.employee_id.contract_id and
                    contract.employee_id.resource_calendar_id.id != vals['resource_calendar_id']):
                    contract.employee_id.with_context(calendar_sync_from_contract=True).sudo().write({
                        'resource_calendar_id': vals['resource_calendar_id']
                    })

        return res