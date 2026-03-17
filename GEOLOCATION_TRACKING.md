# Geolocation Tracking for Attendance

## Overview
This feature allows you to track and visualize where employees marked their attendance when geofencing is enabled.

## What Was Added

### 1. Database Fields
Added 4 new fields to `AttendanceActivity` model:
- `clock_in_latitude` - Stores latitude when employee clocks in
- `clock_in_longitude` - Stores longitude when employee clocks in
- `clock_out_latitude` - Stores latitude when employee clocks out
- `clock_out_longitude` - Stores longitude when employee clocks out

### 2. Location Map View
A new interactive map view to visualize attendance locations:
- **URL**: `/attendance/attendance-location-map/`
- **Features**:
  - Shows company geofence boundary (blue circle)
  - Blue markers for clock-in locations
  - Red markers for clock-out locations
  - Click markers to see employee name, time, and date
  - Filter by date range

### 3. Automatic Location Capture
When employees clock in/out via the mobile app or web with geofencing enabled:
- Their GPS coordinates are automatically captured
- Location is validated against company geofence
- Coordinates are stored in the database

## How to Use

### Step 1: Run Migration
On your server, run:
```bash
python manage.py migrate attendance
```

### Step 2: Access the Map
Navigate to: `https://hrms.meharadvisory.cloud/attendance/attendance-location-map/`

### Step 3: View Attendance Locations
- The map will show all attendance locations for today by default
- Use date filters to view historical data
- Blue markers = Clock In locations
- Red markers = Clock Out locations
- Blue circle = Company allowed geofence area

## Requirements
- Geofencing must be enabled in settings
- Employees must allow location access on their devices
- Location data is only captured when geofencing validation passes

## Privacy Note
Location data is only captured during clock in/out events and is used solely for attendance verification purposes.

## Technical Details
- Uses Leaflet.js for interactive maps
- OpenStreetMap for map tiles
- Stores coordinates as Float fields in PostgreSQL
- Permission-based access (managers can see their team's locations)
