# 🚀 Deployment Checklist - v1.2.0

## ✅ Pre-Deployment

### 1. Backup
- [ ] Database backed up
- [ ] Backup location: `___________________________`
- [ ] Backup verified and accessible
- [ ] Backup size: `_____ GB`

### 2. Code Review
- [ ] All files committed to version control
- [ ] Code reviewed by senior developer
- [ ] No syntax errors in Python files
- [ ] No lint errors blocking deployment

### 3. Documentation Review
- [ ] `README.md` updated with new calculation
- [ ] `CUSTOMER_SUMMARY.md` reviewed
- [ ] `WEEK_OFF_HOURLY_CALCULATION.md` complete
- [ ] `VISUAL_CALCULATION_GUIDE.md` clear and accurate

## 🔧 Deployment Steps

### Step 1: Module Upgrade
```bash
cd c:\odoo\odoo_v18\odoo18
.\.venv\Scripts\python.exe .\odoo-bin -c ..\odoo_v18_payroll.conf -u hr_payroll_workdays_extended --stop-after-init
```

**Status:**
- [ ] Command executed successfully
- [ ] No errors in log
- [ ] Module version shows 1.2.0
- [ ] Time completed: `___________`

### Step 2: Verify Module State
**Odoo UI Check:**
- [ ] Navigate to Apps
- [ ] Search "Payroll Workdays Extended"
- [ ] Version shows: **1.2.0**
- [ ] Status: Installed

### Step 3: Test Environment Setup
- [ ] Test database created/selected
- [ ] Test employees configured
- [ ] Working schedules (resource.calendar) verified
- [ ] Test contracts created (hourly wage type)

## 🧪 Testing Checklist

### Test Case 1: Basic Hourly Rate Calculation

**Setup:**
- Employee: Test Employee 1
- Monthly Wage: $3,000
- Working Schedule: Mon-Fri, 8 hours/day
- Period: Current month

**Execute:**
```python
# In Odoo shell
contract = env['hr.contract'].browse(CONTRACT_ID)
working_hours = contract._get_period_work_hours('2025-01-01', '2025-01-31', include_weekoff=False)
total_hours = contract._get_period_work_hours('2025-01-01', '2025-01-31', include_weekoff=True)
weekoff_hours = total_hours - working_hours

print(f"Working Hours: {working_hours}")
print(f"Week-Off Hours: {weekoff_hours}")
print(f"Total Hours: {total_hours}")
print(f"Hourly Rate: ${3000 / total_hours:.2f}")
```

**Expected Results:**
- [ ] Working Hours: ~176
- [ ] Week-Off Hours: ~64
- [ ] Total Hours: ~240
- [ ] Hourly Rate: ~$12.50

**Actual Results:**
- Working Hours: `_______`
- Week-Off Hours: `_______`
- Total Hours: `_______`
- Hourly Rate: `$_______`

**Status:** [ ] PASS  [ ] FAIL

---

### Test Case 2: Payslip Worked Days

**Setup:**
- Create payslip for Test Employee 1
- Period: January 2025
- Compute payslip

**Execute:**
1. Open payslip
2. Go to "Worked Days" tab
3. Check all lines

**Expected Results:**
- [ ] WORK100/Attendance line exists
- [ ] Amount > 0 for working days
- [ ] WEEKOFF line exists
- [ ] Week-off amount = $0.00
- [ ] Hourly rate matches calculated rate

**Actual Results:**
| Code | Days | Hours | Amount | Hourly Rate |
|------|------|-------|--------|-------------|
| WORK100 | `___` | `___` | `$___` | `$___` |
| WEEKOFF | `___` | `___` | `$___` | `$___` |

**Status:** [ ] PASS  [ ] FAIL

---

### Test Case 3: Week-Off Summary

**Execute:**
```python
payslip = env['hr.payslip'].browse(PAYSLIP_ID)
summary = payslip._get_weekoff_summary()
for key, value in summary.items():
    print(f"{key}: {value}")
```

**Expected Results:**
- [ ] Total calendar days matches period
- [ ] Working days count correct
- [ ] Week-off days count correct
- [ ] Public holidays identified
- [ ] Working weekdays list correct

**Actual Results:**
```
payslip_period: _______________
total_calendar_days: ___
working_days: ___
public_holidays: ___
weekoff_days: ___
working_weekdays: _______________
```

**Status:** [ ] PASS  [ ] FAIL

---

### Test Case 4: Amount Calculation Verification

**Execute:**
```python
payslip = env['hr.payslip'].browse(PAYSLIP_ID)
contract = payslip.contract_id

# Get total hours with week-offs
total_hours = contract._get_period_work_hours(
    payslip.date_from, 
    payslip.date_to, 
    include_weekoff=True
)

# Calculate expected hourly rate
expected_rate = contract.wage / total_hours

# Check worked days amounts
for line in payslip.worked_days_line_ids:
    if line.code == 'WEEKOFF':
        print(f"Week-off: {line.number_of_hours} hrs, Amount: ${line.amount:.2f} (should be $0.00)")
    else:
        calculated = line.number_of_hours * expected_rate
        print(f"{line.code}: {line.number_of_hours} hrs × ${expected_rate:.2f} = ${calculated:.2f}")
        print(f"  Actual amount: ${line.amount:.2f}")
        print(f"  Match: {abs(calculated - line.amount) < 0.01}")
```

**Expected Results:**
- [ ] Week-off amount is exactly $0.00
- [ ] Working days amount = hours × hourly_rate
- [ ] All amounts match calculations
- [ ] No rounding errors > $0.01

**Actual Results:**
```
_______________________________________________
_______________________________________________
_______________________________________________
```

**Status:** [ ] PASS  [ ] FAIL

---

### Test Case 5: Different Working Schedules

**Test 5A: 6-Day Work Week**
- Working Schedule: Mon-Sat
- Expected: Only Sunday as week-off
- [ ] Week-off days count = ~4 days/month
- [ ] Higher hourly rate than 5-day week

**Test 5B: Custom Hours**
- Working Schedule: 40 hours/week, irregular days
- [ ] Week-off days calculated correctly
- [ ] Hours per day from calendar

**Status:** [ ] PASS  [ ] FAIL

---

## 📊 Validation

### Data Integrity
- [ ] No negative week-off days
- [ ] No negative amounts
- [ ] Total days = working + weekoff + holidays
- [ ] All payslips compute without errors

### Performance
- [ ] Payslip computation time: `_____ seconds`
- [ ] No timeout errors
- [ ] No memory issues
- [ ] Bulk processing works (10+ payslips)

### Edge Cases
- [ ] Zero working hours handled gracefully
- [ ] No resource calendar: Falls back correctly
- [ ] Partial month: Calculates correctly
- [ ] Public holidays: Excluded from week-offs

## 📝 Sign-Off

### Development Team
- [ ] Developer: `_________________` Date: `__________`
- [ ] Code Reviewer: `_________________` Date: `__________`
- [ ] QA Tester: `_________________` Date: `__________`

### Business Approval
- [ ] HR Manager: `_________________` Date: `__________`
- [ ] Payroll Manager: `_________________` Date: `__________`
- [ ] Finance Manager: `_________________` Date: `__________`

## 🚨 Rollback Plan

### If Issues Found:

**Option 1: Revert to v1.1.0**
```bash
# Restore database backup
psql -h localhost -p 5433 -U odoo -d your_database < backup_before_v1.2.0.sql

# Revert code changes
git checkout v1.1.0
```

**Option 2: Quick Fix**
```bash
# Make fixes
# Test fixes
# Re-upgrade module
.\odoo-bin -c ..\odoo_v18_payroll.conf -u hr_payroll_workdays_extended --stop-after-init
```

## 📞 Support Contacts

- **Developer**: `_________________` Phone: `__________`
- **System Admin**: `_________________` Phone: `__________`
- **On-Call**: `_________________` Phone: `__________`

## 📅 Schedule

- **Deployment Date**: `__________`
- **Deployment Time**: `__________`
- **Expected Duration**: `___ hours`
- **Rollback Deadline**: `__________`
- **Production Go-Live**: `__________`

## ✅ Post-Deployment

### Immediate (Within 1 hour)
- [ ] System health check
- [ ] Error logs reviewed
- [ ] Test payslips in production
- [ ] Key users notified

### Short Term (Within 24 hours)
- [ ] User training completed
- [ ] Documentation distributed
- [ ] Support tickets monitored
- [ ] Performance metrics collected

### Long Term (Within 1 week)
- [ ] All payrolls processed successfully
- [ ] No calculation disputes
- [ ] User feedback collected
- [ ] Lessons learned documented

---
**Deployment Version**: 1.2.0  
**Deployment Type**: Major Update (Breaking Change)  
**Critical**: YES - Affects hourly wage calculations  
**Backup Required**: YES  
**User Training**: Recommended
