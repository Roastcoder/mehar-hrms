import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horilla.settings")
django.setup()

from employee.models import Employee
from attendance.models import Attendance, AttendanceActivity
import datetime

emp = Employee.objects.filter(badge_id='EMPMA0233').first()
print(f"Employee: {emp}")

time_str = '2026-03-16 15:47:17'
dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
d = dt.date()
t = dt.time()

# Attempt to save directly
try:
    att, created = Attendance.objects.get_or_create(
        employee_id=emp,
        attendance_date=d,
        defaults={
            "attendance_clock_in_date": d,
            "attendance_clock_in": t,
            "minimum_hour": "00:00",
        },
    )
    print(f"Attendance created: {created}, id: {att.id}")
    
    act = AttendanceActivity.objects.create(
        employee_id=emp,
        attendance_date=d,
        clock_in_date=d,
        clock_in=dt,
        in_datetime=dt,
    )
    print(f"Activity created, id: {act.id}")
except Exception as e:
    print(f"Exception: {e}")

