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
        
        # Split name
        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Generate password
        password = generate_password()
        
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
                    send_mail(
                        subject='Welcome to HRMS - Your Login Credentials',
                        message=f'''
Hi {first_name},

Welcome to HRMS! Your account has been created successfully.

Login Details:
Username: {email}
Password: {password}

Please login at: https://hrms.meharadvisory.cloud/login/

Best regards,
HRMS Team
                        ''',
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
