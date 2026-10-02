import frappe

def auto_assign_roles(doc, method):
    # For Employee
    if doc.user_id:
        assign_role_and_permission(doc.user_id, "Employee", doc.name)

    # For Supervisor
    if doc.reports_to:
        supervisor_user = frappe.db.get_value("Employee", doc.reports_to, "user_id")
        if supervisor_user:
            assign_role_and_permission(supervisor_user, "Supervisor", doc.name)
            
    # For Reviewer
    if doc.get("reviewer"):
        reviewer_user = frappe.db.get_value("Employee", doc.reviewer, "user_id")
        if reviewer_user:
            assign_role_and_permission(reviewer_user, "Reviewer", doc.name)

    # For Supervisor 2
    if doc.get("supervisor_2"):
        s2_user = frappe.db.get_value("Employee", doc.supervisor_2, "user_id")
        if s2_user:
            assign_role_and_permission(s2_user, "Supervisor 2", doc.name)

        # Sync supervisor_2_snapshot to employee's existing appraisals and amendments
        frappe.db.sql("""
            UPDATE `tabPMS Appraisal`
            SET supervisor_2_snapshot = %s
            WHERE employee = %s AND (supervisor_2_snapshot IS NULL OR supervisor_2_snapshot = '' OR supervisor_2_snapshot != %s)
        """, (doc.supervisor_2, doc.name, doc.supervisor_2))

        frappe.db.sql("""
            UPDATE `tabPMS Plan Amendment`
            SET supervisor_2_snapshot = %s
            WHERE employee = %s AND (supervisor_2_snapshot IS NULL OR supervisor_2_snapshot = '' OR supervisor_2_snapshot != %s)
        """, (doc.supervisor_2, doc.name, doc.supervisor_2))

def assign_role_and_permission(user_id, role, employee_id):
    # 1. Assign Role if not exists
    if not frappe.db.exists("Has Role", {"parent": user_id, "role": role}):
        try:
            user = frappe.get_doc("User", user_id)
            user.append("roles", {"role": role})
            user.save(ignore_permissions=True)
            frappe.logger().info(f"Auto-assigned {role} role to user {user_id}")
        except Exception as e:
            frappe.logger().error(f"Failed to assign {role} role to user {user_id}: {e}")

    # 2. Assign User Permission
    perm_name = frappe.db.get_value("User Permission", 
        {"user": user_id, "allow": "Employee", "for_value": employee_id, "applicable_for": "PMS Appraisal"})
    
    if not perm_name:
        try:
            doc = frappe.get_doc({
                "doctype": "User Permission",
                "user": user_id,
                "allow": "Employee",
                "for_value": employee_id,
                "applicable_for": "PMS Appraisal",
                "hide_descendants": 0
            })
            doc.insert(ignore_permissions=True)
            frappe.logger().info(f"Created User Permission for {user_id} scoping PMS Appraisal to Employee {employee_id}")
        except Exception as e:
            frappe.logger().error(f"Failed to create User Permission for user {user_id}: {e}")

def sync_all_employee_roles():
    employees = frappe.get_all("Employee", fields=["name", "reports_to", "reviewer", "supervisor_2"])
    for emp in employees:
        emp_doc = frappe.get_doc("Employee", emp.name)
        auto_assign_roles(emp_doc, None)
    frappe.db.commit()
