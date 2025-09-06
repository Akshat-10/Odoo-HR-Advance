/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { TimeOffCalendarCommonPopover } from "@hr_holidays/views/calendar/common/calendar_common_popover";

function getLeaveResIdFromRecord(record) {
    // Works for hr.employee.activity (has leave_id) and hr.leave/report calendars (id is hr.leave)
    const raw = record?.rawRecord || record;
    if (!raw) return undefined;
    // hr.employee.activity provides leave_id as number or [id, name]
    const val = raw.leave_id || raw.id;
    if (Array.isArray(val)) return parseInt(val[0]);
    if (typeof val === "string") {
        const m = val.match(/^(\d+)/);
        return m ? parseInt(m[1]) : undefined;
    }
    if (typeof val === "number") return Math.abs(val);
    return undefined;
}

patch(TimeOffCalendarCommonPopover.prototype, {
    async onClickButton(ev) {
        try {
            // Prefer hr.leave id from leave_id when present (custom unified model)
            const resId = getLeaveResIdFromRecord(this.props.record);
            if (!resId) {
                // Fallback to original behavior
                return await super.onClickButton(ev);
            }
            const action = ev.target?.name;
            const args = action === "action_approve" ? [resId, false] : [resId];
            await this.orm.call("hr.leave", action, args, {
                context: { active_id: resId, active_ids: [resId], active_model: "hr.leave" },
            });
            await this.props.model.load();
            this.props.close();
        } catch (e) {
            // Fallback if anything unexpected
            return super.onClickButton(ev);
        }
    },
});
