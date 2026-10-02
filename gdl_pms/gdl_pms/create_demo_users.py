import frappe
from frappe.utils.password import update_password
from gdl_pms.employee_hooks import auto_assign_roles

def create_demo_users():
    frappe.set_user("Administrator")
    company = frappe.db.get_value("Company", {}, "name") or "DrukSmart Private Limited"

    user_configs = [
        {
            "email": "karma.wangchuk@gdl.bt",
            "first_name": "Karma",
            "last_name": "Wangchuk",
            "roles": ["Employee", "Supervisor"],
            "designation": "Manager",
            "grade_group": "PS_CS"
        },
        {
            "email": "sonam.tobgay@gdl.bt",
            "first_name": "Sonam",
            "last_name": "Tobgay",
            "roles": ["Employee", "Reviewer"],
            "designation": "Vice President",
            "grade_group": "PS_CS"
        },
        {
            "email": "tashi.dorji@gdl.bt",
            "first_name": "Tashi",
            "last_name": "Dorji",
            "roles": ["Employee", "Supervisor 2"],
            "designation": "Project Manager",
            "grade_group": "PS_CS"
        },
        {
            "email": "dechen.peldon@gdl.bt",
            "first_name": "Dechen",
            "last_name": "Peldon",
            "roles": ["Employee"],
            "designation": "Administrative Officer",
            "grade_group": "OS_ESP"
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
                "gender": "Female" if "dechen" in email else "Male",
                "date_of_birth": "1992-05-15",
                "date_of_joining": "2024-01-01",
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

    # 3. Link Dechen Peldon's reporting hierarchy
    dechen_emp = frappe.get_doc("Employee", emp_map["dechen.peldon@gdl.bt"])
    dechen_emp.reports_to = emp_map["karma.wangchuk@gdl.bt"]
    dechen_emp.reviewer = emp_map["sonam.tobgay@gdl.bt"]
    dechen_emp.supervisor_2 = emp_map["tashi.dorji@gdl.bt"]
    dechen_emp.save(ignore_permissions=True)
    print("Linked Dechen Peldon hierarchy: Supervisor=Karma, Reviewer=Sonam, S2=Tashi")

    # Run auto-assign roles hook to ensure user permissions and roles are completely configured
    auto_assign_roles(dechen_emp, None)

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
    print("=== DEMO USERS SETUP COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    create_demo_users()
