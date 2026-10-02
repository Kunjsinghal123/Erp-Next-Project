import frappe
import json
import os

def run():
    print("--- 1. Syncing Workspace Sidebar 'GDL PMS' ---")
    json_path = frappe.get_app_path("gdl_pms", "workspace_sidebar", "gdl_pms.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        
        if frappe.db.exists("Workspace Sidebar", "GDL PMS"):
            sb = frappe.get_doc("Workspace Sidebar", "GDL PMS")
            sb.items = []
            for item in data.get("items", []):
                sb.append("items", item)
            sb.save(ignore_permissions=True)
            print("Updated Workspace Sidebar 'GDL PMS' in database.")
        else:
            sb = frappe.get_doc(data)
            sb.insert(ignore_permissions=True)
            print("Created Workspace Sidebar 'GDL PMS' in database.")

    print("\n--- 2. Updating Workspaces with Appraisal Shortcuts ---")
    # A. PMS Employee
    if frappe.db.exists("Workspace", "PMS Employee"):
        ws = frappe.get_doc("Workspace", "PMS Employee")
        ws.shortcuts = []
        ws.append("shortcuts", {
            "label": "My Performance Plans",
            "type": "DocType",
            "link_to": "PMS Appraisal",
            "doc_view": "List",
            "stats_filter": '[["PMS Appraisal","appraisal_status","=","Not Activated"]]'
        })
        ws.append("shortcuts", {
            "label": "My Appraisals",
            "type": "DocType",
            "link_to": "PMS Appraisal",
            "doc_view": "List",
            "stats_filter": '[["PMS Appraisal","appraisal_status","!=","Not Activated"]]'
        })
        ws.append("shortcuts", {
            "label": "Plan Amendments",
            "type": "DocType",
            "link_to": "PMS Plan Amendment",
            "doc_view": "List"
        })
        content = [
            {"type": "header", "data": {"text": "PMS Employee Portal", "level": 2}},
            {"type": "shortcut", "data": {"shortcut_name": "My Performance Plans"}},
            {"type": "shortcut", "data": {"shortcut_name": "My Appraisals"}},
            {"type": "shortcut", "data": {"shortcut_name": "Plan Amendments"}}
        ]
        ws.content = json.dumps(content)
        ws.save(ignore_permissions=True)
        print("Updated PMS Employee workspace shortcuts.")

    # B. PMS Supervisor
    if frappe.db.exists("Workspace", "PMS Supervisor"):
        ws = frappe.get_doc("Workspace", "PMS Supervisor")
        ws.shortcuts = []
        ws.append("shortcuts", {
            "label": "Team Performance Plans",
            "type": "DocType",
            "link_to": "PMS Appraisal",
            "doc_view": "List",
            "stats_filter": '[["PMS Appraisal","appraisal_status","=","Not Activated"]]'
        })
        ws.append("shortcuts", {
            "label": "Pending Appraisal Reviews",
            "type": "DocType",
            "link_to": "PMS Appraisal",
            "doc_view": "List",
            "stats_filter": '[["PMS Appraisal","appraisal_status","=","Pending Supervisor Review"]]'
        })
        ws.append("shortcuts", {
            "label": "Plan Amendments",
            "type": "DocType",
            "link_to": "PMS Plan Amendment",
            "doc_view": "List"
        })
        content = [
            {"type": "header", "data": {"text": "Supervisor Evaluation & Approvals", "level": 2}},
            {"type": "shortcut", "data": {"shortcut_name": "Team Performance Plans"}},
            {"type": "shortcut", "data": {"shortcut_name": "Pending Appraisal Reviews"}},
            {"type": "shortcut", "data": {"shortcut_name": "Plan Amendments"}}
        ]
        ws.content = json.dumps(content)
        ws.save(ignore_permissions=True)
        print("Updated PMS Supervisor workspace shortcuts.")

    # C. PMS Reviewer
    if frappe.db.exists("Workspace", "PMS Reviewer"):
        ws = frappe.get_doc("Workspace", "PMS Reviewer")
        ws.shortcuts = []
        ws.append("shortcuts", {
            "label": "Reviewer Plan Approvals",
            "type": "DocType",
            "link_to": "PMS Appraisal",
            "doc_view": "List",
            "stats_filter": '[["PMS Appraisal","plan_status","=","Pending Reviewer Approval"]]'
        })
        ws.append("shortcuts", {
            "label": "Disputed Appraisals",
            "type": "DocType",
            "link_to": "PMS Appraisal",
            "doc_view": "List",
            "stats_filter": '[["PMS Appraisal","appraisal_status","=","Disputed - Pending Reviewer"]]'
        })
        ws.append("shortcuts", {
            "label": "Plan Amendments",
            "type": "DocType",
            "link_to": "PMS Plan Amendment",
            "doc_view": "List"
        })
        content = [
            {"type": "header", "data": {"text": "Reviewer Validation & Disputes", "level": 2}},
            {"type": "shortcut", "data": {"shortcut_name": "Reviewer Plan Approvals"}},
            {"type": "shortcut", "data": {"shortcut_name": "Disputed Appraisals"}},
            {"type": "shortcut", "data": {"shortcut_name": "Plan Amendments"}}
        ]
        ws.content = json.dumps(content)
        ws.save(ignore_permissions=True)
        print("Updated PMS Reviewer workspace shortcuts.")

    frappe.db.commit()
    frappe.clear_cache()
    print("Done sync_appraisal_sidebar!")

if __name__ == "__main__":
    run()
