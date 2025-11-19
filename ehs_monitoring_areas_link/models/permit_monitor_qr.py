# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import random
import string
import base64
from io import BytesIO

try:
    import qrcode
except Exception:
    qrcode = None


class PermitMonitorQR(models.Model):
    _name = 'permit.monitor.qr'
    _description = 'Permit Monitoring QR'
    _rec_name = 'display_name'
    _check_company_auto = True
    _sql_constraints = [
        ('code_unique', 'unique(qr_code)', 'QR Code must be unique.'),
        ('permit_area_unique', 'unique(permit_model,permit_res_id,area_id)', 'Only one QR record per permit and area.'),
    ]

    permit_model = fields.Selection([
        ('work.heights.permit', 'Work at Heights'),
        ('daily.permit.work', 'Daily Permit Work'),
        ('hot.work.permit', 'Hot Work'),
        ('energized.work.permit', 'Energized Work'),
    ], required=True, index=True)
    permit_res_id = fields.Integer(required=True, index=True)
    area_id = fields.Many2one('monitoring.areas', string='Monitoring Record', required=True, ondelete='restrict', index=True, check_company=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    qr_code = fields.Char(string='Scan Code', readonly=True, index=True, copy=False)
    qr_image = fields.Binary(string='Scan QR Code', compute='_compute_qr_image', store=False)
    display_name = fields.Char(compute='_compute_display_name', store=False)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.permit_model}-{rec.permit_res_id} / {rec.area_id.name or ''}"

    def _generate_code(self, length=10):
        alphabet = string.ascii_uppercase + string.digits
        for _ in range(10):
            code = ''.join(random.choices(alphabet, k=length))
            if not self.search_count([('qr_code', '=', code)]):
                return code
        return ''.join(random.choices(alphabet, k=length))

    @api.model_create_multi
    def create(self, vals_list):
        Area = self.env['monitoring.areas']
        for vals in vals_list:
            if vals.get('area_id'):
                area = Area.browse(vals['area_id'])
                if area.company_id:
                    vals['company_id'] = area.company_id.id
            else:
                vals.setdefault('company_id', self.env.company.id)
            if not vals.get('qr_code'):
                vals['qr_code'] = self._generate_code()
        return super().create(vals_list)

    def rotate_code(self):
        for rec in self:
            rec.write({'qr_code': self._generate_code()})

    def _compute_qr_image(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        for rec in self:
            if not (qrcode and rec.qr_code and base_url):
                rec.qr_image = False
                continue
            url = f"{base_url}/ehs/monitoring/scan?qr={rec.qr_code}&permit_model={rec.permit_model}&permit_id={rec.permit_res_id}"
            buf = BytesIO()
            qr = qrcode.QRCode(version=1, box_size=4, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(buf, 'PNG')
            rec.qr_image = base64.b64encode(buf.getvalue())

    @api.constrains('area_id', 'company_id')
    def _check_area_company(self):
        for rec in self:
            if rec.area_id and rec.area_id.company_id != rec.company_id:
                raise ValidationError(_('QR record company must match the monitoring record company.'))
