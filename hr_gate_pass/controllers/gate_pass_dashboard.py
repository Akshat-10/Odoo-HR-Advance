# controllers/gate_pass_dashboard.py
from odoo import http
from odoo.http import request
import json


class GatePassDashboardController(http.Controller):

    @http.route('/gate_pass/dashboard_data', type='json', auth='user')
    def get_dashboard_data(self):
        """Get all dashboard data for Gate Pass KPIs and charts"""
        try:
            # Get gate pass model
            gate_pass_obj = request.env['hr.gate.pass']

            # Total counts
            total_passes = gate_pass_obj.search_count([])
            active_passes = gate_pass_obj.search_count([('state', 'in', ['approved', 'in_progress'])])
            pending_approvals = gate_pass_obj.search_count([('state', '=', 'pending')])
            expired_passes = gate_pass_obj.search_count([('state', '=', 'expired')])

            # State distribution
            states_data = gate_pass_obj.read_group(
                [], ['state'], ['state']
            )
            state_chart = {
                'labels': [item['state'] for item in states_data],
                'data': [item['state_count'] for item in states_data]
            }

            # EHS Permit Type distribution
            ehs_data = gate_pass_obj.read_group(
                [('ehs_permit_type', '!=', False)],
                ['ehs_permit_type'],
                ['ehs_permit_type']
            )
            ehs_chart = {
                'labels': [item['ehs_permit_type'] for item in ehs_data],
                'data': [item['ehs_permit_type_count'] for item in ehs_data]
            }

            # Pass Type distribution
            pass_type_data = gate_pass_obj.read_group(
                [], ['pass_type'], ['pass_type']
            )
            pass_type_chart = {
                'labels': [item['pass_type'].replace('_', ' ').title() if item['pass_type'] else 'Not Set' for item in
                           pass_type_data],
                'data': [item['pass_type_count'] for item in pass_type_data]
            }

            # Department distribution
            dept_data = gate_pass_obj.read_group(
                [('department_id', '!=', False)],
                ['department_id'],
                ['department_id']
            )
            dept_chart = {
                'labels': [item['department_id'][1] if item['department_id'] else 'No Department' for item in
                           dept_data],
                'data': [item['department_id_count'] for item in dept_data]
            }

            # Location distribution (assuming location_id field exists)
            location_data = []
            try:
                location_data = gate_pass_obj.read_group(
                    [('location_id', '!=', False)],
                    ['location_id'],
                    ['location_id']
                )
            except:
                pass

            location_chart = {
                'labels': [item['location_id'][1] if item['location_id'] else 'No Location' for item in location_data],
                'data': [item['location_id_count'] for item in location_data]
            }

            # Recent activity - last 7 days
            from datetime import datetime, timedelta
            week_ago = datetime.now() - timedelta(days=7)
            recent_passes = gate_pass_obj.search_count([
                ('create_date', '>=', week_ago.strftime('%Y-%m-%d'))
            ])

            # Monthly trend (last 6 months)
            monthly_data = []
            for i in range(6):
                month_start = datetime.now().replace(day=1) - timedelta(days=30 * i)
                month_end = month_start.replace(day=28) + timedelta(days=4)
                month_end = month_end.replace(day=1) - timedelta(days=1)

                count = gate_pass_obj.search_count([
                    ('create_date', '>=', month_start.strftime('%Y-%m-%d')),
                    ('create_date', '<=', month_end.strftime('%Y-%m-%d'))
                ])

                monthly_data.append({
                    'month': month_start.strftime('%b %Y'),
                    'count': count
                })

            monthly_data.reverse()

            return {
                'success': True,
                'kpis': {
                    'total_passes': total_passes,
                    'active_passes': active_passes,
                    'pending_approvals': pending_approvals,
                    'expired_passes': expired_passes,
                    'recent_passes': recent_passes
                },
                'charts': {
                    'state': state_chart,
                    'ehs_permit_type': ehs_chart,
                    'pass_type': pass_type_chart,
                    'department': dept_chart,
                    'location': location_chart,
                    'monthly_trend': {
                        'labels': [item['month'] for item in monthly_data],
                        'data': [item['count'] for item in monthly_data]
                    }
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }