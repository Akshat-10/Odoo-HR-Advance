from odoo import models
import datetime


class AttendancemasterXlsx(models.AbstractModel):
    _name = 'report.hr_atten_excel_report.attendance_master_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Attendance Master XLSX Report'

    def generate_xlsx_report(self, workbook, data, wizard):
        wizard = wizard.ensure_one()
        
        # Get report data
        if not data or not data.get('company_name'):
            data = wizard._prepare_report_data()

        company_name = data.get('company_name', '')
        from_date = data.get('from_date', '')
        to_date = data.get('to_date', '')
        month_name = data.get('month_name', '')
        date_headers = data.get('date_headers', [])
        employees = data.get('employees', [])

        # Create worksheet with month name
        sheet = workbook.add_worksheet(month_name[:31] if month_name else 'Attendance')

        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': 'black',
        })

        subtitle_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
        })

        header_format = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D9D9D9',
            'border': 1,
            'text_wrap': True,
        })

        day_header_format = workbook.add_format({
            'bold': True,
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#E2EFDA',
            'border': 1,
        })

        date_num_format = workbook.add_format({
            'bold': True,
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#E2EFDA',
            'border': 1,
        })

        data_format = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
        })

        text_left_format = workbook.add_format({
            'font_size': 9,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
        })

        # Present (P) format - Green background
        present_format = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#C6EFCE',
            'font_color': '#006100',
            'bold': True,
        })

        # Weekoff (W) format - Yellow background
        weekoff_format = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#FFEB9C',
            'font_color': '#9C5700',
            'bold': True,
        })

        # Absent (A) format - Red background
        absent_format = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#FFC7CE',
            'font_color': '#9C0006',
            'bold': True,
        })

        # Holiday (H) format - Light blue background
        holiday_format = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#BDD7EE',
            'font_color': '#1F4E79',
            'bold': True,
        })

        # Leave (L) format - Purple background
        leave_format = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#E4DFEC',
            'font_color': '#7030A0',
            'bold': True,
        })

        # Summary header format
        summary_header_format = workbook.add_format({
            'bold': True,
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#FCE4D6',
            'border': 1,
            'text_wrap': True,
        })

        # Summary data format
        summary_format = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#FFF2CC',
        })

        # Calculate column positions
        static_cols = 7  # S.No, Name, Code, Dept, Position, DOJ, W/O
        num_days = len(date_headers)
        summary_cols = 5  # Present, Weekoff, Absent, Holiday, Total
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

        # Row 1: Title - "Attendance Master"
        sheet.merge_range(0, 0, 0, total_cols - 1, 'Attendance Master', title_format)

        # Row 2: Company Name
        sheet.merge_range(1, 0, 1, total_cols - 1, company_name, title_format)

        # Row 3: Month Name
        sheet.merge_range(2, 0, 2, total_cols - 1, month_name, subtitle_format)

        # Row 4: Date Range
        date_info = f"From Date : {from_date} To : {to_date}"
        sheet.merge_range(3, 0, 3, total_cols - 1, date_info, subtitle_format)

        # Row 5: intentionally left blank to avoid duplicate weekday headers
        # (weekday headers will appear in the main header row only)

        # Row 6: Date numbers row (1, 2, 3, etc.) and headers
        row = 5
        # Empty cells for static columns
        for col in range(static_cols):
            sheet.write(row, col, '', header_format)
        
        # Write date numbers
        for i, dh in enumerate(date_headers):
            sheet.write(row, static_cols + i, dh['day_num'], date_num_format)
        
        # Empty cells for summary columns
        for i in range(summary_cols):
            sheet.write(row, summary_start + i, '', summary_header_format)

        # Row 7: Main headers
        row = 6
        headers = ['Sr.\nNo.', 'Employee Name', 'Employee\nCode', 'Department', 
                   'Job Position', 'Date of\nJoining', 'W/O']
        
        for col, h in enumerate(headers):
            sheet.write(row, col, h, header_format)

        # Write day names again in header row (combined with date numbers conceptually)
        for i, dh in enumerate(date_headers):
            sheet.write(row, static_cols + i, dh['day_name'], day_header_format)

        # Summary headers
        summary_headers = ['Present\nDays', 'Weekoff\nDays', 'Absent\nDays', 'Holidays', 'Total']
        for i, h in enumerate(summary_headers):
            sheet.write(row, summary_start + i, h, summary_header_format)

        # Set row height for header rows (skip blank row 5)
        sheet.set_row(5, 18)
        sheet.set_row(6, 30)

        # Write employee data rows
        data_start_row = 7
        for emp_idx, emp in enumerate(employees):
            row = data_start_row + emp_idx
            
            # Static data
            sheet.write(row, 0, emp['sno'], data_format)
            sheet.write(row, 1, emp['name'], text_left_format)
            sheet.write(row, 2, emp['employee_code'], data_format)
            sheet.write(row, 3, emp['department'], text_left_format)
            sheet.write(row, 4, emp['job_position'], text_left_format)
            sheet.write(row, 5, emp['date_of_joining'], data_format)
            sheet.write(row, 6, emp['weekoff_day'], data_format)

            # Daily status with color formatting (initial values)
            for i, dh in enumerate(date_headers):
                col = static_cols + i
                status = emp['daily_status'].get(dh['date'], '')
                # Write the value with default format (conditional formatting will handle colors)
                sheet.write(row, col, status, data_format)

            # Calculate summary columns using Excel formulas
            # Column references for formulas
            first_day_col = static_cols  # First day column (0-indexed)
            last_day_col = static_cols + num_days - 1  # Last day column
            
            # Convert to Excel column letters
            def col_to_letter(col_idx):
                """Convert column index to Excel column letter (0=A, 1=B, etc.)"""
                result = ""
                while col_idx >= 0:
                    result = chr(col_idx % 26 + ord('A')) + result
                    col_idx = col_idx // 26 - 1
                return result

            first_col_letter = col_to_letter(first_day_col)
            last_col_letter = col_to_letter(last_day_col)
            excel_row = row + 1  # Excel rows are 1-indexed

            # Present Days formula: COUNTIF for "P"
            present_formula = f'=COUNTIF({first_col_letter}{excel_row}:{last_col_letter}{excel_row},"P")'
            sheet.write_formula(row, summary_start, present_formula, summary_format)

            # Weekoff Days formula: COUNTIF for "W"
            weekoff_formula = f'=COUNTIF({first_col_letter}{excel_row}:{last_col_letter}{excel_row},"W")'
            sheet.write_formula(row, summary_start + 1, weekoff_formula, summary_format)

            # Absent Days formula: COUNTIF for "A"
            absent_formula = f'=COUNTIF({first_col_letter}{excel_row}:{last_col_letter}{excel_row},"A")'
            sheet.write_formula(row, summary_start + 2, absent_formula, summary_format)

            # Holidays formula: COUNTIF for "H"
            holiday_formula = f'=COUNTIF({first_col_letter}{excel_row}:{last_col_letter}{excel_row},"H")'
            sheet.write_formula(row, summary_start + 3, holiday_formula, summary_format)

            # Total formula: Sum of Present + Weekoff + Absent + Holiday
            present_col = col_to_letter(summary_start)
            weekoff_col = col_to_letter(summary_start + 1)
            absent_col = col_to_letter(summary_start + 2)
            holiday_col = col_to_letter(summary_start + 3)
            total_formula = f'={present_col}{excel_row}+{weekoff_col}{excel_row}+{absent_col}{excel_row}+{holiday_col}{excel_row}'
            sheet.write_formula(row, summary_start + 4, total_formula, summary_format)

        # Add legend at the bottom
        legend_row = data_start_row + len(employees) + 2
        sheet.write(legend_row, 0, 'Legend:', header_format)
        sheet.write(legend_row, 1, 'P = Present', present_format)
        sheet.write(legend_row, 2, 'W = Weekoff', weekoff_format)
        sheet.write(legend_row, 3, 'A = Absent', absent_format)
        sheet.write(legend_row, 4, 'H = Holiday', holiday_format)
        sheet.write(legend_row, 5, 'L = Leave', leave_format)

        # Apply Conditional Formatting for dynamic color changes when user edits P/W/A/H/L
        # Define the range for daily status columns
        def col_to_letter(col_idx):
            """Convert column index to Excel column letter (0=A, 1=B, etc.)"""
            result = ""
            while col_idx >= 0:
                result = chr(col_idx % 26 + ord('A')) + result
                col_idx = col_idx // 26 - 1
            return result

        first_day_col_letter = col_to_letter(static_cols)
        last_day_col_letter = col_to_letter(static_cols + num_days - 1)
        first_data_row = data_start_row + 1  # Excel 1-indexed
        last_data_row = data_start_row + len(employees)  # Excel 1-indexed

        # Range for conditional formatting (all daily status cells)
        cond_range = f'{first_day_col_letter}{first_data_row}:{last_day_col_letter}{last_data_row}'

        # Conditional format for "P" - Green
        sheet.conditional_format(cond_range, {
            'type': 'cell',
            'criteria': '==',
            'value': '"P"',
            'format': present_format
        })

        # Conditional format for "W" - Yellow
        sheet.conditional_format(cond_range, {
            'type': 'cell',
            'criteria': '==',
            'value': '"W"',
            'format': weekoff_format
        })

        # Conditional format for "A" - Red
        sheet.conditional_format(cond_range, {
            'type': 'cell',
            'criteria': '==',
            'value': '"A"',
            'format': absent_format
        })

        # Conditional format for "H" - Blue
        sheet.conditional_format(cond_range, {
            'type': 'cell',
            'criteria': '==',
            'value': '"H"',
            'format': holiday_format
        })

        # Conditional format for "L" - Purple
        sheet.conditional_format(cond_range, {
            'type': 'cell',
            'criteria': '==',
            'value': '"L"',
            'format': leave_format
        })
