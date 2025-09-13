# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import hmac
import hashlib
import base64

class GatePassController(http.Controller):
    @http.route(['/gatepass/scan', '/gatepass/scan/<string:token>'], type='json', auth='public', methods=['POST','GET'], csrf=False)
    def gatepass_scan(self, token=None, **kwargs):
        env = request.env
        if not token:
            token = kwargs.get('token')
        if not token:
            return {'ok': False, 'error': 'missing_token'}
        # token format: id.signature
        try:
            rec_id_str, signature = token.split('.')
            rec_id = int(rec_id_str)
        except Exception:
            return {'ok': False, 'error': 'invalid_token'}
        rec = env['hr.gate.pass'].sudo().browse(rec_id)
        if not rec.exists():
            return {'ok': False, 'error': 'not_found'}
        if not rec._verify_qr_token(token):
            return {'ok': False, 'error': 'invalid_signature'}
        # Simple state transition suggestion without committing yet
        result = {
            'ok': True,
            'id': rec.id,
            'name': rec.name,
            'state': rec.state,
            'pass_type': rec.pass_type,
        }
        return result
