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
        required=True,
        check_company=True,
    )
    employee_code = fields.Char(string="Employee Code")
    father_name = fields.Char(string="Father Name")
    joining_date = fields.Date(string="Joining Date")
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
    _description = "ER1 Covering Letter / Form ER1"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.er1"


class HrCustomFormD(models.Model):
    _name = "hr.custom.form.formd"
    _description = "Form D"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.formd"


class HrCustomFormMinimumWageNotice(models.Model):
    _name = "hr.custom.form.mw_notice"
    _description = "Minimum Wages Display Notice"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.mw_notice"


class HrCustomFormTwo(models.Model):
    _name = "hr.custom.form.form2"
    _description = "Form 2 (Revised)"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.form2"


class HrCustomFormEleven(models.Model):
    _name = "hr.custom.form.form11"
    _description = "Form 11 (Composite Declaration Form)"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.form11"


class HrCustomFormFifteenG(models.Model):
    _name = "hr.custom.form.form15g"
    _description = "Form 15G"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.form15g"


class HrCustomFormLeaveApplication(models.Model):
    _name = "hr.custom.form.leave_application"
    _description = "Leave Application Form"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.leave_application"


class HrCustomFormResignationLetter(models.Model):
    _name = "hr.custom.form.resignation_letter"
    _description = "Resignation Letter"
    _inherit = "hr.custom.form.base"

    _sequence_code = "hr.custom.form.resignation_letter"
