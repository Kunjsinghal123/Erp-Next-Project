import frappe
import json

def update():
    # 1. Update List View Customizations
    if frappe.db.exists("Custom Field", "Employee-reviewer"):
        cf = frappe.get_doc("Custom Field", "Employee-reviewer")
        cf.in_list_view = 1
        cf.save(ignore_permissions=True)
        print("Updated Custom Field Employee-reviewer in_list_view to 1")

    if not frappe.db.exists("Property Setter", "Employee-reports_to-in_list_view"):
        frappe.get_doc({
            "doctype": "Property Setter",
            "doctype_or_field": "DocField",
            "doc_type": "Employee",
            "field_name": "reports_to",
            "property": "in_list_view",
            "property_type": "Check",
            "value": "1",
            "module": "GDL PMS"
        }).insert(ignore_permissions=True)
        print("Created Property Setter for Employee-reports_to in_list_view to 1")

    # 2. Number Card
    card_name = "Total Active Employees"
    if not frappe.db.exists("Number Card", card_name):
        doc = frappe.get_doc({
            "doctype": "Number Card",
            "name": card_name,
            "label": card_name,
            "document_type": "Employee",
            "function": "Count",
            "filters_json": '[["Employee","status","=","Active",false]]',
            "is_standard": 1,
            "module": "GDL PMS"
        })
        doc.insert(ignore_permissions=True)
        print(f"Created Number Card: {card_name}")

    # 3. Workspace Updates
    target_workspaces = ["PMS HR", "PMS HR Workspace"]
    for workspace_name in target_workspaces:
        if frappe.db.exists("Workspace", workspace_name):
            ws = frappe.get_doc("Workspace", workspace_name)

            # Ensure shortcuts exist
            shortcuts_to_add = [
                {
                    "label": "Employees",
                    "type": "DocType",
                    "link_to": "Employee",
                    "doc_view": "List",
                    "stats_filter": '[["Employee","status","=","Active",false]]'
                },
                {
                    "label": "Add Employee",
                    "type": "DocType",
                    "link_to": "Employee",
                    "doc_view": "New",
                },
                {
                    "label": "Approval History",
                    "type": "DocType",
                    "link_to": "PMS Appraisal",
                    "doc_view": "List",
                    "stats_filter": '[["PMS Appraisal","plan_status","in",["Approved", "Rejected"]]]'
                },
                {
                    "label": "PMS Completion Report",
                    "type": "Report",
                    "link_to": "PMS Completion Report"
                },
                {
                    "label": "PMS Score Analysis",
                    "type": "Report",
                    "link_to": "PMS Score Analysis"
                },
                {
                    "label": "PMS Employee Report",
                    "type": "Report",
                    "link_to": "PMS Employee Report"
                },
                {
                    "label": "PMS Office Report",
                    "type": "Report",
                    "link_to": "PMS Office Report"
                }
            ]

            existing_shortcuts = [s.label for s in ws.shortcuts]
            for s in shortcuts_to_add:
                if s["label"] not in existing_shortcuts:
                    ws.append("shortcuts", s)

            # Ensure links (cards) exist
            links_to_add = [
                {
                    "label": "PMS Reports",
                    "type": "Card Break",
                    "icon": "report"
                },
                {
                    "label": "PMS Completion Report",
                    "type": "Link",
                    "link_to": "PMS Completion Report",
                    "link_type": "Report",
                    "is_query_report": 1
                },
                {
                    "label": "PMS Score Analysis",
                    "type": "Link",
                    "link_to": "PMS Score Analysis",
                    "link_type": "Report",
                    "is_query_report": 1
                },
                {
                    "label": "PMS Employee Report",
                    "type": "Link",
                    "link_to": "PMS Employee Report",
                    "link_type": "Report",
                    "is_query_report": 1
                },
                {
                    "label": "PMS Office Report",
                    "type": "Link",
                    "link_to": "PMS Office Report",
                    "link_type": "Report",
                    "is_query_report": 1
                }
            ]

            existing_links = [l.label for l in ws.links]
            for l in links_to_add:
                if l["label"] not in existing_links:
                    ws.append("links", l)

            # Build comprehensive JSON Content
            content_blocks = [
                {"type": "header", "data": {"text": "Employee Management", "level": 2}},
                {"type": "shortcut", "data": {"shortcut_name": "Employees"}},
                {"type": "shortcut", "data": {"shortcut_name": "Add Employee"}},
                {"type": "shortcut", "data": {"shortcut_name": "Approval History"}},
                {"type": "number_card", "data": {"number_card_name": "Total Active Employees"}},

                {"type": "header", "data": {"text": "PMS Dashboard", "level": 2}},
                {"type": "number_card", "data": {"number_card_name": "Total Employees"}},
                {"type": "number_card", "data": {"number_card_name": "Active Cycles"}},
                {"type": "number_card", "data": {"number_card_name": "Pending PERC"}},
                {"type": "number_card", "data": {"number_card_name": "Completion Rate"}},
                {"type": "shortcut", "data": {"shortcut_name": "Pending For Approval"}},

                {"type": "header", "data": {"text": "PMS Reports & Analytics", "level": 2}},
                {"type": "shortcut", "data": {"shortcut_name": "PMS Completion Report"}},
                {"type": "shortcut", "data": {"shortcut_name": "PMS Score Analysis"}},
                {"type": "shortcut", "data": {"shortcut_name": "PMS Employee Report"}},
                {"type": "shortcut", "data": {"shortcut_name": "PMS Office Report"}},
                {"type": "card", "data": {"card_name": "PMS Reports"}}
            ]

            ws.content = json.dumps(content_blocks)
            ws.roles = []
            ws.append("roles", {"role": "HR Admin"})
            ws.append("roles", {"role": "System Manager"})
            ws.save(ignore_permissions=True)
            print(f"Successfully updated Workspace: {workspace_name} with Reports section.")

    frappe.db.commit()
    print("HR Workspace updates completed.")

if __name__ == "__main__":
    update()
