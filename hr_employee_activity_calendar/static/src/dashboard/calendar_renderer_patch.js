/* @odoo-module */

import { CalendarRenderer } from "@web/views/calendar/calendar_renderer";
import { patch } from "@web/core/utils/patch";

// Keep references to original methods/getters
const __origCalendarRendererSetup = CalendarRenderer.prototype.setup;
const __origCalendarKeyDescriptor = Object.getOwnPropertyDescriptor(
    CalendarRenderer.prototype,
    "calendarKey"
);

// Broadcasts the current visible range and scale on render changes so dashboards can react.
patch(CalendarRenderer.prototype, {
    setup(...args) {
        if (typeof __origCalendarRendererSetup === "function") {
            __origCalendarRendererSetup.apply(this, args);
        }
        // initial broadcast with a small delay to ensure the model is initialized
        setTimeout(() => this._broadcastRange(), 100);
    },
    get calendarKey() {
        // compute original key if available, else emulate
        let key;
        if (__origCalendarKeyDescriptor && typeof __origCalendarKeyDescriptor.get === "function") {
            key = __origCalendarKeyDescriptor.get.call(this);
        } else {
            const model = this.props?.model;
            key = `${model?.scale}_${model?.date?.valueOf?.()}`;
        }
        // broadcast on key recompute (scale or date changed)
        this._broadcastRange();
        return key;
    },
    _broadcastRange() {
        try {
            const model = this.props?.model;
            if (!model) {
                console.warn("Calendar model not available for broadcasting range");
                return;
            }
            
            // Validate that we have all required properties before broadcasting
            const start = model.rangeStart;
            const end = model.rangeEnd;
            const scale = model.scale;
            const date = model.date;
            
            if (!start || !end) {
                console.warn("Calendar range start/end not available for broadcasting");
                return;
            }
            
            if (!scale) {
                console.warn("Calendar scale not available for broadcasting");
                return;
            }
            
            if (!date) {
                console.warn("Calendar date not available for broadcasting");
                // Continue anyway as this is not critical
            }
            
            // Only for time off calendar dashboard envs where timeOffBus exists
            const bus = this.env && this.env.timeOffBus;
            if (!bus) {
                // Not an error, just means we're not in a time off dashboard context
                return;
            }
            
            
            // Broadcast the calendar range change event with all relevant data
            bus.trigger("calendar_range_changed", { 
                start, 
                end, 
                scale, 
                date,
                // Include additional metadata that might be useful
                rangeType: scale,
                isFullRange: scale === 'month' || scale === 'year',
                timestamp: new Date().getTime()
            });
            
            // Also trigger a general dashboard update with a small delay
            // to ensure the range change is processed first
            setTimeout(() => {
                bus.trigger("update_dashboard");
            }, 50);
        } catch (e) {
            console.error("Error broadcasting calendar range:", e);
            // Try to recover by triggering a generic update if possible
            try {
                if (this.env && this.env.timeOffBus) {
                    this.env.timeOffBus.trigger("update_dashboard");
                }
            } catch (recoveryError) {
                console.error("Failed to recover from calendar broadcast error:", recoveryError);
            }
        }
    },
});
