"""
Debug script to check employee data
Usage: python manage.py check_employees
"""

from django.core.management.base import BaseCommand
from employee.models import Employee, EmployeeWorkInformation
from base.models import Company, Department, JobPosition


class Command(BaseCommand):
    help = 'Check employee data in database'

    def handle(self, *args, **options):
        # Check total employees
        total_employees = Employee.objects.count()
        self.stdout.write(f"Total Employees: {total_employees}")
        
        # Check active employees
        active_employees = Employee.objects.filter(is_active=True).count()
        self.stdout.write(f"Active Employees: {active_employees}")
        
        # Check employees with work info
        with_work_info = Employee.objects.filter(employee_work_info__isnull=False).count()
        self.stdout.write(f"Employees with work info: {with_work_info}")
        
        # List all employees
        self.stdout.write(f"\n=== ALL EMPLOYEES ===")
        for emp in Employee.objects.all()[:10]:  # Show first 10
            work_info = getattr(emp, 'employee_work_info', None)
            company = getattr(work_info, 'company_id', None) if work_info else None
            dept = getattr(work_info, 'department_id', None) if work_info else None
            
            self.stdout.write(f"{emp.badge_id} - {emp.get_full_name()} - {emp.email}")
            self.stdout.write(f"  Active: {emp.is_active}")
            self.stdout.write(f"  Company: {company}")
            self.stdout.write(f"  Department: {dept}")
            self.stdout.write("---")
        
        # Check companies
        companies = Company.objects.all()
        self.stdout.write(f"\n=== COMPANIES ({companies.count()}) ===")
        for company in companies:
            self.stdout.write(f"{company.company} (HQ: {company.hq})")
        
        # Check departments
        departments = Department.objects.all()
        self.stdout.write(f"\n=== DEPARTMENTS ({departments.count()}) ===")
        for dept in departments:
            self.stdout.write(f"{dept.department}")