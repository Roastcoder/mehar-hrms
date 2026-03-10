"""
Django management command to add work information to employees
Usage: python manage.py setup_employee_work_info
"""

from django.core.management.base import BaseCommand
from employee.models import Employee, EmployeeWorkInformation
from base.models import Company, Department, JobPosition
from django.db import transaction


class Command(BaseCommand):
    help = 'Add work information to employees without work info'

    def handle(self, *args, **options):
        # Get or create default company
        company, created = Company.objects.get_or_create(
            company='Mehar Advisory',
            defaults={'hq': True}
        )
        if created:
            self.stdout.write(f"Created company: {company}")

        # Get or create default department
        department, created = Department.objects.get_or_create(
            department='General',
            defaults={'company_id': company}
        )
        if created:
            self.stdout.write(f"Created department: {department}")

        # Get or create default job position
        job_position, created = JobPosition.objects.get_or_create(
            job_position='Employee',
            defaults={'department_id': department}
        )
        if created:
            self.stdout.write(f"Created job position: {job_position}")

        # Find employees without work information
        employees_without_work_info = Employee.objects.filter(
            employee_work_info__isnull=True
        )

        created_count = 0
        updated_count = 0

        self.stdout.write(f"Found {employees_without_work_info.count()} employees without work info")

        for employee in employees_without_work_info:
            try:
                with transaction.atomic():
                    work_info, created = EmployeeWorkInformation.objects.get_or_create(
                        employee_id=employee,
                        defaults={
                            'company_id': company,
                            'department_id': department,
                            'job_position_id': job_position,
                            'email': employee.email,
                            'mobile': employee.phone,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f"Created work info for: {employee.get_full_name()}")
                    else:
                        # Update existing work info
                        work_info.company_id = company
                        work_info.department_id = department
                        work_info.job_position_id = job_position
                        if not work_info.email:
                            work_info.email = employee.email
                        if not work_info.mobile:
                            work_info.mobile = employee.phone
                        work_info.save()
                        updated_count += 1
                        self.stdout.write(f"Updated work info for: {employee.get_full_name()}")
                        
            except Exception as e:
                self.stdout.write(f"Error processing {employee.get_full_name()}: {str(e)}")

        self.stdout.write(f"\n=== SUMMARY ===")
        self.stdout.write(f"Work info created: {created_count}")
        self.stdout.write(f"Work info updated: {updated_count}")
        self.stdout.write(self.style.SUCCESS('Work information setup completed!'))