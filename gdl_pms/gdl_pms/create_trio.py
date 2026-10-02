import frappe

def execute():
    # Helper to create User and Employee
    def create_user_and_employee(email, first_name, grade_group="OS_ESP"):
        # Create User
        if not frappe.db.exists("User", email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "send_welcome_email": 0,
                "roles": [{"role": "Employee"}]
            })
            user.insert(ignore_permissions=True)
            frappe.utils.password.update_password(email, "123456")
            print(f"Created user {email}")
            
        # Create Employee
        if not frappe.db.exists("Employee", {"user_id": email}):
            emp = frappe.get_doc({
                "doctype": "Employee",
                "first_name": first_name,
                "user_id": email,
                "status": "Active",
                "date_of_joining": "2026-01-01",
                "gender": "Male",
                "date_of_birth": "1990-01-01",
                "company": "DrukSmart Private Limited",
                "company_email": email,
                "grade_group": grade_group
            })
            emp.insert(ignore_permissions=True)
            print(f"Created employee {emp.name} for {email}")
            return emp.name
        else:
            emp_name = frappe.db.get_value("Employee", {"user_id": email}, "name")
            print(f"Employee {emp_name} already exists for {email}")
            return emp_name

    # 1. Create Supervisor 2
    sup2 = create_user_and_employee("supervisor2@test.com", "Supervisor 2")
    
    # 2. Create Reviewer 2
    rev2 = create_user_and_employee("reviewer2@test.com", "Reviewer 2")
    
    # 3. Create Employee 2
    emp2 = create_user_and_employee("employee2@gmail.com", "Employee 2", "PS_CS")
    
    # 4. Link Employee 2 to Sup2 and Rev2
    e2_doc = frappe.get_doc("Employee", emp2)
    e2_doc.reports_to = sup2
    e2_doc.reviewer = rev2
    e2_doc.save(ignore_permissions=True)
    
    frappe.db.commit()
    print("Done setting up new test trio!")
