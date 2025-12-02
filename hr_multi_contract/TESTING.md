# HR Multi Contract Module - Installation & Testing Guide

## Module Structure
```
hr_multi_contract/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── hr_multi_contract.py      # Main multi-contract model
│   ├── hr_employee.py             # Employee extensions
│   └── hr_contract.py             # Contract extensions
├── wizard/
│   ├── __init__.py
│   └── hr_mass_contract_wizard.py # Mass creation wizard
├── views/
│   ├── hr_multi_contract_views.xml    # Multi-contract views & menus
│   ├── hr_employee_views.xml          # Employee view extensions
│   └── hr_mass_contract_wizard_views.xml # Wizard views
├── security/
│   └── ir.model.access.csv        # Access rights
└── static/
    └── description/
        └── index.html             # Module description
```

## Installation Steps

### 1. Install the Module
```powershell
cd c:\odoo\odoo_v18\odoo18
.\odoo-bin -c ..\odoo_v18.conf -d <database_name> -i hr_multi_contract
```

### 2. Update if Already Installed
```powershell
.\odoo-bin -c ..\odoo_v18.conf -d <database_name> -u hr_multi_contract
```

### 3. Development Mode (with auto-reload)
```powershell
.\odoo-bin -c ..\odoo_v18.conf -d <database_name> -u hr_multi_contract --dev xml,qweb,reload
```

## Testing Checklist

### Test 1: Multi Contract Creation (via Menu)
- [ ] Navigate to Employees → Contracts → Multi Contracts → Multi Contracts
- [ ] Click "Create"
- [ ] Add name: "Q1 2025 Contracts"
- [ ] Select 3-5 employees
- [ ] Set start date: 2025-01-01
- [ ] Set wage: 50000
- [ ] Check "Use Employee Joining Date"
- [ ] Check "Auto-fetch Custom Fields"
- [ ] Click "Confirm"
- [ ] Click "Create Contracts"
- [ ] Verify contracts created successfully
- [ ] Check "Contracts Created" smart button shows correct count
- [ ] Click smart button to view created contracts

### Test 2: Mass Contract Creation (via Employee List)
- [ ] Navigate to Employees → Employees
- [ ] Select multiple employees (checkbox)
- [ ] Click "Action" dropdown
- [ ] Select "Create Mass Contracts"
- [ ] Wizard opens with pre-selected employees
- [ ] Configure contract parameters:
  - Start Date: 2025-02-01
  - Wage: 45000
  - Contract Type: Full-time
  - Use Employee Joining Date: Yes
  - Create Multi-Contract Record: Yes
- [ ] Click "Create Contracts"
- [ ] Verify redirected to multi-contract form
- [ ] Check contracts tab shows all created contracts

### Test 3: Custom Field Auto-Population
Prerequisites: Employees must have Employee Code and Father Name filled

- [ ] Open employee record
- [ ] Verify "Employee Code" field has value (e.g., "EMP001")
- [ ] Verify "Father Name" field has value
- [ ] Create mass contract with "Auto-fetch Custom Fields" enabled
- [ ] After creation, open one of the created contracts
- [ ] Verify "Employee Code" is populated
- [ ] Verify "Father Name" is populated

### Test 4: Joining Date Handling
Prerequisites: Employees must have joining_date filled

- [ ] Create mass contract with "Use Employee Joining Date" = True
- [ ] Set common start date = 2025-01-01
- [ ] Select employees with different joining dates
- [ ] Create contracts
- [ ] Verify each contract has employee's joining date, NOT the common date
- [ ] Repeat with "Use Employee Joining Date" = False
- [ ] Verify all contracts use the common start date

### Test 5: Validation - Overlapping Contracts
- [ ] Select an employee who already has an active contract
- [ ] Try to create new contract with overlapping dates
- [ ] Verify error message appears
- [ ] Message should indicate which employee has overlap
- [ ] Message should show existing contract details

### Test 6: Multi-Contract Workflow
- [ ] Create multi-contract in Draft state
- [ ] Verify cannot create contracts yet
- [ ] Click "Confirm"
- [ ] State changes to "Confirmed"
- [ ] Click "Create Contracts"
- [ ] State changes to "Done"
- [ ] Verify cannot edit anymore
- [ ] Try to delete - should show error
- [ ] Click "Reset to Draft" - should work
- [ ] Click "Cancel" - state changes to "Cancelled"

### Test 7: Smart Buttons & Navigation
- [ ] From multi-contract: Click "Contracts" smart button
- [ ] Verify shows only contracts from this multi-contract
- [ ] Open one contract
- [ ] Verify "Multi Contract" field is populated
- [ ] Click "Multi Contract" link
- [ ] Verify opens the parent multi-contract record
- [ ] From employee form: Click "Multi Contracts" smart button
- [ ] Verify shows all multi-contracts this employee is part of

### Test 8: Department & Job Auto-Fill
- [ ] Select 5 employees from SAME department
- [ ] Open mass contract wizard
- [ ] Verify "Department" field auto-fills
- [ ] Select 5 employees from DIFFERENT departments
- [ ] Verify "Department" field is empty
- [ ] Manually set department
- [ ] Create contracts
- [ ] Verify all contracts use the specified department

### Test 9: Security & Permissions
- [ ] Login as HR Manager
- [ ] Verify can create, edit, delete multi-contracts
- [ ] Login as regular Employee
- [ ] Verify can only view multi-contracts
- [ ] Verify cannot create or edit
- [ ] Check access to wizard is restricted

### Test 10: Search & Filters
- [ ] Navigate to Multi Contracts list
- [ ] Test filters:
  - [ ] Draft
  - [ ] Confirmed
  - [ ] Done
  - [ ] This Month
- [ ] Test Group By:
  - [ ] Status
  - [ ] Department
  - [ ] Job Position
  - [ ] Start Date
- [ ] Test search by reference number
- [ ] Test search by employee name

## Expected Results Summary

✓ All contracts created successfully with correct data
✓ Custom fields (Employee Code, Father Name) auto-populated
✓ Joining dates respected when option enabled
✓ Overlapping contract validation works
✓ State workflow functions correctly
✓ Smart buttons show accurate counts
✓ Navigation between records works
✓ Sequence generates unique references (MC/00001, MC/00002, etc.)
✓ Multi-contract record tracks all created contracts
✓ Security restrictions enforced

## Common Issues & Solutions

### Issue 1: Module Not Appearing in Apps
**Solution**: 
- Update app list: Settings → Apps → Update Apps List
- Search for "HR Multi Contract"

### Issue 2: Import Error
**Solution**: 
- Ensure hr_employee_entended is installed first
- Check dependencies in __manifest__.py

### Issue 3: Custom Fields Not Showing
**Solution**: 
- Verify hr_employee_entended module is installed
- Check employee records have these fields populated
- Ensure "Auto-fetch Custom Fields" is enabled

### Issue 4: Sequence Not Working
**Solution**: 
- Check ir.sequence record exists: Settings → Technical → Sequences
- Code: hr.multi.contract
- If missing, re-install module

### Issue 5: Permission Denied
**Solution**: 
- User must be in "HR Officer: Manage all contracts" group
- Settings → Users & Companies → Users → Select user → Access Rights

## Database Backup Recommendation
Before testing in production:
```powershell
cd "C:\Program Files\PostgreSQL\17\bin"
.\pg_dump -U odoo -d <database_name> -F c -f "backup_before_multicontract.dump"
```

## Support Contacts
- Module Author: Akshat Gupta
- Technical Team: [Your Team Contact]
- Documentation: See README.md

## Version History
- 18.0.1.0.0 - Initial release
  - Mass contract creation
  - Custom field support
  - Joining date handling
  - Complete workflow
