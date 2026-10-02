import frappe

def execute():
    email = "reviewer@test.com"
    if not frappe.db.exists("User", email):
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Reviewer",
            "send_welcome_email": 0,
            "roles": [{"role": "Employee"}]
        })
        user.insert(ignore_permissions=True)
        frappe.utils.password.update_password(email, "123456")
        
    emp = frappe.get_doc("Employee", "HR-EMP-00003")
    if not emp.grade_group:
        emp.grade_group = "OS_ESP" # default
    emp.user_id = email
    emp.save(ignore_permissions=True)
    frappe.db.commit()
    print("Reviewer User created and linked.")
