from odoo import models, fields, api


class SalaryStructureCalculation(models.Model):
    _name = 'salary.structure.calculation.custom'
    _description = 'Salary Structure Calculation'
    _rec_name = 'employee_id'

    # Basic Info
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    employee_code = fields.Many2one('hr.employee', string='Employee Code')
    doj = fields.Date(string='Date of Joining')
    revise_date = fields.Date(string='Revise Date')
    designation = fields.Many2one('hr.employee', string='Designation', store=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    store=True)
    ctc = fields.Float(string='CTC', required=True)

    salary_line_ids = fields.One2many('salary.structure.line.custom', 'salary_id', string='Salary Structure')

    total_fixed_ctc = fields.Float(string='Total FIXED CTC/Month', compute='_compute_totals', store=True)
    gross_salary = fields.Float(string='Gross Salary', compute='_compute_totals', store=True)
    total_deduction = fields.Float(string='Total Deduction', compute='_compute_totals', store=True)
    in_hand_salary = fields.Float(string='In Hand Salary', compute='_compute_totals', store=True)

    canteen_rate = fields.Float(string='Canteen Rate', default=845.00)
    canteen_reference = fields.Float(string='Canteen Reference', default=845.00)
    transport_rate = fields.Float(string='Transport Rate', default=500.00)
    transport_reference = fields.Float(string='Transport Reference', default=500.00)
    pt_rate = fields.Float(string='PT Rate', default=200.00)
    pt_reference = fields.Float(string='PT Reference', default=200.00)

    @api.depends('salary_line_ids.rate', 'salary_line_ids.reference', 'gross_salary_line_ids.rate',
                 'gross_salary_line_ids.reference')
    def _compute_totals(self):
        for record in self:
            fixed_lines = record.salary_line_ids.filtered(lambda l: l.section == 'fixed')
            record.total_fixed_ctc = sum(fixed_lines.mapped('rate'))

            gross_line = record.gross_salary_line_ids.filtered(lambda l: l.name == 'Gross Salary')
            if gross_line:
                record.gross_salary = gross_line[0].rate
            else:
                record.gross_salary = 0.0

            deduction_line = record.gross_salary_line_ids.filtered(lambda l: l.name == 'Total Deduction')
            if deduction_line:
                record.total_deduction = deduction_line[0].rate
            else:
                pf_line = record.gross_salary_line_ids.filtered(lambda l: l.name == 'PF (12%)')
                canteen_line = record.gross_salary_line_ids.filtered(lambda l: l.name == 'Canteen')
                transport_line = record.gross_salary_line_ids.filtered(lambda l: l.name == 'Transport')
                pt_line = record.gross_salary_line_ids.filtered(lambda l: l.name == 'PT')

                total_ded = 0.0
                if pf_line:
                    total_ded += pf_line[0].rate
                if canteen_line:
                    total_ded += canteen_line[0].rate
                if transport_line:
                    total_ded += transport_line[0].rate
                if pt_line:
                    total_ded += pt_line[0].rate

                record.total_deduction = total_ded

            in_hand_line = record.gross_salary_line_ids.filtered(lambda l: l.name == 'In Hand Salary')
            if in_hand_line:
                record.in_hand_salary = in_hand_line[0].rate
            else:
                record.in_hand_salary = record.gross_salary - record.total_deduction

    @api.model
    def create(self, vals):
        record = super(SalaryStructureCalculation, self).create(vals)
        if not record.salary_line_ids:
            record._create_default_lines()
        return record

    def _create_default_lines(self):
        """Create default salary structure lines"""
        default_lines = [
            {'pay_head_custom': 'Basic', 'percentage': 50.00, 'calculated_from': 'ctc', 'section': 'fixed', 'sequence': 1},
            {'pay_head_custom': 'HRA', 'percentage': 50.00, 'calculated_from': 'basic', 'section': 'fixed', 'sequence': 2},
            {'pay_head_custom': 'Uniform', 'percentage': 5.00, 'calculated_from': 'basic', 'section': 'fixed', 'sequence': 3},
            {'pay_head_custom': 'LTA Reimburs.', 'percentage': 8.33, 'calculated_from': 'basic', 'section': 'fixed',
             'sequence': 4},
            {'pay_head_custom': 'Adhoc Pay', 'calculated_from': 'balance_ctc', 'section': 'fixed', 'sequence': 5},
            {'pay_head_custom': 'ESIC (3.25%)', 'percentage': 3.25, 'calculated_from': 'gross_below_21000', 'section': 'fixed',
             'is_compliance': True, 'sequence': 6},
            {'pay_head_custom': 'PF (12%)', 'percentage': 12.00, 'calculated_from': 'basic', 'section': 'fixed',
             'is_compliance': True, 'sequence': 7},
            {'pay_head_custom': 'KRA', 'percentage': 3.00, 'calculated_from': 'ctc', 'section': 'fixed', 'is_compliance': True,
             'sequence': 8},

            # {'pay_head_custom': 'PF (12%)', 'percentage': 12.00, 'calculated_from': 'basic', 'section': 'gross',
            #  'sequence': 9},
            #
            # # Deductions
            # {'pay_head_custom': 'Canteen', 'calculated_from': 'fix', 'section': 'deduction', 'sequence': 10},
            # {'pay_head_custom': 'Transport', 'calculated_from': 'fix', 'section': 'deduction', 'sequence': 11},
            # {'pay_head_custom': 'PT', 'calculated_from': 'fix', 'section': 'deduction', 'sequence': 12},
        ]

        for line_data in default_lines:
            line_data['salary_id'] = self.id
            self.env['salary.structure.line.custom'].create(line_data)

    gross_salary_line_ids = fields.One2many('salary.gross.line.custom', 'salary_id', string='Gross Salary Lines')

    def _update_gross_lines(self):
        for record in self:
            if not record.gross_salary_line_ids:
                basic = record.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Basic')
                hra = record.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'HRA')
                uniform = record.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Uniform')
                adhoc = record.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Adhoc Pay')

                gross_rate = sum([basic[0].rate if basic else 0,
                                  hra[0].rate if hra else 0,
                                  uniform[0].rate if uniform else 0,
                                  adhoc[0].rate if adhoc else 0])

                gross_ref = sum([basic[0].reference if basic else 0,
                                 hra[0].reference if hra else 0,
                                 uniform[0].reference if uniform else 0,
                                 adhoc[0].reference if adhoc else 0])

                lines = [
                    {'name': 'Gross Salary', 'rate': gross_rate, 'reference': gross_ref,
                     'calculated_from': 'gross', 'sequence': 1, 'salary_id': record.id},
                    {'name': 'PF (12%)', 'percentage': 12.0, 'calculated_from': 'basic',  # Changed to 'basic'
                     'sequence': 2, 'salary_id': record.id},
                    {'name': 'ESIC (0.75%) EMP', 'percentage': 0.75, 'calculated_from': 'gross_above_21000',
                     'sequence': 3, 'salary_id': record.id},
                    {'name': 'Canteen', 'rate': 845.00, 'reference': 845.00,
                     'calculated_from': 'fix', 'sequence': 3, 'salary_id': record.id},
                    {'name': 'Transport', 'rate': 500.00, 'reference': 500.00,
                     'calculated_from': 'fix', 'sequence': 4, 'salary_id': record.id},
                    {'name': 'PT', 'rate': 200.00, 'reference': 200.00,
                     'calculated_from': 'fix', 'sequence': 5, 'salary_id': record.id},
                    {'name': 'Total Deduction', 'calculated_from': False,
                     'sequence': 6, 'salary_id': record.id},
                    {'name': 'In Hand Salary', 'calculated_from': False,
                     'sequence': 7, 'salary_id': record.id},
                ]

                for line_data in lines:
                    self.env['salary.gross.line.custom'].create(line_data)

    @api.model
    def create(self, vals):
        record = super(SalaryStructureCalculation, self).create(vals)
        if not record.salary_line_ids:
            record._create_default_lines()
        record._update_gross_lines()  # Add this line
        return record

    def action_refresh_gross_lines(self):
        self._update_gross_lines()


class SalaryStructureLine(models.Model):
    _name = 'salary.structure.line.custom'
    _description = 'Salary Structure Line'
    _order = 'sequence, id'

    salary_id = fields.Many2one('salary.structure.calculation.custom', string='Salary', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)

    pay_head_custom = fields.Char(string='Pay Heads', required=True)
    percentage = fields.Float(string='%')
    calculated_from = fields.Selection([
        ('ctc', 'CTC'),
        ('basic', 'Basic'),
        ('fix', 'Fix'),
        ('balance_ctc', 'Balance amount of CTC'),
        ('gross_below_21000', '21000 Gross'),
        ('basic_capped_15000', 'Sealing at 15000')
    ], string='To be Calculated from')

    rate = fields.Float(string='Rate', compute='_compute_rate', store=True)
    reference = fields.Float(string='Reference', compute='_compute_reference', store=True, readonly=False)

    section = fields.Selection([
        ('fixed', 'Fixed CTC/Month'),
        ('gross', 'Gross Salary'),
        ('deduction', 'Deduction')
    ], string='Section', required=True, default='fixed')

    is_compliance = fields.Boolean(string='Compliances')
    remarks = fields.Char(string='Remarks')

    @api.depends('percentage', 'calculated_from', 'salary_id.ctc', 'salary_id.salary_line_ids.rate')
    def _compute_rate(self):
        for line in self:
            ctc = line.salary_id.ctc

            if line.calculated_from == 'ctc':
                # Calculate from CTC
                line.rate = (ctc * line.percentage) / 100

            elif line.calculated_from == 'basic':
                basic_line = line.salary_id.salary_line_ids.filtered(
                    lambda l: l.pay_head_custom == 'Basic' and l.section == 'fixed'
                )
                if basic_line:
                    line.rate = (basic_line[0].rate * line.percentage) / 100
                else:
                    line.rate = 0.0

            elif line.calculated_from == 'basic_capped_15000':
                basic_line = line.salary_id.salary_line_ids.filtered(
                    lambda l: l.pay_head_custom == 'Basic' and l.section == 'fixed'
                )
                if basic_line:
                    basic_amount = basic_line[0].rate

                    if line.percentage and line.percentage > 0:
                        capped_basic = min(basic_amount, 15000)
                        line.rate = (capped_basic * line.percentage) / 100
                    else:
                        if basic_amount >= 15000:
                            line.rate = 15000
                        else:
                            line.rate = basic_amount * 0.12
                else:
                    line.rate = 0.0

            elif line.calculated_from == 'balance_ctc':
                pf_line = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'PF (12%)')
                lines_to_sum = line.salary_id.salary_line_ids.filtered(
                    lambda l: l.id != line.id and
                              l.pay_head_custom in ['Basic', 'HRA', 'Uniform', 'LTA Reimburs.', 'KRA', 'ESIC (3.25%)']
                )
                total_allocated = sum(lines_to_sum.mapped('rate'))

                if pf_line:
                    if pf_line[0].calculated_from == 'basic_capped_15000':
                        total_allocated += pf_line[0].rate
                    else:
                        total_allocated += pf_line[0].rate

                line.rate = ctc - total_allocated

            elif line.calculated_from == 'gross_below_21000':
                basic = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Basic')
                hra = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'HRA')
                uniform = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Uniform')
                adhoc = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Adhoc Pay')

                gross_salary = sum([
                    basic[0].rate if basic else 0,
                    hra[0].rate if hra else 0,
                    uniform[0].rate if uniform else 0,
                    adhoc[0].rate if adhoc else 0
                ])

                if gross_salary <= 21000:
                    line.rate = (gross_salary * line.percentage) / 100
                else:
                    line.rate = 0.0

            elif line.calculated_from == 'fix':
                pass

            else:
                line.rate = 0.0

    @api.depends('rate', 'is_compliance', 'calculated_from', 'percentage', 'pay_head_custom',
                 'salary_id.salary_line_ids.reference', 'salary_id.salary_line_ids.rate')
    def _compute_reference(self):
        for line in self:
            # Get Basic line for reference calculations
            basic_line = line.salary_id.salary_line_ids.filtered(
                lambda l: l.pay_head_custom == 'Basic'
            )

            if line.pay_head_custom == 'Basic':
                # Manual entry - keep existing value or use rate
                if not line.reference:
                    line.reference = line.rate

            elif line.pay_head_custom == 'HRA':
                # Manual entry - keep existing value or use rate
                if not line.reference:
                    line.reference = line.rate

            elif line.pay_head_custom == 'Uniform':
                # Reference = Basic's reference * 5%
                if basic_line and basic_line[0].reference:
                    line.reference = basic_line[0].reference * 0.05
                else:
                    line.reference = 0.0

            elif line.pay_head_custom == 'LTA Reimburs.':
                # Reference = Basic's reference * 8.33%
                if basic_line and basic_line[0].reference:
                    line.reference = basic_line[0].reference * 0.0833
                else:
                    line.reference = 0.0

            elif line.pay_head_custom == 'Adhoc Pay':
                # Manual entry - keep existing value
                pass

            # elif line.pay_head_custom == 'ESIC (3.25%)':
            #     # Reference = Sum of (Basic + HRA + Uniform + Adhoc Pay) rates
            #     basic = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Basic')
            #     hra = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'HRA')
            #     uniform = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Uniform')
            #     adhoc = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Adhoc Pay')
            #
            #     total = 0.0
            #     if basic:
            #         total += basic[0].rate
            #     if hra:
            #         total += hra[0].rate
            #     if uniform:
            #         total += uniform[0].rate
            #     if adhoc:
            #         total += adhoc[0].rate
            #
            #     line.reference = total

            elif line.pay_head_custom == 'PF (12%)':
                # Reference = Basic's reference * 12%
                if basic_line and basic_line[0].reference:
                    line.reference = basic_line[0].reference * 0.12
                else:
                    line.reference = 0.0

            elif line.pay_head_custom == 'KRA':
                # Reference = 59583 * 3%
                line.reference = 59583 * 0.03

            elif line.is_compliance:
                # For other compliance items
                if line.calculated_from == 'basic':
                    if basic_line:
                        line.reference = (basic_line[0].rate * line.percentage) / 100
                    else:
                        line.reference = 0.0
                elif line.calculated_from == 'ctc':
                    line.reference = (line.salary_id.ctc * line.percentage) / 100
                else:
                    line.reference = line.rate
            else:
                line.reference = 0.0


class SalaryGrossLine(models.Model):
    _name = 'salary.gross.line.custom'
    _description = 'Gross Salary Line'
    _order = 'sequence, id'

    salary_id = fields.Many2one('salary.structure.calculation.custom', string='Salary', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Pay Heads', required=True)
    percentage = fields.Float(string='%')
    calculated_from = fields.Selection([
        ('gross', 'Gross'),
        ('basic', 'Basic'),
        ('gross_above_21000', 'Gross 21000'),
        ('fix', 'Fix'),
    ], string='To be Calculated from')
    rate = fields.Float(string='Rate', compute='_compute_amounts', store=True, readonly=False)
    reference = fields.Float(string='Reference', compute='_compute_amounts', store=True, readonly=False)
    remarks = fields.Char(string='Remarks')

    @api.depends('calculated_from', 'percentage', 'salary_id.salary_line_ids.rate',
                 'salary_id.salary_line_ids.reference', 'salary_id.gross_salary_line_ids.rate')
    def _compute_amounts(self):
        for line in self:
            if line.name == 'Total Deduction':
                # Sum of PF + ESIC (0.75%) + Canteen + Transport + PT
                pf_line = line.salary_id.gross_salary_line_ids.filtered(lambda l: l.name == 'PF (12%)')
                esic_emp_line = line.salary_id.gross_salary_line_ids.filtered(lambda l: l.name == 'ESIC (0.75%) EMP')
                canteen_line = line.salary_id.gross_salary_line_ids.filtered(lambda l: l.name == 'Canteen')
                transport_line = line.salary_id.gross_salary_line_ids.filtered(lambda l: l.name == 'Transport')
                pt_line = line.salary_id.gross_salary_line_ids.filtered(lambda l: l.name == 'PT')

                line.rate = sum([
                    pf_line[0].rate if pf_line else 0,
                    esic_emp_line[0].rate if esic_emp_line else 0,
                    canteen_line[0].rate if canteen_line else 0,
                    transport_line[0].rate if transport_line else 0,
                    pt_line[0].rate if pt_line else 0
                ])

                line.reference = sum([
                    pf_line[0].reference if pf_line else 0,
                    esic_emp_line[0].reference if esic_emp_line else 0,
                    canteen_line[0].reference if canteen_line else 0,
                    transport_line[0].reference if transport_line else 0,
                    pt_line[0].reference if pt_line else 0
                ])
                continue

            if line.name == 'In Hand Salary':
                gross_line = line.salary_id.gross_salary_line_ids.filtered(lambda l: l.name == 'Gross Salary')
                deduction_line = line.salary_id.gross_salary_line_ids.filtered(lambda l: l.name == 'Total Deduction')

                line.rate = (gross_line[0].rate if gross_line else 0) - (
                    deduction_line[0].rate if deduction_line else 0)
                line.reference = (gross_line[0].reference if gross_line else 0) - (
                    deduction_line[0].reference if deduction_line else 0)
                continue

            # Get Gross Salary (sum of Basic + HRA + Uniform + Adhoc Pay from first table)
            basic = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Basic')
            hra = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'HRA')
            uniform = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Uniform')
            adhoc = line.salary_id.salary_line_ids.filtered(lambda l: l.pay_head_custom == 'Adhoc Pay')

            gross_rate = sum([basic[0].rate if basic else 0,
                              hra[0].rate if hra else 0,
                              uniform[0].rate if uniform else 0,
                              adhoc[0].rate if adhoc else 0])

            gross_ref = sum([basic[0].reference if basic else 0,
                             hra[0].reference if hra else 0,
                             uniform[0].reference if uniform else 0,
                             adhoc[0].reference if adhoc else 0])

            # Calculate based on selection
            if line.calculated_from == 'gross':
                if line.percentage:
                    line.rate = (gross_rate * line.percentage) / 100
                    line.reference = (gross_ref * line.percentage) / 100
                else:
                    line.rate = gross_rate
                    line.reference = gross_ref

            elif line.calculated_from == 'basic':
                if basic and line.percentage:
                    line.rate = (basic[0].rate * line.percentage) / 100
                    line.reference = (basic[0].reference * line.percentage) / 100
                else:
                    line.rate = basic[0].rate if basic else 0.0
                    line.reference = basic[0].reference if basic else 0.0

            elif line.calculated_from == 'gross_above_21000':
                if gross_rate <= 21000:
                    line.rate = (gross_rate * line.percentage) / 100
                    line.reference = (gross_ref * line.percentage) / 100
                else:
                    line.rate = 0.0
                    line.reference = 0.0

            elif line.calculated_from == 'fix':
                pass
            else:
                pass
