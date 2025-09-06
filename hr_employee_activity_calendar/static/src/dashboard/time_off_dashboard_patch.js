/* @odoo-module */

import { TimeOffDashboard } from "@hr_holidays/dashboard/time_off_dashboard";
import { EmployeeMetrics } from "@hr_employee_activity_calendar/dashboard/employee_activity_dashboard";

// Register component at module load so it is available at render time
TimeOffDashboard.components = {
    ...TimeOffDashboard.components,
    EmployeeMetrics,
};

// Extend accepted props so we can pass calendar range and scale via template inheritance
TimeOffDashboard.props = [
    ...(Array.isArray(TimeOffDashboard.props) ? TimeOffDashboard.props : ["employeeId"]),
    "rangeStart?",
    "rangeEnd?",
    "scale?",
];
