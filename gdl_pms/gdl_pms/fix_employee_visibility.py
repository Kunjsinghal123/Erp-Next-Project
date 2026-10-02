import frappe

def run():
    # Grant Write access to Employee for HR Admin
    perm = frappe.get_doc("Custom DocPerm", {"role": "HR Admin", "parent": "Employee"})
    if perm:
        perm.write = 1
        perm.save(ignore_permissions=True)
        frappe.logger().info("Granted write access to Employee for HR Admin")
        
    # Move the grade_group field to User Details section so it's super visible
    field = frappe.get_doc("Custom Field", {"dt": "Employee", "fieldname": "grade_group"})
    if field:
        field.insert_after = "user_id"
        field.save(ignore_permissions=True)
        frappe.logger().info("Moved grade_group to appear after user_id")
        
    frappe.db.commit()
