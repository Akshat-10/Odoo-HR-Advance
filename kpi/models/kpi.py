from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class KPIIndexing(models.Model):
    _name = 'kpi.indexing'
    _description = 'KPI Indexing'
    _check_company_auto = True

    kpi_id = fields.Many2one('kpi.kpi', string='KPI', required=True, ondelete='cascade', tracking=True, check_company=True)
    company_id = fields.Many2one('res.company', string='Company', related='kpi_id.company_id', store=True, readonly=True)
    category_id = fields.Many2one('kpi.category', string='Category', required=True, tracking=True, check_company=True)
    sub_category_id = fields.Many2one('kpi.sub.category', string='Sub Category', required=True, tracking=True, check_company=True)
    description = fields.Text(string='Description', tracking=True)
    weightage = fields.Float(string='Weightage (%)', tracking=True)
    start_date = fields.Date(string='Start Date', default=fields.Date.today, tracking=True)
    review_date = fields.Date(string='Review Date', tracking=True)

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if self.category_id:
            return {'domain': {'sub_category_id': [('category_id', '=', self.category_id.id)]}}
        else:
            return {'domain': {'sub_category_id': []}}

class KPITrainingPlan(models.Model):
    _name = 'kpi.training.plan'
    _description = 'KPI Training Plan'

    kpi_id = fields.Many2one('kpi.kpi', string='KPI', required=True, ondelete='cascade', tracking=True, check_company=True)
    company_id = fields.Many2one('res.company', string='Company', related='kpi_id.company_id', store=True, readonly=True)
    training_id = fields.Many2one('kpi.training', string='Training', required=True, tracking=True, check_company=True)
    reason = fields.Text(string='Reason', tracking=True)
    budget = fields.Monetary(string='Budget', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, tracking=True)

class KPI(models.Model):
    _name = 'kpi.kpi'
    _description = 'Key Performance Index'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sr_no desc'
    _check_company_auto = True

    sr_no = fields.Integer(string='Sr. No.', required=True, copy=False)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )
    name = fields.Char(string='Name', compute='_compute_name', store=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True, check_company=True)
    employee_code = fields.Char(string='Employee Code', related='employee_id.barcode', store=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', store=True, tracking=True)
    department_hod = fields.Many2one('hr.employee', string='Department HOD', related='department_id.manager_id', store=True, tracking=True)
    designation_id = fields.Many2one('hr.job', string='Designation', related='employee_id.job_id', store=True, tracking=True)
    job_summary = fields.Text(string='Job Summary', tracking=True)
    kpi_indexing_ids = fields.One2many('kpi.indexing', 'kpi_id', string='KPI Indexing', tracking=True)
    training_plan_ids = fields.One2many('kpi.training.plan', 'kpi_id', string='Training Plan', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('employee_approved', 'Approved by Employee'),
        ('hod_approved', 'Approved by HOD'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)
    previous_state = fields.Char(string='Previous State', readonly=True, tracking=True)
    can_approve_employee = fields.Boolean(compute='_compute_can_approve', string='Can Approve (Employee)')
    can_approve_hod = fields.Boolean(compute='_compute_can_approve', string='Can Approve (HOD)')
    employee_count = fields.Integer(string='Employee Count', compute='_compute_employee_count')

    _sql_constraints = [
        ('sr_no_company_uniq', 'unique(sr_no, company_id)', 'SR No must be unique per company!'),
    ]

    @api.model
    def create(self, vals):
        vals = dict(vals)
        company_id = vals.get('company_id') or self.env.company.id
        vals['company_id'] = company_id
        if 'sr_no' not in vals:
            sequence = self.env['ir.sequence'].with_company(company_id).next_by_code('kpi.kpi')
            if not sequence:
                raise UserError("Failed to generate sequence for KPI. Please ensure the sequence with code 'kpi.kpi' is defined in the system.")
            vals['sr_no'] = int(sequence) if sequence else 1
        return super(KPI, self).create(vals)
    
    @api.depends('employee_id', 'sr_no')
    def _compute_name(self):
        for record in self:
            if record.employee_id and record.sr_no:
                record.name = f"KPI - {record.employee_id.name} - {record.sr_no}"
            else:
                record.name = "New KPI"

    @api.depends('state', 'employee_id', 'department_hod')
    def _compute_can_approve(self):
        for record in self:
            current_user = self.env.user
            record.can_approve_employee = (record.state == 'submitted' and record.employee_id.user_id == current_user)
            record.can_approve_hod = (record.state == 'employee_approved' and record.department_hod.user_id == current_user)

    @api.depends('employee_id', 'department_hod', 'department_id')
    def _compute_employee_count(self):
        for record in self:
            if record.employee_id and record.department_hod and record.employee_id == record.department_hod and record.department_id:
                record.employee_count = self.env['hr.employee'].search_count([('department_id', '=', record.department_id.id)])
            else:
                record.employee_count = 0

    def action_submit(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Can only submit from draft state.")
        self.write({
            'previous_state': self.state,
            'state': 'submitted'
        })
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary='KPI Approval Required',
            user_id=self.employee_id.user_id.id,
            note='Please review and approve your KPI.'
        )

    def action_approve_employee(self):
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError("Can only approve from submitted state.")
        if self.env.user != self.employee_id.user_id:
            raise UserError("Only the employee can approve this KPI.")
        self.write({
            'previous_state': self.state,
            'state': 'employee_approved'
        })

    def action_approve_hod(self):
        self.ensure_one()
        if self.state != 'employee_approved':
            raise UserError("Can only approve from employee approved state.")
        if self.env.user != self.department_hod.user_id:
            raise UserError("Only the HOD can approve this KPI.")
        self.write({
            'previous_state': self.state,
            'state': 'hod_approved'
        })

    def action_complete(self):
        self.ensure_one()
        if self.state != 'hod_approved':
            raise UserError("Can only complete from HOD approved state.")
        self.write({
            'previous_state': self.state,
            'state': 'completed'
        })

    def action_reject(self):
        self.ensure_one()
        self.write({
            'previous_state': self.state,
            'state': 'rejected'
        })

    def action_undo(self):
        self.ensure_one()
        if not self.previous_state:
            raise UserError("No previous state to undo to.")
        self.write({
            'state': self.previous_state,
            'previous_state': False
        })

    def action_admin_approve(self):
        self.ensure_one()
        if not self.env.user.has_group('base.group_system'):
            raise UserError("Only administrators can perform this action.")
        self.write({
            'state': 'completed'
        })

    @api.constrains('employee_id', 'company_id')
    def _check_employee_company(self):
        for record in self:
            employee_company = record.employee_id.company_id
            if employee_company and employee_company != record.company_id:
                raise ValidationError(_('The employee must belong to the same company as the KPI.'))