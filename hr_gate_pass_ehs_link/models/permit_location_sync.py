from odoo import models, api

# Helper abstract model to fetch latest attendance address
class PermitLocationMixin(models.AbstractModel):
    _name = 'permit.location.mixin'
    _description = 'Helper to access latest attendance address'

    @api.model
    def _get_latest_attendance_address(self):
        user = self.env.user
        employee = user.employee_id
        if not employee:
            return False
        attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', employee.id)
        ], order='check_in desc', limit=1)
        if not attendance:
            return False
        return attendance.check_in_address or attendance.check_out_address or False

# Work Heights Permit
class WorkHeightsPermit(models.Model):
    _inherit = 'work.heights.permit'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'location' in fields_list and not res.get('location'):
            address = self.env['permit.location.mixin']._get_latest_attendance_address()
            if address:
                res['location'] = address
        return res

    @api.model_create_multi
    def create(self, vals_list):
        # Fetch once; reuse for batch
        address = None
        for vals in vals_list:
            if not vals.get('location'):
                if address is None:
                    address = self.env['permit.location.mixin']._get_latest_attendance_address()
                if address:
                    vals['location'] = address
        return super().create(vals_list)

# Energized Work Permit
class EnergizedWorkPermit(models.Model):
    _inherit = 'energized.work.permit'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'location' in fields_list and not res.get('location'):
            address = self.env['permit.location.mixin']._get_latest_attendance_address()
            if address:
                res['location'] = address
        return res

    @api.model_create_multi
    def create(self, vals_list):
        address = None
        for vals in vals_list:
            if not vals.get('location'):
                if address is None:
                    address = self.env['permit.location.mixin']._get_latest_attendance_address()
                if address:
                    vals['location'] = address
        return super().create(vals_list)

# Daily Permit Work
class DailyPermitWork(models.Model):
    _inherit = 'daily.permit.work'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'location' in fields_list and not res.get('location'):
            address = self.env['permit.location.mixin']._get_latest_attendance_address()
            if address:
                res['location'] = address
        return res

    @api.model_create_multi
    def create(self, vals_list):
        address = None
        for vals in vals_list:
            if not vals.get('location'):
                if address is None:
                    address = self.env['permit.location.mixin']._get_latest_attendance_address()
                if address:
                    vals['location'] = address
        return super().create(vals_list)

# Hot Work Permit
class HotWorkPermit(models.Model):
    _inherit = 'hot.work.permit'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'location' in fields_list and not res.get('location'):
            address = self.env['permit.location.mixin']._get_latest_attendance_address()
            if address:
                res['location'] = address
        return res

    @api.model_create_multi
    def create(self, vals_list):
        address = None
        for vals in vals_list:
            if not vals.get('location'):
                if address is None:
                    address = self.env['permit.location.mixin']._get_latest_attendance_address()
                if address:
                    vals['location'] = address
        return super().create(vals_list)
