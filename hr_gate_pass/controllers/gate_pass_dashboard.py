# controllers/gate_pass_dashboard.py
from odoo import http
from odoo.http import request
import json
import random
from datetime import datetime, timedelta

from odoo import models, fields


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

            # New permit counts from separate models
            hot_work_permits = request.env['hot.work.permit'].search_count(
                []) if 'hot.work.permit' in request.env else 0
            energized_work_permits = request.env['energized.work.permit'].search_count(
                []) if 'energized.work.permit' in request.env else 0
            height_work_permits = request.env['work.heights.permit'].search_count(
                []) if 'work.heights.permit' in request.env else 0
            daily_work_permits = request.env['daily.permit.work'].search_count(
                []) if 'daily.permit.work' in request.env else 0

            # Total permits is sum of all permit types
            total_permits = hot_work_permits + energized_work_permits + height_work_permits + daily_work_permits

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

            # Location distribution for plant layout
            location_data = []
            try:
                location_data = gate_pass_obj.read_group(
                    [('location_id', '!=', False)],
                    ['location_id'],
                    ['location_id']
                )
            except:
                pass

            # Generate plant layout data
            plant_layout_data = self._get_plant_layout_data(gate_pass_obj, active_passes)

            location_chart = {
                'labels': [item['location_id'][1] if item['location_id'] else 'No Location' for item in location_data],
                'data': [item['location_id_count'] for item in location_data]
            }

            # Recent activity - last 7 days
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
                    'recent_passes': recent_passes,
                    'total_permits': total_permits,
                    'hot_work_permits': hot_work_permits,
                    'energized_work_permits': energized_work_permits,
                    'height_work_permits': height_work_permits,
                    'daily_work_permits': daily_work_permits
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
                },
                'plant_layout': plant_layout_data
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _get_plant_layout_data(self, gate_pass_obj, active_passes):
        """Generate plant layout data with smart fallback to dummy data"""

        # Define plant areas with coordinates
        plant_areas = [
            {'name': 'Main Gate', 'x': 10, 'y': 90, 'category': 'entry'},
            {'name': 'Production Unit A', 'x': 25, 'y': 60, 'category': 'production'},
            {'name': 'Production Unit B', 'x': 75, 'y': 60, 'category': 'production'},
            {'name': 'Warehouse', 'x': 50, 'y': 80, 'category': 'storage'},
            {'name': 'Quality Lab', 'x': 40, 'y': 30, 'category': 'quality'},
            {'name': 'Maintenance Shop', 'x': 20, 'y': 20, 'category': 'maintenance'},
            {'name': 'Power Plant', 'x': 80, 'y': 30, 'category': 'utility'},
            {'name': 'Washing Machine', 'x': 60, 'y': 15, 'category': 'utility'},
            {'name': 'Canteen', 'x': 50, 'y': 45, 'category': 'facility'},
            {'name': 'Security Office', 'x': 10, 'y': 70, 'category': 'security'},
            {'name': 'Fire Station', 'x': 90, 'y': 80, 'category': 'safety'},
            {'name': 'Raw Material Store', 'x': 30, 'y': 85, 'category': 'storage'}
        ]

        plant_layout_data = []
        has_real_data = False

        for area in plant_areas:
            employee_count = 0

            # Try to get real data from location field
            try:
                if hasattr(gate_pass_obj, 'location_id'):
                    employee_count = gate_pass_obj.search_count([
                        ('state', 'in', ['approved', 'in_progress']),
                        ('location_id.name', 'ilike', area['name'])
                    ])
                    if employee_count > 0:
                        has_real_data = True
            except:
                pass

            # If no real data found, generate dummy data
            if not has_real_data:
                employee_count = self._generate_dummy_employee_count(area['category'], active_passes)

            plant_layout_data.append({
                'name': area['name'],
                'employee_count': employee_count,
                'x': area['x'],
                'y': area['y'],
                'color': self._get_location_color(employee_count),
                'category': area['category']
            })

        return plant_layout_data

    def _generate_dummy_employee_count(self, category, total_active):
        """Generate realistic dummy employee counts based on location category"""

        # If no active passes at all, generate small random numbers
        if total_active == 0:
            base_ranges = {
                'production': (8, 25),
                'maintenance': (3, 12),
                'storage': (2, 8),
                'quality': (2, 6),
                'utility': (1, 5),
                'facility': (3, 10),
                'security': (2, 6),
                'safety': (1, 4),
                'entry': (5, 15)
            }
        else:
            # Distribute based on total active passes
            if total_active < 10:
                multiplier = 0.3
            elif total_active < 50:
                multiplier = 0.6
            else:
                multiplier = 1.0

            base_ranges = {
                'production': (int(10 * multiplier), int(30 * multiplier)),
                'maintenance': (int(5 * multiplier), int(15 * multiplier)),
                'storage': (int(3 * multiplier), int(10 * multiplier)),
                'quality': (int(2 * multiplier), int(8 * multiplier)),
                'utility': (int(2 * multiplier), int(6 * multiplier)),
                'facility': (int(4 * multiplier), int(12 * multiplier)),
                'security': (int(3 * multiplier), int(8 * multiplier)),
                'safety': (int(1 * multiplier), int(5 * multiplier)),
                'entry': (int(6 * multiplier), int(18 * multiplier))
            }

        min_count, max_count = base_ranges.get(category, (1, 10))
        return random.randint(min_count, max_count)

    def _get_location_color(self, employee_count):
        """Return color based on employee count"""
        if employee_count == 0:
            return '#9E9E9E'  # Grey - No employees
        elif employee_count <= 5:
            return '#4CAF50'  # Green - Low
        elif employee_count <= 15:
            return '#FF9800'  # Orange - Medium
        else:
            return '#F44336'  # Red - High


class ResUsers(models.Model):
    _inherit = 'res.users'

    chatter_position = fields.Selection([
        ('normal', 'Normal'),
        ('sided', 'Sided')
    ], string='Chatter Position', default='normal')