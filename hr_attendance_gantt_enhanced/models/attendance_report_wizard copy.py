# from odoo import models, fields, api

# class AttendanceReportWizard(models.TransientModel):
#     _name = 'attendance.report.wizard'

#     start_date = fields.Date(string='Start Date', required=True)
#     end_date = fields.Date(string='End Date', required=True)
#     employee_ids = fields.Many2many('hr.employee', string='Employees')

#     def action_generate_report(self):
#         self.ensure_one()
#         employees = self.employee_ids or self.env['hr.employee'].search([])
#         data = []
#         for employee in employees:
#             metrics = employee._get_attendance_metrics(self.start_date, self.end_date)
#             row = {
#                 'employee_code': employee.barcode or '',
#                 'full_name': employee.name or '',
#                 'employment_status': employee.contract_id.state if employee.contract_id else '',
#                 'company': employee.company_id.name or '',
#                 'business_unit': employee.company_id.city if employee.company_id else '',
#                 'department': employee.department_id.name if employee.department_id else '',
#                 'designation': employee.job_id.name if employee.job_id else '',
#                 # 'branch': employee.branch_id.name if employee.branch_id else '',
#                 # 'sub_branch': '',
#                 'card_no': employee.barcode or '',
#                 'father_name': '',
#                 'age': '',
#                 'gender': employee.gender if employee.gender else None,
#                 'date_of_joining': employee.first_contract_date or '',
#                 'expected_work_days': metrics.get('expected_work_days', 0),
#                 'present': metrics.get('present', 0),
#                 'weekoff': metrics.get('weekoff', 0),
#                 'holiday': metrics.get('holiday', 0),
#                 'cl': metrics.get('CL', 0),
#                 'co': metrics.get('CO', 0),
#                 'comp-off': metrics.get('Comp-off', 0),
#                 'el': metrics.get('EL', 0),
#                 'sl': metrics.get('SL', 0),
#                 'no_of_leaves_paid': metrics.get('no_of_leaves_paid', 0),
#                 'no_of_leaves_unpaid': metrics.get('no_of_leaves_unpaid', 0),
#                 'absent': metrics.get('absent', 0),
#                 'pay_days': metrics.get('pay_days', 0),
#                 'total': metrics.get('total', 0),
#                 'expected_working_hours': metrics.get('expected_working_hours', 0),
#                 'actual_working_hours': metrics.get('actual_working_hours', 0),
#                 'count_of_ar': 0,
#                 'count_of_od': 0,
#                 'count_of_short_leave': 0,
#                 'count_of_early_late': 0,
#             }
#             data.append(row)
#         return self.env.ref('hr_attendance_gantt_enhanced.attendance_report_xlsx').report_action(self, data={'data': data})