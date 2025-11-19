# -*- coding: utf-8 -*-
from odoo import api, fields, models


class WorkHeightsPermit(models.Model):
    _inherit = 'work.heights.permit'

    monitoring_area_id = fields.Many2one(
        'monitoring.areas',
        string='Monitoring Area',
        ondelete='restrict',
        domain="[('company_id', 'in', allowed_company_ids)]",
        check_company=True,
    )
    monitoring_area_qr_value = fields.Char(string='QR Code', related='monitoring_area_id.qr_value', readonly=True)
    monitoring_area_qr_image = fields.Binary(string='Area QR Code', related='monitoring_area_id.qr_image', readonly=True)
    monitoring_scan_url = fields.Char(string='Monitoring Scan URL', compute='_compute_monitoring_scan_url')
    monitor_qr_id = fields.Many2one('permit.monitor.qr', string='Permit Scan QR', compute='_compute_monitor_qr', store=False)
    monitoring_scan_qr = fields.Binary(string='Scan QR', related='monitor_qr_id.qr_image', readonly=True)
    monitoring_line_ids = fields.One2many(
        'permit.monitoring.line',
        compute='_compute_monitoring_lines',
        string='Monitoring Lines',
        compute_sudo=True,
        help='Computed for performance and avoid inverse recursion')

    def _compute_monitoring_lines(self):
        Line = self.env['permit.monitoring.line']
        for rec in self:
            rec.monitoring_line_ids = Line.search([
                ('permit_model', '=', 'work.heights.permit'),
                ('permit_res_id', '=', rec.id)
            ])

    def _compute_monitoring_scan_url(self):
        base = '/ehs/monitoring/scan'
        for rec in self:
            qr = rec.monitor_qr_id.qr_code if rec.monitor_qr_id else ''
            rec.monitoring_scan_url = f"{base}?qr={qr}&permit_model=work.heights.permit&permit_id={rec.id}" if qr and rec.id else False

    def _compute_monitor_qr(self):
        QR = self.env['permit.monitor.qr'].sudo()
        for rec in self:
            if rec.monitoring_area_id and rec.id:
                qr_rec = QR.search([
                    ('permit_model', '=', 'work.heights.permit'),
                    ('permit_res_id', '=', rec.id),
                    ('area_id', '=', rec.monitoring_area_id.id)
                ], limit=1)
                if not qr_rec:
                    qr_rec = QR.create({
                        'permit_model': 'work.heights.permit',
                        'permit_res_id': rec.id,
                        'area_id': rec.monitoring_area_id.id,
                    })
                rec.monitor_qr_id = qr_rec
            else:
                rec.monitor_qr_id = False

    def action_open_monitoring_scan(self):
        self.ensure_one()
        # If there is an open line for this permit & area, open it instead of scanning/creating
        if self.monitoring_area_id:
            line = self.env['permit.monitoring.line'].search([
                ('permit_model', '=', 'work.heights.permit'),
                ('permit_res_id', '=', self.id),
                ('monitoring_area_id', '=', self.monitoring_area_id.id),
                ('state', '=', 'open')
            ], limit=1)
            if line:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'permit.monitoring.line',
                    'res_id': line.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        return {
            'type': 'ir.actions.act_url',
            'url': self.monitoring_scan_url,
            'target': 'new',
        }

    def action_open_monitoring_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Monitoring Lines',
            'res_model': 'permit.monitoring.line',
            'view_mode': 'list,form',
            'domain': [
                ('permit_model', '=', 'work.heights.permit'),
                ('permit_res_id', '=', self.id),
            ],
            'context': {
                'default_permit_model': 'work.heights.permit',
                'default_permit_res_id': self.id,
                'search_default_permit_model': 'work.heights.permit',
            },
            'target': 'current'
        }


class DailyPermitWork(models.Model):
    _inherit = 'daily.permit.work'

    monitoring_area_id = fields.Many2one(
        'monitoring.areas',
        string='Monitoring Area',
        ondelete='restrict',
        domain="[('company_id', 'in', allowed_company_ids)]",
        check_company=True,
    )
    monitoring_area_qr_value = fields.Char(string='QR Code', related='monitoring_area_id.qr_value', readonly=True)
    monitoring_area_qr_image = fields.Binary(string='Area QR Code', related='monitoring_area_id.qr_image', readonly=True)
    monitoring_scan_url = fields.Char(string='Monitoring Scan URL', compute='_compute_monitoring_scan_url')
    monitor_qr_id = fields.Many2one('permit.monitor.qr', string='Permit Scan QR', compute='_compute_monitor_qr', store=False)
    monitoring_scan_qr = fields.Binary(string='Scan QR', related='monitor_qr_id.qr_image', readonly=True)
    monitoring_line_ids = fields.One2many('permit.monitoring.line', compute='_compute_monitoring_lines', string='Monitoring Lines', compute_sudo=True)

    def _compute_monitoring_lines(self):
        Line = self.env['permit.monitoring.line']
        for rec in self:
            rec.monitoring_line_ids = Line.search([
                ('permit_model', '=', 'daily.permit.work'),
                ('permit_res_id', '=', rec.id)
            ])

    def _compute_monitoring_scan_url(self):
        base = '/ehs/monitoring/scan'
        for rec in self:
            qr = rec.monitor_qr_id.qr_code if rec.monitor_qr_id else ''
            rec.monitoring_scan_url = f"{base}?qr={qr}&permit_model=daily.permit.work&permit_id={rec.id}" if qr and rec.id else False

    def _compute_monitor_qr(self):
        QR = self.env['permit.monitor.qr'].sudo()
        for rec in self:
            if rec.monitoring_area_id and rec.id:
                qr_rec = QR.search([
                    ('permit_model', '=', 'daily.permit.work'),
                    ('permit_res_id', '=', rec.id),
                    ('area_id', '=', rec.monitoring_area_id.id)
                ], limit=1)
                if not qr_rec:
                    qr_rec = QR.create({
                        'permit_model': 'daily.permit.work',
                        'permit_res_id': rec.id,
                        'area_id': rec.monitoring_area_id.id,
                    })
                rec.monitor_qr_id = qr_rec
            else:
                rec.monitor_qr_id = False

    def action_open_monitoring_scan(self):
        self.ensure_one()
        if self.monitoring_area_id:
            line = self.env['permit.monitoring.line'].search([
                ('permit_model', '=', 'daily.permit.work'),
                ('permit_res_id', '=', self.id),
                ('monitoring_area_id', '=', self.monitoring_area_id.id),
                ('state', '=', 'open')
            ], limit=1)
            if line:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'permit.monitoring.line',
                    'res_id': line.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        return {
            'type': 'ir.actions.act_url',
            'url': self.monitoring_scan_url,
            'target': 'new',
        }

    def action_open_monitoring_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Monitoring Lines',
            'res_model': 'permit.monitoring.line',
            'view_mode': 'list,form',
            'domain': [
                ('permit_model', '=', 'daily.permit.work'),
                ('permit_res_id', '=', self.id),
            ],
            'context': {
                'default_permit_model': 'daily.permit.work',
                'default_permit_res_id': self.id,
                'search_default_permit_model': 'daily.permit.work',
            },
            'target': 'current'
        }


class HotWorkPermit(models.Model):
    _inherit = 'hot.work.permit'

    monitoring_area_id = fields.Many2one(
        'monitoring.areas',
        string='Monitoring Area',
        ondelete='restrict',
        domain="[('company_id', 'in', allowed_company_ids)]",
        check_company=True,
    )
    monitoring_area_qr_value = fields.Char(string='QR Code', related='monitoring_area_id.qr_value', readonly=True)
    monitoring_area_qr_image = fields.Binary(string='Area QR Code', related='monitoring_area_id.qr_image', readonly=True)
    monitoring_scan_url = fields.Char(string='Monitoring Scan URL', compute='_compute_monitoring_scan_url')
    monitor_qr_id = fields.Many2one('permit.monitor.qr', string='Permit Scan QR', compute='_compute_monitor_qr', store=False)
    monitoring_scan_qr = fields.Binary(string='Scan QR', related='monitor_qr_id.qr_image', readonly=True)
    monitoring_line_ids = fields.One2many('permit.monitoring.line', compute='_compute_monitoring_lines', string='Monitoring Lines', compute_sudo=True)

    def _compute_monitoring_lines(self):
        Line = self.env['permit.monitoring.line']
        for rec in self:
            rec.monitoring_line_ids = Line.search([
                ('permit_model', '=', 'hot.work.permit'),
                ('permit_res_id', '=', rec.id)
            ])

    def _compute_monitoring_scan_url(self):
        base = '/ehs/monitoring/scan'
        for rec in self:
            qr = rec.monitor_qr_id.qr_code if rec.monitor_qr_id else ''
            rec.monitoring_scan_url = f"{base}?qr={qr}&permit_model=hot.work.permit&permit_id={rec.id}" if qr and rec.id else False

    def _compute_monitor_qr(self):
        QR = self.env['permit.monitor.qr'].sudo()
        for rec in self:
            if rec.monitoring_area_id and rec.id:
                qr_rec = QR.search([
                    ('permit_model', '=', 'hot.work.permit'),
                    ('permit_res_id', '=', rec.id),
                    ('area_id', '=', rec.monitoring_area_id.id)
                ], limit=1)
                if not qr_rec:
                    qr_rec = QR.create({
                        'permit_model': 'hot.work.permit',
                        'permit_res_id': rec.id,
                        'area_id': rec.monitoring_area_id.id,
                    })
                rec.monitor_qr_id = qr_rec
            else:
                rec.monitor_qr_id = False

    def action_open_monitoring_scan(self):
        self.ensure_one()
        if self.monitoring_area_id:
            line = self.env['permit.monitoring.line'].search([
                ('permit_model', '=', 'hot.work.permit'),
                ('permit_res_id', '=', self.id),
                ('monitoring_area_id', '=', self.monitoring_area_id.id),
                ('state', '=', 'open')
            ], limit=1)
            if line:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'permit.monitoring.line',
                    'res_id': line.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        return {
            'type': 'ir.actions.act_url',
            'url': self.monitoring_scan_url,
            'target': 'new',
        }

    def action_open_monitoring_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Monitoring Lines',
            'res_model': 'permit.monitoring.line',
            'view_mode': 'list,form',
            'domain': [
                ('permit_model', '=', 'hot.work.permit'),
                ('permit_res_id', '=', self.id),
            ],
            'context': {
                'default_permit_model': 'hot.work.permit',
                'default_permit_res_id': self.id,
                'search_default_permit_model': 'hot.work.permit',
            },
            'target': 'current'
        }


class EnergizedWorkPermit(models.Model):
    _inherit = 'energized.work.permit'

    monitoring_area_id = fields.Many2one(
        'monitoring.areas',
        string='Monitoring Area',
        ondelete='restrict',
        domain="[('company_id', 'in', allowed_company_ids)]",
        check_company=True,
    )
    monitoring_area_qr_value = fields.Char(string='QR Code', related='monitoring_area_id.qr_value', readonly=True)
    monitoring_area_qr_image = fields.Binary(string='Area QR Code', related='monitoring_area_id.qr_image', readonly=True)
    monitoring_scan_url = fields.Char(string='Monitoring Scan URL', compute='_compute_monitoring_scan_url')
    monitor_qr_id = fields.Many2one('permit.monitor.qr', string='Permit Scan QR', compute='_compute_monitor_qr', store=False)
    monitoring_scan_qr = fields.Binary(string='Scan QR', related='monitor_qr_id.qr_image', readonly=True)
    monitoring_line_ids = fields.One2many('permit.monitoring.line', compute='_compute_monitoring_lines', string='Monitoring Lines', compute_sudo=True)

    def _compute_monitoring_lines(self):
        Line = self.env['permit.monitoring.line']
        for rec in self:
            rec.monitoring_line_ids = Line.search([
                ('permit_model', '=', 'energized.work.permit'),
                ('permit_res_id', '=', rec.id)
            ])

    def _compute_monitoring_scan_url(self):
        base = '/ehs/monitoring/scan'
        for rec in self:
            qr = rec.monitor_qr_id.qr_code if rec.monitor_qr_id else ''
            rec.monitoring_scan_url = f"{base}?qr={qr}&permit_model=energized.work.permit&permit_id={rec.id}" if qr and rec.id else False

    def _compute_monitor_qr(self):
        QR = self.env['permit.monitor.qr'].sudo()
        for rec in self:
            if rec.monitoring_area_id and rec.id:
                qr_rec = QR.search([
                    ('permit_model', '=', 'energized.work.permit'),
                    ('permit_res_id', '=', rec.id),
                    ('area_id', '=', rec.monitoring_area_id.id)
                ], limit=1)
                if not qr_rec:
                    qr_rec = QR.create({
                        'permit_model': 'energized.work.permit',
                        'permit_res_id': rec.id,
                        'area_id': rec.monitoring_area_id.id,
                    })
                rec.monitor_qr_id = qr_rec
            else:
                rec.monitor_qr_id = False

    def action_open_monitoring_scan(self):
        self.ensure_one()
        if self.monitoring_area_id:
            line = self.env['permit.monitoring.line'].search([
                ('permit_model', '=', 'energized.work.permit'),
                ('permit_res_id', '=', self.id),
                ('monitoring_area_id', '=', self.monitoring_area_id.id),
                ('state', '=', 'open')
            ], limit=1)
            if line:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'permit.monitoring.line',
                    'res_id': line.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        return {
            'type': 'ir.actions.act_url',
            'url': self.monitoring_scan_url,
            'target': 'new',
        }

    def action_open_monitoring_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Monitoring Lines',
            'res_model': 'permit.monitoring.line',
            'view_mode': 'list,form',
            'domain': [
                ('permit_model', '=', 'energized.work.permit'),
                ('permit_res_id', '=', self.id),
            ],
            'context': {
                'default_permit_model': 'energized.work.permit',
                'default_permit_res_id': self.id,
                'search_default_permit_model': 'energized.work.permit',
            },
            'target': 'current'
        }
