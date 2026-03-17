#!/usr/bin/env python
"""
Email Test Script for Horilla HRMS
Run this on your server to test email configuration
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_django_email():
    """Test email using Django's email system"""
    print("🧪 Testing Django Email System...")
    print(f"📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"🏠 Email Host: {settings.EMAIL_HOST}")
    print(f"🔌 Email Port: {settings.EMAIL_PORT}")
    print(f"👤 Email User: {settings.EMAIL_HOST_USER}")
    print(f"🔒 Use SSL: {settings.EMAIL_USE_SSL}")
    print(f"🔐 Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"⏰ Timeout: {settings.EMAIL_TIMEOUT}")
    print("-" * 50)
    
    try:
        result = send_mail(
            subject='🧪 Horilla HRMS - Email Test',
            message='''
Hello!

This is a test email from your Horilla HRMS system.

✅ Email Configuration Details:
- Host: smtp.hostinger.com
- Port: 465
- From: noreply@marketvry.com
- Display Name: Mehar Advisory
- SSL: Enabled
- Timeout: 60 seconds

If you receive this email, your email configuration is working correctly!

Best regards,
Horilla HRMS System
            ''',
            from_email='Mehar Advisory <noreply@marketvry.com>',
            recipient_list=['yogendra6378@gmail.com'],
            fail_silently=False,
        )
        
        if result:
            print("✅ SUCCESS: Test email sent successfully!")
            print(f"📨 Sent to: yogendra6378@gmail.com")
            print("📬 Please check your inbox (and spam folder)")
        else:
            print("❌ FAILED: Email was not sent")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("🔍 Check your email configuration settings")

def test_direct_smtp():
    """Test email using direct SMTP connection"""
    print("\n🔧 Testing Direct SMTP Connection...")
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = 'Mehar Advisory <noreply@marketvry.com>'
        msg['To'] = 'yogendra6378@gmail.com'
        msg['Subject'] = '🔧 Direct SMTP Test - Horilla HRMS'
        
        body = '''
Hello!

This is a direct SMTP test from Horilla HRMS.

✅ Connection Details:
- Server: smtp.hostinger.com
- Port: 465
- SSL: Enabled
- Username: noreply@marketvry.com

If you receive this email, your SMTP configuration is working!

Best regards,
Horilla HRMS System
        '''
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP_SSL('smtp.hostinger.com', 465)
        server.login('noreply@marketvry.com', 'Root@637811')
        
        # Send email
        text = msg.as_string()
        server.sendmail('noreply@marketvry.com', 'yogendra6378@gmail.com', text)
        server.quit()
        
        print("✅ SUCCESS: Direct SMTP test email sent!")
        print("📨 Sent to: yogendra6378@gmail.com")
        
    except Exception as e:
        print(f"❌ SMTP ERROR: {str(e)}")

def main():
    print("=" * 60)
    print("📧 HORILLA HRMS EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    # Test Django email
    test_django_email()
    
    # Test direct SMTP
    test_direct_smtp()
    
    print("\n" + "=" * 60)
    print("📋 TEST COMPLETED")
    print("=" * 60)
    print("📝 Instructions:")
    print("1. Check yogendra6378@gmail.com inbox")
    print("2. Check spam/junk folder if not in inbox")
    print("3. If no emails received, check server logs")
    print("4. Verify email credentials are correct")

if __name__ == "__main__":
    main()