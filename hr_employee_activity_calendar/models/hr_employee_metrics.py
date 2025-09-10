"""Wrapper to expose attendance metrics on hr.employee for the calendar dashboard."""
from datetime import datetime, date, timedelta
from odoo import api, fields, models
from odoo.tools import date_utils
from pytz import timezone as _tz, UTC


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def get_attendance_metrics_public(self, employee_id=None, start_date=None, end_date=None, scale=None, **kwargs):
        """Delegate to _get_attendance_metrics and map keys for the dashboard.
        Accepts start_date/end_date as 'YYYY-MM-DD' (or ISO strings) and resolves
        employee from current user when not provided.
        """
        data = kwargs or {}
        if isinstance(data, dict) and data.get("kwargs") and isinstance(data.get("kwargs"), dict):
            data = {**data, **data["kwargs"]}

        employee_id = employee_id if employee_id is not None else data.get("employee_id")
        start_date = start_date if start_date is not None else data.get("start_date")
        end_date = end_date if end_date is not None else data.get("end_date")
        scale = (scale if scale is not None else data.get("scale") or "month").lower()
        ref_date = data.get("date")

        if not employee_id and self.env.user and self.env.user.employee_id:
            employee_id = self.env.user.employee_id.id
        if not employee_id:
            return {}

        # We allow missing start/end; will compute from ref date and scale

        try:
            emp_id_int = int(employee_id)
        except Exception:
            return {}

        emp = self.env["hr.employee"].browse(emp_id_int).exists()
        if not emp:
            return {}

        def _to_date(val):
            if isinstance(val, datetime):
                return val.date()
            s = str(val).strip()
            if "T" in s or "Z" in s or "+" in s:
                try:
                    dt_val = datetime.fromisoformat(s.replace("Z", "+00:00"))
                    return dt_val.date()
                except Exception:
                    pass
            try:
                d = fields.Date.from_string(s)
                if d:
                    return d
            except Exception:
                pass
            try:
                dt_val = fields.Datetime.from_string(s)
                if dt_val:
                    return dt_val.date()
            except Exception:
                pass
            return None

        sd = _to_date(start_date or data.get("start_date"))
        ed = _to_date(end_date or data.get("end_date"))
        if not sd or not ed:
            base = _to_date(ref_date) or fields.Date.context_today(self)
            if scale == "day":
                sd = base
                ed = base
            elif scale == "week":
                sd = date_utils.start_of(base, "week")
                ed = date_utils.end_of(base, "week")
            elif scale == "year":
                sd = date_utils.start_of(base, "year")
                ed = date_utils.end_of(base, "year")
            else:  # month default
                sd = date_utils.start_of(base, "month")
                ed = date_utils.end_of(base, "month")
        else:
            # If a calendar provides a wider range (e.g., full weeks around a month), clamp for month/year
            if scale == "month":
                base = _to_date(ref_date)
                if not base:
                    # pick a middle day between sd and ed
                    delta = (ed - sd).days
                    mid = sd + timedelta(days=delta // 2)
                    base = mid
                sd = date_utils.start_of(base, "month")
                ed = date_utils.end_of(base, "month")
            elif scale == "year":
                base = _to_date(ref_date) or sd
                sd = date_utils.start_of(base, "year")
                ed = date_utils.end_of(base, "year")

        # Date range is now normalized for the given scale

        start_str = sd.strftime('%Y-%m-%d')
        end_str = ed.strftime('%Y-%m-%d')
        total_days = (ed - sd).days + 1
        metrics = {}
        if hasattr(emp, '_get_attendance_metrics'):
            try:
                metrics = emp.sudo()._get_attendance_metrics(start_str, end_str) or {}
            except Exception:
                metrics = {}

        # Fallback computations and derived values
        expected_days = int(metrics.get("expected_work_days") or 0)
        expected_hours = float(metrics.get("expected_working_hours") or 0.0)
        present_days = int(metrics.get("present") or 0)
        actual_hours = float(metrics.get("actual_working_hours") or 0.0)

        # If base method didn't provide present/actual, compute them quickly
        if not metrics or (present_days == 0 and actual_hours == 0.0):
            dt_start = fields.Datetime.to_datetime(f"{start_str} 00:00:00")
            dt_end = fields.Datetime.to_datetime(f"{end_str} 23:59:59")
            attendances = self.env["hr.attendance"].search([
                ("employee_id", "=", emp.id),
                ("check_in", ">=", dt_start),
                ("check_out", "<=", dt_end),
            ])
            present_days = len(set(att.check_in.date() for att in attendances if att.check_in))
            actual_hours = sum(att.worked_hours for att in attendances)
            metrics.setdefault("present", present_days)
            metrics.setdefault("actual_working_hours", actual_hours)

        absent_days = metrics.get("absent")
        # Always ensure 'absent' does NOT include future days: only count up to today
        today = fields.Date.context_today(self)
        effective_end = ed if ed <= today else today
        if effective_end < sd:
            # Entire range is in the future -> no absence yet
            metrics["absent"] = 0
        else:
            # Recompute expected and present up to today
            eff_start_str = sd.strftime('%Y-%m-%d')
            eff_end_str = effective_end.strftime('%Y-%m-%d')
            expected_to_date = 0
            if hasattr(emp, '_get_attendance_metrics'):
                try:
                    m_eff = emp.sudo()._get_attendance_metrics(eff_start_str, eff_end_str) or {}
                    expected_to_date = int(m_eff.get("expected_work_days") or 0)
                except Exception:
                    expected_to_date = 0
            if not expected_to_date:
                # Fallback: approximate Mon-Fri as expected work days
                d = sd
                while d <= effective_end:
                    if d.weekday() < 5:
                        expected_to_date += 1
                    d += timedelta(days=1)

            dt_eff_start = fields.Datetime.to_datetime(f"{eff_start_str} 00:00:00")
            dt_eff_end = fields.Datetime.to_datetime(f"{eff_end_str} 23:59:59")
            attendances_eff = self.env["hr.attendance"].search([
                ("employee_id", "=", emp.id),
                ("check_in", ">=", dt_eff_start),
                ("check_out", "<=", dt_eff_end),
            ])
            present_dates = {att.check_in.date() for att in attendances_eff if att.check_in}
            present_to_date = len(present_dates)

            # Subtract Approved (validate) time off days from absence within the clamped range
            leave_recs_eff = self.env["hr.leave"].sudo().search([
                ("employee_id", "=", emp.id),
                ("state", "=", "validate"),
                ("date_from", "<=", dt_eff_end),
                ("date_to", ">=", dt_eff_start),
            ])
            leave_dates = set()
            for l in leave_recs_eff:
                try:
                    l_start_dt = fields.Datetime.to_datetime(l.date_from)
                    l_end_dt = fields.Datetime.to_datetime(l.date_to)
                    if not l_start_dt or not l_end_dt:
                        continue
                    ov_start = max(l_start_dt.date(), sd)
                    ov_end = min(l_end_dt.date(), effective_end)
                    if ov_start > ov_end:
                        continue
                    cur = ov_start
                    while cur <= ov_end:
                        # Only consider weekdays for absence accounting
                        if cur.weekday() < 5:
                            leave_dates.add(cur)
                        cur += timedelta(days=1)
                except Exception:
                    continue

            # Avoid double subtraction: do not subtract leave on days already present
            leave_exclusive = leave_dates - present_dates

            metrics["absent"] = max(expected_to_date - present_to_date - len(leave_exclusive), 0)

        # Add extras if missing
        # Last attendance worked hours in the period
        if "last_attendance_worked_hours" not in metrics:
            att_last = self.env["hr.attendance"].search([
                ("employee_id", "=", emp.id),
                ("check_in", ">=", f"{start_str} 00:00:00"),
                ("check_out", "<=", f"{end_str} 23:59:59"),
            ], order="check_out desc", limit=1)
            metrics["last_attendance_worked_hours"] = float(att_last.worked_hours or 0.0) if att_last else 0.0

        # Hours previously today (only if today in range)
        if "hours_previously_today" not in metrics:
            hours_today = 0.0
            today = fields.Date.context_today(self)
            if sd <= today <= ed:
                todays_atts = self.env["hr.attendance"].search([
                    ("employee_id", "=", emp.id),
                    ("check_in", ">=", f"{today} 00:00:00"),
                    ("check_out", "<=", f"{today} 23:59:59"),
                ])
                hours_today = sum(a.worked_hours for a in todays_atts)
            metrics["hours_previously_today"] = float(hours_today)

        if "total_overtime" not in metrics:
            metrics["total_overtime"] = float(actual_hours - expected_hours)

        # Compute Time Off days strictly from Approved leaves (state = 'validate')
        # Always override any base metric to ensure consistency with the requirement.
        dt_start = fields.Datetime.to_datetime(f"{start_str} 00:00:00")
        dt_end = fields.Datetime.to_datetime(f"{end_str} 23:59:59")
        leave_recs = self.env["hr.leave"].sudo().search([
            ("employee_id", "=", emp.id),
            ("state", "=", "validate"),
            ("date_from", "<=", dt_end),
            ("date_to", ">=", dt_start),
        ])
        time_off_days = sum(l.number_of_days or 0.0 for l in leave_recs)
        metrics["time_off_days"] = float(time_off_days)

        # Fill weekoff and holiday if missing using employee helpers and calendar timezone
        if ("weekoff" not in metrics) or ("holiday" not in metrics):
            calendar = emp.resource_calendar_id or emp.company_id.resource_calendar_id
            if calendar:
                cal_tz = _tz(calendar.tz) if calendar.tz else UTC
                sd_dt = fields.Datetime.to_datetime(f"{start_str} 00:00:00") or datetime.strptime(f"{start_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
                ed_dt = fields.Datetime.to_datetime(f"{end_str} 23:59:59") or datetime.strptime(f"{end_str} 23:59:59", "%Y-%m-%d %H:%M:%S")
                # Localize if naive
                if sd_dt.tzinfo is None:
                    sd_dt = cal_tz.localize(sd_dt)
                if ed_dt.tzinfo is None:
                    ed_dt = cal_tz.localize(ed_dt)
                # Compute weekoff days
                if "weekoff" not in metrics and hasattr(emp, "_get_weekoff_days"):
                    try:
                        metrics["weekoff"] = int(emp._get_weekoff_days(calendar, sd_dt, ed_dt) or 0)
                    except Exception:
                        metrics.setdefault("weekoff", 0)
                # Compute holiday days
                if "holiday" not in metrics and hasattr(emp, "_get_holiday_days"):
                    try:
                        holidays = emp._get_holiday_days(sd_dt, ed_dt)
                        if isinstance(holidays, (set, list, tuple)):
                            metrics["holiday"] = len(holidays)
                        else:
                            metrics["holiday"] = len(holidays) if isinstance(holidays, (set, list, tuple)) else int(holidays or 0)
                    except Exception:
                        metrics.setdefault("holiday", 0)

        # Derive daily presence transitions if not provided
        need_transitions = not any(k in metrics for k in ("days_pp", "days_pa", "days_ap", "days_aa", "days_p|p"))
        if need_transitions:
            # Get attendance dates in the period
            dt_start = fields.Datetime.to_datetime(f"{start_str} 00:00:00")
            dt_end = fields.Datetime.to_datetime(f"{end_str} 23:59:59")
            att_recs = self.env["hr.attendance"].search([
                ("employee_id", "=", emp.id),
                ("check_in", ">=", dt_start),
                ("check_out", "<=", dt_end),
            ])
            att_dates = {a.check_in.date() for a in att_recs if a.check_in}
            # Consider Monday-Friday as expected working days for transitions
            # Do not count future days in transitions
            d = sd
            end_for_transitions = ed if ed <= today else today
            flags = []  # 'P' or 'A'
            while d <= end_for_transitions:
                if d.weekday() < 5:  # 0..4 are weekdays
                    flags.append('P' if d in att_dates else 'A')
                d += timedelta(days=1)
            pp = pa = ap = aa = 0
            for i in range(1, len(flags)):
                pair = flags[i - 1] + flags[i]
                if pair == 'PP':
                    pp += 1
                elif pair == 'PA':
                    pa += 1
                elif pair == 'AP':
                    ap += 1
                elif pair == 'AA':
                    aa += 1
            metrics.update({
                "days_pp": pp,
                "days_pa": pa,
                "days_ap": ap,
                "days_aa": aa,
            })

        result = {
            "last_attendance_worked_hours": metrics.get("last_attendance_worked_hours", 0),
            "hours_previously_today": metrics.get("hours_previously_today", 0),
            "total_overtime": metrics.get("total_overtime", 0),
            "total_days": metrics.get("total_days", total_days),
            "time_off_days": metrics.get("time_off_days", 0),
            "expected_work_days": metrics.get("expected_work_days", 0),
            "expected_working_hours": metrics.get("expected_working_hours", 0),
            "weekoff": metrics.get("weekoff", 0),
            "holiday": metrics.get("holiday", 0),
            "present": metrics.get("present", 0),
            "actual_working_hours": metrics.get("actual_working_hours", 0),
            "absent": metrics.get("absent", 0),
            "days_pp": metrics.get("days_pp", metrics.get("days_p|p", 0)),
            "days_pa": metrics.get("days_pa", metrics.get("days_p|a", 0)),
            "days_ap": metrics.get("days_ap", metrics.get("days_a|p", 0)),
            "days_aa": metrics.get("days_aa", metrics.get("days_a|a", 0)),
            # Include pipe keys as well for compatibility
            "days_p|p": metrics.get("days_p|p", metrics.get("days_pp", 0)),
            "days_p|a": metrics.get("days_p|a", metrics.get("days_pa", 0)),
            "days_a|p": metrics.get("days_a|p", metrics.get("days_ap", 0)),
            "days_a|a": metrics.get("days_a|a", metrics.get("days_aa", 0)),
        }

        # Also echo back the period and employee for reference in UI
        result.update({
            "employee_id": emp.id,
            "start_date": start_str,
            "end_date": end_str,
            "scale": scale,
        })
        return result
        