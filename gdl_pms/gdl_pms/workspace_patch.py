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
            # Insert the shortcut before Reports block if possible
            reports_idx = -1
            for i, block in enumerate(content):
                if block.get("type") == "header" and block.get("data", {}).get("text") == "Reports":
                    reports_idx = i
                    break
                    
            new_block = {"type": "shortcut", "data": {"shortcut_name": "Pending For Approval"}}
            if reports_idx != -1:
                content.insert(reports_idx, new_block)
            else:
                content.append(new_block)
                
            ws.content = json.dumps(content)
            ws.save(ignore_permissions=True)
            frappe.db.commit()
            print("Workspace updated!")
        else:
            print("Shortcut already exists.")
    else:
        print("Workspace GDL PMS not found.")
