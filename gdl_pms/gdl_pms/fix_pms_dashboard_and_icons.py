import frappe

def execute():
    logo_path = "/assets/gdl_pms/logo_gdl.png"

    # 1. Update Website Settings & Navbar Settings
    try:
        ws = frappe.get_doc("Website Settings", "Website Settings")
        ws.app_logo = logo_path
        ws.banner_image = logo_path
        ws.save(ignore_permissions=True)
        print("Updated Website Settings logo")
    except Exception as e:
        print(f"Error updating Website Settings: {e}")

    try:
        ns = frappe.get_doc("Navbar Settings", "Navbar Settings")
        ns.app_logo = logo_path
        ns.save(ignore_permissions=True)
        print("Updated Navbar Settings logo")
    except Exception as e:
        print(f"Error updating Navbar Settings: {e}")

    # 2. Update Workspaces icons
    ws_icon_map = {
        "PMS Employee Workspace": "user",
        "PMS Employee": "user",
        "PMS Appraisal Cycle": "calendar",
        "PMS Performance Plan": "clipboard",
        "PMS Plan Amendment": "edit-3",
        "PMS Supervisor Workspace": "users",
        "PMS Supervisor": "users",
        "PMS Reviewer Workspace": "check-square",
        "PMS Reviewer": "check-square",
        "PMS HR Workspace": "award",
        "PMS HR": "award",
    }

    for ws_name, icon in ws_icon_map.items():
        if frappe.db.exists("Workspace", ws_name):
            try:
                doc = frappe.get_doc("Workspace", ws_name)
                doc.icon = icon
                doc.save(ignore_permissions=True)
                print(f"Updated Workspace '{ws_name}' icon to '{icon}'")
            except Exception as e:
                print(f"Error updating Workspace {ws_name}: {e}")

    frappe.db.commit()
    print("Logo and icons setup complete.")

if __name__ == "__main__":
    execute()
