from odoo import _, api, fields, models


class HrCustomFormBase(models.AbstractModel):
    _name = "hr.custom.form.base"
    _description = "HR Custom Form Base"
    _abstract = True

    _sequence_code = False

    name = fields.Char(
        string="Document Reference",
        required=True,
        default=lambda self: _("New"),
        copy=False,
    )
    sequence = fields.Integer(string="Sequence", default=10)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        check_company=True,
    )
    employee_code = fields.Char(string="Employee Code")
    father_name = fields.Char(string="Father Name")
    joining_date = fields.Date(string="Joining Date")
    form_date = fields.Date(
        string="Document Date",
        required=True,
        default=fields.Date.context_today,
    )
    department_id = fields.Many2one("hr.department", string="Department")
    job_id = fields.Many2one("hr.job", string="Job Position")

    def _prepare_employee_related_vals(self, vals):
        employee_id = vals.get("employee_id")
        if not employee_id:
            return

        employee = self.env["hr.employee"].browse(employee_id)
        if not employee:
            return

        related_values = {}
        if not vals.get("employee_code") and employee.employee_code:
            related_values["employee_code"] = employee.employee_code
        if not vals.get("father_name") and employee.father_name:
            related_values["father_name"] = employee.father_name
        if not vals.get("joining_date") and (employee.joining_date or employee.join_date):
            related_values["joining_date"] = employee.joining_date or employee.join_date
        if not vals.get("department_id") and employee.department_id:
            related_values["department_id"] = employee.department_id.id
        if not vals.get("job_id") and employee.job_id:
            related_values["job_id"] = employee.job_id.id
        if not vals.get("company_id") and employee.company_id:
            related_values["company_id"] = employee.company_id.id

        vals.update({key: value for key, value in related_values.items() if value})

    def _get_sequence_code(self):
        return getattr(self, "_sequence_code", False) or self._name

    def _next_sequence(self, company_id):
        seq_code = self._get_sequence_code()
        seq_env = self.env["ir.sequence"]
        if company_id:
            company = self.env["res.company"].browse(company_id)
            seq_env = seq_env.with_company(company)
        return seq_env.next_by_code(seq_code) or _("New")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._prepare_employee_related_vals(vals)
            vals.setdefault("company_id", self.env.company.id)
            if not vals.get("name") or vals.get("name") in ("New", _("New")):
                vals["name"] = self._next_sequence(vals.get("company_id"))
        return super().create(vals_list)

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        for record in self:
            employee = record.employee_id
            if not employee:
                continue
            record.employee_code = employee.employee_code or False
            record.father_name = employee.father_name or False
            record.joining_date = employee.joining_date or employee.join_date or False
            record.department_id = employee.department_id or False
            record.job_id = employee.job_id or False
            record.company_id = employee.company_id or record.company_id

    @api.onchange("company_id")
    def _onchange_company_id(self):
        for record in self:
            if record.employee_id and record.employee_id.company_id != record.company_id:
                record.employee_id = False


class HrCustomFormEr1(models.Model):
    _name = "hr.custom.form.er1"
    _description = "Exchange Return (ER1)"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.er1"

    er_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    er_to_address = fields.Text(string="To Address")
    er_subject = fields.Char(string="Subject")
    er_body = fields.Text(string="Body")
    er_quarter_end_date = fields.Date(string="Quarter Ending Date")


class HrCustomFormD(models.Model):
    _name = "hr.custom.form.formd"
    _description = "Form D"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.formd"

    formd_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    month_year = fields.Char(string="Month and Year")
    total_workers = fields.Integer(string="Total Number of Workers")
    company_address = fields.Text(string="Company Address", compute="_compute_company_address", store=True)
    line_ids = fields.One2many(
        "hr.custom.form.formd.line",
        "form_id",
        string="Wage Lines",
    )

    @api.depends("company_id")
    def _compute_company_address(self):
        for record in self:
            if record.company_id and record.company_id.partner_id:
                record.company_address = record.company_id.partner_id._display_address()
            else:
                record.company_address = False


class HrCustomFormMinimumWageNotice(models.Model):
    _name = "hr.custom.form.mw_notice"
    _description = "Minimum Wages Display Notice"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.mw_notice"

    company_address = fields.Text(string="Company Address", compute="_compute_company_address", store=True)
    notice_line_ids = fields.One2many(
        "hr.custom.form.mw.notice.line",
        "notice_id",
        string="Notice Entries",
    )

    @api.depends("company_id")
    def _compute_company_address(self):
        for record in self:
            if record.company_id and record.company_id.partner_id:
                record.company_address = record.company_id.partner_id._display_address()
            else:
                record.company_address = False


class HrCustomFormTwo(models.Model):
    _name = "hr.custom.form.form2"
    _description = "Form 2 (Revised)"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.form2"

    father_husband_name = fields.Char(string="Father's / Husband Name")
    spouse_name = fields.Char(string="Spouse Name")
    date_of_birth = fields.Date(string="Date of Birth")
    gender = fields.Selection(
        [
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
        string="Gender",
    )
    marital_status = fields.Selection(
        [
            ("single", "Single"),
            ("married", "Married"),
            ("widowed", "Widowed"),
            ("divorced", "Divorced"),
        ],
        string="Marital Status",
    )
    account_number = fields.Char(string="Account Number")
    permanent_address = fields.Text(string="Permanent Address")
    temporary_address = fields.Text(string="Temporary Address")
    date_of_joining = fields.Date(string="Date of Joining")
    part_a_line_ids = fields.One2many(
        "hr.custom.form.form2.part.a.line",
        "form_id",
        string="Part A Nominees",
    )
    part_b_family_line_ids = fields.One2many(
        "hr.custom.form.form2.part.b.family.line",
        "form_id",
        string="Part B Family Members",
    )
    part_b_nominee_line_ids = fields.One2many(
        "hr.custom.form.form2.part.b.nominee.line",
        "form_id",
        string="Part B Nominees",
    )
    eps_part_b_date = fields.Date(string="Part B (EPS) Date")

    def _prepare_employee_related_vals(self, vals):
        super()._prepare_employee_related_vals(vals)
        employee_id = vals.get("employee_id")
        if not employee_id:
            return
        employee = self.env["hr.employee"].browse(employee_id)
        if not employee:
            return
        if not vals.get("father_husband_name"):
            vals["father_husband_name"] = employee.father_name or False
        if not vals.get("date_of_birth"):
            vals["date_of_birth"] = employee.birthday or False
        if not vals.get("gender") and employee.gender:
            vals["gender"] = employee.gender
        if not vals.get("marital_status") and employee.marital:
            vals["marital_status"] = employee.marital
        if not vals.get("date_of_joining"):
            vals["date_of_joining"] = employee.joining_date or employee.join_date or False
        if not vals.get("permanent_address") and employee.private_street:
            vals["permanent_address"] = employee.private_street
        if not vals.get("temporary_address") and employee.address_id:
            vals["temporary_address"] = employee.address_id._display_address()

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        super()._onchange_employee_id()
        for record in self:
            employee = record.employee_id
            if not employee:
                continue
            record.father_husband_name = employee.father_name or False
            record.date_of_birth = employee.birthday or False
            record.gender = employee.gender or False
            record.marital_status = employee.marital or False
            record.date_of_joining = employee.joining_date or employee.join_date or False
            if employee.private_street:
                record.permanent_address = employee.private_street
            if employee.address_id:
                record.temporary_address = employee.address_id._display_address()


class HrCustomFormEleven(models.Model):
    _name = "hr.custom.form.form11"
    _description = "Form 11 (Composite Declaration Form)"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.form11"

    form_number = fields.Char(string="No.")
    spouse_name = fields.Char(string="Spouse Name")
    date_of_birth = fields.Date(string="Date of Birth")
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")],
        string="Gender",
    )
    marital_status = fields.Selection(
        [("single", "Single"), ("married", "Married"), ("widowed", "Widowed"), ("divorced", "Divorced")],
        string="Marital Status",
    )
    email = fields.Char(string="Email")
    mobile = fields.Char(string="Mobile")
    present_joining_date = fields.Date(string="Date of Joining (Current)")
    bank_account_no = fields.Char(string="Bank Account No.")
    bank_ifsc = fields.Char(string="IFSC Code")
    aadhaar_number = fields.Char(string="AADHAR Number")
    pan_number = fields.Char(string="PAN")
    member_epf_before = fields.Selection([("yes", "Yes"), ("no", "No")], string="Earlier EPF Member")
    member_eps_before = fields.Selection([("yes", "Yes"), ("no", "No")], string="Earlier EPS Member")
    prev_unexempted_line_ids = fields.One2many(
        "hr.custom.form.form11.prev.unexempted",
        "form_id",
        string="Previous Employment (Un-exempted)",
    )
    prev_exempted_line_ids = fields.One2many(
        "hr.custom.form.form11.prev.exempted",
        "form_id",
        string="Previous Employment (Exempted)",
    )
    international_worker = fields.Selection([("no", "No"), ("yes", "Yes")], string="International Worker", default="no")
    origin_country = fields.Char(string="Country of Origin")
    passport_no = fields.Char(string="Passport No.")
    passport_valid_from = fields.Date(string="Passport Valid From")
    passport_valid_to = fields.Date(string="Passport Valid To")

    def _prepare_employee_related_vals(self, vals):
        super()._prepare_employee_related_vals(vals)
        employee_id = vals.get("employee_id")
        if not employee_id:
            return
        employee = self.env["hr.employee"].browse(employee_id)
        if not employee:
            return
        if not vals.get("date_of_birth"):
            vals["date_of_birth"] = employee.birthday or False
        if not vals.get("gender") and employee.gender:
            vals["gender"] = employee.gender
        if not vals.get("marital_status") and employee.marital:
            vals["marital_status"] = employee.marital
        if not vals.get("email"):
            vals["email"] = employee.work_email or employee.private_email or False
        if not vals.get("mobile"):
            vals["mobile"] = employee.mobile_phone or employee.work_phone or False
        if not vals.get("present_joining_date"):
            vals["present_joining_date"] = employee.joining_date or employee.join_date or False
        if not vals.get("aadhaar_number"):
            vals["aadhaar_number"] = employee.identification_id or False

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        super()._onchange_employee_id()
        for record in self:
            employee = record.employee_id
            if not employee:
                continue
            record.date_of_birth = employee.birthday or False
            record.gender = employee.gender or False
            record.marital_status = employee.marital or False
            record.email = employee.work_email or employee.private_email or False
            record.mobile = employee.mobile_phone or employee.work_phone or False
            record.present_joining_date = employee.joining_date or employee.join_date or False
            record.aadhaar_number = employee.identification_id or False


class HrCustomFormFifteenG(models.Model):
    _name = "hr.custom.form.form15g"
    _description = "Form 15G"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.form15g"

    place = fields.Char(string="Place")
    declaration_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    assessee_name = fields.Char(string="Name of Assessee")
    assessee_pan = fields.Char(string="PAN of Assessee")
    assessee_status = fields.Char(string="Status")
    previous_year = fields.Char(string="Previous Year")
    residential_status = fields.Char(string="Residential Status")
    address_flat = fields.Char(string="Flat / Door / Block No.")
    address_premises = fields.Char(string="Name of Premises")
    address_road = fields.Char(string="Road / Street / Lane")
    address_area = fields.Char(string="Area / Locality")
    address_city = fields.Char(string="Town / City / District")
    address_state = fields.Char(string="State")
    address_pin = fields.Char(string="PIN")
    contact_email = fields.Char(string="Email")
    contact_phone = fields.Char(string="Telephone / Mobile")
    assessed_to_tax = fields.Selection([("yes", "Yes"), ("no", "No")], string="Assessed to Tax")
    latest_assessment_year = fields.Char(string="Latest Assessment Year")
    estimated_income = fields.Float(string="Estimated Income (Declaration)")
    estimated_total_income = fields.Float(string="Estimated Total Income")
    other_form15g_count = fields.Integer(string="Total No. of other Form 15G")
    other_form15g_amount = fields.Float(string="Aggregate amount of income for prior Form 15G")
    other_form15g_details = fields.Text(string="Details of other Form 15G filed")
    income_detail_ids = fields.One2many(
        "hr.custom.form.form15g.income.line",
        "form_id",
        string="Income Details",
    )
    payer_name = fields.Char(string="Name of person responsible for paying")
    payer_uid = fields.Char(string="Unique Identification No.")
    payer_pan = fields.Char(string="PAN of person responsible for paying")
    payer_address = fields.Text(string="Complete Address")
    payer_tan = fields.Char(string="TAN")
    payer_email = fields.Char(string="Payer Email")
    payer_phone = fields.Char(string="Payer Telephone / Mobile")
    payer_income_amount = fields.Float(string="Amount of income paid")
    declaration_received_date = fields.Date(string="Declaration Received On")
    income_paid_date = fields.Date(string="Income Paid / Credited On")


class HrCustomFormLeaveApplication(models.Model):
    _name = "hr.custom.form.leave_application"
    _description = "Leave Application Form"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.leave_application"

    leave_request_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    leave_reason = fields.Text(string="Reason for Leave")
    leave_days = fields.Float(string="Days")
    leave_from = fields.Date(string="From Date")
    leave_to = fields.Date(string="To Date")
    manager_remarks = fields.Text(string="Manager Remarks")
    approval_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Approval Status",
        default="pending",
    )
    permanent_address = fields.Text(string="Permanent Address")
    contact_number = fields.Char(string="Mobile Number")

    def _prepare_employee_related_vals(self, vals):
        super()._prepare_employee_related_vals(vals)
        employee_id = vals.get("employee_id")
        if not employee_id:
            return
        employee = self.env["hr.employee"].browse(employee_id)
        if not employee:
            return
        if not vals.get("permanent_address") and employee.private_street:
            vals["permanent_address"] = employee.private_street
        if not vals.get("contact_number"):
            vals["contact_number"] = employee.mobile_phone or employee.work_phone or False

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        super()._onchange_employee_id()
        for record in self:
            employee = record.employee_id
            if not employee:
                continue
            if employee.private_street:
                record.permanent_address = employee.private_street
            record.contact_number = employee.mobile_phone or employee.work_phone or False


class HrCustomFormResignationLetter(models.Model):
    _name = "hr.custom.form.resignation_letter"
    _description = "Resignation Letter"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.resignation_letter"

    resignation_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    resignation_description = fields.Text(string="Description")


class HrCustomFormFormDLine(models.Model):
    _name = "hr.custom.form.formd.line"
    _description = "Form D Wage Line"

    form_id = fields.Many2one("hr.custom.form.formd", string="Form D", ondelete="cascade")
    category_id = fields.Many2one("hr.job", string="Category of Workers")
    work_description = fields.Char(string="Brief Description of Work")
    men_employed = fields.Integer(string="No. of men employed")
    women_employed = fields.Integer(string="No. of women employed")
    remuneration_rate = fields.Char(string="Rate of remuneration paid")
    basic_wages = fields.Float(string="Basic Wages or Salary")
    part_da = fields.Float(string="D.A")
    part_hra = fields.Float(string="H.R.A")
    part_other_allowances = fields.Float(string="Other Allowances")
    part_cash_value = fields.Float(string="Cash value of concessional supply")


class HrCustomFormMwNoticeLine(models.Model):
    _name = "hr.custom.form.mw.notice.line"
    _description = "Minimum Wage Notice Line"

    notice_id = fields.Many2one("hr.custom.form.mw_notice", string="Notice", ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", string="Employee", check_company=True)
    father_name = fields.Char(string="Father / Husband Name")
    gender = fields.Selection([("male", "Male"), ("female", "Female"), ("other", "Other")], string="Gender")
    department_id = fields.Many2one("hr.department", string="Department")
    absence_date = fields.Date(string="Absence from duty (Date)")
    damages_description = fields.Text(string="Damages or Loss caused")
    damages_date = fields.Date(string="Damages date")
    showed_cause = fields.Selection([("yes", "Yes"), ("no", "No")], string="Worker showed cause?")
    show_cause_date = fields.Date(string="Show cause date")
    deduction_date = fields.Date(string="Date of deduction")
    deduction_amount = fields.Float(string="Amount of deduction")
    installment_count = fields.Integer(string="Number of installments")
    realisation_date = fields.Date(string="Date total realised")
    remarks = fields.Text(string="Remarks")

    @api.onchange("employee_id")
    def _onchange_employee(self):
        for record in self:
            employee = record.employee_id
            if not employee:
                continue
            record.father_name = employee.father_name or False
            record.gender = employee.gender or False
            record.department_id = employee.department_id or False


class HrCustomFormTwoPartALine(models.Model):
    _name = "hr.custom.form.form2.part.a.line"
    _description = "Form 2 Part A Line"

    form_id = fields.Many2one("hr.custom.form.form2", string="Form 2", ondelete="cascade")
    nominee_name = fields.Char(string="Name of nominee")
    nominee_address = fields.Text(string="Address")
    relationship = fields.Char(string="Relationship with member")
    date_of_birth = fields.Date(string="Date of Birth")
    share_amount = fields.Char(string="Share of accumulations")
    guardian_details = fields.Text(string="Guardian details (if nominee minor)")


class HrCustomFormTwoPartBFamilyLine(models.Model):
    _name = "hr.custom.form.form2.part.b.family.line"
    _description = "Form 2 Part B Family Line"

    form_id = fields.Many2one("hr.custom.form.form2", string="Form 2", ondelete="cascade")
    sequence = fields.Integer(string="S. No.")
    member_name = fields.Char(string="Name of family member")
    address = fields.Text(string="Address")
    date_of_birth = fields.Date(string="Date of Birth")
    relationship = fields.Char(string="Relationship with member")


class HrCustomFormTwoPartBNomineeLine(models.Model):
    _name = "hr.custom.form.form2.part.b.nominee.line"
    _description = "Form 2 Part B Nominee Line"

    form_id = fields.Many2one("hr.custom.form.form2", string="Form 2", ondelete="cascade")
    nominee_name = fields.Char(string="Name of nominee")
    nominee_address = fields.Text(string="Address")
    date_of_birth = fields.Date(string="Date of Birth")
    relationship = fields.Char(string="Relationship with member")


class HrCustomForm11PreviousUnexempted(models.Model):
    _name = "hr.custom.form.form11.prev.unexempted"
    _description = "Form 11 Previous Employment (Un-exempted)"

    form_id = fields.Many2one("hr.custom.form.form11", string="Form 11", ondelete="cascade")
    establishment = fields.Char(string="Establishment Name & Address")
    uan = fields.Char(string="Universal Account Number")
    pf_account = fields.Char(string="PF Account Number")
    joining_date = fields.Date(string="Date of joining")
    exit_date = fields.Date(string="Date of exit")
    scheme_certificate = fields.Char(string="Scheme Certificate No.")
    ppo_number = fields.Char(string="PPO Number")
    ncp_days = fields.Integer(string="NCP Days")


class HrCustomForm11PreviousExempted(models.Model):
    _name = "hr.custom.form.form11.prev.exempted"
    _description = "Form 11 Previous Employment (Exempted)"

    form_id = fields.Many2one("hr.custom.form.form11", string="Form 11", ondelete="cascade")
    trust_name = fields.Char(string="Name & Address of Trust")
    uan = fields.Char(string="UAN")
    eps_account = fields.Char(string="Member EPS A/c Number")
    joining_date = fields.Date(string="Date of joining")
    exit_date = fields.Date(string="Date of exit")
    scheme_certificate = fields.Char(string="Scheme Certificate No.")
    ncp_days = fields.Integer(string="NCP Days")


class HrCustomForm15GIncomeLine(models.Model):
    _name = "hr.custom.form.form15g.income.line"
    _description = "Form 15G Income Detail"

    form_id = fields.Many2one("hr.custom.form.form15g", string="Form 15G", ondelete="cascade")
    sequence = fields.Integer(string="Sl. No.")
    investment_identification = fields.Char(string="Investment / Account Identification")
    income_nature = fields.Char(string="Nature of income")
    deduction_section = fields.Char(string="Section")
    income_amount = fields.Float(string="Amount of income")
