import frappe
import json

def setup():
    frappe.logger().info("Setting up PMS Calendar...")

    # 1. Ensure PMS Calendar DocType exists in DB
    if not frappe.db.exists("DocType", "PMS Calendar"):
        frappe.reload_doc("gdl_pms", "doctype", "pms_calendar")
        print("Reloaded doc for PMS Calendar")
    else:
        frappe.reload_doc("gdl_pms", "doctype", "pms_calendar")
        print("Updated doc for PMS Calendar")

    # Reload PMS Appraisal Cycle to register new calendar_year field
    frappe.reload_doc("gdl_pms", "doctype", "pms_appraisal_cycle")
    print("Reloaded PMS Appraisal Cycle")

    # 2. Insert standard default PMS Calendar for 2026 if not exists
    if not frappe.db.exists("PMS Calendar", "2026"):
        cal = frappe.get_doc({
            "doctype": "PMS Calendar",
            "calendar_year": "2026",
            "employee_submission_deadline": "2026-03-31",
            "supervisor_approval_deadline": "2026-04-15",
            "reviewer_approval_deadline": "2026-04-30",
            "enable_appraisal_timeline": 1,
            "self_scoring_start_date": "2026-11-01",
            "self_scoring_end_date": "2026-11-30",
            "supervisor_appraisal_end_date": "2026-12-15",
            "reviewer_appraisal_end_date": "2026-12-31",
            "remarks": "Standard Annual Performance Management Calendar for Year 2026"
        })
        cal.insert(ignore_permissions=True)
        print("Created default PMS Calendar for Year 2026")
    else:
        print("PMS Calendar 2026 already exists")

    # 3. Update Workspace Sidebar for GDL PMS
    sidebar_name = "GDL PMS"
    if frappe.db.exists("Workspace Sidebar", sidebar_name):
        sidebar = frappe.get_doc("Workspace Sidebar", sidebar_name)
        existing_items = [item.label for item in sidebar.items]
        
        if "PMS Calendar" not in existing_items:
            # Find index of PMS Appraisal Cycle
            cycle_idx = -1
            for idx, item in enumerate(sidebar.items):
                if item.label == "PMS Appraisal Cycle":
                    cycle_idx = idx
                    break
            
            new_item = {
                "label": "PMS Calendar",
                "link_type": "DocType",
                "link_to": "PMS Calendar",
                "icon": "calendar",
                "type": "Link",
                "child": 0,
                "collapsible": 1,
                "keep_closed": 0,
                "indent": 0,
                "show_arrow": 0
            }
            
            new_child = sidebar.append("items", new_item)
            if cycle_idx != -1:
                sidebar.items.remove(new_child)
                sidebar.items.insert(cycle_idx, new_child)
                
            # Re-index items
            for idx, item in enumerate(sidebar.items):
                item.idx = idx + 1
                
            sidebar.save(ignore_permissions=True)
            print("Added PMS Calendar to Workspace Sidebar: GDL PMS")
        else:
            print("PMS Calendar already present in Workspace Sidebar")

    # 4. Update HR Workspaces with PMS Calendar shortcut
    for ws_name in ["PMS HR", "PMS HR Workspace"]:
        if frappe.db.exists("Workspace", ws_name):
            ws = frappe.get_doc("Workspace", ws_name)
            existing_shortcuts = [s.label for s in ws.shortcuts]
            
            if "PMS Calendar" not in existing_shortcuts:
                ws.append("shortcuts", {
                    "label": "PMS Calendar",
                    "type": "DocType",
                    "link_to": "PMS Calendar",
                    "doc_view": "List"
                })
                
                # Also add card block in content if JSON
                try:
                    content = json.loads(ws.content) if ws.content else []
                    # Insert after Employee Management or Dashboard
                    content.insert(1, {"type": "shortcut", "data": {"shortcut_name": "PMS Calendar"}})
                    ws.content = json.dumps(content)
                except Exception as e:
                    print("Could not update JSON content:", e)
                    
                ws.save(ignore_permissions=True)
                print(f"Updated Workspace {ws_name} with PMS Calendar shortcut")

    frappe.db.commit()
    print("PMS Calendar setup completed successfully!")

if __name__ == "__main__":
    setup()
