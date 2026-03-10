"""
Signup view for user registration with email notification
"""
import secrets
import string
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from employee.models import Employee
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings


def generate_password():
    """Generate random password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(8))


def signup(request):
    """Handle user signup"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        # Split name
        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Use provided password or generate one
        if not password:
            password = generate_password()
            password_generated = True
        else:
            password_generated = False
        
        # Validate
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'signup.html')
        
        if Employee.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'signup.html')
        
        try:
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create employee
                employee = Employee.objects.create(
                    employee_user_id=user,
                    employee_first_name=first_name,
                    employee_last_name=last_name,
                    email=email,
                    phone=phone
                )
                
                # Send email with credentials
                try:
                    email_html = f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
                            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                            .content {{ padding: 30px; }}
                            .credentials {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                            .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>Welcome to HRMS!</h1>
                                <p>Your account has been created successfully</p>
                            </div>
                            <div class="content">
                                <h2>Hi {first_name},</h2>
                                <p>Welcome to our Human Resource Management System! Your account is now ready to use.</p>
                                
                                <div class="credentials">
                                    <h3>🔐 Login Credentials</h3>
                                    <p><strong>Username:</strong> {email}</p>
                                    <p><strong>Password:</strong> {password}</p>
                                    {'<p><em>Password was auto-generated for security</em></p>' if password_generated else ''}
                                </div>
                                
                                <a href="https://hrms.meharadvisory.cloud/login/" class="btn">Login to HRMS</a>
                                
                                <p>If you have any questions, please contact our support team.</p>
                            </div>
                            <div class="footer">
                                <p>Best regards,<br>HRMS Team</p>
                                <p><small>This is an automated message. Please do not reply to this email.</small></p>
                            </div>
                        </div>
                    </body>
                    </html>
                    '''
                    
                    send_mail(
                        subject='🎉 Welcome to HRMS - Your Login Credentials',
                        message=f'Hi {first_name},\n\nWelcome to HRMS!\n\nUsername: {email}\nPassword: {password}\n\nLogin: https://hrms.meharadvisory.cloud/login/',
                        html_message=email_html,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                    messages.success(request, f'Account created! Login credentials sent to {email}')
                except Exception as e:
                    messages.success(request, f'Account created! Username: {email}, Password: {password}')
                
                return redirect('login')
                
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'signup.html')
    
    return render(request, 'signup.html')
