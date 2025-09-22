/* static/src/js/gate_pass_dashboard.js */

import { Component, useState, onWillStart, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

class GatePassDashboard extends Component {
    setup() {
        this.state = useState({
            kpis: {},
            charts: {},
            loading: true,
            error: null
        });

        this.orm = useService("orm");
        this.action = useService("action");

        // Chart references
        this.stateChartRef = useRef("stateChart");
        this.ehsChartRef = useRef("ehsChart");
        this.passTypeChartRef = useRef("passTypeChart");
        this.deptChartRef = useRef("deptChart");
        this.locationChartRef = useRef("locationChart");
        this.trendChartRef = useRef("trendChart");

        onWillStart(async () => {
            await this.loadDashboardData();
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    async loadDashboardData() {
        try {
            this.state.loading = true;
            const result = await rpc('/gate_pass/dashboard_data');

            if (result.success) {
                this.state.kpis = result.kpis;
                this.state.charts = result.charts;
                this.state.error = null;
            } else {
                this.state.error = result.error || 'Failed to load dashboard data';
            }
        } catch (error) {
            this.state.error = error.message || 'Failed to load dashboard data';
        } finally {
            this.state.loading = false;
        }
    }

    async refreshDashboard() {
        await this.loadDashboardData();
        this.renderCharts();
    }

    renderCharts() {
        // Only render if Chart.js is available and data is loaded
        if (typeof Chart === 'undefined' || this.state.loading || this.state.error) {
            return;
        }

        // State Chart (Doughnut)
        if (this.stateChartRef.el && this.state.charts.state) {
            new Chart(this.stateChartRef.el, {
                type: 'doughnut',
                data: {
                    labels: this.state.charts.state.labels,
                    datasets: [{
                        data: this.state.charts.state.data,
                        backgroundColor: [
                            '#4CAF50', '#FF9800', '#F44336', '#2196F3',
                            '#9C27B0', '#00BCD4', '#FFEB3B', '#795548'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: 'Gate Pass Status Distribution'
                        }
                    }
                }
            });
        }

        // Pass Type Chart (Bar)
        if (this.passTypeChartRef.el && this.state.charts.pass_type) {
            new Chart(this.passTypeChartRef.el, {
                type: 'bar',
                data: {
                    labels: this.state.charts.pass_type.labels,
                    datasets: [{
                        label: 'Count',
                        data: this.state.charts.pass_type.data,
                        backgroundColor: '#2196F3',
                        borderColor: '#1976D2',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Passes by Type'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Department Chart (Horizontal Bar)
        if (this.deptChartRef.el && this.state.charts.department) {
            new Chart(this.deptChartRef.el, {
                type: 'bar',
                data: {
                    labels: this.state.charts.department.labels,
                    datasets: [{
                        label: 'Count',
                        data: this.state.charts.department.data,
                        backgroundColor: '#FF9800',
                        borderColor: '#F57C00',
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Passes by Department'
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // EHS Permit Chart (Pie)
        if (this.ehsChartRef.el && this.state.charts.ehs_permit_type) {
            new Chart(this.ehsChartRef.el, {
                type: 'pie',
                data: {
                    labels: this.state.charts.ehs_permit_type.labels,
                    datasets: [{
                        data: this.state.charts.ehs_permit_type.data,
                        backgroundColor: [
                            '#4CAF50', '#FF5722', '#9C27B0', '#00BCD4',
                            '#FFEB3B', '#795548', '#607D8B'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: 'EHS Permits by Type'
                        }
                    }
                }
            });
        }

        // Location Chart (Bar)
        if (this.locationChartRef.el && this.state.charts.location) {
            new Chart(this.locationChartRef.el, {
                type: 'bar',
                data: {
                    labels: this.state.charts.location.labels,
                    datasets: [{
                        label: 'Count',
                        data: this.state.charts.location.data,
                        backgroundColor: '#9C27B0',
                        borderColor: '#7B1FA2',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Passes by Location'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Monthly Trend Chart (Line)
        if (this.trendChartRef.el && this.state.charts.monthly_trend) {
            new Chart(this.trendChartRef.el, {
                type: 'line',
                data: {
                    labels: this.state.charts.monthly_trend.labels,
                    datasets: [{
                        label: 'Gate Passes',
                        data: this.state.charts.monthly_trend.data,
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Monthly Trend (Last 6 Months)'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }

    async onKpiClick(type) {
        let domain = [];
        let title = '';

        switch(type) {
            case 'active':
                domain = [['state', 'in', ['approved', 'in_progress']]];
                title = 'Active Gate Passes';
                break;
            case 'pending':
                domain = [['state', '=', 'pending']];
                title = 'Pending Approvals';
                break;
            case 'expired':
                domain = [['state', '=', 'expired']];
                title = 'Expired Passes';
                break;
            default:
                domain = [];
                title = 'All Gate Passes';
        }

        await this.action.doAction({
            type: 'ir.actions.act_window',
            name: title,
            res_model: 'hr.gate.pass',
            view_mode: 'tree,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            domain: domain,
        });
    }
}

GatePassDashboard.template = 'hr_gate_pass.DashboardTemplate';

// Register the action
registry.category("actions").add("gate_pass_dashboard", GatePassDashboard);

export default GatePassDashboard;