import frappe

def run():
    frappe.logger().info("Granting HR Admin read access to standard ERPNext doctypes...")
    role = "HR Admin"
    
    standard_doctypes = [
        "Employee",
        "Department",
        "Designation"
    ]
    
    for dt in standard_doctypes:
        exists = frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role})
        if not exists:
            frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": dt,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "read": 1
            }).insert(ignore_permissions=True)
            frappe.logger().info(f"Granted {role} read permission for {dt}")
        else:
            perm = frappe.get_doc("Custom DocPerm", exists)
            perm.read = 1
            perm.save(ignore_permissions=True)
            
    frappe.db.commit()
    print("Granted Employee read permissions to HR Admin.")
