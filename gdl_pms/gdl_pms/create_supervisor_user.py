import frappe

def execute():
    email = "supervisor@test.com"
    if not frappe.db.exists("User", email):
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Supervisor",
            "send_welcome_email": 0,
            "roles": [{"role": "Employee"}]
        })
        user.insert(ignore_permissions=True)
        frappe.utils.password.update_password(email, "123456")
        
    emp = frappe.get_doc("Employee", "HR-EMP-00002")
    if not emp.grade_group:
        emp.grade_group = "OS_ESP" # set a default to bypass validation
    emp.user_id = email
    emp.save(ignore_permissions=True)
    frappe.db.commit()
    print("Supervisor User created and linked.")
