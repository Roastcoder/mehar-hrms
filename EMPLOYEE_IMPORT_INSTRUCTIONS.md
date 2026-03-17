# Employee Import Template - Instructions

## 📋 Template File
**File**: `employee_import_template.csv`

## 📝 Field Descriptions

### **Required Fields** (Must be filled)
1. **badge_id** - Unique employee ID/badge number (e.g., EMP001, EMP002)
2. **employee_first_name** - First name of employee
3. **email** - Unique email address (must be unique for each employee)
4. **phone** - Phone number (can be empty string if not available)

### **Personal Information**
5. **employee_last_name** - Last name of employee (optional)
6. **address** - Full address
7. **country** - Country name (e.g., India, USA)
8. **state** - State/Province name
9. **city** - City name
10. **zip** - Postal/ZIP code
11. **dob** - Date of birth (Format: YYYY-MM-DD, e.g., 1990-01-15)
12. **gender** - Gender (Options: male, female, other)
13. **qualification** - Educational qualification
14. **experience** - Years of experience (number)
15. **marital_status** - Marital status (Options: single, married, divorced, widowed)
16. **children** - Number of children (number, 0 if none)

### **Emergency Contact**
17. **emergency_contact** - Emergency contact phone number
18. **emergency_contact_name** - Emergency contact person name
19. **emergency_contact_relation** - Relationship (e.g., Spouse, Father, Mother, Brother, Sister)

### **Work Information**
20. **date_joining** - Joining date (Format: YYYY-MM-DD, e.g., 2024-01-01)
21. **department** - Department name (must exist in system)
22. **job_position** - Job position/title (must exist in system)
23. **job_role** - Job role (must exist in system)
24. **employee_type** - Employment type (must exist in system, e.g., Permanent, Contract, Intern)
25. **shift** - Shift name (must exist in system, e.g., General Shift, Night Shift)
26. **work_type** - Work type (must exist in system, e.g., Full Time, Part Time)
27. **basic_salary** - Monthly basic salary (number)
28. **reporting_manager_email** - Email of reporting manager (e.g., salim@meharadvisory.com)

## 🎯 Important Notes

### **Before Importing:**
1. ✅ Ensure all departments exist in the system
2. ✅ Ensure all job positions exist in the system
3. ✅ Ensure all job roles exist in the system
4. ✅ Ensure employee types exist (Permanent, Contract, etc.)
5. ✅ Ensure shifts are configured
6. ✅ Ensure work types are configured

### **Data Format Rules:**
- **Dates**: Must be in YYYY-MM-DD format (e.g., 2024-01-15)
- **Email**: Must be unique for each employee
- **Badge ID**: Must be unique for each employee
- **Phone**: Can include country code (e.g., +91 for India)
- **Numbers**: Experience, children, salary should be numbers only
- **Gender**: Use lowercase (male, female, other)

### **Common Values:**
- **Gender**: male, female, other
- **Marital Status**: single, married, divorced, widowed
- **Country**: India, USA, UK, etc.
- **States (India)**: Rajasthan, Delhi, Maharashtra, Karnataka, etc.

## 📥 How to Import

### **Method 1: Via Web Interface**
1. Login to HRMS: `https://hrms.meharadvisory.cloud`
2. Go to: **Employee** → **Import Employees**
3. Upload your CSV file
4. Map the columns if needed
5. Click **Import**

### **Method 2: Via Django Admin**
1. Login to admin: `https://hrms.meharadvisory.cloud/admin`
2. Go to: **Employee** → **Employees**
3. Click **Import** button
4. Upload CSV file
5. Review and confirm

## ⚠️ Common Errors to Avoid

1. **Duplicate Email**: Each employee must have a unique email
2. **Duplicate Badge ID**: Each badge_id must be unique
3. **Invalid Date Format**: Use YYYY-MM-DD format only
4. **Missing Required Fields**: badge_id, employee_first_name, email, phone are required
5. **Non-existent Department/Position**: Create them in system first
6. **Invalid Manager Email**: Reporting manager must exist in system

## 📊 Sample Data Provided

The template includes 5 sample employees:
- EMP001 - John Doe (Sales Executive)
- EMP002 - Jane Smith (Marketing Manager)
- EMP003 - Mike Johnson (Software Developer)
- EMP004 - Sarah Williams (HR Executive)
- EMP005 - David Brown (Accountant)

**All sample employees report to Salim (salim@meharadvisory.com)**

## 🔧 Customization

You can:
- Add more rows for more employees
- Remove sample data and add your own
- Add/remove columns as needed
- Save as Excel (.xlsx) or CSV (.csv)

## 💡 Tips

1. **Start Small**: Import 5-10 employees first to test
2. **Backup**: Keep a backup of your data
3. **Validate**: Check data in Excel before importing
4. **Test**: Use sample data first to understand the process
5. **Support**: Contact admin if you face issues

## 📞 Need Help?

If you encounter any issues:
1. Check the error message carefully
2. Verify all required fields are filled
3. Ensure departments/positions exist in system
4. Contact system administrator

---

**Happy Importing! 🎉**
