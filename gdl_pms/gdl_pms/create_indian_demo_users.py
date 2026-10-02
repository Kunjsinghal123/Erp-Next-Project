import frappe
from frappe.utils.password import update_password
from gdl_pms.employee_hooks import auto_assign_roles

def create_indian_demo_users():
    frappe.set_user("Administrator")
    company = frappe.db.get_value("Company", {}, "name") or "DrukSmart Private Limited"

    user_configs = [
        {
            "email": "rahul.sharma@gdl.bt",
            "first_name": "Rahul",
            "last_name": "Sharma",
            "roles": ["Employee", "Supervisor"],
            "designation": "Manager",
            "grade_group": "PS_CS",
            "gender": "Male"
        },
        {
            "email": "amit.verma@gdl.bt",
            "first_name": "Amit",
            "last_name": "Verma",
            "roles": ["Employee", "Reviewer"],
            "designation": "Vice President",
            "grade_group": "PS_CS",
            "gender": "Male"
        },
        {
            "email": "rajesh.kumar@gdl.bt",
            "first_name": "Rajesh",
            "last_name": "Kumar",
            "roles": ["Employee", "Supervisor 2"],
            "designation": "Project Manager",
            "grade_group": "PS_CS",
            "gender": "Male"
        },
        {
            "email": "priya.patel@gdl.bt",
            "first_name": "Priya",
            "last_name": "Patel",
            "roles": ["Employee"],
            "designation": "Administrative Officer",
            "grade_group": "OS_ESP",
            "gender": "Female"
        }
    ]

    emp_map = {}

    for cfg in user_configs:
        email = cfg["email"]
        desig = cfg["designation"]

        # Ensure Designation exists
        if desig and not frappe.db.exists("Designation", desig):
            frappe.get_doc({"doctype": "Designation", "designation_name": desig}).insert(ignore_permissions=True)

        # 1. Create or update User
        if not frappe.db.exists("User", email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": cfg["first_name"],
                "last_name": cfg["last_name"],
                "enabled": 1,
                "send_welcome_email": 0,
                "user_type": "System User",
                "desk_access": 1
            })
            user.insert(ignore_permissions=True)
            print(f"Created User: {email}")
        else:
            user = frappe.get_doc("User", email)
            user.first_name = cfg["first_name"]
            user.last_name = cfg["last_name"]
            user.enabled = 1
            user.desk_access = 1
            user.save(ignore_permissions=True)
            print(f"Updated User: {email}")

        # Set password to 123456
        update_password(user=email, pwd="123456")

        # Assign Roles
        for role in cfg["roles"]:
            if not frappe.db.exists("Has Role", {"parent": email, "role": role}):
                user.append("roles", {"role": role})
        user.save(ignore_permissions=True)

        # 2. Create or update Employee
        emp_name = frappe.db.get_value("Employee", {"user_id": email}, "name")
        if not emp_name:
            emp = frappe.get_doc({
                "doctype": "Employee",
                "first_name": cfg["first_name"],
                "last_name": cfg["last_name"],
                "user_id": email,
                "company_email": email,
                "prefered_email": email,
                "status": "Active",
                "gender": cfg["gender"],
                "date_of_birth": "1994-08-10",
                "date_of_joining": "2024-02-01",
                "company": company,
                "designation": desig,
                "grade_group": cfg["grade_group"]
            })
            emp.insert(ignore_permissions=True)
            emp_name = emp.name
            print(f"Created Employee: {emp_name} ({cfg['first_name']} {cfg['last_name']}) for {email}")
        else:
            emp = frappe.get_doc("Employee", emp_name)
            emp.first_name = cfg["first_name"]
            emp.last_name = cfg["last_name"]
            emp.company_email = email
            emp.prefered_email = email
            emp.status = "Active"
            emp.designation = desig
            emp.grade_group = cfg["grade_group"]
            emp.save(ignore_permissions=True)
            print(f"Updated Employee: {emp_name} ({cfg['first_name']} {cfg['last_name']}) for {email}")

        emp_map[email] = emp_name

    # 3. Link Priya Patel's reporting hierarchy (OS Level)
    priya_emp = frappe.get_doc("Employee", emp_map["priya.patel@gdl.bt"])
    priya_emp.reports_to = emp_map["rahul.sharma@gdl.bt"]
    priya_emp.reviewer = emp_map["amit.verma@gdl.bt"]
    priya_emp.supervisor_2 = emp_map["rajesh.kumar@gdl.bt"]
    priya_emp.grade_group = "OS_ESP"
    priya_emp.save(ignore_permissions=True)
    print("Linked Priya Patel hierarchy: Supervisor=Rahul, Reviewer=Amit, S2=Rajesh (Grade Group: OS_ESP)")

    # Run auto-assign roles hook to ensure user permissions and roles are completely configured
    auto_assign_roles(priya_emp, None)

    # 4. Sync Applicable Employees in Active Appraisal Cycles
    cycles = frappe.get_all("PMS Appraisal Cycle", filters={"status": ["in", ["Active", "Planning Open"]]}, pluck="name")
    for cycle_name in cycles:
        try:
            from gdl_pms.gdl_pms.doctype.pms_appraisal_cycle.pms_appraisal_cycle import sync_cycle_employees
            sync_cycle_employees(cycle_name)
            print(f"Synced cycle employees for {cycle_name}")
        except Exception as e:
            print(f"Could not auto-sync cycle {cycle_name}: {e}")

    frappe.db.commit()
    print("=== INDIAN DEMO USERS (OS LEVEL) SETUP COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    create_indian_demo_users()
