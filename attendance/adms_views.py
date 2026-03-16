# attendance/adms_views.py
"""
ZKTeco ADMS (iClock) Push Protocol Handlers for Horilla HRMS.
This module handles the handshake, data push, and command polling from ZKTeco devices.
"""

import logging
from datetime import datetime
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from attendance.models import Attendance, AttendanceActivity
from employee.models import Employee
from attendance.methods.utils import Request
from attendance.views.clock_in_out import clock_in, clock_out

logger = logging.getLogger('attendance.adms')

def _parse_datetime(timestamp_str):
    """Parse ZKTeco datetime format: YYYY-MM-DD HH:MM:SS"""
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
    """Match device PIN to Employee.badge_id"""
    return Employee.objects.filter(badge_id=pin).first()

def _process_attlog_line(line, device_sn):
    """
    Parse a single ATTLOG line and create attendance record.
    Line format: ATTLOG <PIN> <Timestamp> <Status> <Verify> <WorkCode> <Reserved>
    Status: 0=Check-In, 1=Check-Out, 2=Break-Out, 3=Break-In, 4=Overtime-In, 5=Overtime-Out
    """
    parts = line.split('\t')
    if len(parts) < 3:
        return False

    # Skip header if present
    if parts[0] == "ATTLOG":
        parts = parts[1:]

    if len(parts) < 2:
        return False

    pin = parts[0].strip()
    time_str = parts[1].strip()
    status = parts[2].strip() if len(parts) > 2 else "0"

    attendance_dt = _parse_datetime(time_str)
    if not attendance_dt:
        logger.warning(f"Invalid timestamp from SN={device_sn}: {time_str}")
        return False

    employee = _resolve_employee(pin)
    if not employee:
        logger.warning(f"No employee found for PIN={pin} (SN={device_sn})")
        return False

    # Check for exact duplicate activity
    is_out = status in ["1", "2", "5"]
    attendance_date = attendance_dt.date()
    attendance_time = attendance_dt.time()

    if AttendanceActivity.objects.filter(
        employee_id=employee,
        attendance_date=attendance_date,
        clock_in=attendance_time if not is_out else None,
        clock_out=attendance_time if is_out else None,
    ).exists():
        logger.info(f"Duplicate log ignored: PIN={pin} Time={time_str}")
        return False

    try:
        if employee.employee_user_id:
            # Use Horilla's standard clock_in/out flow if user exists
            biometric_request = Request(
                user=employee.employee_user_id,
                date=attendance_date,
                time=attendance_time,
                datetime=attendance_dt,
            )
            if is_out:
                clock_out(biometric_request)
            else:
                clock_in(biometric_request)
        else:
            # Fallback to manual creation if no user object (common in some LDAP/Biometric setups)
            attendance, created = Attendance.objects.get_or_create(
                employee_id=employee,
                attendance_date=attendance_date,
                defaults={
                    "attendance_clock_in_date": attendance_date,
                    "attendance_clock_in": attendance_time,
                    "shift_id": employee.get_shift(),
                    "work_type_id": employee.get_work_type(),
                },
            )

            if not is_out:
                if attendance.attendance_clock_in is None or attendance.attendance_clock_in > attendance_time:
                    attendance.attendance_clock_in = attendance_time
                    attendance.attendance_clock_in_date = attendance_date
                    attendance.save(update_fields=["attendance_clock_in", "attendance_clock_in_date"])
                
                AttendanceActivity.objects.create(
                    employee_id=employee,
                    attendance_date=attendance_date,
                    clock_in_date=attendance_date,
                    clock_in=attendance_time,
                    in_datetime=attendance_dt,
                )
            else:
                attendance.attendance_clock_out = attendance_time
                attendance.attendance_clock_out_date = attendance_date
                attendance.save(update_fields=["attendance_clock_out", "attendance_clock_out_date"])

                open_activity = AttendanceActivity.objects.filter(
                    employee_id=employee,
                    attendance_date=attendance_date,
                    clock_out__isnull=True,
                ).order_by("-in_datetime").first()
                
                if open_activity:
                    open_activity.clock_out = attendance_time
                    open_activity.clock_out_date = attendance_date
                    open_activity.out_datetime = attendance_dt
                    open_activity.save(update_fields=["clock_out", "clock_out_date", "out_datetime"])

        logger.info(f"Attendance recorded: PIN={pin} Status={'OUT' if is_out else 'IN'} Time={time_str}")
        return True
    except Exception as e:
        logger.error(f"Error processing PIN={pin}: {str(e)}")
        return False

@csrf_exempt
@require_http_methods(["GET", "POST"])
def iclock_cdata(request):
    """
    Handle ZKTeco ADMS push protocol endpoint `/iclock/cdata`.
    """
    sn = request.GET.get('SN', 'UNKNOWN')
    
    # Handshake (GET)
    if request.method == "GET":
        logger.info(f"Handshake from SN={sn}")
        # Standard ADMS configuration response
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

    # Log Push (POST)
    if request.method == "POST":
        raw_body = request.body.decode("utf-8", errors="ignore").strip()
        logger.info(f"Log push from SN={sn}: {len(raw_body)} bytes")
        
        lines = raw_body.splitlines()
        processed_count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if _process_attlog_line(line, sn):
                processed_count += 1
        
        logger.info(f"Processed {processed_count}/{len(lines)} logs from SN={sn}")
        return HttpResponse("OK", content_type="text/plain")

@csrf_exempt
@require_http_methods(["GET", "POST"])
def iclock_getrequest(request):
    """
    Handle ADMS getrequest calls (device polling for commands).
    """
    sn = request.GET.get('SN', 'UNKNOWN')
    # logger.debug(f"Command poll from SN={sn}")
    return HttpResponse("OK", content_type="text/plain")

@csrf_exempt
@require_http_methods(["GET", "POST"])
def iclock_ping(request):
    """
    Handle ADMS ping heartbeat.
    """
    # sn = request.GET.get('SN', 'UNKNOWN')
    return HttpResponse("OK", content_type="text/plain")
