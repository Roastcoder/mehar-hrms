"""
ZKTeco Biometric Device Integration
Handles ADMS push mode for attendance data
"""

import logging
from datetime import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from attendance.models import Attendance, AttendanceActivity
from employee.models import Employee

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def iclock_cdata(request):
    """
    Handle ZKTeco device push requests
    Endpoint: /iclock/cdata
    """
    try:
        # Get device serial number
        sn = request.GET.get('SN', '')
        
        if not sn:
            logger.warning("Request received without device serial number")
            return HttpResponse("OK", content_type="text/plain")
        
        # Get attendance data from POST body
        data = request.body.decode('utf-8')
        
        if not data:
            logger.info(f"Empty data from device {sn}")
            return HttpResponse("OK", content_type="text/plain")
        
        # Parse ATTLOG data
        lines = data.strip().split('\n')
        
        for line in lines:
            if line.startswith('ATTLOG'):
                process_attlog(line, sn)
        
        logger.info(f"Successfully processed data from device {sn}")
        return HttpResponse("OK", content_type="text/plain")
        
    except Exception as e:
        logger.error(f"Error processing ZKTeco data: {str(e)}", exc_info=True)
        return HttpResponse("OK", content_type="text/plain")


def process_attlog(line, device_sn):
    """
    Process ATTLOG line from ZKTeco device
    Format: ATTLOG\tPIN\ttime\tstatus\tverify\tworkcode\treserved
    Example: ATTLOG\t1\t2024-01-15 09:30:00\t0\t0\t0\t0
    """
    try:
        parts = line.split('\t')
        
        if len(parts) < 3:
            logger.warning(f"Invalid ATTLOG format: {line}")
            return
        
        pin = parts[1].strip()
        timestamp_str = parts[2].strip()
        
        # Parse timestamp
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.error(f"Invalid timestamp format: {timestamp_str}")
            return
        
        # Find employee by badge_id (PIN)
        try:
            employee = Employee.objects.get(badge_id=pin)
        except Employee.DoesNotExist:
            logger.warning(f"Employee not found for PIN: {pin}")
            return
        
        attendance_date = timestamp.date()
        check_in_time = timestamp.time()
        
        # Check for duplicate entry
        existing_activity = AttendanceActivity.objects.filter(
            employee_id=employee,
            attendance_date=attendance_date,
            clock_in_date=attendance_date,
            clock_in=check_in_time
        ).first()
        
        if existing_activity:
            logger.info(f"Duplicate entry ignored for {employee} at {timestamp}")
            return
        
        # Create or update attendance
        with transaction.atomic():
            attendance, created = Attendance.objects.get_or_create(
                employee_id=employee,
                attendance_date=attendance_date,
                defaults={
                    'attendance_clock_in_date': attendance_date,
                    'attendance_clock_in': check_in_time,
                    'shift_id': employee.get_shift(),
                    'work_type_id': employee.get_work_type(),
                }
            )
            
            # Create attendance activity
            AttendanceActivity.objects.create(
                employee_id=employee,
                attendance_date=attendance_date,
                clock_in_date=attendance_date,
                clock_in=check_in_time,
                in_datetime=timestamp
            )
            
            logger.info(
                f"Attendance recorded: {employee} - {timestamp} - Device: {device_sn}"
            )
            
    except Exception as e:
        logger.error(f"Error processing ATTLOG: {str(e)}", exc_info=True)
