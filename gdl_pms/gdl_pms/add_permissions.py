import frappe

def run():
    doctypes = frappe.get_all("DocType", filters={"module": "GDL PMS", "custom": 0})
    for d in doctypes:
        dt_name = d.name
        dt = frappe.get_doc("DocType", dt_name)
        
        # Check if System Manager role exists
        if not frappe.db.exists("DocPerm", {"parent": dt_name, "role": "System Manager"}):
            perm = {
                "role": "System Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "report": 1,
                "export": 1,
                "share": 1
            }
            if dt.is_submittable:
                perm["submit"] = 1
                perm["cancel"] = 1
            
            dt.append("permissions", perm)
            dt.save(ignore_permissions=True)
            print(f"Added System Manager permissions to {dt_name}")
        else:
            print(f"Permissions already exist for {dt_name}")
