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
            # Fetch latest attendance address for current user
            address = self.env['permit.location.mixin']._get_latest_attendance_address() if hasattr(self.env['permit.location.mixin'], '_get_latest_attendance_address') else False
            permit = self.env['work.heights.permit'].create({
                'name': _('New'),
                'location': address or False,
                # 'location': self.reason or _('N/A'),
                'permit_type': 'work_at_heights',
            })
            self.work_heights_permit_id = permit.id
        return self._open_record(self.work_heights_permit_id)

    def action_create_energized_work_permit(self):
        self.ensure_one()
        if not self.energized_work_permit_id:
            address = self.env['permit.location.mixin']._get_latest_attendance_address() if hasattr(self.env['permit.location.mixin'], '_get_latest_attendance_address') else False
            permit = self.env['energized.work.permit'].create({
                'work_order_no': self.name or _('GatePass'),
                'location': address or False,
            })
            self.energized_work_permit_id = permit.id
        return self._open_record(self.energized_work_permit_id)

    def action_create_daily_permit_work(self):
        self.ensure_one()
        if not self.daily_permit_work_id:
            address = self.env['permit.location.mixin']._get_latest_attendance_address() if hasattr(self.env['permit.location.mixin'], '_get_latest_attendance_address') else False
            permit = self.env['daily.permit.work'].create({
                'german_po_number': self.name or _('GatePass'),
                'location': address or False,
                # 'facility': self.reason or _('N/A'),
                # 'contractor_company_name': _('Contractor'),
                # 'contractor_project_manager_name': self.requester_user_id.name if self.requester_user_id else _('N/A'),
                # 'specific_work_location': self.reason or _('N/A'),
                # 'description_of_work': self.reason or _('N/A'),
            })
            self.daily_permit_work_id = permit.id
        return self._open_record(self.daily_permit_work_id)

    def action_create_hot_work_permit(self):
        self.ensure_one()
        if not self.hot_work_permit_id:
            address = self.env['permit.location.mixin']._get_latest_attendance_address() if hasattr(self.env['permit.location.mixin'], '_get_latest_attendance_address') else False
            permit = self.env['hot.work.permit'].create({
                'permit_number': _('New'),
                'location': address or False,
                # 'facility': 'German green steel and power ltd.',
                # 'work_location': self.reason or _('N/A'),
                # 'work_description': self.reason or _('N/A'),
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

    # -----------------------
    # Transitions guards
    # -----------------------
    def _ensure_ehs_permit_finalized(self):
        """
        If any supported EHS permit is linked to the gate pass, ensure that at least one
        of them is finalized before allowing state transitions like checkout/close.

        Rules:
        - Work at Heights Permit (work.heights.permit) must be in state 'completed'
        - Daily Permit to Work (daily.permit.work) must be in state 'completed'
        - Hot Work Permit (hot.work.permit) must be in state 'completed'
        - Energized Work Permit (energized.work.permit) must be in state 'completed'
        """
        for rec in self:
            # Only consider if any of the supported permits exists on the record
            has_any_supported_permit = bool(
                rec.work_heights_permit_id or rec.daily_permit_work_id or rec.hot_work_permit_id
            )

            if not has_any_supported_permit:
                continue

            is_finalized = (
                (rec.work_heights_permit_id and rec.work_heights_permit_id.state == 'completed') or
                (rec.daily_permit_work_id and rec.daily_permit_work_id.state == 'completed') or
                (rec.hot_work_permit_id and rec.hot_work_permit_id.state == 'completed') or 
                (rec.energized_work_permit_id and rec.energized_work_permit_id.state == 'completed')
            )

            if not is_finalized:
                raise ValidationError(_('First complete/close your work permit before proceeding.'))

    def action_checkout(self):
        # Block checkout if linked EHS permit(s) are not finalized as per rules
        self._ensure_ehs_permit_finalized()
        return super().action_checkout()

    def action_close(self):
        # Block close if linked EHS permit(s) are not finalized as per rules
        self._ensure_ehs_permit_finalized()
        return super().action_close()
