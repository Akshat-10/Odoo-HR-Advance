/* @odoo-module */

import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";

export class EmployeeMetrics extends Component {
    static template = "hr_employee_activity.EmployeeMetrics";
    static props = ["employeeId", "date?", "rangeStart?", "rangeEnd?", "scale?"];

    setup() {
        this.orm = useService("orm");
    this.state = useState({ metrics: null, loading: true, error: null });
        this.currentCalendarDate = null; // Track the current calendar date
        this.currentCalendarRange = { start: null, end: null }; // Track the current calendar range
        this.currentScale = null; // Track the current scale
        
        // Listen to calendar range changes
        useBus(this.env.timeOffBus, "calendar_range_changed", async (ev) => {
            // Update the current calendar date and range from the event
            if (ev.detail) {
                if (ev.detail.date) {
                    this.currentCalendarDate = ev.detail.date;
                }
                
                if (ev.detail.start && ev.detail.end) {
                    this.currentCalendarRange = {
                        start: ev.detail.start,
                        end: ev.detail.end
                    };
                }
                
                if (ev.detail.scale) {
                    this.currentScale = ev.detail.scale;
                }
                
                // Small delay to ensure all data is properly set before loading
                setTimeout(async () => {
                    await this.load();
                }, 100);
            } else {
                await this.load();
            }
        });
        
        // Also listen for any calendar navigation events
        useBus(this.env.timeOffBus, "update_dashboard", async () => {
            await this.load();
        });
        
        onWillStart(async () => {
            await this.load();
        });
        
        onWillUpdateProps(async (nextProps) => {
            const prev = this.props;
            
            // Better date comparison - compare the actual date values
            const getDateString = (d) => d ? d.toFormat('yyyy-MM-dd') : null;
            const dateChanged = getDateString(nextProps.date) !== getDateString(prev.date);
            
            // Also check if the month/year changed for month view
            const getMonthYear = (d) => d ? d.toFormat('yyyy-MM') : null;
            const monthYearChanged = getMonthYear(nextProps.date) !== getMonthYear(prev.date);
            
            const scaleChanged = (nextProps.scale || null) !== (prev.scale || null);
            const empChanged = nextProps.employeeId !== prev.employeeId;
            
            if (dateChanged || monthYearChanged || scaleChanged || empChanged) {
                // Update state.currentDate when props.date changes
                if (nextProps.date && dateChanged) {
                    this.state.currentDate = nextProps.date;
                }
                await this.load(nextProps);
            }
        });
    }

    get period() {
        const props = this.props;
        // Always normalize the date range based on scale and current date
        // Use the calendar date if available, otherwise fall back to props.date
        const scale = this.currentScale || props.scale || 'month';
        const refDate = this.currentCalendarDate || props.date || luxon.DateTime.now();
        
    let start, end;
        
        // If we have a valid calendar range from the calendar component, use it directly
        if (this.currentCalendarRange.start && this.currentCalendarRange.end) {
            // Use the calendar range directly for all scales
            start = this.currentCalendarRange.start;
            end = this.currentCalendarRange.end;
        } else if (this.props.rangeStart && this.props.rangeEnd) {
            // Fallback to props provided via template inheritance if available
            start = this.props.rangeStart;
            end = this.props.rangeEnd;
        } else {
            // Fall back to calculating based on refDate and scale
            switch (scale) {
                case 'day':
                    start = refDate.startOf('day');
                    end = refDate.endOf('day');
                    break;
                case 'week':
                    start = refDate.startOf('week');
                    end = refDate.endOf('week');
                    break;
                case 'month':
                    start = refDate.startOf('month');
                    end = refDate.endOf('month');
                    break;
                case 'year':
                    start = refDate.startOf('year');
                    end = refDate.endOf('year');
                    break;
                default:
                    // Fallback to month if scale is unknown
                    start = refDate.startOf('month');
                    end = refDate.endOf('month');
            }
        }
        return { start, end };
    }

    async load(nextProps = null) {
        const props = nextProps || this.props;
        
        // Always normalize the date range based on scale and current date
        // Use the calendar date if available, otherwise fall back to props.date
        const scale = this.currentScale || props.scale || 'month';
        const refDate = this.currentCalendarDate || props.date || luxon.DateTime.now();
        
        // Update state.currentDate with the reference date being used
        this.state.currentDate = refDate;
        
        // Get the normalized period
        const period = this.period;
        const start = period.start;
        const end = period.end;
        
        // Force reload if this is a different date range than what we last loaded
        const lastLoadedRange = this.lastLoadedRange;
        const currentRange = `${start.toFormat('yyyy-MM-dd')}_${end.toFormat('yyyy-MM-dd')}`;
        this.lastLoadedRange = currentRange;
        
        try {
            const round2 = (v) => Math.round((Number(v) || 0) * 100) / 100;
            const asInt = (v) => parseInt(v || 0, 10) || 0;
            const raw = await this.orm.call(
                "hr.employee",
                "get_attendance_metrics_public",
                [],
                {
                    context: {},
                    kwargs: {
                        employee_id: props.employeeId || null,
                        start_date: start.toFormat("yyyy-MM-dd"),
                        end_date: end.toFormat("yyyy-MM-dd"),
                        scale: scale || null,
                    },
                }
            );
            this.state.metrics = {
                total_days: asInt(raw.total_days),
                time_off_days: asInt(raw.time_off_days),
                last_attendance_worked_hours: round2(raw.last_attendance_worked_hours),
                hours_previously_today: round2(raw.hours_previously_today),
                total_overtime: round2(raw.total_overtime),
                expected_working_hours: round2(raw.expected_working_hours),
                actual_working_hours: round2(raw.actual_working_hours),
                weekoff: asInt(raw.weekoff),
                holiday: asInt(raw.holiday),
                days_pp: asInt(raw["days_p|p"] || raw.days_pp),
                days_pa: asInt(raw["days_p|a"] || raw.days_pa),
                days_ap: asInt(raw["days_a|p"] || raw.days_ap),
                days_aa: asInt(raw["days_a|a"] || raw.days_aa),
                expected_work_days: asInt(raw.expected_work_days),
                present: asInt(raw.present),
                absent: asInt(raw.absent),
            };
        } catch (e) {
            this.state.metrics = {};
            console.error("Failed to load metrics:", e);
        }
    }
    
    // Method to manually trigger reload (can be called externally)
    async forceReload() {
        await this.load();
    }
}
