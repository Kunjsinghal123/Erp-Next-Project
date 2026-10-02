import frappe
import json

def update():
    workspace_name = "PMS Employee"
    if frappe.db.exists("Workspace", workspace_name):
        ws = frappe.get_doc("Workspace", workspace_name)

        s = {
            "label": "Approval History",
            "type": "DocType",
            "link_to": "PMS Appraisal",
            "doc_view": "List",
            "stats_filter": '[["PMS Appraisal","plan_status","in",["Approved", "Rejected"]]]'
        }
        
        existing_shortcuts = [x.label for x in ws.shortcuts]
        if s["label"] not in existing_shortcuts:
            ws.append("shortcuts", s)

        content = json.loads(ws.content) if ws.content else []
        
        has_approval = any(b.get("type") == "shortcut" and b.get("data", {}).get("shortcut_name") == "Approval History" for b in content)
        
        if not has_approval:
            new_block = {"type": "shortcut", "data": {"shortcut_name": "Approval History", "col": 12}}
            content.append(new_block)
            ws.content = json.dumps(content)
            
        ws.save(ignore_permissions=True)
        print(f"Added Approval History to {workspace_name}")
    else:
        print(f"Workspace {workspace_name} not found")
