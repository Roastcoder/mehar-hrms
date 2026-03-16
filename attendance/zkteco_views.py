"""
ZKTeco ADMS push endpoint handlers.
"""

import logging
from datetime import datetime
from urllib.parse import parse_qs

from django.http import HttpResponse
from django.core.cache import cache
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from attendance.methods.utils import Request
from attendance.models import Attendance, AttendanceActivity
from attendance.views.clock_in_out import clock_in
from employee.models import Employee

logger = logging.getLogger(__name__)
ADMS_LAST_SEEN_ANY_KEY = "zkteco_adms_last_seen_any"
ADMS_LAST_SEEN_SN_PREFIX = "zkteco_adms_last_seen_sn_"


def _first(values, default=""):
    if not values:
        return default
    return values[0]


def _parse_datetime(timestamp_str):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            if timezone.is_naive(dt):
                return timezone.make_aware(dt, timezone.get_current_timezone())
            return dt
        except ValueError:
            continue
    return None


def _parse_adms_lines(raw_text, query_string):
    """
    Parse ADMS key/value records and return normalized dictionaries.
    """
    records = []
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()] if raw_text else []

    if not lines and query_string:
        lines = [query_string]

    for line in lines:
        # Backward compatibility for tab-separated ATTLOG payloads
        if line.startswith("ATTLOG\t"):
            parts = line.split("\t")
            if len(parts) >= 4:
                records.append(
                    {
                        "sn": "",
                        "table": "ATTLOG",
                        "pin": parts[1].strip(),
                        "time": parts[2].strip(),
                        "status": parts[3].strip(),
                    }
                )
            continue

        parsed = parse_qs(line, keep_blank_values=True)
        records.append(
            {
                "sn": _first(parsed.get("SN"), ""),
                "table": _first(parsed.get("table"), ""),
                "pin": _first(parsed.get("PIN"), ""),
                "time": _first(parsed.get("time"), ""),
                "status": _first(parsed.get("status"), ""),
            }
        )

    return records


def _create_or_update_attendance(employee, attendance_dt, device_sn, status):
    """
    Mark biometric check-in using Horilla clock_in flow and dedupe by exact timestamp.
    """
    attendance_date = attendance_dt.date()
    attendance_time = attendance_dt.time()

    duplicate_exists = AttendanceActivity.objects.filter(
        employee_id=employee,
        in_datetime=attendance_dt,
    ).exists() or AttendanceActivity.objects.filter(
        employee_id=employee,
        attendance_date=attendance_date,
        clock_in_date=attendance_date,
        clock_in=attendance_time,
    ).exists()

    if duplicate_exists:
        logger.info(
            "Duplicate biometric log ignored. device_sn=%s pin=%s time=%s status=%s",
            device_sn,
            employee.badge_id,
            attendance_dt.isoformat(),
            status,
        )
        return False

    # Source is biometric by using the biometric flow (request.datetime is consumed by clock_in)
    if employee.employee_user_id:
        biometric_request = Request(
            user=employee.employee_user_id,
            date=attendance_date,
            time=attendance_time,
            datetime=attendance_dt,
        )
        clock_in(biometric_request)
    else:
        attendance, _ = Attendance.objects.get_or_create(
            employee_id=employee,
            attendance_date=attendance_date,
            defaults={
                "attendance_clock_in_date": attendance_date,
                "attendance_clock_in": attendance_time,
                "shift_id": employee.get_shift(),
                "work_type_id": employee.get_work_type(),
            },
        )
        if (
            attendance.attendance_clock_in is None
            or attendance.attendance_clock_in > attendance_time
        ):
            attendance.attendance_clock_in = attendance_time
            attendance.attendance_clock_in_date = attendance_date
            attendance.shift_id = attendance.shift_id or employee.get_shift()
            attendance.work_type_id = attendance.work_type_id or employee.get_work_type()
            attendance.save(
                update_fields=[
                    "attendance_clock_in",
                    "attendance_clock_in_date",
                    "shift_id",
                    "work_type_id",
                ]
            )

        AttendanceActivity.objects.create(
            employee_id=employee,
            attendance_date=attendance_date,
            clock_in_date=attendance_date,
            clock_in=attendance_time,
            in_datetime=attendance_dt,
        )

    logger.info(
        "Biometric attendance accepted. source=biometric device_sn=%s pin=%s time=%s status=%s",
        device_sn,
        employee.badge_id,
        attendance_dt.isoformat(),
        status,
    )
    return True


@csrf_exempt
@require_http_methods(["POST", "GET"])
def iclock_cdata(request):
    """
    Handle ZKTeco ADMS push protocol endpoint `/iclock/cdata`.
    """
    raw_body = request.body.decode("utf-8", errors="ignore").strip()
    query_string = request.META.get("QUERY_STRING", "")
    remote_ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))

    logger.info(
        "ZKTeco /iclock/cdata request: method=%s ip=%s query=%s body=%s",
        request.method,
        remote_ip,
        query_string,
        raw_body[:2000],
    )
    now_iso = timezone.now().isoformat()
    cache.set(ADMS_LAST_SEEN_ANY_KEY, now_iso, timeout=60 * 60 * 24)

    try:
        records = _parse_adms_lines(raw_body, query_string)
        processed = 0

        for record in records:
            table = (record.get("table") or "").upper()
            if table and table != "ATTLOG":
                continue

            device_sn = (record.get("sn") or request.GET.get("SN") or "").strip()
            if device_sn:
                cache.set(
                    f"{ADMS_LAST_SEEN_SN_PREFIX}{device_sn}",
                    now_iso,
                    timeout=60 * 60 * 24,
                )
            pin = (record.get("pin") or "").strip()
            time_str = (record.get("time") or "").strip()
            status = (record.get("status") or "").strip()

            if not pin or not time_str:
                continue

            attendance_dt = _parse_datetime(time_str)
            if not attendance_dt:
                logger.warning(
                    "Invalid attendance timestamp ignored. device_sn=%s pin=%s time=%s",
                    device_sn,
                    pin,
                    time_str,
                )
                continue

            employee = Employee.objects.filter(badge_id=pin).first()
            if not employee:
                logger.warning(
                    "No employee found for biometric PIN. device_sn=%s pin=%s",
                    device_sn,
                    pin,
                )
                continue

            if _create_or_update_attendance(employee, attendance_dt, device_sn, status):
                processed += 1

        logger.info("ZKTeco /iclock/cdata completed. processed=%s", processed)
    except Exception:
        logger.exception("Unhandled error in ZKTeco /iclock/cdata")

    return HttpResponse("OK", status=200, content_type="text/plain")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def iclock_ping(request):
    """
    Handle ADMS ping probes from devices.
    """
    logger.info(
        "ZKTeco ping request: path=%s query=%s",
        request.path,
        request.META.get("QUERY_STRING", ""),
    )
    now_iso = timezone.now().isoformat()
    cache.set(ADMS_LAST_SEEN_ANY_KEY, now_iso, timeout=60 * 60 * 24)
    sn = request.GET.get("SN", "").strip()
    if sn:
        cache.set(f"{ADMS_LAST_SEEN_SN_PREFIX}{sn}", now_iso, timeout=60 * 60 * 24)
    return HttpResponse("OK", status=200, content_type="text/plain")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def iclock_getrequest(request):
    """
    Handle ADMS getrequest calls (device polling for commands).
    """
    logger.info(
        "ZKTeco getrequest: path=%s query=%s",
        request.path,
        request.META.get("QUERY_STRING", ""),
    )
    now_iso = timezone.now().isoformat()
    cache.set(ADMS_LAST_SEEN_ANY_KEY, now_iso, timeout=60 * 60 * 24)
    sn = request.GET.get("SN", "").strip()
    if sn:
        cache.set(f"{ADMS_LAST_SEEN_SN_PREFIX}{sn}", now_iso, timeout=60 * 60 * 24)
    return HttpResponse("OK", status=200, content_type="text/plain")
