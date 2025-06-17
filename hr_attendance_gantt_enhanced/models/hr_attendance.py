from odoo import models, api, fields
from odoo.addons.resource.models.utils import Intervals
from pytz import UTC

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    def _gantt_unavailability(self, field, res_ids, start, stop, scale):
        result = super()._gantt_unavailability(field, res_ids, start, stop, scale)
        if field != "employee_id":
            return result

        employees = self.env['hr.employee'].browse(res_ids)
        leaves = self.env['hr.leave'].search([
            ('employee_id', 'in', res_ids),
            ('state', '=', 'validate'),
            ('date_from', '<', stop),
            ('date_to', '>', start),
        ])

        leave_intervals_by_employee = {}
        for leave in leaves:
            employee_id = leave.employee_id.id
            leave_start = leave.date_from.astimezone(UTC)
            leave_stop = leave.date_to.astimezone(UTC)
            if employee_id not in leave_intervals_by_employee:
                leave_intervals_by_employee[employee_id] = []
            leave_intervals_by_employee[employee_id].append((leave_start, leave_stop))

        for employee_id in res_ids:
            if employee_id not in result:
                continue
            unavailabilities = result[employee_id]
            leave_intervals = leave_intervals_by_employee.get(employee_id, [])
            for unavail in unavailabilities:
                unavail_start = unavail['start']
                unavail_stop = unavail['stop']
                for leave_start, leave_stop in leave_intervals:
                    if max(unavail_start, leave_start) < min(unavail_stop, leave_stop):
                        unavail['reason'] = 'leave'
                        break
                else:
                    unavail['reason'] = 'non-working'

        return result