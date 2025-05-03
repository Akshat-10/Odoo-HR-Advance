/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { Component } from "@odoo/owl";

export class KPIEmployeeList extends Component {
    static template = "kpi.EmployeeList";
    static props = {
        ...standardWidgetProps,
    };

    setup() {
        super.setup();
        this.action = useService("action");
        this.orm = useService("orm");
        this.employeeCount = this.props.record.data.employee_count;
    }

    async openEmployees() {
        const departmentId = this.props.record.data.department_id[0];
        const dialogAction = await this.orm.call(
            "hr.department",
            "action_employee_from_department",
            [departmentId],
            {}
        );
        this.action.doAction(dialogAction);
    }
}

export const kpiEmployeeList = {
    component: KPIEmployeeList,
};

registry.category("view_widgets").add("kpi_employee_list", kpiEmployeeList);