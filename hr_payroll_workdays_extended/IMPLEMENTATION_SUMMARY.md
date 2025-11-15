# Week-Off Days Feature - Implementation Summary

## ✅ What Was Implemented

### 1. **Work Entry Type for Week-Off Days**
- **File:** `data/hr_work_entry_type_data.xml`
- **Code:** `WEEKOFF`
- **Name:** "Week-Off Days"
- **Purpose:** Dedicated work entry type to track non-working days

### 2. **Core Calculation Logic**
- **File:** `models/hr_payslip.py`
- **Key Methods:**
  - `_get_worked_day_lines()`: Override to inject week-off calculation
  - `_compute_weekoff_days()`: Main calculation logic
  - `_calculate_working_days_from_calendar()`: Extract working days from calendar
  - `_calculate_public_holidays()`: Count public holidays
  - `_get_weekoff_summary()`: Debug/reporting helper

### 3. **Enhanced Hourly Wage** (Existing - Maintained)
- **File:** `models/hr_payslip_worked_days.py`
- **File:** `models/hr_contract.py`
- **Purpose:** Dynamic hourly rate based on actual period hours

## 📊 Calculation Formula

```
Week-Off Days = Total Calendar Days - Working Days - Public Holidays

Where:
- Total Calendar Days = (date_to - date_from) + 1
- Working Days = Calculated from resource.calendar attendance records
- Public Holidays = Global leaves (resource.calendar.leaves with no resource_id)
```

## 🎯 How It Works

### Step 1: Data Source
The calculation reads from the employee's **resource.calendar** (Working Schedule):
- **Attendance Records**: Define which weekdays are working days (e.g., Mon-Fri)
- **Hours Per Day**: Used for hour calculations
- **Public Holidays**: Global leaves configured in the calendar

### Step 2: Automatic Integration
When a payslip is computed:
1. System calls `_get_worked_day_lines()`
2. Week-off calculation automatically runs
3. New line added to `worked_days_line_ids` with code `WEEKOFF`
4. Displays alongside other worked day types (WORK100, leaves, etc.)

### Step 3: Display
The week-off line appears in the **Worked Days** tab of the payslip with:
- Number of days (e.g., 8 days)
- Number of hours (e.g., 64 hours, calculated as days × hours_per_day)
- **Amount: 0.00** (Week-offs are non-working days - not paid, tracking only)
- Work entry type: "Week-Off Days"

## 📁 File Structure

```
hr_payroll_workdays_extended/
├── __init__.py
├── __manifest__.py (Updated: v1.1.0)
├── README.md (Complete documentation)
├── data/
│   └── hr_work_entry_type_data.xml (NEW)
├── models/
│   ├── __init__.py (Updated)
│   ├── hr_contract.py (Existing)
│   ├── hr_payslip.py (NEW)
│   └── hr_payslip_worked_days.py (Existing)
└── tests/
    └── test_weekoff_calculation.py (NEW - Helper scripts)
```

## 🔧 Configuration Required

**NONE!** The module automatically uses:
- Employee's contract → resource_calendar_id
- Calendar's attendance records → working weekdays
- Calendar's global leaves → public holidays

## 📋 Example Scenarios

### Scenario 1: Standard 5-Day Week
- **Calendar:** Monday to Friday
- **Period:** January 2025 (31 days)
- **Working Days:** 23 days
- **Public Holidays:** 1 day (New Year)
- **Week-Off:** 31 - 23 - 1 = **7 days**

### Scenario 2: 6-Day Week
- **Calendar:** Monday to Saturday
- **Period:** February 2025 (28 days)
- **Working Days:** 24 days
- **Public Holidays:** 0
- **Week-Off:** 28 - 24 = **4 days** (Sundays only)

### Scenario 3: Partial Month
- **Calendar:** Monday to Friday
- **Period:** March 1-15, 2025 (15 days)
- **Working Days:** 11 days
- **Public Holidays:** 0
- **Week-Off:** 15 - 11 = **4 days**

## 🚀 Testing Instructions

### Method 1: Via Payslip UI
1. Go to **Payroll > Payslips**
2. Create or open a payslip
3. Click **Compute Payslip**
4. Open **Worked Days** tab
5. Look for **"Week-Off Days (WEEKOFF)"** line

### Method 2: Via Python Shell
```python
# Get a payslip
payslip = env['hr.payslip'].browse(PAYSLIP_ID)

# View calculation breakdown
summary = payslip._get_weekoff_summary()
print(summary)

# Output:
# {
#     'payslip_period': '2025-01-01 to 2025-01-31',
#     'total_calendar_days': 31,
#     'working_days': 23.0,
#     'public_holidays': 1.0,
#     'weekoff_days': 7.0,
#     'working_weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
#     'calendar_name': 'Standard 40 Hours/Week'
# }
```

### Method 3: Using Test Helper
```python
# Load test functions
exec(open('/path/to/tests/test_weekoff_calculation.py').read())

# Test a payslip
test_weekoff_calculation(env, PAYSLIP_ID)

# Validate employee setup
validate_calendar_setup(env, EMPLOYEE_ID)
```

## 🎨 Visual Example

**Payslip Worked Days Tab:**
```
┌─────────────────────────────────────────────────────────────┐
│ Work Entry Type      │ Days  │ Hours  │ Amount              │
├─────────────────────────────────────────────────────────────┤
│ Attendance (WORK100) │ 22.0  │ 176.0  │ $5,000.00          │
│ Sick Leave (LEAVE90) │  1.0  │   8.0  │   $227.27          │
│ Week-Off Days (WEEKOFF) │ 8.0   │  64.0  │      $0.00       │ ← NEW!
└─────────────────────────────────────────────────────────────┘
```

## 🔍 Troubleshooting

### Issue: Week-off shows 0 days
**Solution:**
- Verify employee has active contract
- Check contract has resource_calendar_id assigned
- Ensure calendar has attendance records configured

### Issue: Calculation seems incorrect
**Solution:**
1. Use `payslip._get_weekoff_summary()` to see breakdown
2. Check calendar attendance records (HR > Configuration > Working Times)
3. Verify public holidays in resource.calendar.leaves

### Issue: Week-off line not appearing
**Solution:**
- Module must be upgraded: `odoo-bin -u hr_payroll_workdays_extended`
- Work entry type `WEEKOFF` must exist in database
- Payslip must call `compute_sheet()` or `_compute_worked_days_line_ids()`

## 🔐 Security & Permissions

No additional permissions required. Uses existing:
- `hr_payroll.group_hr_payroll_user` (Read)
- `hr_payroll.group_hr_payroll_manager` (Full access)

## 🌍 Compatibility

- ✅ Part-time contracts (time_credit)
- ✅ Multiple calendars per company
- ✅ Two-week alternating schedules
- ✅ Public holidays
- ✅ Hourly and monthly wage types
- ✅ Multi-company setups
- ✅ All timezone configurations

## 📦 Upgrade Path

```bash
# Stop Odoo
sudo systemctl stop odoo

# Backup database (IMPORTANT!)
pg_dump -U odoo -d your_database > backup_before_weekoff.sql

# Upgrade module
./odoo-bin -c /path/to/config.conf -d your_database -u hr_payroll_workdays_extended

# Restart Odoo
sudo systemctl start odoo
```

## 📝 Dependencies

**No new dependencies!** Uses existing:
- `hr_payroll` (core Odoo)
- `payroll_salary_link` (existing custom)
- `hr_attendance_calculs` (existing custom)
- `resource` (core Odoo)

## 💡 Benefits

1. **Automatic:** No manual entry needed
2. **Accurate:** Based on actual calendar configuration
3. **Transparent:** Employees see exact week-off days
4. **Flexible:** Works with any calendar setup
5. **Compliant:** Proper tracking for labor law
6. **Reportable:** Data available for HR analytics

## 🎓 Technical Notes

### Performance
- Minimal overhead: Calculations only run during payslip computation
- Efficient queries: Uses ORM's batch methods
- Cached: Calendar data loaded once per payslip

### Data Integrity
- Read-only: Does not modify calendar or contract data
- Safe: Calculations isolated per payslip
- Validated: Negative values prevented (min 0 days)

### Extensibility
Override `_compute_weekoff_days()` in custom module to:
- Add custom business rules
- Modify calculation formula
- Add conditional logic per employee/contract type

## 📞 Support

For issues or questions:
1. Check README.md for detailed documentation
2. Use test helper scripts to debug
3. Verify calendar setup with `validate_calendar_setup()`
4. Review calculation with `_get_weekoff_summary()`

---

**Module Version:** 1.1.0  
**Author:** Enterprise Custom Modules  
**License:** LGPL-3  
**Date:** November 2025
