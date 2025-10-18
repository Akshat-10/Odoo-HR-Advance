# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class HrContractSalaryOfferModal(http.Controller):

    @http.route('/salary_package/offer_lines', type='json', auth='public')
    def get_offer_lines(self, offer_id=None):
        """
        Returns a list of tuples matching the payroll modal shape:
        (label, valueText, code, sign, currency_position, currency_symbol)
        where sign is -1 for deduction, +1 for others.
        """
        datas = []
        if not offer_id:
            return {'datas': datas}

        # sudo to allow public access during portal flow; ensure safe fields only
        Offer = request.env['hr.contract.salary.offer'].sudo()
        offer = Offer.browse(int(offer_id))
        if not offer.exists():
            return {'datas': datas}

        currency = offer.currency_id or offer.company_id.currency_id
        symbol = currency.symbol or ''
        position = currency.position or 'after'

        # Read minimal fields from structure lines
        # Do not sort by id to avoid comparing NewId in onchanges; use sequence + code/name
        for line in offer.structure_line_ids.sorted(key=lambda l: (l.sequence or 0, (l.code or '').lower(), (l.name or '').lower())):
            sign = -1 if line.impact == 'deduction' else 1
            amount = abs(round(float(line.amount_monthly or 0.0), 2))
            datas.append((
                line.name or '',      # label
                amount,               # numeric; front-end will format if needed
                line.code or '',      # code (technical)
                sign,                 # sign or 'no_sign'
                position,             # currency position
                symbol,               # currency symbol
            ))
        return {'datas': datas}

