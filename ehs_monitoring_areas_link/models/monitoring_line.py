# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class PermitMonitoringLine(models.Model):
    _name = 'permit.monitoring.line'
    _description = 'Work Permit Monitoring Line'
    _order = 'name desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    name = fields.Integer(string='Serial No.', readonly=True)
    permit_model = fields.Selection([
        ('work.heights.permit', 'Work at Heights'),
        ('daily.permit.work', 'Daily Permit Work'),
        ('hot.work.permit', 'Hot Work'),
        ('energized.work.permit', 'Energized Work'),
    ], string='Permit Type', required=True, index=True)
    permit_res_id = fields.Integer(string='Permit Record ID', required=True, index=True)
    permit_ref = fields.Reference(selection='_get_permit_models', string='Permit', compute='_compute_permit_ref', store=False)

    # Convenience direct links (computed) to the concrete permit record
    work_heights_permit_id = fields.Many2one('work.heights.permit', string='Work at Heights Permit', compute='_compute_permit_m2os', store=False, readonly=True)
    daily_permit_work_id = fields.Many2one('daily.permit.work', string='Daily Permit Work', compute='_compute_permit_m2os', store=False, readonly=True)
    hot_work_permit_id = fields.Many2one('hot.work.permit', string='Hot Work Permit', compute='_compute_permit_m2os', store=False, readonly=True)
    energized_work_permit_id = fields.Many2one('energized.work.permit', string='Energized Work Permit', compute='_compute_permit_m2os', store=False, readonly=True)

    monitoring_area_id = fields.Many2one('monitoring.areas', string='Monitoring Record', required=True, ondelete='restrict', index=True, check_company=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )

    user_id = fields.Many2one('res.users', string='Logged User', default=lambda self: self.env.user, tracking=True, index=True, readonly=True)
    datetime = fields.Datetime(string='Time and Date', default=lambda self: fields.Datetime.now(), tracking=True, readonly=True)

    input_checked = fields.Html(string='What Checked', sanitize=True)
    compliance_status = fields.Selection([
        ('standard', 'Work going as per standard'),
        ('not_standard', 'Work not going as per standard'),
    ], string='Compliance', default='standard', required=True, tracking=True)
    call_meeting = fields.Boolean(string='Call Meeting', help='Triggered when work is not as per standard', tracking=True)
    action_taken = fields.Text(string='Action Taken')
    attachment_ids = fields.Many2many('ir.attachment', 'permit_monitoring_attachment_rel', 'line_id', 'attachment_id', string='Attachments')
    remarks = fields.Html(string='Remarks', sanitize=True)

    state = fields.Selection([
        # ('draft', 'Draft'),
        ('open', 'Open'),
        ('done', 'Done'),
        ('expired', 'Expired'),
        ('cancel', 'Cancelled'),
    ], default='open', tracking=True)

    expiry_datetime = fields.Datetime(string='Expiry At', index=True)
    time_limit_minutes = fields.Integer(string='Time Limit (min)', help='Copied from configuration at creation for traceability')

    # Notification flags to avoid duplicate emails
    meeting_mail_sent = fields.Boolean(string='Meeting Mail Sent', default=False, readonly=True)
    expiry_warn_mail_sent = fields.Boolean(string='Expiry Warning Mail Sent', default=False, readonly=True)
    expired_mail_sent = fields.Boolean(string='Expired Mail Sent', default=False, readonly=True)

    _sql_constraints = [
        ('serial_unique_per_group', 'unique(permit_model, monitoring_area_id, name)', 'Serial number must be unique per permit type and monitoring area.'),
    ]

    def _get_permit_models(self):
        return [
            ('work.heights.permit', 'Work at Heights'),
            ('daily.permit.work', 'Daily Permit Work'),
            ('hot.work.permit', 'Hot Work'),
            ('energized.work.permit', 'Energized Work'),
        ]

    @api.model_create_multi
    def create(self, vals_list):
        Param = self.env['ir.config_parameter'].sudo()
        for vals in vals_list:
            vals['company_id'] = self._resolve_company(vals)
            # Assign per-group incremental serial starting at 1 for each (permit_model, monitoring_area_id)
            if not vals.get('name'):
                permit_model = vals.get('permit_model')
                area_id = vals.get('monitoring_area_id')
                if permit_model and area_id:
                    last = self.search([
                        ('permit_model', '=', permit_model),
                        ('monitoring_area_id', '=', area_id),
                        ('company_id', '=', vals['company_id']),
                    ], order='name desc', limit=1)
                    next_no = (last.name or 0) + 1
                    vals['name'] = next_no
                else:
                    # Fallback if context is incomplete
                    vals['name'] = 1
            # Always ensure time_limit_minutes is set
            limit_min = int(Param.get_param('ehs_monitoring.time_limit_minutes', 30))
            vals.setdefault('time_limit_minutes', limit_min)
            # Set expiry if not provided
            if not vals.get('expiry_datetime'):
                vals['expiry_datetime'] = fields.Datetime.now() + timedelta(minutes=limit_min)
        recs = super().create(vals_list)
        # Do NOT auto trigger emails on create; emails are triggered when user explicitly sets both
        # compliance_status='not_standard' and call_meeting=True (handled in write())
        return recs

    def write(self, vals):
        if {'monitoring_area_id', 'permit_model', 'permit_res_id', 'company_id'} & set(vals.keys()):
            vals = dict(vals)
            vals.setdefault('company_id', self._resolve_company(vals))
        res = super().write(vals)
        # After write, check if non-compliance and call_meeting True to trigger mail once
        for rec in self:
            if (rec.compliance_status == 'not_standard' and rec.call_meeting and not rec.meeting_mail_sent):
                if rec._send_admin_mail('ehs_monitoring_areas_link.mail_template_monitoring_non_compliance'):
                    rec.meeting_mail_sent = True
                    # Log in chatter
                    rec.message_post(body=_('Non-compliance email sent to admins.'))
        return res

    def _resolve_company(self, vals):
        Area = self.env['monitoring.areas']
        if vals.get('monitoring_area_id'):
            area = Area.browse(vals['monitoring_area_id'])
            if area.company_id:
                return area.company_id.id
        permit_model = vals.get('permit_model')
        permit_res_id = vals.get('permit_res_id')
        if permit_model and permit_res_id:
            permit = self.env[permit_model].browse(permit_res_id)
            if permit and hasattr(permit, 'company_id') and permit.company_id:
                return permit.company_id.id
        return vals.get('company_id') or self.env.company.id

    def action_mark_done(self):
        for rec in self:
            rec.state = 'done'
        self._rotate_qr_for_lines(self)

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_set_draft(self):
        """Reset the line back to Draft. Admin-only button in views.

        Resets time-related fields and notification flags as requested.
        """
        for rec in self:
            rec.write({
                'state': 'open',
                # 'datetime': False,
                # 'expiry_datetime': False,
                # 'call_meeting': False,
                # 'action_taken': False,
                'meeting_mail_sent': False,
                'expiry_warn_mail_sent': False,
                'expired_mail_sent': False,
            })

    def _get_admin_emails(self):
        group_id = int(self.env['ir.config_parameter'].sudo().get_param('ehs_monitoring.admin_group_id') or 0)
        if not group_id:
            return []
        group = self.env['res.groups'].browse(group_id)
        return [u.email for u in group.users if u.email]

    def _send_admin_mail(self, template_xmlid):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template or not isinstance(template, type(self.env['mail.template'])):
            return False
        emails = self._get_admin_emails()
        email_to = ','.join(emails)
        if not email_to:
            return False
        template = template.sudo().with_context(lang=self.env.user.lang)
        template.send_mail(self.id, force_send=True, email_values={'email_to': email_to})
        return True

    @api.depends('permit_model', 'permit_res_id')
    def _compute_permit_ref(self):
        model_map = {
            'work.heights.permit': 'work.heights.permit',
            'daily.permit.work': 'daily.permit.work',
            'hot.work.permit': 'hot.work.permit',
            'energized.work.permit': 'energized.work.permit',
        }
        for rec in self:
            model = model_map.get(rec.permit_model)
            if model and rec.permit_res_id:
                rec.permit_ref = f"{model},{rec.permit_res_id}"
            else:
                rec.permit_ref = False

    @api.depends('permit_model', 'permit_res_id')
    def _compute_permit_m2os(self):
        for rec in self:
            rec.work_heights_permit_id = False
            rec.daily_permit_work_id = False
            rec.hot_work_permit_id = False
            rec.energized_work_permit_id = False

            if not rec.permit_model or not rec.permit_res_id:
                continue

            if rec.permit_model == 'work.heights.permit':
                rec.work_heights_permit_id = self.env['work.heights.permit'].browse(rec.permit_res_id).exists()
            elif rec.permit_model == 'daily.permit.work':
                rec.daily_permit_work_id = self.env['daily.permit.work'].browse(rec.permit_res_id).exists()
            elif rec.permit_model == 'hot.work.permit':
                rec.hot_work_permit_id = self.env['hot.work.permit'].browse(rec.permit_res_id).exists()
            elif rec.permit_model == 'energized.work.permit':
                rec.energized_work_permit_id = self.env['energized.work.permit'].browse(rec.permit_res_id).exists()

    @api.constrains('permit_model', 'permit_res_id', 'monitoring_area_id', 'state')
    def _check_no_parallel_open_line(self):
        for rec in self:
            if rec.state in ('open',):
                domain = [
                    ('id', '!=', rec.id),
                    ('permit_model', '=', rec.permit_model),
                    ('permit_res_id', '=', rec.permit_res_id),
                    ('monitoring_area_id', '=', rec.monitoring_area_id.id),
                    ('state', 'in', ['open'])
                ]
                if self.search_count(domain):
                    raise ValidationError(_('You cannot create a new monitoring line until the previous one is done or expired.'))

    @api.model
    def _cron_expire_overdue_lines(self):
        now = fields.Datetime.now()
        Param = self.env['ir.config_parameter'].sudo()
        warn_minutes = int(Param.get_param('ehs_monitoring.expiry_warning_minutes', 10))

        # 1) Send near-expiry warnings
        warn_deadline = now + timedelta(minutes=warn_minutes)
        warn_domain = [
            ('state', '=', 'open'),
            ('expiry_datetime', '>=', now),
            ('expiry_datetime', '<=', warn_deadline),
            ('expiry_warn_mail_sent', '=', False),
        ]
        to_warn = self.search(warn_domain)
        for rec in to_warn:
            if rec._send_admin_mail('ehs_monitoring_areas_link.mail_template_monitoring_expiry_warning'):
                rec.expiry_warn_mail_sent = True
                rec.message_post(body=_('Near-expiry warning email sent to admins.'))

        # 2) Expire overdue lines and notify
        expire_domain = [('state', '=', 'open'), ('expiry_datetime', '<', now)]
        to_expire = self.search(expire_domain)
        if to_expire:
            to_expire.write({'state': 'expired'})
            for rec in to_expire:
                if not rec.expired_mail_sent:
                    if rec._send_admin_mail('ehs_monitoring_areas_link.mail_template_monitoring_expired'):
                        rec.expired_mail_sent = True
                        rec.message_post(body=_('Expired email sent to admins.'))
            self._rotate_qr_for_lines(to_expire)

    def _rotate_qr_for_lines(self, lines):
        QR = self.env['permit.monitor.qr'].sudo()
        for rec in lines:
            qr_rec = QR.search([
                ('permit_model', '=', rec.permit_model),
                ('permit_res_id', '=', rec.permit_res_id),
                ('area_id', '=', rec.monitoring_area_id.id),
                ('company_id', '=', rec.company_id.id),
            ], limit=1)
            if qr_rec:
                qr_rec.rotate_code()

    @api.constrains('monitoring_area_id', 'company_id')
    def _check_monitoring_area_company(self):
        for rec in self:
            if rec.monitoring_area_id and rec.monitoring_area_id.company_id != rec.company_id:
                raise ValidationError(_('Monitoring line company must match the monitoring record company.'))

    @api.constrains('permit_model', 'permit_res_id', 'company_id')
    def _check_permit_company(self):
        for rec in self:
            if rec.permit_model and rec.permit_res_id:
                permit = self.env[rec.permit_model].browse(rec.permit_res_id)
                if permit and hasattr(permit, 'company_id') and permit.company_id and permit.company_id != rec.company_id:
                    raise ValidationError(_('Monitoring line company must match the permit company.'))
