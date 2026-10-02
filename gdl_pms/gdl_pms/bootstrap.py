import frappe

def create_doctypes():
    doctypes = [
        {
            "doctype": "DocType",
            "module": "Gdl Pms",
            "custom": 0,
            "name": "PMS Appraisal Cycle",
            "fields": [
                {"fieldname": "cycle_type", "fieldtype": "Select", "label": "Cycle Type", "options": "Annual\nHalf-Yearly\nProbation", "reqd": 1, "in_list_view": 1},
                {"fieldname": "start_date", "fieldtype": "Date", "label": "Start Date", "reqd": 1, "in_list_view": 1},
                {"fieldname": "end_date", "fieldtype": "Date", "label": "End Date", "reqd": 1, "in_list_view": 1},
                {"fieldname": "status", "fieldtype": "Select", "label": "Status", "options": "Draft\nActive\nClosed", "default": "Draft", "in_list_view": 1},
                {"fieldname": "grade_group", "fieldtype": "Select", "label": "Grade Group", "options": "PS_CS\nOS_ESP", "reqd": 1, "in_list_view": 1}
            ]
        },

        {
            "doctype": "DocType",
            "module": "Gdl Pms",
            "custom": 0,
            "name": "PMS Target",
            "istable": 1,
            "fields": [
                {"fieldname": "description", "fieldtype": "Text Editor", "label": "Target Description", "reqd": 1, "in_list_view": 1},
                {"fieldname": "weight", "fieldtype": "Float", "label": "Weight", "reqd": 1, "in_list_view": 1},
                {"fieldname": "self_score", "fieldtype": "Float", "label": "Self Score", "in_list_view": 1},
                {"fieldname": "supervisor_score", "fieldtype": "Float", "label": "Supervisor Score", "in_list_view": 1},
                {"fieldname": "reviewer_score", "fieldtype": "Float", "label": "Reviewer Score", "in_list_view": 1},
                {"fieldname": "evidence", "fieldtype": "Attach", "label": "Evidence"}
            ]
        },
        {
            "doctype": "DocType",
            "module": "Gdl Pms",
            "custom": 0,
            "name": "PMS Competency Score",
            "istable": 1,
            "fields": [
                {"fieldname": "competency", "fieldtype": "Data", "label": "Competency", "reqd": 1, "in_list_view": 1},
                {"fieldname": "weight", "fieldtype": "Float", "label": "Weight", "reqd": 1, "in_list_view": 1},
                {"fieldname": "self_rating", "fieldtype": "Float", "label": "Self Rating", "in_list_view": 1},
                {"fieldname": "supervisor_rating", "fieldtype": "Float", "label": "Supervisor Rating", "in_list_view": 1},
                {"fieldname": "reviewer_rating", "fieldtype": "Float", "label": "Reviewer Rating", "in_list_view": 1}
            ]
        },
        {
            "doctype": "DocType",
            "module": "Gdl Pms",
            "custom": 0,
            "name": "PMS Appraisal",
            "fields": [
                {"fieldname": "employee", "fieldtype": "Link", "options": "Employee", "label": "Employee", "reqd": 1, "in_list_view": 1},
                {"fieldname": "cycle", "fieldtype": "Link", "options": "PMS Appraisal Cycle", "label": "Cycle", "reqd": 1, "in_list_view": 1},
                {"fieldname": "grade_group", "fieldtype": "Select", "label": "Grade Group", "options": "PS_CS\nOS_ESP", "reqd": 1},
                {"fieldname": "workflow_state", "fieldtype": "Data", "label": "Workflow State", "read_only": 1, "in_list_view": 1},
                {"fieldname": "total_score", "fieldtype": "Float", "label": "Total Score", "read_only": 1, "in_list_view": 1},
                {"fieldname": "rating_band", "fieldtype": "Data", "label": "Rating Band", "read_only": 1, "in_list_view": 1},
                {"fieldname": "dispute_flag", "fieldtype": "Check", "label": "Disputed", "default": "0"},
                {"fieldname": "targets", "fieldtype": "Table", "options": "PMS Target", "label": "Targets"},
                {"fieldname": "competencies", "fieldtype": "Table", "options": "PMS Competency Score", "label": "Competencies"}
            ]
        },
        {
            "doctype": "DocType",
            "module": "Gdl Pms",
            "custom": 0,
            "name": "PERC Committee Member",
            "istable": 1,
            "fields": [
                {"fieldname": "member", "fieldtype": "Link", "options": "User", "label": "Committee Member", "reqd": 1, "in_list_view": 1},
                {"fieldname": "role", "fieldtype": "Data", "label": "Role", "in_list_view": 1}
            ]
        },
        {
            "doctype": "DocType",
            "module": "Gdl Pms",
            "custom": 0,
            "name": "PERC Case",
            "fields": [
                {"fieldname": "appraisal", "fieldtype": "Link", "options": "PMS Appraisal", "label": "Appraisal", "reqd": 1, "in_list_view": 1},
                {"fieldname": "raised_by", "fieldtype": "Link", "options": "Employee", "label": "Raised By", "reqd": 1, "in_list_view": 1},
                {"fieldname": "justification", "fieldtype": "Text Editor", "label": "Justification", "reqd": 1},
                {"fieldname": "committee_members", "fieldtype": "Table", "options": "PERC Committee Member", "label": "Committee Members"},
                {"fieldname": "hearing_notes", "fieldtype": "Text Editor", "label": "Hearing Notes"},
                {"fieldname": "final_score", "fieldtype": "Float", "label": "Final Score"},
                {"fieldname": "minutes_attachment", "fieldtype": "Attach", "label": "Minutes Attachment"},
                {"fieldname": "status", "fieldtype": "Select", "options": "Draft\nOpen\nResolved", "default": "Draft", "label": "Status", "in_list_view": 1}
            ]
        }
    ]

    for dt in doctypes:
        if not frappe.db.exists("DocType", dt["name"]):
            doc = frappe.get_doc(dt)
            doc.insert(ignore_permissions=True)
            print(f"Created DocType: {dt['name']}")
        else:
            print(f"DocType {dt['name']} already exists.")
            
    # Create Custom Field for Employee
    custom_field = {
        "doctype": "Custom Field",
        "dt": "Employee",
        "fieldname": "reviewer",
        "label": "Reviewer",
        "fieldtype": "Link",
        "options": "Employee",
        "insert_after": "reports_to"
    }
    if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "reviewer"}):
        frappe.get_doc(custom_field).insert(ignore_permissions=True)
        print("Created Custom Field: reviewer on Employee")
        
    frappe.db.commit()
