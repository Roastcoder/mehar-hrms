"""
Attendance location tracking views
"""
import json
from datetime import date, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from attendance.models import AttendanceActivity
from geofencing.models import GeoFencing
from base.methods import filtersubordinates


@login_required
def attendance_location_map(request):
    """
    Display attendance locations on a map
    """
    # Get date range from request or default to today
    start_date = request.GET.get('start_date', date.today())
    end_date = request.GET.get('end_date', date.today())
    
    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)
    if isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)
    
    # Get attendance activities with location data
    activities = AttendanceActivity.objects.filter(
        Q(clock_in_latitude__isnull=False) | Q(clock_out_latitude__isnull=False),
        attendance_date__range=[start_date, end_date]
    ).select_related('employee_id')
    
    # Filter based on permissions
    activities = filtersubordinates(
        request, 
        activities, 
        perm='attendance.view_attendanceactivity',
        field='employee_id'
    )
    
    # Prepare data for map
    attendance_locations = []
    for activity in activities:
        attendance_locations.append({
            'employee': activity.employee_id.get_full_name(),
            'date': str(activity.attendance_date),
            'clock_in_time': activity.clock_in.strftime('%I:%M %p') if activity.clock_in else None,
            'clock_in_lat': float(activity.clock_in_latitude) if activity.clock_in_latitude else None,
            'clock_in_lng': float(activity.clock_in_longitude) if activity.clock_in_longitude else None,
            'clock_out_time': activity.clock_out.strftime('%I:%M %p') if activity.clock_out else None,
            'clock_out_lat': float(activity.clock_out_latitude) if activity.clock_out_latitude else None,
            'clock_out_lng': float(activity.clock_out_longitude) if activity.clock_out_longitude else None,
        })
    
    # Get company geofence
    geofence = None
    try:
        company = request.user.employee_get.get_company()
        geofence = GeoFencing.objects.filter(company_id=company).first()
    except:
        pass
    
    # Calculate map center
    center_lat = geofence.latitude if geofence else 0
    center_lng = geofence.longitude if geofence else 0
    
    context = {
        'attendance_locations': json.dumps(attendance_locations),
        'geofence': geofence,
        'center_lat': center_lat,
        'center_lng': center_lng,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'attendance_location_map.html', context)
