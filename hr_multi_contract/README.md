# HR Multi Contract Management Module

## Overview
This module enables HR managers to create multiple employee contracts at once, streamlining the contract creation process for bulk hiring, annual renewals, or organizational restructuring.

## Features

### 1. Multi Contract Management
- Create and manage multi-contract records
- Track all contracts created from a single batch
- View statistics: employee count, contract count
- Complete workflow: Draft → Confirmed → Done
- Activity tracking and messaging

### 2. Mass Contract Creation
- Create contracts for multiple employees with one click
- Wizard interface from employee list view
- Automatic field population from employee records
- Custom field support (Employee Code, Father Name)
- Smart date handling (use joining date or custom date)

### 3. Key Capabilities
- **Auto-fetch Custom Fields**: Automatically populate employee_code and father_name from employee records
- **Flexible Start Dates**: Use employee joining dates or specify a common start date
- **Validation**: Prevents creation of overlapping contracts
- **Batch Tracking**: Optional multi-contract record creation for audit trail
- **Smart Defaults**: Auto-populate department, job, and calendar if all employees share values

## Usage

### Method 1: Using Multi Contract (New Menu)
1. Navigate to **Employees → Contracts → Multi Contracts → Multi Contracts**
2. Click **Create**
3. Select multiple employees
4. Configure contract parameters
5. Click **Confirm**, then **Create Contracts**

### Method 2: From Employee List View (Action Button)
1. Navigate to **Employees → Employees**
2. Select one or more employees from the list
3. Click **Action → Create Mass Contracts**
4. Configure contract parameters in wizard
5. Click **Create Contracts**

### Method 3: From Employee Form
1. Open an employee record
2. Click the **Multi Contracts** smart button
3. Create a new multi-contract including this employee

## Configuration

### Prerequisites
- **hr**: Base HR module
- **hr_contract**: Contract management
- **hr_employee_entended**: Custom employee fields (Employee Code, Father Name, Joining Date)

### Fields Mapping
- **Employee Joining Date** (`hr.employee.joining_date`) → **Contract Start Date** (`hr.contract.date_start`)
- **Employee Code** (`hr.employee.employee_code`) → **Contract Employee Code** (`hr.contract.employee_code`)
- **Father Name** (`hr.employee.father_name`) → **Contract Father Name** (`hr.contract.father_name`)

## Security

### Access Rights
- **HR Contract Manager**: Full access to create, read, update, delete multi-contracts
- **Base Users**: Read-only access to view multi-contracts

## Technical Details

### Models
- **hr.multi.contract**: Main model for batch contract management
- **hr.mass.contract.wizard**: Transient wizard for mass creation
- **hr.employee**: Extended with multi-contract relationship
- **hr.contract**: Extended with multi-contract reference

### Views
- Multi Contract: Form, List, Kanban, Search
- Mass Contract Wizard: Form
- Employee: Inherited form and list views

### Workflow States
1. **Draft**: Initial state, editable
2. **Confirmed**: Validated, ready to create contracts
3. **Done**: Contracts created
4. **Cancelled**: Abandoned

## Benefits
- **Time Saving**: Create 50 contracts in the time it takes to create 1
- **Consistency**: Ensure all contracts use same parameters
- **Accuracy**: Auto-populate fields from employee records
- **Traceability**: Track which contracts were created together
- **Flexibility**: Override defaults per employee (via joining date)

## Example Scenarios

### Scenario 1: New Hire Batch
Company hired 15 new employees on different dates:
1. Select all 15 employees
2. Enable "Use Employee Joining Date"
3. Set common wage and contract type
4. Create contracts - each gets their actual joining date

### Scenario 2: Annual Renewal
Renew contracts for 30 employees on same date:
1. Select all 30 employees
2. Set January 1, 2025 as start date
3. Disable "Use Employee Joining Date"
4. Create contracts - all start on January 1

### Scenario 3: Department-wide Update
Update contracts for entire department:
1. Filter employees by department
2. Select all
3. Set new wage and structure type
4. Create contracts with tracking

## Troubleshooting

### "Overlapping Contract" Error
- An employee already has a contract in the date range
- Check existing contracts and adjust dates

### "No Joining Date" Warning
- If using joining dates, ensure all employees have this field populated
- Or disable "Use Employee Joining Date"

### Custom Fields Not Populated
- Ensure "Auto-fetch Custom Fields" is enabled
- Verify hr_employee_entended module is installed
- Check that employees have these fields filled

## Version
- **Module Version**: 18.0.1.0.0
- **Odoo Version**: 18.0
- **Author**: Akshat Gupta
- **License**: LGPL-3

## Support
For issues or feature requests, please contact the development team.
