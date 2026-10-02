import frappe
import json

def setup():
    # 1. Create Roles
    roles = ["Supervisor", "Reviewer", "PERC Member", "Employee", "HR Admin"]
    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role
            }).insert(ignore_permissions=True)
            print(f"Created Role: {role}")
            
    # 2. Create Number Cards
    cards = [
        {
            "name": "Total Employees",
            "document_type": "Employee",
            "function": "Count"
        },
        {
            "name": "Active Cycles",
            "document_type": "PMS Appraisal Cycle",
            "function": "Count",
            "filters_json": '[["PMS Appraisal Cycle","status","=","Active",false]]'
        },
        {
            "name": "Pending PERC",
            "document_type": "PERC Case",
            "function": "Count",
            "filters_json": '[["PERC Case","status","=","Open",false]]'
        },
        {
            "name": "Completion Rate",
            "document_type": "PMS Appraisal",
            "function": "Count"
        }
    ]
    
    for card in cards:
        if not frappe.db.exists("Number Card", card["name"]):
            doc = frappe.get_doc({
                "doctype": "Number Card",
                "name": card["name"],
                "label": card["name"],
                "document_type": card["document_type"],
                "function": card["function"],
                "filters_json": card.get("filters_json", "[]"),
                "is_standard": 1,
                "module": "GDL PMS"
            })
            doc.insert(ignore_permissions=True)
            print(f"Created Number Card: {card['name']}")
            
    # 3. Create Workspaces
    workspaces = [
        {"label": "PMS HR Workspace", "title": "PMS HR", "role": "HR Admin"},
        {"label": "PMS Employee Workspace", "title": "PMS Employee", "role": "Employee"},
        {"label": "PMS Supervisor Workspace", "title": "PMS Supervisor", "role": "Supervisor"},
        {"label": "PMS Reviewer Workspace", "title": "PMS Reviewer", "role": "Reviewer"},
        {"label": "PMS PERC Workspace", "title": "PMS PERC", "role": "PERC Member"},
    ]
    
    workspace_content = json.dumps([
        {"type": "header", "data": {"text": "PMS Dashboard", "level": 2}},
        {"type": "number_card", "data": {"number_card_name": "Total Employees"}},
        {"type": "number_card", "data": {"number_card_name": "Active Cycles"}},
        {"type": "number_card", "data": {"number_card_name": "Pending PERC"}},
        {"type": "number_card", "data": {"number_card_name": "Completion Rate"}}
    ])
    
    for ws in workspaces:
        if not frappe.db.exists("Workspace", ws["label"]):
            doc = frappe.get_doc({
                "doctype": "Workspace",
                "label": ws["label"],
                "title": ws["title"],
                "module": "GDL PMS",
                "is_standard": 1,
                "public": 1,
                "roles": [{"role": ws["role"]}],
                "content": workspace_content
            })
            doc.insert(ignore_permissions=True)
            print(f"Created Workspace: {ws['label']} for role {ws['role']}")
        else:
            print(f"Workspace {ws['label']} already exists")
            
    frappe.db.commit()
    print("Setup completed.")

setup()
