# Week-Off Hours in Hourly Wage Calculation - Implementation Guide

## 🎯 Overview

**Version 1.2.0** introduces a major change in how hourly wages are calculated for employees on hourly contracts. Week-off hours are now **included in the hourly rate calculation**, resulting in a lower hourly rate that accounts for non-working days.

## 📊 Calculation Logic

### Old Calculation (v1.1.0 and below)
```
Hourly Rate = Monthly Wage / Working Hours Only
Example: $3,000 / 176 hours = $17.05/hour
```

### New Calculation (v1.2.0)
```
Hourly Rate = Monthly Wage / (Working Hours + Week-Off Hours)
Example: $3,000 / (176 + 64) = $3,000 / 240 = $12.50/hour
```

## 🔢 Detailed Example

### Scenario: January 2025 (31 days)

**Employee Details:**
- Monthly Wage: $3,000
- Working Schedule: Monday to Friday (5 days/week)
- Hours per Day: 8 hours

**Period Breakdown:**
- Total Calendar Days: 31 days
- Working Days: 22 days (Mon-Fri)
- Week-Off Days: 8 days (Saturdays & Sundays)
- Public Holidays: 1 day (New Year)

**Hours Calculation:**
- Working Hours: 22 days × 8 hours = 176 hours
- Week-Off Hours: 8 days × 8 hours = 64 hours
- Total Period Hours: 176 + 64 = 240 hours

**Hourly Rate Calculation:**
```
Hourly Rate = $3,000 / 240 hours = $12.50/hour
```

**Payslip Worked Days:**
```
Work Entry Type          Days    Hours   Hourly Rate   Amount
─────────────────────────────────────────────────────────────
Attendance              22.0    176.0      $12.50    $2,200.00
Week-Off Days            8.0     64.0      $12.50        $0.00
Public Holiday           1.0      8.0      $12.50        $0.00
─────────────────────────────────────────────────────────────
TOTAL                   31.0    248.0                $2,200.00
```

**Important Notes:**
- ✅ Hourly rate is **$12.50** (includes week-offs in divisor)
- ✅ Working days: 22 days × $12.50 × 8 hours = **$2,200**
- ✅ Week-off days: **$0.00** (not paid)
- ✅ Total pay: **$2,200** (not full monthly wage)

## 💡 Why This Change?

### Business Logic

1. **Proportional Pay**: Employees are paid only for days worked
2. **Fair Rate**: Hourly rate reflects total period hours including week-offs
3. **Consistent Calculations**: Same rate applies to all work entry types
4. **Accounting Accuracy**: Week-offs are tracked but unpaid

### Use Cases

**✅ Best for:**
- Part-time employees
- Hourly wage contracts
- Variable schedules
- Attendance-based pay

**⚠️ Consider carefully for:**
- Salaried employees expecting full monthly pay
- Fixed monthly contracts
- Employees with guaranteed minimums

## 🔧 Technical Implementation

### Modified Functions

#### 1. `hr.contract._get_monthly_hour_volume()`
**Location:** `models/hr_contract.py`

**What Changed:**
- Now calls `_get_period_work_hours()` with `include_weekoff=True`
- Returns: Working Hours + Week-Off Hours

**Code:**
```python
def _get_monthly_hour_volume(self):
    if date_from and date_to:
        hours = self._get_period_work_hours(date_from, date_to, include_weekoff=True)
        return hours
```

#### 2. `hr.contract._get_period_work_hours()`
**Location:** `models/hr_contract.py`

**What Changed:**
- New parameter: `include_weekoff=False` (default)
- When `True`, adds week-off hours to working hours
- Calls `_calculate_weekoff_hours()` for calculation

**Code:**
```python
def _get_period_work_hours(self, date_from, date_to, include_weekoff=False):
    working_hours = # ... calculate working hours ...
    
    if include_weekoff:
        weekoff_hours = self._calculate_weekoff_hours(date_from, date_to)
        return working_hours + weekoff_hours
    
    return working_hours
```

#### 3. `hr.contract._calculate_weekoff_hours()` (NEW)
**Location:** `models/hr_contract.py`

**What It Does:**
- Calculates week-off days: Total Days - Working Days - Public Holidays
- Converts to hours: Week-off Days × Hours Per Day
- Returns week-off hours for the period

**Code:**
```python
def _calculate_weekoff_hours(self, date_from, date_to):
    total_days = (date_to - date_from).days + 1
    working_days = self._calculate_working_days(date_from, date_to)
    public_holidays = self._calculate_public_holidays(date_from, date_to)
    
    weekoff_days = max(0, total_days - working_days - public_holidays)
    hours_per_day = self.resource_calendar_id.hours_per_day or 8.0
    
    return weekoff_days * hours_per_day
```

#### 4. `hr.payslip.worked.days._compute_amount()`
**Location:** `models/hr_payslip_worked_days.py`

**What Changed:**
- Updated comments to clarify week-off inclusion
- Hourly rate now reflects week-off hours in calculation
- Week-off lines still get `amount = 0.0`

**Effect:**
- All paid work entry types use the adjusted hourly rate
- Week-offs remain unpaid but affect the rate

## 📋 Testing Guide

### Test Case 1: Standard Month
**Setup:**
- Employee: John Doe
- Monthly Wage: $3,000
- Working Schedule: Mon-Fri, 8 hours/day
- Period: January 1-31, 2025

**Expected Results:**
```python
# Run in Odoo shell
payslip = env['hr.payslip'].browse(PAYSLIP_ID)

# Check calculation
contract = payslip.contract_id
period_hours = contract._get_period_work_hours(
    payslip.date_from, 
    payslip.date_to, 
    include_weekoff=True
)

print(f"Total Hours (with week-offs): {period_hours}")
# Expected: ~240 hours (176 working + 64 week-off)

hourly_rate = 3000 / period_hours
print(f"Hourly Rate: ${hourly_rate:.2f}")
# Expected: ~$12.50/hour

# Check worked days
for line in payslip.worked_days_line_ids:
    print(f"{line.code}: {line.number_of_hours} hrs @ ${hourly_rate:.2f} = ${line.amount:.2f}")
# Expected:
# WORK100: 176 hrs @ $12.50 = $2,200.00
# WEEKOFF: 64 hrs @ $0.00 = $0.00
```

### Test Case 2: With Leave
**Setup:**
- Same as Test Case 1
- + 2 days of paid leave

**Expected:**
- Working Days: 20 (was 22)
- Leave Days: 2
- Week-Off Days: 8
- Hourly Rate: Still $12.50 (same total hours)
- Working Amount: 20 × 8 × $12.50 = $2,000
- Leave Amount: 2 × 8 × $12.50 = $200
- Total: $2,200

## 🚨 Important Warnings

### 1. Monthly Salary Changes
**Issue:** Employees on hourly contracts may not receive full monthly wage if they don't work all scheduled days.

**Solution Options:**
- Use fixed monthly contracts for guaranteed pay
- Add minimum pay guarantees in salary rules
- Adjust working schedule to match expected pay

### 2. Overtime Calculations
**Issue:** Overtime rates must use the adjusted hourly rate.

**Check:** Ensure overtime rules multiply the correct base rate.

### 3. Historical Payslips
**Issue:** Old payslips used different calculation.

**Action:** Do NOT recompute old payslips - they were correct for their version.

## 🔄 Migration Guide

### Upgrading from v1.1.0 to v1.2.0

**Step 1: Backup**
```bash
# Backup database first
pg_dump -h localhost -p 5433 -U odoo -d your_database > backup_before_v1.2.0.sql
```

**Step 2: Upgrade Module**
```bash
cd c:\odoo\odoo_v18\odoo18
.\.venv\Scripts\python.exe .\odoo-bin -c ..\odoo_v18_payroll.conf -u hr_payroll_workdays_extended --stop-after-init
```

**Step 3: Test Sample Payslip**
- Create test payslip for one employee
- Verify hourly rate calculation
- Check amounts match expectations
- Review worked days breakdown

**Step 4: Communicate Changes**
- Inform HR team about new calculation
- Update documentation
- Train payroll staff
- Set expectations with employees if applicable

## 📞 Support

### Debug Commands

**Check hourly rate calculation:**
```python
contract = env['hr.contract'].browse(CONTRACT_ID)
working_hours = contract._get_period_work_hours('2025-01-01', '2025-01-31', include_weekoff=False)
total_hours = contract._get_period_work_hours('2025-01-01', '2025-01-31', include_weekoff=True)
weekoff_hours = total_hours - working_hours

print(f"Working Hours: {working_hours}")
print(f"Week-Off Hours: {weekoff_hours}")
print(f"Total Hours: {total_hours}")
print(f"Hourly Rate: ${contract.wage / total_hours:.2f}")
```

**Check week-off calculation:**
```python
payslip = env['hr.payslip'].browse(PAYSLIP_ID)
summary = payslip._get_weekoff_summary()
for key, value in summary.items():
    print(f"{key}: {value}")
```

## 📚 Related Documentation

- `README.md` - Module overview and features
- `IMPLEMENTATION_SUMMARY.md` - Week-off days feature details
- `QUICKSTART.md` - Quick reference guide

---
**Version**: 1.2.0  
**Last Updated**: November 2025  
**Breaking Change**: YES - Hourly rate calculation modified
