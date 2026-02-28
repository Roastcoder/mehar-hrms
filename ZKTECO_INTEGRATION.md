# ZKTeco K40 Pro Integration - Testing & Configuration Guide

## 1. Test with cURL

### Test Single Attendance Entry
```bash
curl -X POST "http://hrms.meharadvisory.cloud/attendance/iclock/cdata?SN=K40PRO001" \
  -H "Content-Type: text/plain" \
  -d "ATTLOG	1	2024-01-15 09:30:00	0	0	0	0"
```

### Test Multiple Entries
```bash
curl -X POST "http://hrms.meharadvisory.cloud/attendance/iclock/cdata?SN=K40PRO001" \
  -H "Content-Type: text/plain" \
  -d "ATTLOG	1	2024-01-15 09:30:00	0	0	0	0
ATTLOG	2	2024-01-15 09:35:00	0	0	0	0
ATTLOG	1	2024-01-15 18:00:00	0	0	0	0"
```

### Test from Local Network
```bash
curl -X POST "http://192.168.1.100:8000/attendance/iclock/cdata?SN=K40PRO001" \
  -H "Content-Type: text/plain" \
  -d "ATTLOG	1	2024-01-15 09:30:00	0	0	0	0"
```

## 2. ZKTeco Device Configuration

### Step 1: Access Device Settings
1. Login to K40 Pro device admin panel
2. Go to **Communication** → **ADMS Settings**

### Step 2: Configure ADMS Push Mode
```
Server IP: hrms.meharadvisory.cloud (or your VPS IP)
Port: 80
Push Interval: 1 minute
Push URL: /attendance/iclock/cdata
```

### Step 3: Enable Push Mode
- Enable **Real-time Push**
- Enable **Auto Push**
- Set **Push Protocol**: HTTP

### Step 4: Test Connection
- Click **Test Connection** in device settings
- Check device logs for successful connection

## 3. Employee Setup in Horilla

### Map Employee Badge ID to PIN
1. Go to **Employee** → **Employee List**
2. Edit employee
3. Set **Badge ID** field to match device PIN
   - Example: If device PIN is "1", set Badge ID to "1"
   - If device PIN is "EMP001", set Badge ID to "EMP001"

### Verify Employee Shift
1. Ensure employee has a shift assigned
2. Go to **Employee** → **Work Information**
3. Assign appropriate shift

## 4. Logging & Monitoring

### View Logs
```bash
# On VPS
tail -f /path/to/horilla/logs/django.log

# Or check Gunicorn logs
tail -f /var/log/gunicorn/error.log
```

### Enable Debug Logging (settings.py)
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/path/to/horilla/logs/zkteco.log',
        },
    },
    'loggers': {
        'attendance.zkteco_views': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## 5. Troubleshooting

### Issue: Device cannot connect
**Solution:**
- Check firewall: `sudo ufw allow 80/tcp`
- Verify Nginx is running: `sudo systemctl status nginx`
- Check if port 80 is open: `netstat -tuln | grep :80`

### Issue: Employee not found
**Solution:**
- Verify Badge ID matches device PIN exactly
- Check employee is active in system
- View logs for specific error

### Issue: Duplicate entries
**Solution:**
- System automatically prevents duplicates
- Check logs to confirm duplicate detection

### Issue: Attendance not creating
**Solution:**
- Verify employee has shift assigned
- Check employee work information is complete
- Review Django logs for errors

## 6. ATTLOG Format Reference

```
ATTLOG	PIN	Timestamp	Status	Verify	WorkCode	Reserved
```

**Fields:**
- **PIN**: Employee badge ID (1-8 digits)
- **Timestamp**: YYYY-MM-DD HH:MM:SS
- **Status**: 0=Check In, 1=Check Out, 2=Break Out, 3=Break In
- **Verify**: Verification method (0=Password, 1=Fingerprint, 15=Face)
- **WorkCode**: Work code (usually 0)
- **Reserved**: Reserved field (usually 0)

## 7. Security Considerations

### Optional: Add Device Serial Number Validation
Edit `/attendance/zkteco_views.py`:

```python
ALLOWED_DEVICES = ['K40PRO001', 'K40PRO002']

def iclock_cdata(request):
    sn = request.GET.get('SN', '')
    
    if sn not in ALLOWED_DEVICES:
        logger.warning(f"Unauthorized device: {sn}")
        return HttpResponse("OK", content_type="text/plain")
    
    # ... rest of code
```

### Optional: Add IP Whitelist
In Nginx config:

```nginx
location /iclock/ {
    # Allow only local network
    allow 192.168.1.0/24;
    deny all;
    
    proxy_pass http://127.0.0.1:8000;
    # ... rest of config
}
```

## 8. Production Checklist

- [ ] Employee Badge IDs configured
- [ ] Employee shifts assigned
- [ ] Device configured with correct server URL
- [ ] Nginx configuration applied
- [ ] Firewall rules configured
- [ ] Logging enabled
- [ ] Test attendance entry successful
- [ ] Monitor logs for 24 hours

## 9. Support

For issues, check:
1. Django logs: `/path/to/horilla/logs/`
2. Nginx logs: `/var/log/nginx/`
3. Device logs: Check device admin panel
4. Database: Verify AttendanceActivity table

## 10. API Response

Device expects simple "OK" response:
```
HTTP/1.1 200 OK
Content-Type: text/plain

OK
```

System always returns "OK" to prevent device errors, even if processing fails.
Actual errors are logged for admin review.
