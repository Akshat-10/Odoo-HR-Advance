from odoo import models
import datetime

class AttendanceReportXlsx(models.AbstractModel):
    _name = 'report.hr_attendance_gantt_enhanced.attendance_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet('Attendance Report')
        bold = workbook.add_format({'bold': True})
        
        # Define header sections
        static_headers = [
            'Employee Code', 'Full Name', 'Employment Status', 'Company', 'Business Unit',
            'Department', 'Designation', 'Branch', 'Sub Branch', 'Card No', 'Father Name',
            'Age', 'Gender', 'Date of Joining'
        ]
        date_headers = [str(wizard.start_date + datetime.timedelta(days=x)) for x in range((wizard.end_date - wizard.start_date).days + 1)]
        summary_headers = [
            'Days P|P', 'Days P|A', 'Days A|P', 'Days A|A',
            'Expected Work Days', 'Present', 'Weekoff', 'Holiday', 'CL', 'CO', 'Comp-off', 'EL', 'SL',
            'No of Leaves (Paid)', 'No of Leaves (Unpaid)', 'Absent', 'Pay Days', 'Total',
            'Expected Working Hours', 'Actual Working Hours', 'Count of AR', 'Count of OD',
            'Count of Short Leave', 'Count of Early Late', 'Last Attendance Worked Hours',
            'Attendance State', 'Total Overtime', 'Remaining Leaves', 'Leaves Count',
            'Hours Previously Today', 'Hours Last Month', 'Allocation Count', 'Allocations Count',
            'Contracts Count', 'Resource Calendar', 'Expense Manager', 'Leave Manager'
        ]
        headers = static_headers + date_headers + summary_headers

        # Write headers
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)
        
        # Write data rows
        for row, record in enumerate(data['data'], start=1):
            for col, field in enumerate(headers):
                key = field.lower().replace(' ', '_') if field not in date_headers else field
                value = record.get(key, '')
                sheet.write(row, col, value)