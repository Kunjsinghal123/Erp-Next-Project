import frappe
import json

def execute():
    # Update PMS Employee workspace
    if frappe.db.exists("Workspace", "PMS Employee"):
        ws = frappe.get_doc("Workspace", "PMS Employee")
        ws.shortcuts = []
        
        ws.append("shortcuts", {
            "label": "My Performance Plans",
            "type": "DocType",
            "link_to": "PMS Appraisal",
            "doc_view": "List"
        })
        
        ws.append("shortcuts", {
            "label": "Plan Amendments",
            "type": "DocType",
            "link_to": "PMS Plan Amendment",
            "doc_view": "List"
        })
        
        ws.append("shortcuts", {
            "label": "Approval History",
            "type": "DocType",
            "link_to": "PMS Appraisal",
            "doc_view": "List",
            "stats_filter": '[["PMS Appraisal","plan_status","in",["Approved", "Rejected"]]]'
        })
        
        content = [
            {"type": "header", "data": {"text": "PMS Dashboard", "level": 2}},
            {"type": "shortcut", "data": {"shortcut_name": "My Performance Plans"}},
            {"type": "shortcut", "data": {"shortcut_name": "Plan Amendments"}},
            {"type": "shortcut", "data": {"shortcut_name": "Approval History"}}
        ]
        
        ws.content = json.dumps(content)
        ws.save(ignore_permissions=True)
        print("Updated PMS Employee workspace with Plan Amendments shortcut.")

    # Update PMS Supervisor & Reviewer workspaces
    for ws_name in ["PMS Supervisor", "PMS Reviewer", "PMS HR"]:
        if frappe.db.exists("Workspace", ws_name):
            ws = frappe.get_doc("Workspace", ws_name)
            existing = [s.label for s in ws.shortcuts]
            if "Plan Amendments" not in existing:
                ws.append("shortcuts", {
                    "label": "Plan Amendments",
                    "type": "DocType",
                    "link_to": "PMS Plan Amendment",
                    "doc_view": "List"
                })
                content = json.loads(ws.content) if ws.content else []
                content.append({"type": "shortcut", "data": {"shortcut_name": "Plan Amendments"}})
                ws.content = json.dumps(content)
                ws.save(ignore_permissions=True)
                print(f"Added Plan Amendments shortcut to {ws_name}")

    frappe.db.commit()

if __name__ == "__main__":
    execute()
