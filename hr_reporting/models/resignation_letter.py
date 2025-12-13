from odoo import models, fields, api

class ResignationLetter(models.Model):
    _inherit = "hr.custom.form.resignation_letter"
    
    def action_generate_resignation_report(self):
        return self.env.ref('hr_reporting.resignation_letter_report').report_action(self,config=False) 
