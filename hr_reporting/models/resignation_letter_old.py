from odoo import models, fields, api
from odoo.exceptions import UserError

class ResignationLetter(models.Model):
    _inherit = "hr.custom.form.resignation_letter"
    
    
    def action_generate_resignation_report(self):
        pass