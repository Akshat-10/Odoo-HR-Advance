# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ehs_monitoring_time_limit_minutes = fields.Integer(string='Monitoring Line Time Limit (minutes)', default=30, config_parameter='ehs_monitoring.time_limit_minutes')
    # add a default group - "ehs_monitoring_areas_link.group_ehs_monitoring_admin" in ehs_monitoring_admin_group_id field
    # guard against the group not existing yet (e.g. during module install/upgrade before xml data loaded)
    def _default_ehs_monitoring_admin_group_id(self):
        group = self.env.ref('ehs_monitoring_areas_link.group_ehs_monitoring_admin', raise_if_not_found=False)
        return group.id if group else False

    ehs_monitoring_admin_group_id = fields.Many2one(
        'res.groups',
        string='Admins Group for Notifications',
        config_parameter='ehs_monitoring.admin_group_id',
        default=_default_ehs_monitoring_admin_group_id,
        help='Group whose users receive monitoring expiry / warning notifications.'
    )
    ehs_monitoring_expiry_warning_minutes = fields.Integer(
        string='Monitoring Expiry Warning (minutes)',
        default=15,
        config_parameter='ehs_monitoring.expiry_warning_minutes',
        help='Send a near-expiry warning this many minutes before expiry_datetime.'
    )
