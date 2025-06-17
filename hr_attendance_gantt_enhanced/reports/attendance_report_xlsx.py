from odoo import models

class AttendanceReportXlsx(models.AbstractModel):
    _name = 'report.hr_attendance_gantt_enhanced.attendance_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    # def generate_xlsx_report(self, workbook, data, wizard):
    #     sheet = workbook.add_worksheet('Attendance Report')
    #     bold = workbook.add_format({'bold': True})
    #     headers = [
    #         'Employee Code', 'Full Name', 'Employment Status', 'Company', 'Business Unit',
    #         'Department', 'Designation', 'Branch', 'Sub Branch', 'Card No', 'Father Name',
    #         'Age', 'Gender', 'Date of Joining', 'Expected Work Days', 'Present', 'Weekoff',
    #         'Holiday', 'CL', 'CO', 'Comp-off', 'EL', 'SL', 'No of Leaves (Paid)',
    #         'No of Leaves (Unpaid)', 'Absent', 'Pay Days', 'Total', 'Expected Working Hours',
    #         'Actual Working Hours', 'Count of AR', 'Count of OD', 'Count of Short Leave',
    #         'Count of Early Late'
    #     ]
    #     for col, header in enumerate(headers):
    #         sheet.write(0, col, header, bold)
    #     for row, record in enumerate(data['data'], start=1):
    #         for col, field in enumerate(headers):
    #             key = field.lower().replace(' ', '_')
    #             value = record.get(key, '')
    #             sheet.write(row, col, value)
    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet('Attendance Report')
        bold = workbook.add_format({'bold': True})
        headers = [
            'Employee Code', 'Full Name', 'Employment Status', 'Company', 'Business Unit',
            'Department', 'Designation', 'Branch', 'Sub Branch', 'Card No', 'Father Name',
            'Age', 'Gender', 'Date of Joining', 'Expected Work Days', 'Present', 'Weekoff',
            'Holiday', 'CL', 'CO', 'Comp-off', 'EL', 'SL', 'No of Leaves (Paid)',
            'No of Leaves (Unpaid)', 'Absent', 'Pay Days', 'Total', 'Expected Working Hours',
            'Actual Working Hours', 'Count of AR', 'Count of OD', 'Count of Short Leave',
            'Count of Early Late', 'Last Attendance Worked Hours', 'Attendance State',
            'Total Overtime', 'Remaining Leaves', 'Leaves Count', 'Hours Previously Today',
            'Hours Last Month', 'Allocation Count', 'Allocations Count', 'Contracts Count',
            'Resource Calendar', 'Expense Manager', 'Leave Manager'
        ]
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)
        for row, record in enumerate(data['data'], start=1):
            for col, field in enumerate(headers):
                key = field.lower().replace(' ', '_')
                value = record.get(key, '')
                sheet.write(row, col, value)