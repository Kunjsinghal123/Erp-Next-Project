import frappe
import json

def setup():
    # 1. Create Role: Supervisor 2
    role_name = "Supervisor 2"
    if not frappe.db.exists("Role", role_name):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": role_name,
            "desk_access": 1
        }).insert(ignore_permissions=True)
        print(f"Created Role: {role_name}")
    else:
        print(f"Role {role_name} already exists")

    # 2. Create Custom Field on Employee: supervisor_2
    cf_data = {
        "doctype": "Custom Field",
        "dt": "Employee",
        "fieldname": "supervisor_2",
        "label": "Supervisor 2",
        "fieldtype": "Link",
        "options": "Employee",
        "insert_after": "reviewer",
        "in_list_view": 1
    }
    cf_name = frappe.db.get_value("Custom Field", {"dt": "Employee", "fieldname": "supervisor_2"})
    if not cf_name:
        frappe.get_doc(cf_data).insert(ignore_permissions=True)
        print("Created Custom Field 'supervisor_2' on Employee")
    else:
        print("Custom Field 'supervisor_2' on Employee already exists")

    # 3. Reload DocTypes so schema changes take effect
    frappe.reload_doc("gdl_pms", "doctype", "pms_appraisal")
    frappe.reload_doc("gdl_pms", "doctype", "pms_plan_amendment")
    print("Reloaded PMS Appraisal and PMS Plan Amendment doctypes")

    # 4. Set ignore_user_permissions = 1 on snapshot fields in DocField if present
    for dt in ["PMS Appraisal", "PMS Plan Amendment"]:
        for f in ["employee", "supervisor_snapshot", "reviewer_snapshot", "supervisor_2_snapshot"]:
            if frappe.db.exists("DocField", {"parent": dt, "fieldname": f}):
                frappe.db.set_value("DocField", {"parent": dt, "fieldname": f}, "ignore_user_permissions", 1)
    print("Configured ignore_user_permissions for snapshot fields")

    # 5. Create or update Workspace for Supervisor 2
    ws_name = "PMS Supervisor 2"
    ws_content = json.dumps([
        {"type": "header", "data": {"text": "Supervisor 2 Monitoring Dashboard", "level": 2}},
        {"type": "shortcut", "data": {"shortcut_name": "Monitored Performance Plans"}},
        {"type": "shortcut", "data": {"shortcut_name": "Plan Amendments"}}
    ])
    
    shortcuts = [
        {
            "doc_view": "List",
            "label": "Monitored Performance Plans",
            "link_to": "PMS Appraisal",
            "type": "DocType"
        },
        {
            "doc_view": "List",
            "label": "Plan Amendments",
            "link_to": "PMS Plan Amendment",
            "type": "DocType"
        }
    ]

    if not frappe.db.exists("Workspace", ws_name):
        doc = frappe.get_doc({
            "doctype": "Workspace",
            "label": ws_name,
            "title": ws_name,
            "module": "GDL PMS",
            "is_standard": 1,
            "public": 1,
            "icon": "eye",
            "roles": [{"role": "Supervisor 2"}],
            "content": ws_content,
            "shortcuts": shortcuts
        })
        doc.insert(ignore_permissions=True)
        print(f"Created Workspace: {ws_name}")
    else:
        ws = frappe.get_doc("Workspace", ws_name)
        ws.set("roles", [{"role": "Supervisor 2"}])
        ws.set("shortcuts", shortcuts)
        ws.content = ws_content
        ws.icon = "eye"
        ws.save(ignore_permissions=True)
        print(f"Updated Workspace: {ws_name}")

    frappe.db.commit()
    print("Supervisor 2 setup completed successfully.")

if __name__ == "__main__":
    setup()
