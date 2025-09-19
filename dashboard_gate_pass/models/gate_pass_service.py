from odoo import models, fields, api
from datetime import datetime, date, timedelta
from collections import defaultdict


class GatePassService(models.AbstractModel):
    _name = "gate.pass.service"
    _description = "Gate Pass Service"

    @api.model
    def get_initial_kpis(self):
        return self.get_dashboard_data()['kpis']

    @api.model
    def get_dashboard_data(self):
        # Get date ranges
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        # Base domain for current company
        base_domain = [('company_id', '=', self.env.company.id)]

        # Get all gate passes
        all_passes = self.env['hr.gate.pass'].search(base_domain)

        # Today's passes
        today_passes = all_passes.filtered(
            lambda p: p.create_date and p.create_date.date() == today
        )

        # This week's passes
        week_passes = all_passes.filtered(
            lambda p: p.create_date and p.create_date.date() >= week_start
        )

        # This month's passes
        month_passes = all_passes.filtered(
            lambda p: p.create_date and p.create_date.date() >= month_start
        )

        # Active passes (issued, checked_out)
        active_passes = all_passes.filtered(lambda p: p.state in ('issued', 'checked_out'))

        # Pending approvals
        pending_passes = all_passes.filtered(lambda p: p.state == 'to_approve')

        # Overdue returns
        overdue_passes = all_passes.filtered(
            lambda p: p.is_returnable and p.state in ('issued', 'checked_out') and
                      p.expected_return_datetime and p.expected_return_datetime < fields.Datetime.now()
        )

        # Get permit data
        work_heights_permits = self.env['work.heights.permit'].search([])
        energized_permits = self.env['energized.work.permit'].search([])
        daily_permits = self.env['daily.permit.work'].search([])
        hot_work_permits = self.env['hot.work.permit'].search([])

        total_permits = len(work_heights_permits) + len(energized_permits) + len(daily_permits) + len(hot_work_permits)

        # Active permits (not completed/cancelled)
        active_permits_count = (
                len(work_heights_permits.filtered(lambda p: p.state not in ('completed', 'cancelled'))) +
                len(energized_permits.filtered(lambda p: p.state not in ('completed', 'cancelled'))) +
                len(daily_permits.filtered(lambda p: p.state not in ('completed', 'cancelled'))) +
                len(hot_work_permits.filtered(lambda p: p.state not in ('completed', 'cancelled')))
        )

        kpis = {
            'total_passes': len(all_passes),
            'today_passes': len(today_passes),
            'week_passes': len(week_passes),
            'month_passes': len(month_passes),
            'active_passes': len(active_passes),
            'pending_approvals': len(pending_passes),
            'overdue_returns': len(overdue_passes),
            'total_permits': total_permits,
            'active_permits': active_permits_count,
            'visitors_today': len(today_passes.filtered(lambda p: p.pass_type == 'visitor')),
            'employees_out_today': len(today_passes.filtered(lambda p: p.pass_type == 'employee_out')),
            'materials_today': len(today_passes.filtered(lambda p: p.pass_type == 'material')),
        }

        # Chart data
        charts = {
            'state_chart': self._get_state_chart_data(all_passes),
            'pass_type_chart': self._get_pass_type_chart_data(all_passes),
            'department_chart': self._get_department_chart_data(all_passes),
            'ehs_permit_chart': self._get_ehs_permit_chart_data(all_passes),
            'location_chart': self._get_location_chart_data(all_passes),
            'daily_trend_chart': self._get_daily_trend_chart_data(),
            'permit_status_chart': self._get_permit_status_chart_data(),
        }

        return {
            'kpis': kpis,
            'charts': charts
        }

    def _get_state_chart_data(self, passes):
        """Gate Pass by State"""
        state_counts = {}
        state_labels = dict(self.env['hr.gate.pass']._fields['state'].selection)

        for pass_rec in passes:
            state = pass_rec.state
            state_counts[state] = state_counts.get(state, 0) + 1

        return {
            'labels': [state_labels.get(k, k) for k in state_counts.keys()],
            'data': list(state_counts.values()),
            'colors': self._get_state_colors(list(state_counts.keys()))
        }

    def _get_pass_type_chart_data(self, passes):
        """Gate Pass by Type"""
        type_counts = {}
        type_labels = dict(self.env['hr.gate.pass']._fields['pass_type'].selection)

        for pass_rec in passes:
            pass_type = pass_rec.pass_type
            type_counts[pass_type] = type_counts.get(pass_type, 0) + 1

        return {
            'labels': [type_labels.get(k, k) for k in type_counts.keys()],
            'data': list(type_counts.values()),
            'colors': self._get_pass_type_colors(list(type_counts.keys()))
        }

    def _get_department_chart_data(self, passes):
        """Gate Pass by Department"""
        dept_counts = {}

        for pass_rec in passes:
            dept_name = pass_rec.department_id.name if pass_rec.department_id else 'No Department'
            dept_counts[dept_name] = dept_counts.get(dept_name, 0) + 1

        # Sort by count descending and take top 10
        sorted_depts = sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'labels': [item[0] for item in sorted_depts],
            'data': [item[1] for item in sorted_depts],
            'colors': self._generate_colors(len(sorted_depts))
        }

    def _get_ehs_permit_chart_data(self, passes):
        """EHS Permits by Type"""
        permit_counts = {}
        permit_labels = dict(self.env['hr.gate.pass']._fields['ehs_permit_type'].selection)

        for pass_rec in passes:
            if pass_rec.ehs_permit_type:
                permit_type = pass_rec.ehs_permit_type
                permit_counts[permit_type] = permit_counts.get(permit_type, 0) + 1

        return {
            'labels': [permit_labels.get(k, k) for k in permit_counts.keys()],
            'data': list(permit_counts.values()),
            'colors': self._get_permit_colors(list(permit_counts.keys()))
        }

    def _get_location_chart_data(self, passes):
        """Gate Pass by Location/Gate"""
        location_counts = {}

        for pass_rec in passes:
            location_name = pass_rec.gate_id.name if pass_rec.gate_id else 'No Gate Specified'
            location_counts[location_name] = location_counts.get(location_name, 0) + 1

        return {
            'labels': list(location_counts.keys()),
            'data': list(location_counts.values()),
            'colors': self._generate_colors(len(location_counts))
        }

    def _get_daily_trend_chart_data(self):
        """Last 30 days trend"""
        today = date.today()
        dates = [(today - timedelta(days=i)) for i in range(29, -1, -1)]

        daily_counts = []
        labels = []

        for day in dates:
            day_passes = self.env['hr.gate.pass'].search([
                ('company_id', '=', self.env.company.id),
                ('create_date', '>=', datetime.combine(day, datetime.min.time())),
                ('create_date', '<', datetime.combine(day + timedelta(days=1), datetime.min.time()))
            ])
            daily_counts.append(len(day_passes))
            labels.append(day.strftime('%m/%d'))

        return {
            'labels': labels,
            'data': daily_counts,
            'colors': ['#3498db'] * len(labels)
        }

    def _get_permit_status_chart_data(self):
        """All Permits Status Overview"""
        status_counts = defaultdict(int)

        # Work Heights Permits
        for permit in self.env['work.heights.permit'].search([]):
            status_counts[f"Heights - {permit.state}"] += 1

        # Energized Work Permits
        for permit in self.env['energized.work.permit'].search([]):
            status_counts[f"Energized - {permit.state}"] += 1

        # Daily Permits
        for permit in self.env['daily.permit.work'].search([]):
            status_counts[f"Daily - {permit.state}"] += 1

        # Hot Work Permits
        for permit in self.env['hot.work.permit'].search([]):
            status_counts[f"Hot Work - {permit.state}"] += 1

        return {
            'labels': list(status_counts.keys()),
            'data': list(status_counts.values()),
            'colors': self._generate_colors(len(status_counts))
        }

    def _get_state_colors(self, states):
        """Color mapping for gate pass states"""
        color_map = {
            'draft': '#95a5a6',
            'to_approve': '#f39c12',
            'approved': '#2ecc71',
            'issued': '#3498db',
            'checked_out': '#9b59b6',
            'returned': '#1abc9c',
            'closed': '#34495e',
            'rejected': '#e74c3c',
            'cancel': '#7f8c8d'
        }
        return [color_map.get(state, '#bdc3c7') for state in states]

    def _get_pass_type_colors(self, types):
        """Color mapping for pass types"""
        color_map = {
            'visitor': '#3498db',
            'employee_out': '#2ecc71',
            'material': '#f39c12',
            'vehicle': '#9b59b6',
            'contractor': '#e67e22'
        }
        return [color_map.get(t, '#bdc3c7') for t in types]

    def _get_permit_colors(self, permits):
        """Color mapping for permit types"""
        color_map = {
            'work_heights': '#e74c3c',
            'energized': '#f39c12',
            'daily': '#2ecc71',
            'hot_work': '#fd79a8'
        }
        return [color_map.get(p, '#bdc3c7') for p in permits]

    def _generate_colors(self, count):
        """Generate distinct colors for charts"""
        colors = [
            '#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6',
            '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#f1c40f',
            '#8e44ad', '#16a085', '#2c3e50', '#d35400', '#7f8c8d'
        ]
        return (colors * ((count // len(colors)) + 1))[:count]

    @api.model
    def get_recent_activities(self, limit=10):
        """Get recent gate pass activities"""
        recent_logs = self.env['hr.gate.log'].search([
            ('gate_pass_id.company_id', '=', self.env.company.id)
        ], order='timestamp desc', limit=limit)

        activities = []
        for log in recent_logs:
            activities.append({
                'id': log.id,
                'action': log.action,
                'gate_pass': log.gate_pass_id.name,
                'user': log.by_user_id.name,
                'timestamp': log.timestamp,
                'remarks': log.remarks
            })

        return activities

    @api.model
    def get_alerts(self):
        """Get system alerts and notifications"""
        alerts = []

        # Overdue returns
        overdue = self.env['hr.gate.pass'].search([
            ('company_id', '=', self.env.company.id),
            ('is_returnable', '=', True),
            ('state', 'in', ('issued', 'checked_out')),
            ('expected_return_datetime', '<', fields.Datetime.now())
        ])

        if overdue:
            alerts.append({
                'type': 'warning',
                'title': f'{len(overdue)} Overdue Returns',
                'message': 'Some items are past their expected return date',
                'action': 'hr_gate_pass.action_hr_gate_pass',
                'count': len(overdue)
            })

        # Pending approvals
        pending = self.env['hr.gate.pass'].search([
            ('company_id', '=', self.env.company.id),
            ('state', '=', 'to_approve')
        ])

        if pending:
            alerts.append({
                'type': 'info',
                'title': f'{len(pending)} Pending Approvals',
                'message': 'Gate passes waiting for approval',
                'action': 'hr_gate_pass.action_hr_gate_pass',
                'count': len(pending)
            })

        return alerts