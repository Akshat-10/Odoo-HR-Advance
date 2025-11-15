# HR Payroll Workdays Extended

## Overview
This module extends Odoo's payroll functionality with advanced worked days calculations:

1. **Dynamic Hourly Wage Calculation**: Adjusts hourly rates based on actual monthly working hours from the payroll period
2. **Week-Off Days Calculation**: Automatically calculates and displays non-working days (week-offs) based on the employee's working schedule

## Features

### 1. Amount Rounding (NEW in v1.4.0)
- **All payslip amounts rounded to whole numbers** (no decimal cents)
- Payslip line totals: e.g., 32424.43 → 32424.00, 32424.67 → 32425.00
- Paid amounts rounded using standard mathematical rounding
- **Benefits**: Cleaner payslips, easier bank transfers, better employee understanding
- See `AMOUNT_ROUNDING.md` for details

### 2. Dynamic Hourly Wage (INCLUDING Week-Off Hours)
- Calculates hourly wage based on **total hours in period (working + week-off)**
- Uses the employee's resource calendar to determine exact working hours and week-off hours
- Respects public holidays, two-week schedules, and custom calendars
- **Formula**: `monthly_wage / (working_hours + weekoff_hours)`
- **Effect**: Lower hourly rate since week-offs are included in divisor but unpaid
- **Example**: 
  - Monthly Wage: $3,000
  - Working Hours: 176 hours (22 days × 8 hours)
  - Week-off Hours: 64 hours (8 days × 8 hours)
  - **Hourly Rate**: $3,000 / (176 + 64) = $3,000 / 240 = **$12.50/hour**
  - Traditional calculation would be: $3,000 / 176 = $17.05/hour

### 3. Week-Off Days Calculation
Automatically adds a "Week-Off Days" line to payslip worked days with intelligent calculation:

**Calculation Logic:**
```
Week-Off Days = Total Calendar Days - Working Days - Public Holidays
```

**Components:**
- **Total Calendar Days**: Number of days in payslip period (date_from to date_to)
- **Working Days**: Calculated from resource.calendar attendance records (respects configured weekdays)
- **Public Holidays**: Global leaves from resource.calendar.leaves (no specific resource assigned)

**Example:**
- Payslip Period: Jan 1-31 (31 days)
- Working Days: 22 days (Mon-Fri schedule)
- Public Holidays: 1 day (New Year)
- **Week-Off Days: 31 - 22 - 1 = 8 days**

**Important Notes:**
- Week-off days **ARE PAID** at the adjusted hourly rate
- Week-off hours are included in the hourly rate calculation (divisor)
- This means: Lower hourly rate, but applied to ALL hours (working + week-off)
- Result: **Full monthly wage distributed across all days** in the period

## Technical Details

### Models Extended

#### `hr.payslip`
- `_get_worked_day_lines()`: Override to inject week-off calculation
- `_compute_weekoff_days()`: Core calculation logic
- `_calculate_working_days_from_calendar()`: Determines working days from calendar
- `_calculate_public_holidays()`: Counts public holidays in period
- `_get_weekoff_summary()`: Debug helper for calculation breakdown

#### `hr.payslip.worked_days`
- `_compute_amount()`: Enhanced hourly wage calculation with period-aware context

#### `hr.contract`
- `_get_monthly_hour_volume()`: Period-aware working hours calculation
- `_get_period_work_hours()`: Exact hours for specific date range

### Work Entry Type

**Code:** `WEEKOFF`
**Name:** Week-Off Days
**Color:** 7 (Light Gray)
**Sequence:** 99 (Displays last)

### Configuration

No manual configuration required! The module automatically:
- Uses the employee's resource calendar (Working Schedule)
- Detects working weekdays from attendance records
- Identifies public holidays from calendar leaves
- Calculates week-offs dynamically per payslip period

### Calendar Integration

The module respects all resource.calendar settings:
- **Attendance Records**: Defines working days (e.g., Mon-Fri, Mon-Sat)
- **Two-Week Schedules**: Handles alternating weekly patterns
- **Hours Per Day**: Used for hour-to-day conversions
- **Timezone**: All calculations are timezone-aware
- **Public Holidays**: Global leaves (no resource_id) are excluded from working days

## Usage

### For Payroll Managers

1. **Create/Open Payslip**
   - Select employee and period as usual
   - Click "Compute Payslip"

2. **Review Worked Days Tab**
   - Standard working hours (WORK100)
   - Leave types (if any)
   - **NEW: Week-Off Days (WEEKOFF)** - automatically calculated
   - Days and hours displayed for each type

3. **Verify Calculation**
   ```python
   # From Python shell or debugging
   payslip._get_weekoff_summary()
   ```
   Returns:
   ```python
   {
       'payslip_period': '2025-01-01 to 2025-01-31',
       'total_calendar_days': 31,
       'working_days': 22.0,
       'public_holidays': 1.0,
       'weekoff_days': 8.0,
       'working_weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
       'calendar_name': 'Standard 40 Hours/Week'
   }
   ```

### For Salary Rules

Week-off days can be used in salary rule computations:

```python
# In salary rule Python code
weekoff = worked_days.WEEKOFF if worked_days.WEEKOFF else 0
weekoff_days = weekoff.number_of_days if weekoff else 0

# Example: Deduction for excessive week-offs (if applicable)
result = -100 * max(0, weekoff_days - 8)  # Deduct if more than 8 week-offs
```

## Examples

### Example 1: Standard 5-Day Week
**Calendar:** Monday to Friday, 8 hours/day
**Period:** March 2025 (31 days)
**Working Days:** 21 days (Mon-Fri only)
**Public Holidays:** 0
**Week-Off Days:** 31 - 21 - 0 = **10 days** (Saturdays & Sundays)

### Example 2: 6-Day Week with Holiday
**Calendar:** Monday to Saturday, 8 hours/day
**Period:** February 2025 (28 days)
**Working Days:** 24 days (Mon-Sat only)
**Public Holidays:** 1 day (National Holiday)
**Week-Off Days:** 28 - 24 - 1 = **3 days** (Only Sundays)

### Example 3: Partial Month
**Calendar:** Monday to Friday, 8 hours/day
**Period:** Jan 15 - Jan 31, 2025 (17 days)
**Working Days:** 13 days
**Public Holidays:** 0
**Week-Off Days:** 17 - 13 - 0 = **4 days**

## Compatibility

- **Odoo Version:** 18.0
- **Dependencies:**
  - `hr_payroll` (core)
  - `payroll_salary_link` (custom)
  - `hr_attendance_calculs` (custom)
- **Compatible With:**
  - Part-time contracts (time_credit)
  - Multiple calendar schedules
  - Two-week alternating patterns
  - Public holidays
  - All wage types (monthly/hourly)

## Benefits

1. **Transparency**: Employees see exact week-off days on payslips
2. **Accuracy**: Automatic calculation eliminates manual errors
3. **Flexibility**: Works with any calendar configuration
4. **Compliance**: Proper tracking for labor law requirements
5. **Reporting**: Week-off data available for analytics and reports

## Troubleshooting

### Week-off days showing 0?
- **Check:** Employee has a contract with resource_calendar_id set
- **Check:** Calendar has attendance records configured
- **Check:** Payslip period is valid (date_from < date_to)

### Week-off calculation seems wrong?
1. Use `payslip._get_weekoff_summary()` to see breakdown
2. Verify calendar attendance records (HR > Configuration > Working Times)
3. Check if public holidays are configured correctly

### Hours per day incorrect?
- Set `hours_per_day` on resource.calendar
- Default: 8 hours/day if not specified

## Development

### Extending Calculations

To customize week-off calculation logic:

```python
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    def _compute_weekoff_days(self):
        """Override to add custom logic"""
        res = super()._compute_weekoff_days()
        if res:
            # Custom adjustments
            res['number_of_days'] = res['number_of_days'] * 1.5  # Example
        return res
```

### Adding More Worked Day Types

Follow the same pattern:
1. Create work entry type in XML data
2. Override `_get_worked_day_lines()` in hr.payslip
3. Add calculation method
4. Update manifest

## License

LGPL-3

## Author

Enterprise Custom Modules

## Version History

- **1.1.0** (Current)
  - Added Week-Off Days calculation
  - Enhanced documentation
  
- **1.0.0**
  - Initial release
  - Dynamic hourly wage calculation
