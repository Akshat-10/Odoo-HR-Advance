# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError


class MonitoringQRController(http.Controller):
    @http.route(['/ehs/monitoring/scan'], type='http', auth='user', website=True, csrf=False)
    def scan(self, qr=None, permit_model=None, permit_id=None, **kwargs):
        if not qr or not permit_model or not permit_id:
            return request.render('ehs_monitoring_areas_link.template_qr_error', {'message': 'Missing parameters'})

        # Resolve scan QR to permit+area
        QR = request.env['permit.monitor.qr'].sudo()
        qr_rec = QR.search([('qr_code', '=', qr), ('permit_model', '=', permit_model), ('permit_res_id', '=', int(permit_id))], limit=1)
        if not qr_rec:
            return request.render('ehs_monitoring_areas_link.template_qr_error', {'message': 'Invalid or unknown QR code'})

        area = qr_rec.area_id

        # Check existing open line
        Line_public = request.env['permit.monitoring.line']
        existing = Line_public.search([
            ('permit_model', '=', permit_model),
            ('permit_res_id', '=', int(permit_id)),
            ('monitoring_area_id', '=', area.id),
            ('state', '=', 'open')
        ], limit=1)
        if existing:
            return request.redirect('/web#id=%s&view_type=form&model=permit.monitoring.line' % existing.id)

        # Create new line for this user
        try:
            new_line = Line_public.create({
                'permit_model': permit_model,
                'permit_res_id': int(permit_id),
                'monitoring_area_id': area.id,
            })
        except AccessError:
            return request.render('ehs_monitoring_areas_link.template_qr_error', {'message': 'You do not have access to create monitoring lines'})

        return request.redirect('/web#id=%s&view_type=form&model=permit.monitoring.line' % new_line.id)
