import frappe
import json

def execute():
    workspaces = frappe.get_all("Workspace", fields=["name", "content"])
    
    shortcut = {
        "label": "Pending For Approval",
        "type": "DocType",
        "link_to": "PMS Appraisal",
        "doc_view": "List",
        "stats_filter": '[["PMS Appraisal","plan_status","in",["Pending Supervisor Approval","Pending Reviewer Approval"]]]'
    }
    
    for w in workspaces:
        ws = frappe.get_doc("Workspace", w.name)
        existing_shortcuts = [s.label for s in ws.shortcuts]
        
        # If the workspace currently has a shortcut to "PMS Appraisal" OR the user wants it everywhere relevant
        # Let's add it to any workspace that has "PMS Performance Plan" or similar
        has_pms = any("PMS" in str(s.link_to) for s in ws.shortcuts)
        if has_pms and shortcut["label"] not in existing_shortcuts:
            ws.append("shortcuts", shortcut)
            content = json.loads(ws.content) if ws.content else []
            content.append({"type": "shortcut", "data": {"shortcut_name": "Pending For Approval"}})
            ws.content = json.dumps(content)
            ws.save(ignore_permissions=True)
            print(f"Added shortcut to Workspace: {w.name}")

    frappe.db.commit()
    print("Done!")
