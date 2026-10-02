import frappe

def run():
    print("--- 1. Updating Role Home Pages ---")
    role_home_pages = {
        "HR Admin": "/desk/pms-hr",
        "Reviewer": "/desk/pms-reviewer",
        "Supervisor 2": "/desk/pms-supervisor-2",
        "Supervisor": "/desk/pms-supervisor",
        "Employee": "/desk/pms-employee",
    }
    
    for role_name, hp in role_home_pages.items():
        if frappe.db.exists("Role", role_name):
            frappe.db.set_value("Role", role_name, "home_page", hp)
            print(f"Updated Role {role_name} home_page -> {hp}")

    print("\n--- 2. Updating User Default Workspaces ---")
    users = frappe.get_all("User", filters={"user_type": "System User", "enabled": 1}, fields=["name"])
    for u in users:
        roles = set(frappe.get_roles(u.name))
        if "System Manager" in roles or "Administrator" in roles:
            continue
        
        target_ws = None
        if "HR Admin" in roles:
            target_ws = "PMS HR"
        elif "Reviewer" in roles:
            target_ws = "PMS Reviewer"
        elif "Supervisor 2" in roles:
            target_ws = "PMS Supervisor 2"
        elif "Supervisor" in roles:
            target_ws = "PMS Supervisor"
        elif "Employee" in roles:
            target_ws = "PMS Employee"
            
        if target_ws and frappe.db.exists("Workspace", target_ws):
            frappe.db.set_value("User", u.name, "default_workspace", target_ws)
            print(f"User {u.name} default_workspace -> {target_ws}")

    print("\n--- 3. Restricting ERPNext Desktop Icons to Relevant Roles ---")
    erpnext_icon_roles = {
        "Organization": ["HR Manager", "System Manager"],
        "Accounting": ["Accounts User", "Accounts Manager", "System Manager"],
        "Buying": ["Purchase User", "Purchase Manager", "System Manager"],
        "Selling": ["Sales User", "Sales Manager", "System Manager"],
        "Projects": ["Projects User", "Projects Manager", "System Manager"],
        "Quality": ["Quality Manager", "System Manager"],
        "ERPNext Settings": ["System Manager"],
        "CRM": ["Sales User", "Sales Manager", "System Manager"],
        "Support": ["Support Team", "System Manager"],
        "Assets": ["Accounts User", "Accounts Manager", "System Manager"],
        "Stock": ["Stock User", "Stock Manager", "System Manager"],
        "Manufacturing": ["Manufacturing User", "Manufacturing Manager", "System Manager"],
        "Subcontracting": ["Stock User", "Purchase User", "System Manager"],
        "Invoicing": ["Accounts User", "Accounts Manager", "System Manager"],
        "Payments": ["Accounts User", "Accounts Manager", "System Manager"],
        "Financial Reports": ["Accounts User", "Accounts Manager", "System Manager"],
        "Accounts Setup": ["Accounts Manager", "System Manager"],
        "Banking": ["Accounts User", "Accounts Manager", "System Manager"],
        "Budget": ["Accounts Manager", "System Manager"],
        "Taxes": ["Accounts Manager", "System Manager"],
        "Subscription": ["Accounts User", "System Manager"],
        "Share Management": ["Accounts Manager", "System Manager"],
        "ERPNext": ["System Manager"],
        "Home": ["System Manager"],
        "System": ["System Manager"],
        "Framework": ["System Manager"],
        "Website": ["Website Manager", "System Manager"],
        "Users": ["System Manager"],
        "Integrations": ["System Manager"],
        "Build": ["System Manager"],
        "Automation": ["System Manager"],
        "Email": ["System Manager"],
        "My Workspaces": ["System Manager"]
    }

    for icon_name, roles in erpnext_icon_roles.items():
        if frappe.db.exists("Desktop Icon", icon_name):
            doc = frappe.get_doc("Desktop Icon", icon_name)
            current_roles = [r.role for r in doc.roles]
            for r in roles:
                if r not in current_roles and frappe.db.exists("Role", r):
                    doc.append("roles", {"role": r})
            doc.save(ignore_permissions=True)
            print(f"Restricted Desktop Icon '{icon_name}' to roles: {roles}")

    print("\n--- 4. Ensuring PMS Desktop Icons Exist ---")
    pms_icons = [
        {"name": "PMS HR", "label": "PMS HR Dashboard", "link": "/desk/pms-hr", "link_to": "PMS HR", "role": "HR Admin"},
        {"name": "PMS Reviewer", "label": "PMS Reviewer Dashboard", "link": "/desk/pms-reviewer", "link_to": "PMS Reviewer", "role": "Reviewer"},
        {"name": "PMS Supervisor 2", "label": "PMS Supervisor 2 Dashboard", "link": "/desk/pms-supervisor-2", "link_to": "PMS Supervisor 2", "role": "Supervisor 2"},
        {"name": "PMS Supervisor", "label": "PMS Supervisor Dashboard", "link": "/desk/pms-supervisor", "link_to": "PMS Supervisor", "role": "Supervisor"},
        {"name": "PMS Employee", "label": "PMS Employee Dashboard", "link": "/desk/pms-employee", "link_to": "PMS Employee", "role": "Employee"},
    ]

    for p in pms_icons:
        if not frappe.db.exists("Desktop Icon", p["name"]):
            icon = frappe.new_doc("Desktop Icon")
            icon.label = p["label"]
            icon.icon_type = "Link"
            icon.link_type = "External"
            icon.link = p["link"]
            icon.standard = 0
            icon.hidden = 0
            icon.bg_color = "blue"
            icon.append("roles", {"role": p["role"]})
            icon.insert(ignore_permissions=True)
            print(f"Created Desktop Icon: {p['name']} for role {p['role']}")
        else:
            icon = frappe.get_doc("Desktop Icon", p["name"])
            existing_roles = [r.role for r in icon.roles]
            if p["role"] not in existing_roles:
                icon.append("roles", {"role": p["role"]})
                icon.save(ignore_permissions=True)
                print(f"Updated Desktop Icon: {p['name']} with role {p['role']}")


    frappe.db.commit()
    frappe.clear_cache()
    print("\n--- Finished successfully! ---")

if __name__ == "__main__":
    run()
