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
        print("ED", ed, "SD", sd, "START", start_str, "END", end_str)
        print("Days -- ", (ed - sd).days)
        total_days = (ed - sd).days + 1
        print("Total Days", total_days)
        print("$$$$$$$$$$$$$$")
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
        if absent_days is None:
            absent_days = max(expected_days - present_days, 0)
            metrics["absent"] = absent_days

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

        # Compute Time Off days from base model (approved hr.leave overlapping the period)
        # Sum number_of_days, which accounts for the employee calendar.
        # Keep as float in metrics, but UI can display rounded if desired.
        if "time_off_days" not in metrics:
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
                            metrics["holiday"] = int(holidays or 0)
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
            d = sd
            flags = []  # 'P' or 'A'
            while d <= ed:
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

        # Debug logging
        # print(f"EmployeeMetrics: {emp.name} (ID: {emp_id_int})")
        # print(f"Period: {start_str} to {end_str} (scale: {scale})")
        # print(f"Period start month name: {sd.strftime('%B')}, period end month name: {ed.strftime('%B')}, period start month: {sd.month}, period end month: {ed.month}, period year: {sd.year}")
        # print(f"Expected date range for {scale} view: {sd.strftime('%Y-%m-%d')} to {ed.strftime('%Y-%m-%d')}")
        # print(f"Metrics calculated: {len(metrics)} fields")
        # print(f"Key metrics: present={metrics.get('present', 0)}, absent={metrics.get('absent', 0)}, expected_days={metrics.get('expected_work_days', 0)}")
        # print(f"Expected work hours: {metrics.get('expected_working_hours', 0)}")
        # print(f"Calendar: {emp.resource_calendar_id.name if emp.resource_calendar_id else 'None'}")

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
        