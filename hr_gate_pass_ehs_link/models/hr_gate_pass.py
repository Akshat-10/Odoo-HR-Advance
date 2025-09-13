from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrGatePass(models.Model):
    _inherit = 'hr.gate.pass'
    
    contractor_visit_type = fields.Selection(selection_add=[
        ('work_permit', 'Work Permit'),
    ])

    ehs_permit_type = fields.Selection([
        ('work_heights', 'Work at Heights Permit'),
        ('energized', 'Energized Work Permit'),
        ('daily', 'Daily Permit to Work'),
        ('hot_work', 'Hot Work Permit'),
    ], string='EHS Work Permit Type')

    work_heights_permit_id = fields.Many2one('work.heights.permit', string='Work at Heights Permit', ondelete='set null')
    energized_work_permit_id = fields.Many2one('energized.work.permit', string='Energized Work Permit', ondelete='set null')
    daily_permit_work_id = fields.Many2one('daily.permit.work', string='Daily Permit to Work', ondelete='set null')
    hot_work_permit_id = fields.Many2one('hot.work.permit', string='Hot Work Permit', ondelete='set null')

    # Creation actions (header buttons) - only create if absent, no opening
    def action_create_work_heights_permit(self):
        self.ensure_one()
        if not self.work_heights_permit_id:
            permit = self.env['work.heights.permit'].create({
                'name': _('New'),
                # 'location': self.reason or _('N/A'),
                'permit_type': 'work_at_heights',
            })
            self.work_heights_permit_id = permit.id
        return self._open_record(self.work_heights_permit_id)

    def action_create_energized_work_permit(self):
        self.ensure_one()
        if not self.energized_work_permit_id:
            permit = self.env['energized.work.permit'].create({
                'work_order_no': self.name or _('GatePass'),
            })
            self.energized_work_permit_id = permit.id
        return self._open_record(self.energized_work_permit_id)

    def action_create_daily_permit_work(self):
        self.ensure_one()
        if not self.daily_permit_work_id:
            permit = self.env['daily.permit.work'].create({
                'german_po_number': self.name or _('GatePass'),
                # 'facility': self.reason or _('N/A'),
                'contractor_company_name': _('Contractor'),
                # 'contractor_project_manager_name': self.requester_user_id.name if self.requester_user_id else _('N/A'),
                # 'specific_work_location': self.reason or _('N/A'),
                'description_of_work': self.reason or _('N/A'),
            })
            self.daily_permit_work_id = permit.id
        return self._open_record(self.daily_permit_work_id)

    def action_create_hot_work_permit(self):
        self.ensure_one()
        if not self.hot_work_permit_id:
            permit = self.env['hot.work.permit'].create({
                'permit_number': _('New'),
                # 'facility': 'German green steel and power ltd.',
                # 'work_location': self.reason or _('N/A'),
                'work_description': self.reason or _('N/A'),
                'date': fields.Date.context_today(self),
                # 'start_time': fields.Datetime.now(),
                # 'expiration_time': fields.Datetime.now(),
            })
            self.hot_work_permit_id = permit.id
        return self._open_record(self.hot_work_permit_id)
            
    #  def action_create_hot_work_permit(self):
    #     self.ensure_one()
    #     if not self.hot_work_permit_id:
    #         permit = self.env['hot.work.permit'].create({
    #             'permit_number': _('New'),
    #             'facility': 'German green steel and power ltd.',
    #             'work_location': self.reason or _('N/A'),
    #             'work_description': self.reason or _('N/A'),
    #             'date': fields.Date.context_today(self),
    #             'start_time': fields.Datetime.now(),
    #             'expiration_time': fields.Datetime.now(),
    #         })
    #         self.hot_work_permit_id = permit.id
    #     return self._open_linked_record(self.hot_work_permit_id)

    # Open actions (stat buttons)
    def action_open_work_heights_permit(self):
        self.ensure_one()
        return self._open_record(self.work_heights_permit_id)

    def action_open_energized_work_permit(self):
        self.ensure_one()
        return self._open_record(self.energized_work_permit_id)

    def action_open_daily_permit_work(self):
        self.ensure_one()
        return self._open_record(self.daily_permit_work_id)

    def action_open_hot_work_permit(self):
        self.ensure_one()
        return self._open_record(self.hot_work_permit_id)

    def _open_record(self, record):
        if not record:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': record.display_name,
            'res_model': record._name,
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'current',
        }
    def action_submit(self):
        for rec in self:
            if (rec.pass_type == 'contractor' and rec.contractor_visit_type == 'work_permit'
                and not (rec.work_heights_permit_id or rec.energized_work_permit_id or rec.daily_permit_work_id or rec.hot_work_permit_id)):
                raise ValidationError(_('Work Permit not created. Create at least one (Heights / Energized / Daily / Hot Work) permit before submitting.'))
        return super().action_submit()

    @api.constrains('contractor_visit_type', 'ehs_permit_type')
    def _check_ehs_permit_required(self):
        for rec in self:
            if rec.contractor_visit_type == 'work_permit' and not rec.ehs_permit_type:
                raise ValidationError(_('You must select an EHS Work Permit Type when Contractor Visit Type is Work Permit.'))
