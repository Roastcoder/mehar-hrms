"""
Django management command to test email configuration
Usage: python manage.py test_email yogendra6378@gmail.com
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            nargs='?',
            default='yogendra6378@gmail.com',
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write("=" * 60)
        self.stdout.write("📧 TESTING EMAIL CONFIGURATION")
        self.stdout.write("=" * 60)
        
        # Display current settings
        self.stdout.write(f"📧 Email Backend: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
        self.stdout.write(f"🏠 Email Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        self.stdout.write(f"🔌 Email Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        self.stdout.write(f"👤 Email User: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
        self.stdout.write(f"🔒 Use SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}")
        self.stdout.write(f"🔐 Use TLS: {getattr(settings, 'EMAIL_USE_TLS', False)}")
        self.stdout.write(f"⏰ Timeout: {getattr(settings, 'EMAIL_TIMEOUT', 'Not set')}")
        self.stdout.write(f"📨 Sending to: {email}")
        self.stdout.write("-" * 60)
        
        # Test Django email
        try:
            result = send_mail(
                subject='🧪 Horilla HRMS - Email Configuration Test',
                message=f'''
Hello!

This is a test email from your Horilla HRMS system.

✅ Email Configuration Test Results:
- Host: {getattr(settings, 'EMAIL_HOST', 'Not configured')}
- Port: {getattr(settings, 'EMAIL_PORT', 'Not configured')}
- From: {getattr(settings, 'EMAIL_HOST_USER', 'Not configured')}
- SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}
- TLS: {getattr(settings, 'EMAIL_USE_TLS', False)}
- Timeout: {getattr(settings, 'EMAIL_TIMEOUT', 'Not set')} seconds

✅ Test Status: SUCCESS
📅 Test Date: {self.get_current_datetime()}

If you receive this email, your Horilla HRMS email configuration is working correctly!

You can now:
- Send employee notifications
- Send leave approval emails
- Send attendance reports
- Send system alerts

Best regards,
Horilla HRMS System
                ''',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=[email],
                fail_silently=False,
            )
            
            if result:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ SUCCESS: Test email sent to {email}")
                )
                self.stdout.write("📬 Please check inbox and spam folder")
            else:
                self.stdout.write(
                    self.style.ERROR("❌ FAILED: Email was not sent")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ ERROR: {str(e)}")
            )
            self.stdout.write("🔍 Please check your email configuration")
            
            # Try direct SMTP test
            self.test_direct_smtp(email)
    
    def test_direct_smtp(self, email):
        """Test direct SMTP connection"""
        self.stdout.write("\n🔧 Trying direct SMTP connection...")
        
        try:
            # Get settings
            host = getattr(settings, 'EMAIL_HOST', 'smtp.hostinger.com')
            port = getattr(settings, 'EMAIL_PORT', 465)
            username = getattr(settings, 'EMAIL_HOST_USER', 'noreply@marketvry.com')
            password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = 'Mehar Advisory <noreply@marketvry.com>'
            msg['To'] = email
            msg['Subject'] = '🔧 Direct SMTP Test - Horilla HRMS'
            
            body = f'''
Hello!

This is a direct SMTP test from Horilla HRMS.

✅ SMTP Connection Details:
- Server: {host}
- Port: {port}
- Username: {username}
- SSL: Enabled

✅ Test Status: SUCCESS
📅 Test Date: {self.get_current_datetime()}

Your SMTP configuration is working correctly!

Best regards,
Horilla HRMS System
            '''
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Create SMTP session
            if port == 465:
                server = smtplib.SMTP_SSL(host, port)
            else:
                server = smtplib.SMTP(host, port)
                if getattr(settings, 'EMAIL_USE_TLS', False):
                    server.starttls()
            
            server.login(username, password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(username, email, text)
            server.quit()
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ SMTP SUCCESS: Direct test email sent to {email}")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ SMTP ERROR: {str(e)}")
            )
    
    def get_current_datetime(self):
        """Get current datetime as string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")