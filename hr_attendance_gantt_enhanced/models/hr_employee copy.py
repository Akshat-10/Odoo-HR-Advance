# from odoo import models, fields, api
# from dateutil.relativedelta import relativedelta
# from odoo.addons.resource.models.utils import Intervals
# from pytz import timezone, UTC
# import datetime

# class HrEmployee(models.Model):
#     _inherit = 'hr.employee'

#     def _get_attendance_metrics(self, start_date, end_date):
#         self.ensure_one()
#         metrics = {}
#         start = fields.Datetime.from_string(start_date).replace(hour=0, minute=0, second=0)
#         stop = fields.Datetime.from_string(end_date).replace(hour=23, minute=59, second=59)

#         calendar = self.resource_calendar_id or self.company_id.resource_calendar_id
#         tz = timezone(calendar.tz) if calendar.tz else UTC
#         start = tz.localize(start)
#         stop = tz.localize(stop)

#         expected_days, expected_hours = self._get_expected_work_days_hours(calendar, start, stop)
#         metrics['expected_work_days'] = expected_days
#         metrics['expected_working_hours'] = expected_hours

#         attendances = self.env['hr.attendance'].search([
#             ('employee_id', '=', self.id),
#             ('check_in', '>=', start),
#             ('check_out', '<=', stop),
#         ])
#         present_days = len(set(att.check_in.date() for att in attendances))
#         actual_hours = sum(att.worked_hours for att in attendances)
#         metrics['present'] = present_days
#         metrics['actual_working_hours'] = actual_hours

#         leaves = self.env['hr.leave'].search([
#             ('employee_id', '=', self.id),
#             ('state', '=', 'validate'),
#             ('date_from', '<', stop),
#             ('date_to', '>', start),
#         ])
#         leave_days_by_type = {}
#         paid_leave_days = 0
#         unpaid_leave_days = 0
#         for leave in leaves:
#             leave_type = leave.holiday_status_id.name
#             days = leave.number_of_days
#             leave_days_by_type[leave_type] = leave_days_by_type.get(leave_type, 0) + days
#             if leave.holiday_status_id.unpaid:
#                 unpaid_leave_days += days
#             else:
#                 paid_leave_days += days
#         metrics.update(leave_days_by_type)
#         metrics['no_of_leaves_paid'] = paid_leave_days
#         metrics['no_of_leaves_unpaid'] = unpaid_leave_days

#         weekoff_days = self._get_weekoff_days(calendar, start, stop)
#         holiday_days = self._get_holiday_days(start, stop)
#         metrics['weekoff'] = weekoff_days
#         metrics['holiday'] = holiday_days

#         leave_days = sum(leave_days_by_type.values())
#         absent_days = expected_days - present_days - leave_days
#         metrics['absent'] = max(absent_days, 0)
#         metrics['pay_days'] = present_days + paid_leave_days
#         metrics['total'] = (stop - start).days + 1

#         return metrics

#     def _get_expected_work_days_hours(self, calendar, start, stop):
#         if not self.resource_id:
#             return 0, 0
#         attendance_intervals = calendar._attendance_intervals_batch(start, stop, self.resource_id)
#         days = set()
#         total_hours = 0
#         for interval in attendance_intervals[self.resource_id.id]:
#             days.add(interval[0].date())
#             total_hours += (interval[1] - interval[0]).total_seconds() / 3600
#         return len(days), total_hours

#     def _get_weekoff_days(self, calendar, start, stop):
#         if not self.resource_id:
#             return 0
#         work_intervals = calendar._work_intervals_batch(start, stop, self.resource_id)
#         full_interval = Intervals([(start, stop, self.env['resource.calendar'])])
#         non_work_intervals = full_interval - work_intervals[self.resource_id.id]
#         weekoff_days = set(interval[0].date() for interval in non_work_intervals)
#         return len(weekoff_days)

#     # def _get_holiday_days(self, start, stop):
#     #     # Get the calendar's timezone, defaulting to UTC
#     #     tz = timezone(self.resource_calendar_id.tz) if self.resource_calendar_id.tz else UTC
#     #     holidays = self.env['resource.calendar.leaves'].search([
#     #         ('resource_id', '=', False),  # Global holidays
#     #         ('date_from', '<', stop),
#     #         ('date_to', '>', start),
#     #     ])
#     #     holiday_days = set()
#     #     for holiday in holidays:
#     #         # Convert holiday datetimes to the calendar's timezone
#     #         holiday_start_local = holiday.date_from.astimezone(tz)
#     #         holiday_stop_local = holiday.date_to.astimezone(tz)
#     #         # Compare with start and stop, which are already in tz
#     #         effective_start = max(holiday_start_local, start)
#     #         effective_stop = min(holiday_stop_local, stop)
#     #         # Calculate days in the local timezone
#     #         current = effective_start.date()
#     #         end_date = effective_stop.date()
#     #         while current <= end_date:
#     #             holiday_days.add(current)
#     #             current += datetime.timedelta(days=1)
#     #     return len(holiday_days)
    
#     def _get_holiday_days(self, start, stop):
#         tz = timezone(self.resource_calendar_id.tz) if self.resource_calendar_id.tz else UTC
#         holidays = self.env['resource.calendar.leaves'].search([
#             ('resource_id', '=', False),
#             ('date_from', '<', stop),
#             ('date_to', '>', start),
#         ])
#         holiday_days = set()
#         for holiday in holidays:
#             holiday_start_local = holiday.date_from.astimezone(tz)
#             holiday_stop_local = holiday.date_to.astimezone(tz)
#             effective_start = max(holiday_start_local, start)
#             effective_stop = min(holiday_stop_local, stop)
#             current = effective_start.date()
#             end_date = effective_stop.date()
#             while current <= end_date:
#                 holiday_days.add(current)
#                 current += datetime.timedelta(days=1)
#         return len(holiday_days)