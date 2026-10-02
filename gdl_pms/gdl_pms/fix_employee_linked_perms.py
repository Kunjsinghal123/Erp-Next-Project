import frappe

def run():
    frappe.logger().info("Granting Employee role read access to linked doctypes...")
    role = "Employee"
    
    linked_doctypes = [
        "Employee",
        "PMS Appraisal Cycle"
    ]
    
    for dt in linked_doctypes:
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
    print("Granted read permissions for linked doctypes to Employee.")
