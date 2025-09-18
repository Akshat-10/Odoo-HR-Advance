# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ehs_monitoring_time_limit_minutes = fields.Integer(string='Monitoring Line Time Limit (minutes)', default=30, config_parameter='ehs_monitoring.time_limit_minutes')
    #add a default group - "ehs_monitoring_areas_link.group_ehs_monitoring_admin" in ehs_monitoring_admin_group_id field
    ehs_monitoring_admin_group_id = fields.Many2one('res.groups', string='Admins Group for Notifications', config_parameter='ehs_monitoring.admin_group_id', default=lambda self: self.env.ref('ehs_monitoring_areas_link.group_ehs_monitoring_admin', raise_if_not_found=False).id)
    ehs_monitoring_expiry_warning_minutes = fields.Integer(
        string='Monitoring Expiry Warning (minutes)',
        default=15,
        config_parameter='ehs_monitoring.expiry_warning_minutes',
        help='Send a near-expiry warning this many minutes before expiry_datetime.'
    )
