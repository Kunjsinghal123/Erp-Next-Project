import frappe
import json

def execute():
    workspaces = ["PMS HR Workspace", "GDL PMS", "PMS Supervisor", "PMS Reviewer", "PMS PERC", "PMS HR"]
    
    shortcut = {
        "label": "Pending For Approval",
        "type": "DocType",
        "link_to": "PMS Appraisal",
        "doc_view": "List",
        "stats_filter": '[["PMS Appraisal","plan_status","in",["Pending Supervisor Approval","Pending Reviewer Approval"]]]'
    }
    
    for w in workspaces:
        if frappe.db.exists("Workspace", w):
            ws = frappe.get_doc("Workspace", w)
            existing_shortcuts = [s.label for s in ws.shortcuts]
            
            if shortcut["label"] not in existing_shortcuts:
                ws.append("shortcuts", shortcut)
                content = json.loads(ws.content) if ws.content else []
                content.append({"type": "shortcut", "data": {"shortcut_name": "Pending For Approval"}})
                ws.content = json.dumps(content)
                ws.save(ignore_permissions=True)
                print(f"Added shortcut to Workspace: {w}")

    frappe.db.commit()
    print("Done!")
