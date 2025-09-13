# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from io import BytesIO

try:
    import qrcode
except Exception:
    qrcode = None


class HrGatePassLine(models.Model):
    _name = 'hr.gate.pass.line'
    _description = 'Gate Pass Line'

    gate_pass_id = fields.Many2one('hr.gate.pass', string='Gate Pass', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', domain="[('type','!=','service')]")
    name = fields.Char(string='Description')
    product_uom_qty = fields.Float(string='Quantity', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='UoM')
    is_returned = fields.Boolean(string='Returned', default=False)
    returned_qty = fields.Float(string='Returned Qty', default=0.0)


class HrGatePass(models.Model):
    _name = 'hr.gate.pass'
    _description = 'Gate Pass'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Pass No', copy=False, index=True, default='New')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    pass_type = fields.Selection([
        ('employee_out', 'Employee Out'),
        ('visitor', 'Visitor'),
        ('material', 'Material'),
        ('vehicle', 'Vehicle'),
        ('contractor', 'Contractor')
    ], string='Pass Type', required=True, default='visitor', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('issued', 'Issued'),
        ('checked_out', 'Checked Out'),
        ('returned', 'Returned'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
        ('cancel', 'Canceled'),
    ], string='Status', default='draft', tracking=True)

    requester_user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user, tracking=True)
    host_employee_id = fields.Many2one('hr.employee', string='Host Employee')
    department_id = fields.Many2one('hr.department', string='Department', default=lambda self: self.host_employee_id.department_id.id if self.host_employee_id and self.host_employee_id.department_id else False)
    approval_profile_id = fields.Many2one(string='Approval Profile', comodel_name='hr.gate.pass.approval.profile')
    current_approver_ids = fields.Many2many(string='Current Approvers', comodel_name='res.users')

    reason = fields.Char(string='Reason')
    start_datetime = fields.Datetime(string='Start', required=True, default=lambda self: fields.Datetime.now())
    end_datetime = fields.Datetime(string='End')
    request_datetime = fields.Datetime(string='Requested At', default=lambda self: fields.Datetime.now())
    issued_datetime = fields.Datetime(string='Issued At')
    checked_out_datetime = fields.Datetime(string='Checked Out At')
    returned_datetime = fields.Datetime(string='Returned At')

    is_returnable = fields.Boolean(string='Returnable', default=False)
    expected_return_datetime = fields.Datetime(string='Expected Return')

    line_ids = fields.One2many('hr.gate.pass.line', 'gate_pass_id', string='Items')

    value_total = fields.Monetary(string='Total Value', currency_field='currency_id', compute='_compute_value_total', store=False)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # Vehicle/Visitor
    vehicle_no = fields.Char(string='Vehicle No')
    driver_name = fields.Char(string='Driver Name')

    visitor_name = fields.Char(string='Visitor Name')
    visitor_contact = fields.Char(string='Visitor Contact')
    visitor_company = fields.Char(string='Visitor Company')
    id_proof_type = fields.Selection([('id', 'ID'), ('passport', 'Passport'), ('license', 'License')], string='ID Proof Type')
    id_proof_attachment_id = fields.Many2many('ir.attachment', string='ID Proof Attachment')
    # attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    # Visitor specific: representing info
    representing_from = fields.Selection([
        ('company', 'Company'),
        ('government', 'Government'),
        ('institution', 'Institution'),
        ('personal', 'Personal'),
        ('health_checkup', 'Health Check up'),
        ('interview', 'Interview'),
        ('other', 'Other'),
    ], string='Representing From')
    representing_from_text = fields.Char(string='Representing From (Details)')

    # QR
    qr_token = fields.Char(string='QR Token', copy=False)
    qr_image = fields.Binary(string='QR', attachment=True)
    qr_token_expiry = fields.Datetime(string='QR Expiry')

    # Printing
    printed_by_id = fields.Many2one('res.users', string='Printed By')
    printed_at = fields.Datetime(string='Printed At')
    printed_count = fields.Integer(string='Print Count', default=0)

    # New fields: Gate, Vehicle Image, Employees for employee_out
    gate_id = fields.Many2one('hr.gate', string='Gate')
    vehicle_image = fields.Binary(string='Vehicle/Image', attachment=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    # Contractor specific
    contractor_visit_type = fields.Selection([
        ('visit', 'Only Visit'),
    ], string='Visit Type')

    image = fields.Binary(string='Image', attachment=True)
    log_ids = fields.One2many('hr.gate.log', 'gate_pass_id', string='Logs')

    # -----------------------
    # Helpers
    # -----------------------
    def _get_profile_for_pass_type(self, pass_type):
        """Return the first approval profile matching the pass_type, or empty recordset."""
        if not pass_type:
            return self.env['hr.gate.pass.approval.profile']
        return self.env['hr.gate.pass.approval.profile'].search([('pass_type', '=', pass_type)], limit=1)

    def _get_users_from_profile(self, profile):
        """Union of explicit approver users and users from approver groups."""
        if not profile:
            return self.env['res.users']
        users_from_groups = profile.approver_group_ids.mapped('users')
        return (profile.approver_user_ids | users_from_groups).sudo().filtered(lambda u: u.active)

    def _format_local_dt(self, dt=None):
        """Return a user-timezone localized datetime string.
        Format: MM/DD/YYYY HH:MM:SS to match list view timestamp style.
        """
        dt = dt or fields.Datetime.now()
        local_dt = fields.Datetime.context_timestamp(self, dt)
        # Ensure naive for strftime if needed
        try:
            return local_dt.strftime('%m/%d/%Y %H:%M:%S')
        except Exception:
            # Fallback in unexpected cases
            return str(local_dt)

    # -----------------------
    # Onchanges
    # -----------------------
    @api.onchange('pass_type')
    def _onchange_pass_type_set_profile_and_approvers(self):
        for rec in self:
            profile = rec._get_profile_for_pass_type(rec.pass_type)
            rec.approval_profile_id = profile
            rec.current_approver_ids = rec._get_users_from_profile(profile)

    @api.onchange('approval_profile_id')
    def _onchange_approval_profile_id_set_approvers(self):
        for rec in self:
            profile = rec.approval_profile_id
            rec.current_approver_ids = rec._get_users_from_profile(profile)

    # -----------------------
    # Create/Write overrides to ensure values are set even via RPC/import
    # -----------------------
    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        Profile = self.env['hr.gate.pass.approval.profile']
        for vals in vals_list:
            # Ensure sequence-generated name
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.gate.pass')
            pass_type = vals.get('pass_type')
            profile_id = vals.get('approval_profile_id')
            profile = None
            if not profile_id and pass_type:
                profile = Profile.search([('pass_type', '=', pass_type)], limit=1)
                if profile:
                    vals['approval_profile_id'] = profile.id
            if not vals.get('current_approver_ids'):
                # Only set approvers if not provided explicitly
                if not profile and (profile_id or vals.get('approval_profile_id')):
                    profile = Profile.browse(profile_id or vals.get('approval_profile_id'))
                if profile:
                    users = (profile.approver_user_ids | profile.approver_group_ids.mapped('users')).sudo().filtered(lambda u: u.active).ids
                    vals['current_approver_ids'] = [(6, 0, users)]
            new_vals_list.append(vals)
        return super().create(new_vals_list)

    def write(self, vals):
        res = super().write(vals)
        # Handle pass_type change or profile change to refresh approvers if not explicitly provided
        need_refresh = 'pass_type' in vals or 'approval_profile_id' in vals
        approvers_provided = 'current_approver_ids' in vals
        if need_refresh and not approvers_provided:
            Profile = self.env['hr.gate.pass.approval.profile']
            for rec in self:
                profile = rec.approval_profile_id
                if not profile and rec.pass_type:
                    profile = Profile.search([('pass_type', '=', rec.pass_type)], limit=1)
                    if profile:
                        super(HrGatePass, rec).write({'approval_profile_id': profile.id})
                users = rec._get_users_from_profile(profile)
                super(HrGatePass, rec).write({'current_approver_ids': [(6, 0, users.ids)]})
        return res
    
    
    @api.depends('line_ids.product_uom_qty', 'line_ids.product_id')
    def _compute_value_total(self):
        for rec in self:
            total = 0.0
            for l in rec.line_ids:
                total += (l.product_id.lst_price or 0.0) * (l.product_uom_qty or 0.0)
            rec.value_total = total

    

    @api.onchange('host_employee_id')
    def _onchange_host_employee_id(self):
        for rec in self:
            rec.department_id = rec.host_employee_id.department_id.id if rec.host_employee_id and rec.host_employee_id.department_id else False

    # State actions
    def _log_action(self, action, remarks=None):
        for rec in self:
            self.env['hr.gate.log'].create({
                'gate_pass_id': rec.id,
                'gate_id': rec.gate_id.id if rec.gate_id else False,
                'action': action,
                'by_user_id': self.env.user.id,
                'remarks': remarks or '',
            })

    def action_submit(self):
        for rec in self:
            if rec.pass_type == 'material' and not rec.line_ids:
                raise exceptions.UserError(_('Material pass must contain at least one item.'))
            if rec.is_returnable and not rec.expected_return_datetime:
                raise exceptions.UserError(_('Expected return date is required for returnable passes.'))
            # Send email notification to current approvers
            if rec.current_approver_ids:
                template = self.env.ref('hr_gate_pass.mail_template_gatepass_submit')
                for approver in rec.current_approver_ids:
                    template.send_mail(
                        rec.id,
                        force_send=True,
                        email_values={
                            'recipient_ids': [(4, approver.partner_id.id)],
                            'email_to': approver.email,
                        }
                    )
            rec.state = 'to_approve'
            rec._log_action('submitted', remarks='Submitted by %s' % (self.env.user.name or ''))
        return True

    def action_approve(self):
        for rec in self:
            # Basic approval: if no profile, allow if user in manager/hr/admin groups
            if not (
                self.env.user.has_group('hr_gate_pass.group_gatepass_manager')
                # or self.env.user.has_group('hr_gate_pass.group_gatepass_hr')
                or self.env.user.has_group('hr_gate_pass.group_gatepass_admin')
            ):
                raise exceptions.AccessError(_('You are not allowed to approve.'))
            rec.state = 'approved'
            rec._log_action('approved', remarks='Approved by %s' % (self.env.user.name or ''))
        return True

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
            rec._log_action('rejected', remarks='Rejected by %s' % (self.env.user.name or ''))
        return True

    def action_issue(self):
        for rec in self:
            if rec.state != 'approved':
                raise exceptions.UserError(_('Only approved passes can be issued.'))
            now = fields.Datetime.now()
            rec.issued_datetime = now
            rec.state = 'issued'
            if not rec.qr_token:
                rec._generate_qr_token()
            rec._log_action('issued', remarks='Issued at %s' % rec._format_local_dt(now))
        return True

    def action_checkout(self):
        for rec in self:
            if rec.state not in ('issued', 'approved'):
                raise exceptions.UserError(_('Only issued passes can be checked out.'))
            now = fields.Datetime.now()
            rec.checked_out_datetime = now
            rec.state = 'checked_out'
            # rec._log_action('scanned_out', remarks='Checked out')
            rec._log_action('checked_out', remarks='Checked out at %s' % rec._format_local_dt(now))
        return True

    def action_return(self):
        for rec in self:
            if rec.state != 'checked_out':
                raise exceptions.UserError(_('Only checked out passes can be returned.'))
            now = fields.Datetime.now()
            rec.returned_datetime = now
            rec.state = 'returned'
            rec._log_action('returned', remarks='Returned at %s' % rec._format_local_dt(now))
        return True

    def action_close(self):
        for rec in self:
            now = fields.Datetime.now()
            rec.end_datetime = now
            rec.state = 'closed'
            rec._log_action('closed', remarks='Closed at %s' % rec._format_local_dt(now))
        return True

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
            rec._log_action('canceled', remarks='to canceled, reason: ' + (rec.reason or ''))
        return True

    # Back one state and reset to draft
    def action_back(self):
        mapping = {
            'issued': 'approved',
            'checked_out': 'issued',
            'returned': 'checked_out',
            'closed': 'returned',
            'rejected': 'to_approve',
            'cancel': 'draft',
        }
        for rec in self:
            prev = mapping.get(rec.state)
            # Special case: for non-returnable passes, going back from 'closed'
            # should jump to 'checked_out' (skip 'returned').
            if rec.state == 'closed' and not rec.is_returnable:
                prev = 'checked_out'
            if not prev:
                continue
            # Adjust timestamps when moving back
            if rec.state in ('issued', 'checked_out', 'returned', 'closed'):
                if rec.state == 'issued':
                    rec.issued_datetime = False
                elif rec.state == 'checked_out':
                    rec.checked_out_datetime = False
                elif rec.state == 'returned':
                    rec.returned_datetime = False
                elif rec.state == 'closed':
                    # no dedicated timestamp; keep returned_datetime as-is
                    pass
            rec.state = prev
            rec._log_action('reverted', remarks='to %s' % prev)
        return True

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            # Clean operational timestamps on full reset
            rec.issued_datetime = False
            rec.checked_out_datetime = False
            rec.returned_datetime = False
            rec._log_action('reset', remarks='to draft')
        return True

    # QR Generation & validation
    def _qr_secret(self):
        # Use system parameter as secret; fallback to dbuuid.
        IrConfig = self.env['ir.config_parameter'].sudo()
        secret = IrConfig.get_param('hr_gate_pass.qr_secret') or IrConfig.get_param('database.uuid') or 'odoo-secret'
        return str(secret)

    def _generate_qr_token(self):
        for rec in self:
            payload = str(rec.id)
            secret = (self._qr_secret() or '').encode()
            signature = hmac.new(secret, payload.encode(), hashlib.sha256).digest()
            token = payload + '.' + base64.urlsafe_b64encode(signature).decode().rstrip('=')
            rec.qr_token = token
            rec.qr_token_expiry = fields.Datetime.now() + timedelta(days=7)
            rec._generate_qr_image()

    def _verify_qr_token(self, token):
        self.ensure_one()
        if not token or not self.qr_token or token != self.qr_token:
            return False
        if self.qr_token_expiry and fields.Datetime.now() > self.qr_token_expiry:
            return False
        # recompute signature
        try:
            rec_id_str, signature_b64 = token.split('.')
            secret = (self._qr_secret() or '').encode()
            expected_sig = hmac.new(secret, rec_id_str.encode(), hashlib.sha256).digest()
            expected_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')
            return hmac.compare_digest(signature_b64, expected_b64)
        except Exception:
            return False

    def _generate_qr_image(self):
        if qrcode is None:
            return False
        for rec in self:
            buf = BytesIO()
            qrdata = rec.qr_token or ''
            qr = qrcode.QRCode(version=1, box_size=4, border=2)
            qr.add_data(qrdata)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(buf, 'PNG')
            rec.qr_image = base64.b64encode(buf.getvalue())
        return True

    # Cron
    def _cron_check_overdue_returns(self):
        domain = [
            ('is_returnable', '=', True),
            ('state', 'in', ('issued', 'checked_out')),
            ('expected_return_datetime', '<', fields.Datetime.now()),
        ]
        overdue = self.search(domain)
        for rec in overdue:
            rec.activity_schedule('mail.mail_activity_data_todo', summary=_('Overdue Return'), note=_('Please ensure return of items for %s') % rec.name)
        return True

    # UI button helpers
    def action_generate_qr(self):
        for rec in self:
            if not rec.qr_token:
                rec._generate_qr_token()
                rec._log_action('qr_generated')
        return True

    def action_view_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Logs'),
            'res_model': 'hr.gate.log',
            'view_mode': 'list,form',
            'domain': [('gate_pass_id', '=', self.id)],
            'target': 'current',
        }

    def action_print(self):
        self.ensure_one()
        report_action = self.env.ref('hr_gate_pass.action_report_gate_pass_full')
        # log print action
        self._log_action('printed')
        return report_action.report_action(self)
