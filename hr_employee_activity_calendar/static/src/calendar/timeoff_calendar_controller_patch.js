/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { TimeOffCalendarController } from "@hr_holidays/views/calendar/calendar_controller";
import { TimeOffFormViewDialog } from "@hr_holidays/views/view_dialog/form_view_dialog";

function normalizeId(val) {
    // Accept number, string (possibly "12,Name"), or m2o tuple [id, name]
    if (val == null) return undefined;
    if (Array.isArray(val)) return Number.parseInt(val[0]);
    if (typeof val === "number") return val;
    if (typeof val === "string") {
        const num = Number.parseInt(val, 10);
        return Number.isNaN(num) ? undefined : num;
    }
    return undefined;
}

function sanitizeDialogContext(ctx = {}) {
    const clean = { ...(ctx || {}) };
    // Convert M2O defaults like default_employee_id, default_holiday_status_id from [id,name] or "id,name" to int
    for (const key of Object.keys(clean)) {
        if (!key.startsWith("default_")) continue;
        const v = clean[key];
        if (Array.isArray(v)) {
            const nid = normalizeId(v);
            if (nid !== undefined) clean[key] = nid;
        } else if (typeof v === "string" && /^(\d+),/.test(v)) {
            const nid = normalizeId(v);
            if (nid !== undefined) clean[key] = nid;
        }
    }
    return clean;
}

function reloadCalendar(ctrl) {
    try {
        // Safest refresh that works across versions
        ctrl.model && ctrl.model.load && ctrl.model.load();
        if (ctrl.env && ctrl.env.timeOffBus) {
            ctrl.env.timeOffBus.trigger("update_dashboard");
        }
    } catch (e) {
        // no-op
    }
}

patch(TimeOffCalendarController.prototype, {
    async editRecord(record, context = {}, shouldFetchFormViewId = true) {
        const raw = record && record.rawRecord ? record.rawRecord : record;
        const resModel = this.model?.meta?.resModel;

    // 1) Time Off Overview (report) -> open hr.leave by record.id
    if (resModel === "hr.leave.report.calendar" && record) {
        const rawId = record?.rawRecord?.id ?? record?.id;
        let resId = normalizeId(rawId);
        // ensure positive numeric ID
        if (typeof resId === "number") resId = Math.abs(resId);
        const safeContext = {
            active_id: resId,
            active_ids: [resId],
            active_model: "hr.leave",
            ...sanitizeDialogContext(context),
        };
            return new Promise((resolve) => {
                this.displayDialog(TimeOffFormViewDialog, {
                    resModel: "hr.leave",
            resId,
                    onRecordDeleted: () => {
                        reloadCalendar(this);
                        resolve();
                    },
                    onLeaveCancelled: () => {
                        reloadCalendar(this);
                        resolve();
                    },
                onRecordSaved: () => {
                    reloadCalendar(this);
                    resolve();
                },
            context: safeContext,
                });
            });
        }

        // 2) Unified Employee Activity (custom) -> route time_off to hr.leave, attendance to hr.attendance
        if (resModel === "hr.employee.activity" && raw) {
            // Open Time Off dialog for leave lines
            if (raw.activity_type === "time_off" && raw.leave_id) {
                let resId = normalizeId(raw.leave_id);
                if (typeof resId === "number") resId = Math.abs(resId);
                const safeContext = {
                    active_id: resId,
                    active_ids: [resId],
                    active_model: "hr.leave",
                    ...sanitizeDialogContext(context),
                };
                return new Promise((resolve) => {
                    this.displayDialog(TimeOffFormViewDialog, {
                        resModel: "hr.leave",
                        resId,
                        onRecordDeleted: () => {
                            reloadCalendar(this);
                            resolve();
                        },
                        onLeaveCancelled: () => {
                            reloadCalendar(this);
                            resolve();
                        },
                        onRecordSaved: () => {
                            reloadCalendar(this);
                            resolve();
                        },
                        context: safeContext,
                    });
                });
            }

            // Open standard Attendance form for attendance lines
            if (raw.activity_type === "attendance" && raw.attendance_id) {
                const attId = Math.abs(normalizeId(raw.attendance_id));
                const action = {
                    type: "ir.actions.act_window",
                    res_model: "hr.attendance",
                    res_id: attId,
                    views: [[false, "form"]],
                    target: "current",
                };
                await this.env.services.action.doAction(action);
                return;
            }
        }

        // Fallback to original behavior
        return super.editRecord(record, context, shouldFetchFormViewId);
    },

    // Intercept delete and route through the dialog so business rules apply
    deleteRecord(record) {
        const resModel = this.model?.meta?.resModel;
        const raw = record && record.rawRecord ? record.rawRecord : record;

        if (resModel === "hr.leave.report.calendar") {
            // Open leave dialog for delete/cancel operations
            return this.editRecord(record);
        }

        if (resModel === "hr.employee.activity") {
            // Only allow delete via the leave dialog for time off entries
            if (raw?.activity_type === "time_off" && raw?.leave_id) {
                return this.editRecord(record);
            }
            // For attendance entries, open the form; deletion is managed there by rules
            if (raw?.activity_type === "attendance" && raw?.attendance_id) {
                const attId = Math.abs(normalizeId(raw.attendance_id));
                const action = {
                    type: "ir.actions.act_window",
                    res_model: "hr.attendance",
                    res_id: attId,
                    views: [[false, "form"]],
                    target: "current",
                };
                return this.env.services.action.doAction(action);
            }
        }

        return super.deleteRecord(record);
    },
});
