# attendance/adms_views.py
"""
ZKTeco ADMS (iClock) Push Protocol Handlers for Horilla HRMS.
Handles handshake, data push (URL-encoded + tab-separated), and command polling.
Bypasses decorated clock_in/clock_out and calls internal functions directly.
"""

import sys
import os
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs

from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from attendance.models import Attendance, AttendanceActivity
from attendance.views.clock_in_out import (
    clock_in_attendance_and_activity,
    clock_out_attendance_and_activity,
)
from attendance.methods.utils import (
    format_time,
    shift_schedule_today,
    strtime_seconds,
)
from base.models import EmployeeShiftDay
from employee.models import Employee

# Direct file + stdout logging (reliable under Gunicorn)
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "zkteco.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def _log(msg):
    """Write to both stdout and log file."""
    line = f"[ADMS] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now().isoformat()} {line}\n")
    except Exception:
        pass

ADMS_ATT_TABLES = {"ATTLOG", "RTLOG"}

def _first(values, default=""):
    return values[0] if values else default

def _qs_get(parsed, keys, default=""):
    for key in keys:
        if key in parsed and parsed.get(key):
            return _first(parsed.get(key), default)
    return default

def _parse_datetime(timestamp_str):
    """Parse ZKTeco datetime format."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            if timezone.is_naive(dt):
                return timezone.make_aware(dt, timezone.get_current_timezone())
            return dt
        except ValueError:
            continue
    return None

def _resolve_employee(pin):
    """Match device PIN to Employee.badge_id, with BiometricEmployees fallback."""
    employee = Employee.objects.filter(badge_id=pin).first()
    if employee:
        return employee
    try:
        from biometric.models import BiometricEmployees
        mapped = BiometricEmployees.objects.filter(user_id=pin).select_related("employee_id").first()
        if mapped:
            return mapped.employee_id
        mapped = BiometricEmployees.objects.filter(ref_user_id=pin).select_related("employee_id").first()
        if mapped:
            return mapped.employee_id
    except Exception:
        pass
    return None

def _is_out_status(status, employee, attendance_dt):
    """
    Determine if this punch should be treated as an OUT punch.
    Standard IN punches are 0, 3, 4. OUT punches are 1, 2, 5.
    If the device only sends IN punches (e.g. 0), auto-toggle based on
    whether the employee already has an open IN activity today.
    """
    status_str = str(status).strip()
    if status_str in {"1", "2", "5", "out", "OUT"}:
        return True
    
    # If it's a generic or default IN punch, check for auto-toggling
    if status_str in {"", "0", "3", "4", "255"}:
        # Find if there's an open activity (clock_out is None) created BEFORE this punch today
        has_open_in = AttendanceActivity.objects.filter(
            employee_id=employee,
            attendance_date=attendance_dt.date(),
            clock_out__isnull=True,
            in_datetime__lt=attendance_dt
        ).exists()
        if has_open_in:
            return True
        
    return False

def _parse_adms_lines(raw_text, query_string=""):
    """
    Parse ADMS records from POST body. Handles:
    1. URL-encoded: table=ATTLOG&PIN=1&time=2026-03-16 15:00:00&status=0
    2. Tab-separated: ATTLOG\t1\t2026-03-16 15:00:00\t0
    3. Plain tab: 1\t2026-03-16 15:00:00\t0
    """
    records = []
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()] if raw_text else []

    if not lines and query_string:
        lines = [query_string]

    for line in lines:
        # URL-encoded format
        if "=" in line and "&" in line:
            parsed = parse_qs(line, keep_blank_values=True)
            table = _qs_get(parsed, ["table", "TABLE"], "")
            table_upper = str(table).upper()

            if not table_upper and (
                _qs_get(parsed, ["PIN", "pin"], "")
                and _qs_get(parsed, ["time", "Time", "timestamp", "Timestamp"], "")
            ):
                table_upper = "RTLOG"

            if table_upper in ADMS_ATT_TABLES:
                records.append({
                    "sn": _qs_get(parsed, ["SN", "sn"], ""),
                    "table": table_upper,
                    "pin": _qs_get(parsed, ["PIN", "pin"], ""),
                    "time": _qs_get(parsed, ["time", "Time", "timestamp", "Timestamp", "datetime", "DateTime"], ""),
                    "status": _qs_get(parsed, ["status", "Status", "punch", "Punch"], ""),
                })
            continue

        # Tab-separated: ATTLOG\tPIN\ttime\tstatus
        if line.startswith("ATTLOG\t"):
            parts = line.split("\t")
            if len(parts) >= 4:
                records.append({
                    "sn": "",
                    "table": "ATTLOG",
                    "pin": parts[1].strip(),
                    "time": parts[2].strip(),
                    "status": parts[3].strip(),
                })
            continue

        # Plain tab-separated: PIN\ttime\tstatus
        parts = line.split("\t")
        if len(parts) >= 2:
            first_col = parts[0].strip().upper()
            if first_col in ADMS_ATT_TABLES and len(parts) >= 4:
                pin = parts[1].strip()
                time_str = parts[2].strip()
                status = parts[3].strip()
            else:
                pin = parts[0].strip()
                time_str = parts[1].strip()
                status = parts[2].strip() if len(parts) > 2 else ""

            if not _parse_datetime(time_str):
                continue

            records.append({
                "sn": "",
                "table": "RTLOG",
                "pin": pin,
                "time": time_str,
                "status": status,
            })
            continue

    return records


def _process_record(record, device_sn):
    """
    Process a single attendance record by directly calling Horilla's internal
    clock_in_attendance_and_activity / clock_out_attendance_and_activity.
    This bypasses the @login_required and @hx_request_required decorators.
    """
    pin = record["pin"]
    time_str = record["time"]
    status = record.get("status", "0")

    attendance_dt = _parse_datetime(time_str)
    if not attendance_dt:
        _log(f"  Invalid timestamp: PIN={pin} time={repr(time_str)}")
        return False

    employee = _resolve_employee(pin)
    if not employee:
        _log(f"  No employee for PIN={pin}")
        return False

    is_out = _is_out_status(status, employee, attendance_dt)
    attendance_date = attendance_dt.date()
    attendance_time = attendance_dt.time()

    # Duplicate check
    if is_out:
        dup = AttendanceActivity.objects.filter(
            employee_id=employee, out_datetime=attendance_dt
        ).exists() or AttendanceActivity.objects.filter(
            employee_id=employee, attendance_date=attendance_date,
            clock_out_date=attendance_date, clock_out=attendance_time,
        ).exists()
    else:
        dup = AttendanceActivity.objects.filter(
            employee_id=employee, in_datetime=attendance_dt
        ).exists() or AttendanceActivity.objects.filter(
            employee_id=employee, attendance_date=attendance_date,
            clock_in_date=attendance_date, clock_in=attendance_time,
        ).exists()

    if dup:
        _log(f"  Duplicate: PIN={pin} Time={time_str}")
        return False

    try:
        # Get employee work info for shift details
        work_info = getattr(employee, "employee_work_info", None)
        shift = work_info.shift_id if work_info else None

        # Determine shift day and schedule
        day_name = attendance_date.strftime("%A").lower()
        try:
            day = EmployeeShiftDay.objects.get(day=day_name)
        except EmployeeShiftDay.DoesNotExist:
            _log(f"  No shift day config for '{day_name}', creating attendance directly")
            day = None

        minimum_hour = "00:00"
        start_time_sec = 0
        end_time_sec = 0

        if shift and day:
            minimum_hour, start_time_sec, end_time_sec = shift_schedule_today(
                day=day, shift=shift
            )
            # Handle night shift
            now_sec = strtime_seconds(attendance_time.strftime("%H:%M"))
            mid_day_sec = strtime_seconds("12:00")
            if start_time_sec > end_time_sec and mid_day_sec > now_sec:
                # Night shift – attendance belongs to yesterday
                date_yesterday = attendance_date - timedelta(days=1)
                day_yesterday_name = date_yesterday.strftime("%A").lower()
                try:
                    day = EmployeeShiftDay.objects.get(day=day_yesterday_name)
                    minimum_hour, start_time_sec, end_time_sec = shift_schedule_today(
                        day=day, shift=shift
                    )
                    attendance_date = date_yesterday
                except EmployeeShiftDay.DoesNotExist:
                    pass

        if not is_out:
            # Clock IN – use Horilla's internal function
            if shift and day:
                now_str = attendance_time.strftime("%H:%M")
                clock_in_attendance_and_activity(
                    employee=employee,
                    date_today=attendance_dt.date(),
                    attendance_date=attendance_date,
                    day=day,
                    now=now_str,
                    shift=shift,
                    minimum_hour=minimum_hour,
                    start_time=start_time_sec,
                    end_time=end_time_sec,
                    in_datetime=attendance_dt,
                )
            else:
                # No shift configured – create records directly
                attendance, _ = Attendance.objects.get_or_create(
                    employee_id=employee,
                    attendance_date=attendance_date,
                    defaults={
                        "attendance_clock_in_date": attendance_date,
                        "attendance_clock_in": attendance_time,
                        "minimum_hour": "00:00",
                    },
                )
                AttendanceActivity.objects.create(
                    employee_id=employee,
                    attendance_date=attendance_date,
                    clock_in_date=attendance_dt.date(),
                    clock_in=attendance_dt,
                    in_datetime=attendance_dt,
                )
        else:
            # Clock OUT – use Horilla's internal function
            now_str = attendance_time.strftime("%H:%M")
            result = clock_out_attendance_and_activity(
                employee=employee,
                date_today=attendance_dt.date(),
                now=now_str,
                out_datetime=attendance_dt,
            )
            if not result:
                # No open activity to clock out – create one with clock_out set
                _log(f"  No open clock-in found for clock-out. Creating standalone record.")
                attendance, _ = Attendance.objects.get_or_create(
                    employee_id=employee,
                    attendance_date=attendance_date,
                    defaults={
                        "attendance_clock_in_date": attendance_date,
                        "attendance_clock_in": attendance_time,
                        "minimum_hour": "00:00",
                    },
                )
                attendance.attendance_clock_out = attendance_time
                attendance.attendance_clock_out_date = attendance_dt.date()
                attendance.save(update_fields=["attendance_clock_out", "attendance_clock_out_date"])

        _log(f"  OK: PIN={pin} {'OUT' if is_out else 'IN'} Time={time_str} Employee={employee}")
        return True
    except Exception as e:
        import traceback
        _log(f"  ERROR: PIN={pin} - {str(e)}")
        _log(f"  TRACEBACK: {traceback.format_exc()}")
        return False


@csrf_exempt
@require_http_methods(["GET", "POST"])
def iclock_cdata(request):
    """Handle ZKTeco ADMS /iclock/cdata endpoint."""
    sn = request.GET.get("SN", "UNKNOWN")

    if request.method == "GET":
        _log(f"Handshake from SN={sn}")
        response_content = (
            "GET_OPTION_FROM_DEVICE=1\n"
            "ErrorDelay=60\n"
            "Delay=60\n"
            "TransInterval=1\n"
            "TransFlag=1111000000\n"
            "Realtime=1\n"
            "Encrypt=0"
        )
        return HttpResponse(response_content, content_type="text/plain")

    if request.method == "POST":
        raw_body = request.body.decode("utf-8", errors="ignore").strip()
        _log(f"POST from SN={sn}: {len(raw_body)} bytes")
        _log(f"RAW: {repr(raw_body[:1000])}")

        records = _parse_adms_lines(raw_body, request.META.get("QUERY_STRING", ""))
        _log(f"Parsed {len(records)} attendance records")

        processed = 0
        for rec in records:
            if _process_record(rec, sn):
                processed += 1

        _log(f"Processed {processed}/{len(records)} records from SN={sn}")
        return HttpResponse("OK", content_type="text/plain")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def iclock_getrequest(request):
    """Handle ADMS command polling."""
    return HttpResponse("OK", content_type="text/plain")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def iclock_ping(request):
    """Handle ADMS heartbeat."""
    return HttpResponse("OK", content_type="text/plain")
