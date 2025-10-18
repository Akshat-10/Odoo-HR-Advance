# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrContractSalaryOffer(models.Model):
    _inherit = 'hr.contract.salary.offer'

    structure_line_ids = fields.One2many(
        'hr.contract.salary.offer.structure.line', 'offer_id', string='Salary Structure Lines', copy=True)
    monthly_budget = fields.Monetary(
        string='Monthly Budget', currency_field='currency_id', compute='_compute_monthly_budget', store=False
    )
    inhand_amount = fields.Monetary(string='In Hand Salary', currency_field='currency_id', compute='_compute_inhand_amount', store=False, help='Monthly In Hand Salary derived from the INHAND line.')

    @api.depends('final_yearly_costs')
    def _compute_monthly_budget(self):
        for rec in self:
            rec.monthly_budget = (rec.final_yearly_costs or 0.0) / 12.0

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for offer in records:
            offer._apply_default_salary_structure()
        return records

    def write(self, vals):
        res = super().write(vals)
        # Recompute line amounts when budget or structure lines change
        if 'final_yearly_costs' in vals or 'structure_line_ids' in vals:
            self._recompute_structure_line_amounts()
        return res

    @api.onchange('final_yearly_costs')
    def _onchange_final_yearly_costs(self):
        self._recompute_structure_line_amounts()

    @api.onchange('contract_template_id')
    def _onchange_contract_template_id_reapply_structure(self):
        # When changing the contract template (and thus potentially the structure type),
        # only populate default structure if there are no lines yet. Do NOT wipe user edits.
        if self.contract_template_id and not self.structure_line_ids:
            self._apply_default_salary_structure()

    @api.onchange('structure_line_ids')
    def _onchange_structure_line_ids(self):
        # When the user edits lines in the O2M, recompute all amounts live for correctness
        self._recompute_structure_line_amounts()

    def _apply_default_salary_structure(self):
        self.ensure_one()
        structure = False
        # Prefer the structure tied to the contract's salary structure type
        if self.contract_template_id and self.contract_template_id.structure_type_id and \
           self.contract_template_id.structure_type_id.salary_config_structure_id:
            structure = self.contract_template_id.structure_type_id.salary_config_structure_id
        # Fallback: try job default contract's structure type
        elif self.employee_job_id and self.employee_job_id.default_contract_id and \
             self.employee_job_id.default_contract_id.structure_type_id and \
             self.employee_job_id.default_contract_id.structure_type_id.salary_config_structure_id:
            structure = self.employee_job_id.default_contract_id.structure_type_id.salary_config_structure_id
        if not structure:
            return
        lines_vals = []
        for line in structure.line_ids.filtered(lambda l: l.show_in_offer):
            lines_vals.append({
                'name': line.name,
                'code': line.code,
                'sequence': line.sequence,
                'impact': line.impact,
                'compute_mode': line.compute_mode,
                'value': line.value,
                'python_code': line.python_code,
            })
        # Only populate if still empty (avoid deleting user-provided lines)
        if lines_vals and not self.structure_line_ids:
            self.structure_line_ids = [(0, 0, v) for v in lines_vals]
            # compute amounts after creating all lines to respect dependencies
            self._recompute_structure_line_amounts()

    def _recompute_structure_line_amounts(self):
        for offer in self:
            # Stabilize values across dependent lines: iterate up to 4 passes or until no changes
            # Avoid using record.id in sorting because new (unsaved) lines have NewId which is not orderable
            sorted_lines = offer.structure_line_ids.sorted(
                key=lambda x: (x.sequence or 0, (x.code or '').lower(), (x.name or '').lower())
            )
            for _ in range(4):
                changed = False
                for l in sorted_lines:
                    old = float(l.amount_monthly or 0.0)
                    new = float(l._compute_amount_from_offer() or 0.0)
                    if abs(new - old) > 0.005:
                        l.amount_monthly = new
                        changed = True
                if not changed:
                    break

    @api.depends('structure_line_ids.amount_monthly')
    def _compute_inhand_amount(self):
        for offer in self:
            inhand_line = offer.structure_line_ids.filtered(lambda l: l.code == 'INHAND')[:1]
            offer.inhand_amount = float(inhand_line.amount_monthly) if inhand_line else 0.0


class HrContractSalaryOfferStructureLine(models.Model):
    _name = 'hr.contract.salary.offer.structure.line'
    _description = 'Offer Salary Structure Line'
    _order = 'sequence, id'

    offer_id = fields.Many2one('hr.contract.salary.offer', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    code_id = fields.Many2one('salary.config.code', string='Code')
    code = fields.Char()  # retain plain char for backward compatibility
    impact = fields.Selection([
        ('cost', 'Employer Cost'),
        ('benefit', 'Benefit'),
        ('deduction', 'Deduction'),
    ], default='cost', required=True)
    compute_mode = fields.Selection([
        ('percent_yearly', 'Percent of Employer Budget (yearly)'),
        ('fixed_monthly', 'Fixed Monthly Amount'),
        ('formula', 'Python Formula')
    ], required=True)
    value = fields.Float()
    python_code = fields.Text()

    amount_monthly = fields.Monetary(string='Monthly Amount', currency_field='currency_id', compute=False, store=True)
    currency_id = fields.Many2one(related='offer_id.currency_id', store=False, readonly=True)

    def _compute_amount_from_offer(self):
        self.ensure_one()
        monthly_budget = (self.offer_id.final_yearly_costs or 0.0) / 12.0
        if self.compute_mode == 'percent_yearly':
            return monthly_budget * (float(self.value or 0.0) / 100.0)
        elif self.compute_mode == 'fixed_monthly':
            return float(self.value or 0.0)
        elif self.compute_mode == 'formula':
            # Reference other lines by code without relying on sequence
            all_lines = self.offer_id.structure_line_ids
            # Use the latest available amounts for all other lines (exclude current to avoid self-reference)
            amounts_by_code = {l.code: float(l.amount_monthly or 0.0) for l in all_lines if l.code and l.id != self.id}
            localdict = {
                'final_yearly_costs': float(self.offer_id.final_yearly_costs or 0.0),
                'monthly_budget': monthly_budget,
                # helper to get line by code (returns 0.0 if missing)
                'get': lambda code: float(amounts_by_code.get(code, 0.0)),
                'amount': lambda code: float(amounts_by_code.get(code, 0.0)),
                # Aggregates across all lines (excluding self)
                'sum_previous_cost': sum(float(l.amount_monthly or 0.0) for l in all_lines if l.id != self.id and l.impact == 'cost'),
                'sum_previous_benefit': sum(float(l.amount_monthly or 0.0) for l in all_lines if l.id != self.id and l.impact == 'benefit'),
                'sum_previous_deduction': sum(float(l.amount_monthly or 0.0) for l in all_lines if l.id != self.id and l.impact == 'deduction'),
                'result': 0.0,
            }
            try:
                exec((self.python_code or ''), {}, localdict)
                return float(localdict.get('result') or 0.0)
            except Exception:
                return 0.0
        return 0.0

    @api.onchange('code_id')
    def _onchange_code_id(self):
        for rec in self:
            if rec.code_id:
                rec.code = rec.code_id.code
    @api.onchange('code')
    def _onchange_code(self):
        for rec in self:
            if rec.code and not rec.code_id:
                match = self.env['salary.config.code'].search([('code', '=', rec.code)], limit=1)
                if match:
                    rec.code_id = match
    @api.onchange('compute_mode', 'value', 'python_code', 'code')
    def _onchange_recompute_amount(self):
        for rec in self:
            rec.amount_monthly = rec._compute_amount_from_offer()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code') and not vals.get('code_id'):
                match = self.env['salary.config.code'].search([('code', '=', vals['code'])], limit=1)
                if match:
                    vals['code_id'] = match.id
        records = super().create(vals_list)
        for rec in records:
            rec.amount_monthly = rec._compute_amount_from_offer()
        return records

    def write(self, vals):
        res = super().write(vals)
        # If key compute inputs changed, recompute this line amount
        if {'compute_mode', 'value', 'python_code', 'code', 'offer_id'} & set(vals.keys()):
            for rec in self:
                rec.amount_monthly = rec._compute_amount_from_offer()
        if 'code' in vals and not vals.get('code_id'):
            for rec in self:
                if rec.code and not rec.code_id:
                    match = self.env['salary.config.code'].search([('code', '=', rec.code)], limit=1)
                    if match:
                        rec.code_id = match
        return res
