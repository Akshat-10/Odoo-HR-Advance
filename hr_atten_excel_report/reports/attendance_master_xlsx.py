from odoo import models
import datetime


class AttendancemasterXlsx(models.AbstractModel):
    _name = 'report.hr_atten_excel_report.attendance_master_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Attendance Master XLSX Report'

    def _col_to_letter(self, col_idx):
        """Convert column index to Excel column letter (0=A, 1=B, etc.)"""
        result = ""
        while col_idx >= 0:
            result = chr(col_idx % 26 + ord('A')) + result
            col_idx = col_idx // 26 - 1
        return result

    def _create_formats(self, workbook):
        """Create all the formats needed for the report."""
        formats = {}
        
        formats['title'] = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': 'black',
        })

        formats['subtitle'] = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
        })

        formats['header'] = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D9D9D9',
            'border': 1,
            'text_wrap': True,
        })

        formats['day_header'] = workbook.add_format({
            'bold': True,
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#E2EFDA',
            'border': 1,
        })

        formats['date_num'] = workbook.add_format({
            'bold': True,
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#E2EFDA',
            'border': 1,
        })

        formats['data'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
        })

        formats['text_left'] = workbook.add_format({
            'font_size': 9,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
        })

        # Present (P) format - Green background
        formats['present'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#C6EFCE',
            'font_color': '#006100',
            'bold': True,
        })

        # Weekoff (W) format - Yellow background
        formats['weekoff'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#FFEB9C',
            'font_color': '#9C5700',
            'bold': True,
        })

        # Absent (A) format - Red background
        formats['absent'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#FFC7CE',
            'font_color': '#9C0006',
            'bold': True,
        })

        # Holiday (H) format - Light blue background
        formats['holiday'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#BDD7EE',
            'font_color': '#1F4E79',
            'bold': True,
        })

        # Leave (L) format - Purple background
        formats['leave'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#E4DFEC',
            'font_color': '#7030A0',
            'bold': True,
        })

        # Half Day (HD) format - Light Orange background
        formats['half_day'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#FCE4D6',
            'font_color': '#C65911',
            'bold': True,
        })

        # Casual Leave (CL) format - Light Cyan
        formats['cl'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#E0FFFF',
            'font_color': '#008B8B',
            'bold': True,
        })

        # Earned Leave (EL) format - Light Green
        formats['el'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#90EE90',
            'font_color': '#006400',
            'bold': True,
        })

        # Sick Leave (SL) format - Light Pink
        formats['sl'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#FFB6C1',
            'font_color': '#8B0000',
            'bold': True,
        })

        # Unpaid Leave (UL) format - Gray
        formats['ul'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#D3D3D3',
            'font_color': '#404040',
            'bold': True,
        })

        # Management Leave (ML) format - Light Gold
        formats['ml'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#FFD700',
            'font_color': '#8B4513',
            'bold': True,
        })

        # Summary header format
        formats['summary_header'] = workbook.add_format({
            'bold': True,
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#FCE4D6',
            'border': 1,
            'text_wrap': True,
        })

        # Summary data format
        formats['summary'] = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#FFF2CC',
        })

        return formats

    def _write_sheet_header(self, sheet, formats, total_cols, company_name, month_name, from_date, to_date):
        """Write common header rows for both sheets."""
        # Row 1: Title - "Attendance Master"
        sheet.merge_range(0, 0, 0, total_cols - 1, 'Attendance Master', formats['title'])
        # Row 2: Company Name
        sheet.merge_range(1, 0, 1, total_cols - 1, company_name, formats['title'])
        # Row 3: Month Name
        sheet.merge_range(2, 0, 2, total_cols - 1, month_name, formats['subtitle'])
        # Row 4: Date Range
        date_info = f"From Date : {from_date} To : {to_date}"
        sheet.merge_range(3, 0, 3, total_cols - 1, date_info, formats['subtitle'])

    def _generate_summary_sheet(self, workbook, sheet, data, formats):
        """Generate the first sheet with basic P/W/A/H/L status."""
        company_name = data.get('company_name', '')
        from_date = data.get('from_date', '')
        to_date = data.get('to_date', '')
        month_name = data.get('month_name', '')
        date_headers = data.get('date_headers', [])
        employees = data.get('employees', [])

        # Calculate column positions
        static_cols = 7  # S.No, Name, Code, Dept, Position, DOJ, W/O
        num_days = len(date_headers)
        summary_cols = 6  # Present, Weekoff, Absent, Holiday, Leave, Total
        total_cols = static_cols + num_days + summary_cols

        # Set column widths
        sheet.set_column(0, 0, 5)   # S.No
        sheet.set_column(1, 1, 30)  # Employee Name
        sheet.set_column(2, 2, 12)  # Employee Code
        sheet.set_column(3, 3, 18)  # Department
        sheet.set_column(4, 4, 18)  # Job Position
        sheet.set_column(5, 5, 12)  # Date of Joining
        sheet.set_column(6, 6, 6)   # W/O
        
        # Day columns
        for i in range(num_days):
            sheet.set_column(static_cols + i, static_cols + i, 5)
        
        # Summary columns
        summary_start = static_cols + num_days
        sheet.set_column(summary_start, summary_start + summary_cols - 1, 10)

        # Write header
        self._write_sheet_header(sheet, formats, total_cols, company_name, month_name, from_date, to_date)

        # Row 6: Date numbers row
        row = 5
        for col in range(static_cols):
            sheet.write(row, col, '', formats['header'])
        for i, dh in enumerate(date_headers):
            sheet.write(row, static_cols + i, dh['day_num'], formats['date_num'])
        for i in range(summary_cols):
            sheet.write(row, summary_start + i, '', formats['summary_header'])

        # Row 7: Main headers
        row = 6
        headers = ['Sr.\nNo.', 'Employee Name', 'Employee\nCode', 'Department', 
                   'Job Position', 'Date of\nJoining', 'W/O']
        
        for col, h in enumerate(headers):
            sheet.write(row, col, h, formats['header'])

        for i, dh in enumerate(date_headers):
            sheet.write(row, static_cols + i, dh['day_name'], formats['day_header'])

        summary_headers = ['Present\nDays', 'Weekoff\nDays', 'Absent\nDays', 'Holidays', 'Leave\nDays', 'Total']
        for i, h in enumerate(summary_headers):
            sheet.write(row, summary_start + i, h, formats['summary_header'])

        sheet.set_row(5, 18)
        sheet.set_row(6, 30)

        # Write employee data
        data_start_row = 7
        for emp_idx, emp in enumerate(employees):
            row = data_start_row + emp_idx
            
            sheet.write(row, 0, emp['sno'], formats['data'])
            sheet.write(row, 1, emp['name'], formats['text_left'])
            sheet.write(row, 2, emp['employee_code'], formats['data'])
            sheet.write(row, 3, emp['department'], formats['text_left'])
            sheet.write(row, 4, emp['job_position'], formats['text_left'])
            sheet.write(row, 5, emp['date_of_joining'], formats['data'])
            sheet.write(row, 6, emp['weekoff_day'], formats['data'])

            for i, dh in enumerate(date_headers):
                col = static_cols + i
                status = emp['daily_status'].get(dh['date'], '')
                sheet.write(row, col, status, formats['data'])

            # Excel formulas for summary - using direct COUNTIF from date range
            first_col_letter = self._col_to_letter(static_cols)
            last_col_letter = self._col_to_letter(static_cols + num_days - 1)
            excel_row = row + 1
            date_range = f'{first_col_letter}{excel_row}:{last_col_letter}{excel_row}'

            # Present Days: COUNTIF for "P"
            present_formula = f'=COUNTIF({date_range},"P")'
            sheet.write_formula(row, summary_start, present_formula, formats['summary'])

            # Weekoff Days: COUNTIF for "W"
            weekoff_formula = f'=COUNTIF({date_range},"W")'
            sheet.write_formula(row, summary_start + 1, weekoff_formula, formats['summary'])

            # Absent Days: COUNTIF for "A"
            absent_formula = f'=COUNTIF({date_range},"A")'
            sheet.write_formula(row, summary_start + 2, absent_formula, formats['summary'])

            # Holidays: COUNTIF for "H"
            holiday_formula = f'=COUNTIF({date_range},"H")'
            sheet.write_formula(row, summary_start + 3, holiday_formula, formats['summary'])

            # Leave Days: COUNTIF for "L"
            leave_formula = f'=COUNTIF({date_range},"L")'
            sheet.write_formula(row, summary_start + 4, leave_formula, formats['summary'])

            # Total: Direct COUNTIF for all status types (P + W + A + H + L)
            total_formula = f'=COUNTIF({date_range},"P")+COUNTIF({date_range},"W")+COUNTIF({date_range},"A")+COUNTIF({date_range},"H")+COUNTIF({date_range},"L")'
            sheet.write_formula(row, summary_start + 5, total_formula, formats['summary'])

        # Add legend
        legend_row = data_start_row + len(employees) + 2
        sheet.write(legend_row, 0, 'Legend:', formats['header'])
        sheet.write(legend_row, 1, 'P = Present', formats['present'])
        sheet.write(legend_row, 2, 'W = Weekoff', formats['weekoff'])
        sheet.write(legend_row, 3, 'A = Absent', formats['absent'])
        sheet.write(legend_row, 4, 'H = Holiday', formats['holiday'])
        sheet.write(legend_row, 5, 'L = Leave', formats['leave'])

        # Apply conditional formatting
        first_day_col_letter = self._col_to_letter(static_cols)
        last_day_col_letter = self._col_to_letter(static_cols + num_days - 1)
        first_data_row = data_start_row + 1
        last_data_row = data_start_row + len(employees)
        cond_range = f'{first_day_col_letter}{first_data_row}:{last_day_col_letter}{last_data_row}'

        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"P"', 'format': formats['present']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"W"', 'format': formats['weekoff']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"A"', 'format': formats['absent']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"H"', 'format': formats['holiday']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"L"', 'format': formats['leave']})

    def _generate_detailed_sheet(self, workbook, sheet, data, formats):
        """Generate the second sheet with detailed leave type breakdown."""
        company_name = data.get('company_name', '')
        from_date = data.get('from_date', '')
        to_date = data.get('to_date', '')
        month_name = data.get('month_name', '')
        date_headers = data.get('date_headers', [])
        employees = data.get('employees', [])

        # Calculate column positions
        static_cols = 7  # S.No, Name, Code, Dept, Position, DOJ, W/O
        num_days = len(date_headers)
        # Extended summary columns: Present, Half Day Present, Weekoff, Absent, Holiday, CL, EL, SL, UL (Unpaid), ML (Management), Total Leave, Total
        summary_cols = 12
        total_cols = static_cols + num_days + summary_cols

        # Set column widths
        sheet.set_column(0, 0, 5)   # S.No
        sheet.set_column(1, 1, 30)  # Employee Name
        sheet.set_column(2, 2, 12)  # Employee Code
        sheet.set_column(3, 3, 18)  # Department
        sheet.set_column(4, 4, 18)  # Job Position
        sheet.set_column(5, 5, 12)  # Date of Joining
        sheet.set_column(6, 6, 6)   # W/O
        
        # Day columns
        for i in range(num_days):
            sheet.set_column(static_cols + i, static_cols + i, 5)
        
        # Summary columns
        summary_start = static_cols + num_days
        sheet.set_column(summary_start, summary_start + summary_cols - 1, 8)

        # Write header
        self._write_sheet_header(sheet, formats, total_cols, company_name, month_name, from_date, to_date)

        # Row 6: Date numbers row
        row = 5
        for col in range(static_cols):
            sheet.write(row, col, '', formats['header'])
        for i, dh in enumerate(date_headers):
            sheet.write(row, static_cols + i, dh['day_num'], formats['date_num'])
        for i in range(summary_cols):
            sheet.write(row, summary_start + i, '', formats['summary_header'])

        # Row 7: Main headers with detailed leave types
        row = 6
        headers = ['Sr.\nNo.', 'Employee Name', 'Employee\nCode', 'Department', 
                   'Job Position', 'Date of\nJoining', 'W/O']
        
        for col, h in enumerate(headers):
            sheet.write(row, col, h, formats['header'])

        for i, dh in enumerate(date_headers):
            sheet.write(row, static_cols + i, dh['day_name'], formats['day_header'])

        # Extended summary headers
        summary_headers = [
            'Present\n(P)', 'Half Day\n(HD)', 'Weekoff\n(W)', 'Absent\n(A)', 
            'Holiday\n(H)', 'CL', 'EL', 'SL', 'Unpaid\n(UL)', 'Mgmt\n(ML)', 
            'Total\nLeave', 'Total\nDays'
        ]
        for i, h in enumerate(summary_headers):
            sheet.write(row, summary_start + i, h, formats['summary_header'])

        sheet.set_row(5, 18)
        sheet.set_row(6, 35)

        # Write employee data with detailed status
        data_start_row = 7
        for emp_idx, emp in enumerate(employees):
            row = data_start_row + emp_idx
            
            sheet.write(row, 0, emp['sno'], formats['data'])
            sheet.write(row, 1, emp['name'], formats['text_left'])
            sheet.write(row, 2, emp['employee_code'], formats['data'])
            sheet.write(row, 3, emp['department'], formats['text_left'])
            sheet.write(row, 4, emp['job_position'], formats['text_left'])
            sheet.write(row, 5, emp['date_of_joining'], formats['data'])
            sheet.write(row, 6, emp['weekoff_day'], formats['data'])

            # Write detailed status (with leave type codes)
            daily_status_detailed = emp.get('daily_status_detailed', {})
            for i, dh in enumerate(date_headers):
                col = static_cols + i
                detailed = daily_status_detailed.get(dh['date'], {})
                status = detailed.get('status', '') if detailed else ''
                sheet.write(row, col, status, formats['data'])

            # Excel formulas for detailed summary
            first_col_letter = self._col_to_letter(static_cols)
            last_col_letter = self._col_to_letter(static_cols + num_days - 1)
            excel_row = row + 1
            date_range = f'{first_col_letter}{excel_row}:{last_col_letter}{excel_row}'

            col_idx = summary_start

            # Present Days (P) - counts cells containing exactly "P"
            present_formula = f'=COUNTIF({date_range},"P")'
            sheet.write_formula(row, col_idx, present_formula, formats['summary'])
            col_idx += 1

            # Half Day Present (HD) - counts cells containing exactly "HD"
            half_day_formula = f'=COUNTIF({date_range},"HD")'
            sheet.write_formula(row, col_idx, half_day_formula, formats['summary'])
            col_idx += 1

            # Weekoff Days (W) - counts cells containing exactly "W"
            weekoff_formula = f'=COUNTIF({date_range},"W")'
            sheet.write_formula(row, col_idx, weekoff_formula, formats['summary'])
            col_idx += 1

            # Absent Days (A) - counts cells containing exactly "A"
            absent_formula = f'=COUNTIF({date_range},"A")'
            sheet.write_formula(row, col_idx, absent_formula, formats['summary'])
            col_idx += 1

            # Holidays (H) - counts cells containing exactly "H"
            holiday_formula = f'=COUNTIF({date_range},"H")'
            sheet.write_formula(row, col_idx, holiday_formula, formats['summary'])
            col_idx += 1

            # Casual Leave (CL) - counts cells containing exactly "CL"
            cl_formula = f'=COUNTIF({date_range},"CL")'
            sheet.write_formula(row, col_idx, cl_formula, formats['summary'])
            col_idx += 1

            # Earned Leave (EL) - counts cells containing exactly "EL"
            el_formula = f'=COUNTIF({date_range},"EL")'
            sheet.write_formula(row, col_idx, el_formula, formats['summary'])
            col_idx += 1

            # Sick Leave (SL) - counts cells containing exactly "SL"
            sl_formula = f'=COUNTIF({date_range},"SL")'
            sheet.write_formula(row, col_idx, sl_formula, formats['summary'])
            col_idx += 1

            # Unpaid Leave (UL) - counts cells containing exactly "UL"
            ul_formula = f'=COUNTIF({date_range},"UL")'
            sheet.write_formula(row, col_idx, ul_formula, formats['summary'])
            col_idx += 1

            # Management Leave (ML) - counts cells containing exactly "ML"
            ml_formula = f'=COUNTIF({date_range},"ML")'
            sheet.write_formula(row, col_idx, ml_formula, formats['summary'])
            col_idx += 1

            # Total Leave - Direct COUNTIF from date range for all leave types (CL + EL + SL + UL + ML + HD)
            # This counts directly from the date cells so it updates when user edits
            total_leave_formula = f'=COUNTIF({date_range},"CL")+COUNTIF({date_range},"EL")+COUNTIF({date_range},"SL")+COUNTIF({date_range},"UL")+COUNTIF({date_range},"ML")+COUNTIF({date_range},"HD")'
            sheet.write_formula(row, col_idx, total_leave_formula, formats['summary'])
            col_idx += 1

            # Total Days - Direct COUNTIF from date range for all status types
            # P + HD + W + A + H + CL + EL + SL + UL + ML
            total_formula = f'=COUNTIF({date_range},"P")+COUNTIF({date_range},"HD")+COUNTIF({date_range},"W")+COUNTIF({date_range},"A")+COUNTIF({date_range},"H")+COUNTIF({date_range},"CL")+COUNTIF({date_range},"EL")+COUNTIF({date_range},"SL")+COUNTIF({date_range},"UL")+COUNTIF({date_range},"ML")'
            sheet.write_formula(row, col_idx, total_formula, formats['summary'])

        # Add legend for detailed sheet
        legend_row = data_start_row + len(employees) + 2
        sheet.write(legend_row, 0, 'Legend:', formats['header'])
        sheet.write(legend_row, 1, 'P = Present', formats['present'])
        sheet.write(legend_row, 2, 'HD = Half Day', formats['half_day'])
        sheet.write(legend_row, 3, 'W = Weekoff', formats['weekoff'])
        sheet.write(legend_row, 4, 'A = Absent', formats['absent'])
        sheet.write(legend_row, 5, 'H = Holiday', formats['holiday'])
        
        legend_row2 = legend_row + 1
        sheet.write(legend_row2, 0, '', formats['header'])
        sheet.write(legend_row2, 1, 'CL = Casual Leave', formats['cl'])
        sheet.write(legend_row2, 2, 'EL = Earned Leave', formats['el'])
        sheet.write(legend_row2, 3, 'SL = Sick Leave', formats['sl'])
        sheet.write(legend_row2, 4, 'UL = Unpaid Leave', formats['ul'])
        sheet.write(legend_row2, 5, 'ML = Mgmt Leave', formats['ml'])

        # Apply conditional formatting for all status codes
        first_day_col_letter = self._col_to_letter(static_cols)
        last_day_col_letter = self._col_to_letter(static_cols + num_days - 1)
        first_data_row = data_start_row + 1
        last_data_row = data_start_row + len(employees)
        cond_range = f'{first_day_col_letter}{first_data_row}:{last_day_col_letter}{last_data_row}'

        # Basic status codes
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"P"', 'format': formats['present']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"W"', 'format': formats['weekoff']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"A"', 'format': formats['absent']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"H"', 'format': formats['holiday']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"L"', 'format': formats['leave']})
        
        # Detailed leave type codes
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"HD"', 'format': formats['half_day']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"CL"', 'format': formats['cl']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"EL"', 'format': formats['el']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"SL"', 'format': formats['sl']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"UL"', 'format': formats['ul']})
        sheet.conditional_format(cond_range, {'type': 'cell', 'criteria': '==', 'value': '"ML"', 'format': formats['ml']})

    def generate_xlsx_report(self, workbook, data, wizard):
        wizard = wizard.ensure_one()
        
        # Get report data
        if not data or not data.get('company_name'):
            data = wizard._prepare_report_data()

        month_name = data.get('month_name', '')
        
        # Create formats
        formats = self._create_formats(workbook)

        # Sheet 1: Summary Sheet (P/W/A/H/L)
        sheet1_name = f"{month_name[:25]} Summary" if month_name else 'Summary'
        sheet1 = workbook.add_worksheet(sheet1_name[:31])
        self._generate_summary_sheet(workbook, sheet1, data, formats)

        # Sheet 2: Detailed Leave Types Sheet
        sheet2_name = f"{month_name[:25]} Detailed" if month_name else 'Detailed'
        sheet2 = workbook.add_worksheet(sheet2_name[:31])
        self._generate_detailed_sheet(workbook, sheet2, data, formats)
