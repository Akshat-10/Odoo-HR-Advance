/* @odoo-module */

import { patch } from "@web/core/utils/patch";
import { TimeOffCardPopover, TimeOffCard } from "@hr_holidays/dashboard/time_off_card";
import { formatNumber } from "@hr_holidays/views/hooks";
import { user } from "@web/core/user";

// 1) Extend popover props and add handlers to open filtered lists
patch(TimeOffCardPopover.prototype, {
    setup() {
        // call original setup
        if (super.setup) {
            super.setup();
        }
        // ensure we have action service from original component
    },
    /**
     * Open hr.leave list filtered to approved states
     */
    async openApproved() {
        const domain = [
            ["state", "in", ["validate", "validate1"]],
        ];
        if (this.props?.holidayStatusId) {
            domain.push(["holiday_status_id", "=", this.props.holidayStatusId]);
        }
        if (this.props?.employeeId) {
            domain.push(["employee_id", "=", this.props.employeeId]);
        }
        await this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "hr.leave",
            // name: this.env._t("Leaves"),
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain,
            context: {
                from_dashboard: true,
            },
        });
    },
    /**
     * Open hr.leave list filtered to planned (confirm + approved) states
     */
    async openPlanned() {
        const domain = [
            ["state", "in", ["confirm", "validate1", "validate"]],
        ];
        if (this.props?.holidayStatusId) {
            domain.push(["holiday_status_id", "=", this.props.holidayStatusId]);
        }
        if (this.props?.employeeId) {
            domain.push(["employee_id", "=", this.props.employeeId]);
        }
        await this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "hr.leave",
            // name: this.env._t("Leaves"),
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain,
            context: {
                from_dashboard: true,
            },
        });
    },
});

// Ensure optional props are accepted by popover
try {
    const extra = ["employeeId?", "holidayStatusId?"];
    if (Array.isArray(TimeOffCardPopover.props)) {
        for (const p of extra) {
            if (!TimeOffCardPopover.props.includes(p) && !TimeOffCardPopover.props.includes(p.replace("?", ""))) {
                TimeOffCardPopover.props.push(p);
            }
        }
    }
} catch (e) {
    // ignore
}

// 2) Pass employee/type info to popover when opening it
const __origOnClickInfo = TimeOffCard.prototype.onClickInfo;
patch(TimeOffCard.prototype, {
    onClickInfo(ev) {
        // If original exists, replicate its payload and extend with identifiers
        if (__origOnClickInfo) {
            // Rebuild payload using current public API, aligning with core implementation
            const { data } = this.props;
            const lang = user.lang;
            const payload = {
                allocated: formatNumber(lang, data.max_leaves),
                accrual_bonus: formatNumber(lang, data.accrual_bonus),
                approved: formatNumber(lang, data.leaves_approved),
                planned: formatNumber(lang, data.leaves_requested),
                left: formatNumber(lang, data.virtual_remaining_leaves),
                warning: this.warning,
                closest: data.closest_allocation_duration,
                request_unit: data.request_unit,
                exceeding_duration: data.exceeding_duration,
                allows_negative: data.allows_negative,
                max_allowed_negative: data.max_allowed_negative,
                onClickNewAllocationRequest: this.newAllocationRequestFrom.bind(this),
                errorLeaves: this.errorLeaves,
                accrualExcess: this.getAccrualExcess(data),
                // Added
                employeeId: this.props.employeeId || null,
                holidayStatusId: this.props.holidayStatusId || null,
            };
            this.popover.open(ev.target, payload);
        } else {
            // Fallback
            return super.onClickInfo(ev);
        }
    },
});
