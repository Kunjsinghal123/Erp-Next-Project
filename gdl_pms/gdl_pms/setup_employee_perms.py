import frappe

def run():
    frappe.logger().info("Setting up Employee Role permissions for PMS...")
    
    doctypes = [
        "PMS Appraisal",
        "PMS Target",
        "PMS Competency Score"
    ]
    
    role = "Employee"
    
    for dt in doctypes:
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
                "submit": 0, # They just save it, Workflow handles submission if needed, or they can submit if workflow demands
                "amend": 0,
                "export": 0,
                "report": 1,
            }).insert(ignore_permissions=True)
            frappe.logger().info(f"Granted {role} permissions for {dt}")
        else:
            perm = frappe.get_doc("Custom DocPerm", exists)
            perm.read = 1
            perm.write = 1
            perm.create = 1
            perm.save(ignore_permissions=True)
            frappe.logger().info(f"Updated {role} permissions for {dt}")
            
    frappe.db.commit()
    print("Employee permissions configured.")
