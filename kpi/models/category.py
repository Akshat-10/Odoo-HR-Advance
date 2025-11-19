from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KPICategory(models.Model):
    _name = 'kpi.category'
    _description = 'KPI Category'
    _check_company_auto = True

    name = fields.Char(string='Category', required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    _sql_constraints = [
        ('name_company_unique', 'unique(name, company_id)', 'Category name must be unique per company.'),
    ]


class KPISubCategory(models.Model):
    _name = 'kpi.sub.category'
    _description = 'KPI Sub Category'
    _check_company_auto = True

    name = fields.Char(string='Sub Category', required=True, tracking=True)
    category_id = fields.Many2one(
        'kpi.category',
        string='Category',
        required=True,
        tracking=True,
        check_company=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    @api.onchange('category_id')
    def _onchange_category_company(self):
        if self.category_id:
            self.company_id = self.category_id.company_id

    @api.constrains('category_id', 'company_id')
    def _check_category_company(self):
        for rec in self:
            if rec.category_id and rec.category_id.company_id != rec.company_id:
                raise ValidationError(_('The sub-category must use a category from the same company.'))


class KPITraining(models.Model):
    _name = 'kpi.training'
    _description = 'KPI Training'
    _check_company_auto = True

    name = fields.Char(string='Training', required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    _sql_constraints = [
        ('training_company_unique', 'unique(name, company_id)', 'Training name must be unique per company.'),
    ]

