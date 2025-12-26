# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from pytz import timezone, UTC

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrAttendanceBulkWizard(models.TransientModel):
    _name = 'hr.attendance.bulk.wizard'
    _description = 'Bulk Attendance Entry Wizard'

    # Date Range Fields
    date_from = fields.Date(
        string='From Date',
        required=True,
        default=fields.Date.context_today,
        help="Start date for bulk attendance entry"
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        default=fields.Date.context_today,
        help="End date for bulk attendance entry"
    )

    # Time Fields (stored as float for easy computation)
    check_in_time = fields.Float(
        string='Check-In Time',
        required=True,
        default=9.0,
        help="Check-in time in 24-hour format (e.g., 9.0 for 9:00 AM, 13.5 for 1:30 PM)"
    )
    check_out_time = fields.Float(
        string='Check-Out Time',
        required=True,
        default=18.0,
        help="Check-out time in 24-hour format (e.g., 18.0 for 6:00 PM)"
    )

    # Employee Selection
    employee_ids = fields.Many2many(
        'hr.employee',
        'hr_attendance_bulk_wizard_employee_rel',
        'wizard_id',
        'employee_id',
        string='Employees',
        required=True,
        help="Select employees for bulk attendance entry"
    )

    # Options
    skip_non_working_days = fields.Boolean(
        string='Skip Non-Working Days',
        default=True,
        help="If checked, attendance will not be created for days that are not in the employee's working schedule (resource calendar)"
    )
    skip_existing = fields.Boolean(
        string='Skip Existing Attendance',
        default=True,
        help="If checked, will skip dates where attendance already exists for the employee"
    )
    overwrite_existing = fields.Boolean(
        string='Overwrite Existing Attendance',
        default=False,
        help="If checked, will delete and recreate attendance records for dates where attendance already exists"
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    # Preview Line
    preview_line_ids = fields.One2many(
        'hr.attendance.bulk.wizard.line',
        'wizard_id',
        string='Preview Lines',
        readonly=True
    )

    # Statistics
    total_records_to_create = fields.Integer(
        string='Total Records to Create',
        compute='_compute_statistics',
        store=False
    )
    total_days = fields.Integer(
        string='Total Days',
        compute='_compute_statistics',
        store=False
    )
    total_employees = fields.Integer(
        string='Total Employees',
        compute='_compute_statistics',
        store=False
    )

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to and wizard.date_from > wizard.date_to:
                raise ValidationError(_("'From Date' must be earlier than or equal to 'To Date'."))

    @api.constrains('check_in_time', 'check_out_time')
    def _check_times(self):
        for wizard in self:
            if wizard.check_in_time < 0 or wizard.check_in_time >= 24:
                raise ValidationError(_("Check-In Time must be between 0 and 24."))
            if wizard.check_out_time < 0 or wizard.check_out_time >= 24:
                raise ValidationError(_("Check-Out Time must be between 0 and 24."))
            if wizard.check_in_time >= wizard.check_out_time:
                raise ValidationError(_("Check-In Time must be earlier than Check-Out Time."))

    @api.constrains('skip_existing', 'overwrite_existing')
    def _check_existing_options(self):
        for wizard in self:
            if wizard.skip_existing and wizard.overwrite_existing:
                raise ValidationError(_("You cannot enable both 'Skip Existing' and 'Overwrite Existing' options."))

    @api.depends('date_from', 'date_to', 'employee_ids', 'skip_non_working_days')
    def _compute_statistics(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to and wizard.employee_ids:
                # Count total working days across all employees
                total_days_count = 0
                for employee in wizard.employee_ids:
                    working_days = wizard._get_employee_working_days(employee)
                    current_date = wizard.date_from
                    while current_date <= wizard.date_to:
                        if not wizard.skip_non_working_days or current_date.weekday() in working_days:
                            total_days_count += 1
                        current_date += timedelta(days=1)
                wizard.total_days = total_days_count // len(wizard.employee_ids) if wizard.employee_ids else 0
                wizard.total_records_to_create = total_days_count
            else:
                wizard.total_days = 0
                wizard.total_records_to_create = 0
            
            wizard.total_employees = len(wizard.employee_ids)

    def _get_employee_working_days(self, employee):
        """
        Get the working days (weekday numbers) from employee's resource calendar.
        Returns a set of integers (0=Monday, 1=Tuesday, ..., 6=Sunday).
        """
        # Get employee's resource calendar or company's default calendar
        calendar = employee.resource_calendar_id or employee.company_id.resource_calendar_id
        
        if not calendar:
            # Default to Monday-Friday if no calendar is set
            return {0, 1, 2, 3, 4}
        
        # Get unique working days from calendar attendance lines
        # dayofweek in resource.calendar.attendance is stored as string '0' to '6'
        working_days = set()
        for attendance in calendar.attendance_ids:
            working_days.add(int(attendance.dayofweek))
        
        return working_days if working_days else {0, 1, 2, 3, 4}

    def _get_working_dates_for_employee(self, employee):
        """Get list of working dates for a specific employee based on their resource calendar."""
        self.ensure_one()
        dates = []
        working_days = self._get_employee_working_days(employee)
        current_date = self.date_from
        while current_date <= self.date_to:
            # Check if the day is a working day for this employee
            if not self.skip_non_working_days or current_date.weekday() in working_days:
                dates.append(current_date)
            current_date += timedelta(days=1)
        return dates

    def _float_to_time(self, float_time):
        """Convert float time (e.g., 9.5) to hours and minutes (9, 30)."""
        hours = int(float_time)
        minutes = int((float_time - hours) * 60)
        return hours, minutes

    def _get_datetime_in_utc(self, date, float_time, employee):
        """Convert date and float time to UTC datetime based on employee's timezone."""
        hours, minutes = self._float_to_time(float_time)
        
        # Get employee's timezone or use company timezone or UTC
        tz_name = employee.tz or employee.company_id.resource_calendar_id.tz or 'UTC'
        try:
            local_tz = timezone(tz_name)
        except Exception:
            local_tz = UTC
        
        # Create naive datetime in local timezone
        local_dt = datetime.combine(date, datetime.min.time().replace(hour=hours, minute=minutes))
        
        # Localize to employee's timezone and convert to UTC
        local_dt = local_tz.localize(local_dt)
        utc_dt = local_dt.astimezone(UTC).replace(tzinfo=None)
        
        return utc_dt

    def action_preview(self):
        """Generate preview of attendance records to be created."""
        self.ensure_one()
        
        if not self.employee_ids:
            raise UserError(_("Please select at least one employee."))
        
        # Clear existing preview lines
        self.preview_line_ids.unlink()
        
        preview_lines = []
        
        for employee in self.employee_ids:
            # Get working dates specific to this employee's calendar
            working_dates = self._get_working_dates_for_employee(employee)
            for date in working_dates:
                check_in_utc = self._get_datetime_in_utc(date, self.check_in_time, employee)
                check_out_utc = self._get_datetime_in_utc(date, self.check_out_time, employee)
                
                # Check for existing attendance
                existing_attendance = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(date, datetime.min.time())),
                    ('check_in', '<', datetime.combine(date + timedelta(days=1), datetime.min.time())),
                ], limit=1)
                
                status = 'new'
                if existing_attendance:
                    if self.skip_existing:
                        status = 'skip'
                    elif self.overwrite_existing:
                        status = 'overwrite'
                    else:
                        status = 'conflict'
                
                preview_lines.append({
                    'wizard_id': self.id,
                    'employee_id': employee.id,
                    'date': date,
                    'check_in': check_in_utc,
                    'check_out': check_out_utc,
                    'status': status,
                    'existing_attendance_id': existing_attendance.id if existing_attendance else False,
                })
        
        self.env['hr.attendance.bulk.wizard.line'].create(preview_lines)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance.bulk.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_create_attendance(self):
        """Create attendance records based on wizard configuration."""
        self.ensure_one()
        
        if not self.employee_ids:
            raise UserError(_("Please select at least one employee."))
        
        attendance_vals_list = []
        skipped_count = 0
        overwritten_count = 0
        conflict_count = 0
        no_working_days_employees = []
        
        for employee in self.employee_ids:
            # Get working dates specific to this employee's calendar
            working_dates = self._get_working_dates_for_employee(employee)
            
            if not working_dates:
                no_working_days_employees.append(employee.name)
                continue
            
            for date in working_dates:
                check_in_utc = self._get_datetime_in_utc(date, self.check_in_time, employee)
                check_out_utc = self._get_datetime_in_utc(date, self.check_out_time, employee)
                
                # Check for existing attendance
                existing_attendance = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(date, datetime.min.time())),
                    ('check_in', '<', datetime.combine(date + timedelta(days=1), datetime.min.time())),
                ])
                
                if existing_attendance:
                    if self.skip_existing:
                        skipped_count += 1
                        continue
                    elif self.overwrite_existing:
                        existing_attendance.unlink()
                        overwritten_count += 1
                    else:
                        conflict_count += 1
                        continue
                
                attendance_vals_list.append({
                    'employee_id': employee.id,
                    'check_in': check_in_utc,
                    'check_out': check_out_utc,
                })
        
        if conflict_count > 0 and not self.skip_existing and not self.overwrite_existing:
            raise UserError(_(
                "%(count)s attendance records already exist for the selected dates and employees.\n"
                "Please enable 'Skip Existing' or 'Overwrite Existing' option to proceed.",
                count=conflict_count
            ))
        
        created_attendances = self.env['hr.attendance']
        if attendance_vals_list:
            created_attendances = self.env['hr.attendance'].create(attendance_vals_list)
        
        # Prepare message for user
        message_parts = []
        if created_attendances:
            message_parts.append(_("%(count)s attendance record(s) created successfully.", count=len(created_attendances)))
        if skipped_count:
            message_parts.append(_("%(count)s record(s) skipped (existing attendance).", count=skipped_count))
        if overwritten_count:
            message_parts.append(_("%(count)s record(s) overwritten.", count=overwritten_count))
        
        message = '\n'.join(message_parts) if message_parts else _("No records were created.")
        
        # Return action to view created attendances
        if created_attendances:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Created Attendances'),
                'res_model': 'hr.attendance',
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_attendances.ids)],
                'target': 'current',
            }
        else:
            # If no records created, just close the wizard
            return {'type': 'ir.actions.act_window_close'}

    def action_select_all_employees(self):
        """Select all active employees."""
        self.ensure_one()
        employees = self.env['hr.employee'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
        ])
        self.employee_ids = [(6, 0, employees.ids)]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance.bulk.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_clear_employees(self):
        """Clear all selected employees."""
        self.ensure_one()
        self.employee_ids = [(5, 0, 0)]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance.bulk.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }


class HrAttendanceBulkWizardLine(models.TransientModel):
    _name = 'hr.attendance.bulk.wizard.line'
    _description = 'Bulk Attendance Entry Wizard Line'

    wizard_id = fields.Many2one(
        'hr.attendance.bulk.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True
    )
    date = fields.Date(string='Date', required=True)
    check_in = fields.Datetime(string='Check-In')
    check_out = fields.Datetime(string='Check-Out')
    status = fields.Selection([
        ('new', 'New'),
        ('skip', 'Will be Skipped'),
        ('overwrite', 'Will be Overwritten'),
        ('conflict', 'Conflict - Existing'),
    ], string='Status', default='new')
    existing_attendance_id = fields.Many2one(
        'hr.attendance',
        string='Existing Attendance'
    )
