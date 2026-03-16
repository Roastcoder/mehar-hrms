"""
Management command to send credentials or password reset links to all users
"""

import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from employee.models import Employee

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send credentials or password reset links to all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--domain',
            type=str,
            default='hrms.meharadvisory.cloud',
            help='Domain for password reset links',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        domain = options['domain']
        
        users = User.objects.filter(is_active=True)
        sent_count = 0
        error_count = 0
        
        self.stdout.write(f"Processing {users.count()} users...")
        
        for user in users:
            try:
                employee = None
                try:
                    employee = user.employee_get
                except:
                    pass
                
                # Check if user has a usable password
                if user.has_usable_password():
                    # Send credentials email
                    success = self.send_credentials_email(user, employee, domain, dry_run)
                else:
                    # Send password reset email
                    success = self.send_password_reset_email(user, employee, domain, dry_run)
                
                if success:
                    sent_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing user {user.username}: {str(e)}')
                )
                error_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN: Would send {sent_count} emails, {error_count} errors')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Sent {sent_count} emails successfully, {error_count} errors')
            )

    def send_credentials_email(self, user, employee, domain, dry_run):
        """Send email with login credentials"""
        try:
            subject = 'Your Mehar Advisory HRMS Login Credentials'
            
            context = {
                'user': user,
                'employee': employee,
                'domain': domain,
                'username': user.username,
                'login_url': f'https://{domain}/login/',
                'company_name': 'Mehar Advisory'
            }
            
            # Create email content
            message = f"""
Dear {employee.get_full_name() if employee else user.get_full_name() or user.username},

Welcome to Mehar Advisory HRMS!

Your login credentials are:
- Username: {user.username}
- Login URL: https://{domain}/login/

Please log in to access your employee portal and update your profile information.

If you have forgotten your password, you can reset it using the "Forgot Password" link on the login page.

Best regards,
Mehar Advisory HR Team
            """
            
            if dry_run:
                self.stdout.write(f'Would send credentials email to: {user.email}')
                return True
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            self.stdout.write(f'Sent credentials email to: {user.email}')
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send credentials email to {user.email}: {str(e)}')
            )
            return False

    def send_password_reset_email(self, user, employee, domain, dry_run):
        """Send password reset email"""
        try:
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            subject = 'Set Your Mehar Advisory HRMS Password'
            
            reset_url = f'https://{domain}/password-reset-confirm/{uid}/{token}/'
            
            message = f"""
Dear {employee.get_full_name() if employee else user.get_full_name() or user.username},

Welcome to Mehar Advisory HRMS!

Your account has been created. Please set your password by clicking the link below:

{reset_url}

Your username is: {user.username}

After setting your password, you can log in at: https://{domain}/login/

This link will expire in 24 hours for security reasons.

Best regards,
Mehar Advisory HR Team
            """
            
            if dry_run:
                self.stdout.write(f'Would send password reset email to: {user.email}')
                return True
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            self.stdout.write(f'Sent password reset email to: {user.email}')
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send password reset email to {user.email}: {str(e)}')
            )
            return False