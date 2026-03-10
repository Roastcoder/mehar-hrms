#!/usr/bin/env python3
"""
Bulk Employee Creation Script
Run: python manage.py shell < create_employees.py
"""

import secrets
import string
from django.contrib.auth.models import User
from employee.models import Employee
from django.db import transaction

def generate_password():
    """Generate random password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(8))

# Employee data
employees_data = [
    ("EMPMA0186", "AMIT KUMAR", "9828633224", "tigeramitkaswanjtsr@gmail.com"),
    ("EMPMA0159", "ASHOK KUMAR DUSAD", "8949450173", "akdusad236@gmail.com"),
    ("EMPMA0092", "CHANDAN SAIN", "7014355704", "sunny7014355704@gmail.com"),
    ("EMPMA0160", "DHANRAJ", "6379364154", "dhanraj637936@gmail.com"),
    ("EMPMA0090", "GIRRAJ MORYA", "9828958959", "girrajmorya1109@gmail.com"),
    ("EMPMA0172", "JASPREET KAUR", "9521880812", "kour18141@gmail.com"),
    ("EMPMA0001", "MANBHR KHANGAR", "9119207366", "manu@meharadvisory.com"),
    ("EMPMA0123", "MANSINGH MEHARA", "8107162634", "mansinghjyotimehra3031@gmail.com"),
    ("EMPMA0101", "MOHAMMAD FARUKH", "9928814338", "farukhmehar100@gmail.com"),
    ("EMPMA0002", "NIDHI AGARWAL", "8963074629", "Nidheegoyal@gmail.com"),
    ("EMPMA0168", "PARVEEN BANO", "8005997115", "parveen.bikaner@gmail.com"),
    ("EMPMA0156", "PAWAN BHUSHAN SHARMA", "9887100900", "pawansharma@meharadvisory.com"),
    ("EMPMA0045", "RAMAVTAR NEN", "8432180130", "ramavtarnain228@gmail.com"),
    ("EMPMA0003", "RAMRAJ JAT", "8104188155", "Ramrajchoudhary0418@gmail.com"),
    ("EMPMA0107", "ROHIT GAUR", "8824819917", "rohitgaur7792@gmail.com"),
    ("EMPMA0183", "SAHIL KHAN", "9664179953", "sahilbalghat@gmail.com"),
    ("EMPMA0137", "SUNIL KUMAR", "8302948586", "sunilkumargodara6@gmail.com"),
    ("EMPMA0019", "SUNIL NAIN", "9982340310", "sunilnain228@gmail.com"),
    ("EMPMA0196", "KISMAT NAGRA", "7737122520", "Kismat0773@gmail.com"),
    ("EMPMA0197", "MANISHA VERMA", "6375473072", "maniv191432@gmail.com"),
    ("EMPMA0207", "PAVAN KHANGAR", "7877248700", "PAWANKHANGAROT533@GMAIL.COM"),
    ("EMPMA0211", "BHARATI REGAR", "8433686452", "bhartiojirporiya@gmail.com"),
    ("EMPMA0213", "KUSHVEER SINGH BHATI", "9983030009", "kushveersingh7@gmail.com"),
    ("EMPMA0215", "IQBAL KHAN", "8529250750", "IKBALKHAN5493@GMAIL.COM"),
    ("EMPMA0216", "POOJA VERMA", "6375378758", "pv39189@gmail.com"),
    ("EMPMA0217", "MANISHA", "8619149125", "NISHUMAHRA824@GMAIL.COM"),
    ("EMPMA0221", "KIRNA", "9649816029", "kirnbishnoi81@gmail.com"),
    ("EMPMA0223", "SHARWAN KUMAR SAIN", "8385886030", "Sharwankumar4july@gmail.com"),
    ("EMPMA0224", "AJAY KUMAR", "8955563151", "Ajaykhoth1994@gmail.com"),
    ("EMPMA0225", "ROHIT KUMAR", "9829740276", "rohit978929@gmail.com"),
    ("EMPMA0226", "VICKY PRAJAPAT", "7014439761", "Vickeyprajapat928@gmail.com"),
    ("EMPMA0230", "HANUMAN JAT", "9079317574", "hanuman02081998@gmail.com"),
    ("EMPMA0231", "PREM KUMAR", "9828573086", "prembhakar86@gmail.com"),
    ("EMPMA0232", "IRAM", "9571383217", "Alizahayat9887@gmail.com"),
    ("EMPMA0233", "YOGENDRA SINGH", "6378110608", "Yogendra6378@gmail.com"),
    ("EMPMA0235", "SITA RAM", "9660802631", "sitaramsinhmar9169@gmail.com"),
]

created_count = 0
skipped_count = 0

for badge_id, name, phone, email in employees_data:
    # Split name
    name_parts = name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # Generate password
    password = generate_password()
    
    # Check if already exists
    if User.objects.filter(email=email).exists() or Employee.objects.filter(email=email).exists():
        print(f"SKIPPED: {name} - {email} (already exists)")
        skipped_count += 1
        continue
    
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
                badge_id=badge_id,
                employee_user_id=user,
                employee_first_name=first_name,
                employee_last_name=last_name,
                email=email,
                phone=phone
            )
            
            print(f"CREATED: {badge_id} - {name} - {email} - Password: {password}")
            created_count += 1
            
    except Exception as e:
        print(f"ERROR: {name} - {str(e)}")

print(f"\n=== SUMMARY ===")
print(f"Created: {created_count}")
print(f"Skipped: {skipped_count}")
print(f"Total: {len(employees_data)}")