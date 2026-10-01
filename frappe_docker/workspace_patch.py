import frappe
import json

def execute():
    workspace_name = "GDL PMS"
    if frappe.db.exists("Workspace", workspace_name):
        ws = frappe.get_doc("Workspace", workspace_name)
        
        shortcut = {
            "label": "Pending For Approval",
            "type": "DocType",
            "link_to": "PMS Appraisal",
            "doc_view": "List",
            "stats_filter": '[["PMS Appraisal","plan_status","in",["Pending Supervisor Approval","Pending Reviewer Approval"]]]'
        }
        
        existing_shortcuts = [s.label for s in ws.shortcuts]
        if shortcut["label"] not in existing_shortcuts:
            ws.append("shortcuts", shortcut)
            
            content = json.loads(ws.content) if ws.content else []
            # Find the best place to put it
            # Just append it as a shortcut block
            content.append({"type": "shortcut", "data": {"shortcut_name": "Pending For Approval"}})
            ws.content = json.dumps(content)
            ws.save(ignore_permissions=True)
            frappe.db.commit()
            print("Workspace updated!")
        else:
            print("Shortcut already exists.")
    else:
        print("Workspace GDL PMS not found.")
