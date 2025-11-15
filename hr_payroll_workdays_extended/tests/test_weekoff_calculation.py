# -*- coding: utf-8 -*-
"""
Test/Demo scenarios for Week-Off Days calculation

Usage from Odoo shell:
    # Get a payslip
    payslip = env['hr.payslip'].browse(PAYSLIP_ID)
    
    # Get week-off summary
    summary = payslip._get_weekoff_summary()
    print(summary)
    
    # Test calculation
    weekoff_line = payslip._compute_weekoff_days()
    print(weekoff_line)
"""

# Example test scenarios
SCENARIOS = {
    'standard_5_day': {
        'description': 'Standard Monday-Friday, 40 hours/week',
        'calendar_days': ['0', '1', '2', '3', '4'],  # Mon-Fri
        'hours_per_day': 8.0,
        'period': ('2025-01-01', '2025-01-31'),  # 31 days
        'expected_working_days': 23,  # Approximately
        'expected_weekoff_days': 8,   # 4 Saturdays + 4 Sundays
    },
    
    'six_day_week': {
        'description': 'Monday-Saturday, 48 hours/week',
        'calendar_days': ['0', '1', '2', '3', '4', '5'],  # Mon-Sat
        'hours_per_day': 8.0,
        'period': ('2025-02-01', '2025-02-28'),  # 28 days
        'expected_working_days': 24,
        'expected_weekoff_days': 4,  # 4 Sundays only
    },
    
    'partial_month': {
        'description': 'Mid-month payslip (15 days)',
        'calendar_days': ['0', '1', '2', '3', '4'],  # Mon-Fri
        'hours_per_day': 8.0,
        'period': ('2025-03-01', '2025-03-15'),  # 15 days
        'expected_working_days': 11,
        'expected_weekoff_days': 4,  # 2 Saturdays + 2 Sundays
    },
    
    'with_public_holiday': {
        'description': 'Month with public holiday',
        'calendar_days': ['0', '1', '2', '3', '4'],  # Mon-Fri
        'hours_per_day': 8.0,
        'period': ('2025-01-01', '2025-01-31'),  # 31 days
        'public_holidays': 1,  # New Year's Day
        'expected_working_days': 22,  # 23 - 1 holiday
        'expected_weekoff_days': 8,
    },
}


def test_weekoff_calculation(env, payslip_id):
    """
    Test week-off calculation for a specific payslip
    
    Args:
        env: Odoo environment
        payslip_id: ID of payslip to test
    
    Returns:
        dict with test results
    """
    payslip = env['hr.payslip'].browse(payslip_id)
    
    if not payslip.exists():
        return {'error': 'Payslip not found'}
    
    print(f"\n{'='*60}")
    print(f"Testing Payslip: {payslip.name}")
    print(f"Employee: {payslip.employee_id.name}")
    print(f"Period: {payslip.date_from} to {payslip.date_to}")
    print(f"{'='*60}\n")
    
    # Get summary
    summary = payslip._get_weekoff_summary()
    
    print("CALCULATION BREAKDOWN:")
    print(f"  Calendar: {summary.get('calendar_name', 'N/A')}")
    print(f"  Working Weekdays: {', '.join(summary.get('working_weekdays', []))}")
    print(f"  Total Calendar Days: {summary.get('total_calendar_days', 0)}")
    print(f"  Working Days: {summary.get('working_days', 0)}")
    print(f"  Public Holidays: {summary.get('public_holidays', 0)}")
    print(f"  Week-Off Days: {summary.get('weekoff_days', 0)}")
    
    # Get actual worked days line
    weekoff_line = payslip._compute_weekoff_days()
    
    if weekoff_line:
        print(f"\nWORKED DAYS LINE:")
        print(f"  Number of Days: {weekoff_line.get('number_of_days', 0)}")
        print(f"  Number of Hours: {weekoff_line.get('number_of_hours', 0)}")
    else:
        print("\n⚠️  No week-off line generated!")
    
    # Verify in worked_days_line_ids
    payslip._compute_worked_days_line_ids()
    weekoff_lines = payslip.worked_days_line_ids.filtered(
        lambda l: l.work_entry_type_id.code == 'WEEKOFF'
    )
    
    if weekoff_lines:
        print(f"\n✓ Week-off line found in payslip!")
        print(f"  Days: {weekoff_lines[0].number_of_days}")
        print(f"  Hours: {weekoff_lines[0].number_of_hours}")
    else:
        print(f"\n✗ Week-off line NOT found in worked_days_line_ids")
    
    print(f"\n{'='*60}\n")
    
    return {
        'summary': summary,
        'weekoff_line': weekoff_line,
        'in_worked_days': bool(weekoff_lines),
    }


def validate_calendar_setup(env, employee_id):
    """
    Validate that employee's calendar is properly configured for week-off calculation
    
    Args:
        env: Odoo environment
        employee_id: ID of employee
    
    Returns:
        dict with validation results
    """
    employee = env['hr.employee'].browse(employee_id)
    
    if not employee.exists():
        return {'error': 'Employee not found'}
    
    print(f"\n{'='*60}")
    print(f"Validating Calendar Setup for: {employee.name}")
    print(f"{'='*60}\n")
    
    # Check contract
    contract = employee.contract_id
    if not contract:
        print("✗ No active contract found!")
        return {'valid': False, 'reason': 'No contract'}
    
    print(f"✓ Active Contract: {contract.name}")
    
    # Check calendar
    calendar = contract.resource_calendar_id
    if not calendar:
        print("✗ No resource calendar assigned to contract!")
        return {'valid': False, 'reason': 'No calendar'}
    
    print(f"✓ Resource Calendar: {calendar.name}")
    print(f"  Timezone: {calendar.tz or 'UTC'}")
    print(f"  Hours per Day: {calendar.hours_per_day}")
    print(f"  Hours per Week: {calendar.hours_per_week}")
    
    # Check attendance records
    if not calendar.attendance_ids:
        print("✗ No attendance records in calendar!")
        return {'valid': False, 'reason': 'No attendance records'}
    
    print(f"✓ Attendance Records: {len(calendar.attendance_ids)} lines")
    
    # Show working days
    weekdays_map = {
        '0': 'Monday',
        '1': 'Tuesday',
        '2': 'Wednesday',
        '3': 'Thursday',
        '4': 'Friday',
        '5': 'Saturday',
        '6': 'Sunday',
    }
    
    working_days = set()
    for att in calendar.attendance_ids:
        day = weekdays_map.get(att.dayofweek, f"Day {att.dayofweek}")
        working_days.add(day)
        print(f"    {day}: {att.hour_from:05.2f} - {att.hour_to:05.2f} ({att.name or 'Unnamed'})")
    
    weekoff_days = set(weekdays_map.values()) - working_days
    print(f"\n  Week-Off Days: {', '.join(sorted(weekoff_days)) if weekoff_days else 'None (7-day schedule)'}")
    
    # Check public holidays
    holidays = env['resource.calendar.leaves'].search([
        ('calendar_id', '=', calendar.id),
        ('resource_id', '=', False),
    ], limit=10)
    
    if holidays:
        print(f"\n✓ Public Holidays Configured: {len(holidays)} found (showing up to 10)")
        for holiday in holidays[:10]:
            print(f"    {holiday.name}: {holiday.date_from.date()} to {holiday.date_to.date()}")
    else:
        print(f"\nℹ  No public holidays configured (optional)")
    
    print(f"\n{'='*60}")
    print("✓ CALENDAR SETUP IS VALID FOR WEEK-OFF CALCULATION")
    print(f"{'='*60}\n")
    
    return {
        'valid': True,
        'calendar': calendar.name,
        'working_days': len(working_days),
        'weekoff_days': len(weekoff_days),
        'public_holidays': len(holidays),
    }


# Example usage commands for Odoo shell:
"""
# Test a specific payslip
test_weekoff_calculation(env, 123)  # Replace 123 with actual payslip ID

# Validate employee calendar
validate_calendar_setup(env, 456)  # Replace 456 with actual employee ID

# Create and test a new payslip
employee = env['hr.employee'].search([('name', '=', 'John Doe')], limit=1)
if employee and employee.contract_id:
    payslip = env['hr.payslip'].create({
        'employee_id': employee.id,
        'contract_id': employee.contract_id.id,
        'struct_id': employee.contract_id.structure_type_id.default_struct_id.id,
        'date_from': '2025-01-01',
        'date_to': '2025-01-31',
    })
    payslip._compute_worked_days_line_ids()
    test_weekoff_calculation(env, payslip.id)
"""
