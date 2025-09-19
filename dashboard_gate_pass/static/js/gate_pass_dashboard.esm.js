/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

import { Component, useState, onMounted, onWillUnmount, useRef } from "@odoo/owl";

const { DateTime } = luxon;

class GatePassDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        // Chart refs
        this.stateChart = useRef("stateChart");
        this.passTypeChart = useRef("passTypeChart");
        this.departmentChart = useRef("departmentChart");
        this.ehsPermitChart = useRef("ehsPermitChart");
        this.locationChart = useRef("locationChart");
        this.dailyTrendChart = useRef("dailyTrendChart");

        this.state = useState({
            loading: true,
            currentTime: this.getCurrentTime(),
            kpis: {},
            charts: {},
            activities: [],
            alerts: []
        });

        this.charts = {}; // Store Chart.js instances
        this.refreshInterval = null;

        onMounted(() => {
            this.loadDashboardData();
            this.startTimeUpdate();
            this.startAutoRefresh();
        });

        onWillUnmount(() => {
            this.stopTimeUpdate();
            this.stopAutoRefresh();
            this.destroyCharts();
        });
    }

    // Time Management
    getCurrentTime() {
        return DateTime.now().toFormat('DDDD, t');
    }

    startTimeUpdate() {
        this.timeInterval = setInterval(() => {
            this.state.currentTime = this.getCurrentTime();
        }, 1000);
    }

    stopTimeUpdate() {
        if (this.timeInterval) {
            clearInterval(this.timeInterval);
        }
    }

    startAutoRefresh() {
        // Refresh every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData(false);
        }, 300000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }

    // Data Loading
    async loadDashboardData(showLoading = true) {
        if (showLoading) {
            this.state.loading = true;
        }

        try {
            const [dashboardData, activities, alerts] = await Promise.all([
                this.orm.call("gate.pass.service", "get_dashboard_data", []),
                this.orm.call("gate.pass.service", "get_recent_activities", [10]),
                this.orm.call("gate.pass.service", "get_alerts", [])
            ]);

            this.state.kpis = dashboardData.kpis;
            this.state.charts = dashboardData.charts;
            this.state.activities = activities;
            this.state.alerts = alerts;

            // Create charts after data is loaded
            await new Promise(resolve => setTimeout(resolve, 50)); // Wait for DOM update
            this.createCharts();

        } catch (error) {
            console.error("Failed to load dashboard data:", error);
            this.notification.add(_t("Failed to load dashboard data"), { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    // Chart Creation
    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    createCharts() {
        this.destroyCharts();

        // State Chart (Doughnut)
        if (this.stateChart.el && this.state.charts.state_chart) {
            this.charts.state = new Chart(this.stateChart.el, {
                type: 'doughnut',
                data: {
                    labels: this.state.charts.state_chart.labels,
                    datasets: [{
                        data: this.state.charts.state_chart.data,
                        backgroundColor: this.state.charts.state_chart.colors,
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: this.getDoughnutOptions()
            });
        }

        // Pass Type Chart (Pie)
        if (this.passTypeChart.el && this.state.charts.pass_type_chart) {
            this.charts.passType = new Chart(this.passTypeChart.el, {
                type: 'pie',
                data: {
                    labels: this.state.charts.pass_type_chart.labels,
                    datasets: [{
                        data: this.state.charts.pass_type_chart.data,
                        backgroundColor: this.state.charts.pass_type_chart.colors,
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: this.getPieOptions()
            });
        }

        // Department Chart (Horizontal Bar)
        if (this.departmentChart.el && this.state.charts.department_chart) {
            this.charts.department = new Chart(this.departmentChart.el, {
                type: 'bar',
                data: {
                    labels: this.state.charts.department_chart.labels,
                    datasets: [{
                        label: 'Gate Passes',
                        data: this.state.charts.department_chart.data,
                        backgroundColor: this.state.charts.department_chart.colors,
                        borderWidth: 1,
                        borderColor: '#ffffff'
                    }]
                },
                options: this.getBarOptions(true)
            });
        }

        // EHS Permit Chart (Doughnut)
        if (this.ehsPermitChart.el && this.state.charts.ehs_permit_chart) {
            this.charts.ehsPermit = new Chart(this.ehsPermitChart.el, {
                type: 'doughnut',
                data: {
                    labels: this.state.charts.ehs_permit_chart.labels,
                    datasets: [{
                        data: this.state.charts.ehs_permit_chart.data,
                        backgroundColor: this.state.charts.ehs_permit_chart.colors,
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: this.getDoughnutOptions()
            });
        }

        // Location Chart (Bar)
        if (this.locationChart.el && this.state.charts.location_chart) {
            this.charts.location = new Chart(this.locationChart.el, {
                type: 'bar',
                data: {
                    labels: this.state.charts.location_chart.labels,
                    datasets: [{
                        label: 'Gate Passes',
                        data: this.state.charts.location_chart.data,
                        backgroundColor: this.state.charts.location_chart.colors,
                        borderWidth: 1,
                        borderColor: '#ffffff'
                    }]
                },
                options: this.getBarOptions()
            });
        }

        // Daily Trend Chart (Line)
        if (this.dailyTrendChart.el && this.state.charts.daily_trend_chart) {
            this.charts.dailyTrend = new Chart(this.dailyTrendChart.el, {
                type: 'line',
                data: {
                    labels: this.state.charts.daily_trend_chart.labels,
                    datasets: [{
                        label: 'Gate Passes',
                        data: this.state.charts.daily_trend_chart.data,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#3498db',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 5
                    }]
                },
                options: this.getLineOptions()
            });
        }
    }

    // Chart Options
    getDoughnutOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 15,
                        font: { size: 11 },
                        color: '#333'
                    }
                }
            }
        };
    }

    getPieOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        font: { size: 11 },
                        color: '#333'
                    }
                }
            }
        };
    }

    getBarOptions(horizontal = false) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: horizontal ? 'y' : 'x',
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.05)' },
                    ticks: { font: { size: 10 }, color: '#666' }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.05)' },
                    ticks: { font: { size: 10 }, color: '#666' }
                }
            }
        };
    }

    getLineOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(0,0,0,0.05)' },
                    ticks: { font: { size: 10 }, color: '#666' }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.05)' },
                    ticks: { font: { size: 10 }, color: '#666' }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        };
    }

    // Navigation Actions
    async openGatePasses(filter) {
        let domain = [];
        let name = "Gate Passes";

        switch (filter) {
            case 'today':
                const today = DateTime.now().toISODate();
                domain = [['create_date', '>=', today], ['create_date', '<', DateTime.now().plus({days: 1}).toISODate()]];
                name = "Today's Gate Passes";
                break;
            case 'active':
                domain = [['state', 'in', ['issued', 'checked_out']]];
                name = "Active Gate Passes";
                break;
            case 'pending':
                domain = [['state', '=', 'to_approve']];
                name = "Pending Approvals";
                break;
            case 'overdue':
                domain = [
                    ['is_returnable', '=', true],
                    ['state', 'in', ['issued', 'checked_out']],
                    ['expected_return_datetime', '<', DateTime.now().toISO()]
                ];
                name = "Overdue Returns";
                break;
        }

        await this.action.doAction({
            type: 'ir.actions.act_window',
            name: name,
            res_model: 'hr.gate.pass',
            view_mode: 'list,form',
            domain: domain,
            target: 'current'
        });
    }

    async openPermits() {
        await this.action.doAction({
            type: 'ir.actions.act_window',
            name: "Work Permits",
            res_model: 'work.heights.permit',
            view_mode: 'list,form',
            target: 'current'
        });
    }

    // Utility Functions
    getActivityIcon(action) {
        const iconMap = {
            'submitted': 'paper-plane',
            'approved': 'check-circle',
            'printed': 'print',
            'issued': 'id-card',
            'checked_out': 'sign-out',
            'returned': 'sign-in',
            'rejected': 'times-circle',
            'canceled': 'ban',
            'closed': 'lock'
        };
        return iconMap[action] || 'circle';
    }

    getAlertIcon(type) {
        const iconMap = {
            'warning': 'exclamation-triangle',
            'info': 'info-circle',
            'danger': 'exclamation-circle',
            'success': 'check-circle'
        };
        return iconMap[type] || 'bell';
    }

    formatTime(datetime) {
        if (!datetime) return '';
        return DateTime.fromISO(datetime).toRelative();
    }
}

GatePassDashboard.template = "hr_gate_pass.Dashboard";

registry.category("actions").add("gate_pass.dashboard.client_action", GatePassDashboard);