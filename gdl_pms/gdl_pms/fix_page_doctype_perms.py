import frappe

def run():
    roles = ["Desk User", "Employee", "Supervisor", "Supervisor 2", "Reviewer", "HR Admin", "All"]
    for role in roles:
        if not frappe.db.exists("Role", role):
            continue
        exists = frappe.db.exists("Custom DocPerm", {"parent": "Page", "role": role})
        if not exists:
            frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": "Page",
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "read": 1,
                "select": 1,
                "write": 0,
                "create": 0,
                "delete": 0,
                "report": 0,
                "export": 0,
                "share": 0
            }).insert(ignore_permissions=True)
            print(f"Granted Page read permission to role: {role}")
        else:
            doc = frappe.get_doc("Custom DocPerm", exists)
            doc.read = 1
            doc.select = 1
            doc.save(ignore_permissions=True)
            print(f"Updated Page read permission for role: {role}")

    frappe.db.commit()
    print("Page permissions updated successfully.")
