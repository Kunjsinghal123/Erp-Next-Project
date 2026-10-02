import frappe

def run():
    frappe.logger().info("Fixing HR Admin permissions...")
    role = "HR Admin"
    
    if not frappe.db.exists("Role", role):
        frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)
        
    doctypes = [
        "PMS Appraisal Cycle",
        "PMS Appraisal",
        "PMS Target",
        "PMS Competency Score",
        "PERC Case"
    ]
    
    for dt in doctypes:
        # Check if permission already exists
        exists = frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role})
        if not exists:
            frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": dt,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "read": 1,
                "write": 1,
                "create": 1,
                "submit": 1,
                "amend": 1,
                "delete": 1,
                "export": 1,
                "report": 1
            }).insert(ignore_permissions=True)
            frappe.logger().info(f"Granted {role} permissions for {dt}")
        else:
            # Update existing permission
            perm = frappe.get_doc("Custom DocPerm", exists)
            perm.read = 1
            perm.write = 1
            perm.create = 1
            perm.submit = 1
            perm.amend = 1
            perm.delete = 1
            perm.export = 1
            perm.report = 1
            perm.save(ignore_permissions=True)
            frappe.logger().info(f"Updated {role} permissions for {dt}")
            
    frappe.db.commit()
    print("Permissions fixed successfully.")
