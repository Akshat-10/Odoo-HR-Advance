from odoo import models, fields


class KPICategory(models.Model): 
    _name = 'kpi.category' 
    _description = 'KPI Category'
    
    name = fields.Char(string='Category', required=True, tracking=True)


class KPISubCategory(models.Model): 
    _name = 'kpi.sub.category' 
    _description = 'KPI Sub Category'
    
    name = fields.Char(string='Sub Category', required=True, tracking=True)
    category_id = fields.Many2one('kpi.category', string='Category', required=True, tracking=True)
    
class KPITraining(models.Model): 
    _name = 'kpi.training' 
    _description = 'KPI Training'
    
    name = fields.Char(string='Training', required=True, tracking=True)

