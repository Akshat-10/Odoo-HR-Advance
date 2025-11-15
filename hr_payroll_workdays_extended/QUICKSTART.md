# 🚀 Quick Start Guide - Week-Off Days Feature

## Upgrade Command

```bash
cd c:\odoo\odoo_v18\odoo18
.\odoo-bin -c ..\odoo_v18_payroll.conf -d <your_database> -u hr_payroll_workdays_extended
```

## Verify Installation

### 1. Check Work Entry Type
```python
# From Odoo shell
weekoff_type = env.ref('hr_payroll_workdays_extended.hr_work_entry_type_weekoff')
print(f"✓ Code: {weekoff_type.code}")
print(f"✓ Name: {weekoff_type.name}")
```

### 2. Test on a Payslip
```python
# Create test payslip
employee = env['hr.employee'].search([('name', 'ilike', 'test')], limit=1)
payslip = env['hr.payslip'].create({
    'employee_id': employee.id,
    'contract_id': employee.contract_id.id,
    'struct_id': employee.contract_id.structure_type_id.default_struct_id.id,
    'date_from': '2025-01-01',
    'date_to': '2025-01-31',
})

# Compute and check
payslip.compute_sheet()
weekoff_lines = payslip.worked_days_line_ids.filtered(lambda l: l.code == 'WEEKOFF')
print(f"✓ Week-off days: {weekoff_lines[0].number_of_days if weekoff_lines else 'NOT FOUND'}")
```

## Quick Test Commands

### View Calculation Details
```python
payslip = env['hr.payslip'].browse(PAYSLIP_ID)
summary = payslip._get_weekoff_summary()
for key, value in summary.items():
    print(f"{key}: {value}")
```

### Validate Employee Calendar
```python
employee = env['hr.employee'].browse(EMPLOYEE_ID)
contract = employee.contract_id
calendar = contract.resource_calendar_id

print(f"Calendar: {calendar.name}")
print(f"Working days: {set(calendar.attendance_ids.mapped('dayofweek'))}")
print(f"Hours/day: {calendar.hours_per_day}")
```

## Expected Result

In payslip **Worked Days** tab:
```
Work Entry Type          Days    Hours   Amount
─────────────────────────────────────────────────
Attendance              22.0    176.0   $5,000.00
Week-Off Days            8.0     64.0       $0.00  ← NEW LINE (No amount - tracking only)
```

**Note:** Week-off days always show **$0.00** amount - they are non-working days for tracking purposes only.

## Common Issues

| Issue | Solution |
|-------|----------|
| Week-off = 0 | Check: Contract has calendar, Calendar has attendance records |
| Line not showing | Run: `payslip.compute_sheet()` or upgrade module |
| Wrong calculation | Use: `payslip._get_weekoff_summary()` to debug |

## Key Files Created/Modified

```
✓ data/hr_work_entry_type_data.xml     (NEW)
✓ models/hr_payslip.py                 (NEW)
✓ models/__init__.py                   (UPDATED)
✓ __manifest__.py                      (UPDATED v1.1.0)
✓ README.md                            (NEW)
✓ IMPLEMENTATION_SUMMARY.md            (NEW)
✓ tests/test_weekoff_calculation.py    (NEW)
```

## What Changed

### Before (v1.0.0)
- ✓ Dynamic hourly wage calculation

### After (v1.1.0)
- ✓ Dynamic hourly wage calculation
- ✓ **Week-off days calculation** (NEW!)
- ✓ Automatic integration with payslip
- ✓ Based on resource.calendar configuration

## Features

1. **Automatic Calculation**: Runs when computing payslip
2. **Calendar-Based**: Uses employee's working schedule
3. **Smart Logic**: `Total Days - Working Days - Public Holidays`
4. **Zero Configuration**: Works out of the box
5. **Reporting Ready**: Data available for HR analytics

## Next Steps

1. ✅ Upgrade module (command above)
2. ✅ Test on a sample payslip
3. ✅ Verify calculation with `_get_weekoff_summary()`
4. ✅ Review in production with actual employee data
5. ✅ Train HR team on new field

## Support

📖 **Documentation**: See `README.md`  
🔧 **Detailed Guide**: See `IMPLEMENTATION_SUMMARY.md`  
🧪 **Test Scripts**: See `tests/test_weekoff_calculation.py`

---
**Version**: 1.1.0 | **Status**: Ready for Production ✅
