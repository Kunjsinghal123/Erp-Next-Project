import frappe

def create_pms_target():
    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": "PMS Target",
        "module": "GDL PMS",
        "custom": 0,
        "istable": 1,
        "editable_grid": 1,
        "fields": [
            {
                "fieldname": "target_description",
                "fieldtype": "Small Text",
                "label": "Target Description",
                "in_list_view": 1,
                "reqd": 1
            },
            {
                "fieldname": "weight",
                "fieldtype": "Float",
                "label": "Weight",
                "in_list_view": 1,
                "reqd": 1,
                "columns": 1
            }
        ]
    })
    doc.insert(ignore_permissions=True)
    print("Created PMS Target")

def create_pms_competency_score():
    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": "PMS Competency Score",
        "module": "GDL PMS",
        "custom": 0,
        "istable": 1,
        "editable_grid": 1,
        "fields": [
            {
                "fieldname": "competency",
                "fieldtype": "Select",
                "label": "Competency",
                "options": "Job Knowledge & Skills\nQuality of Work\nCommunication & Teamwork\nInitiative & Problem Solving\nAttendance & Punctuality",
                "in_list_view": 1,
                "reqd": 1,
                "read_only": 1
            },
            {
                "fieldname": "weight",
                "fieldtype": "Float",
                "label": "Weight",
                "in_list_view": 1,
                "reqd": 1,
                "read_only": 1,
                "columns": 1
            }
        ]
    })
    doc.insert(ignore_permissions=True)
    print("Created PMS Competency Score")

def create_pms_appraisal():
    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": "PMS Appraisal",
        "module": "GDL PMS",
        "custom": 0,
        "autoname": "format:PMS-{YYYY}-{MM}-{#####}",
        "fields": [
            {
                "fieldname": "employee",
                "fieldtype": "Link",
                "label": "Employee",
                "options": "Employee",
                "reqd": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "cycle",
                "fieldtype": "Link",
                "label": "Cycle",
                "options": "PMS Appraisal Cycle",
                "reqd": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "grade_group",
                "fieldtype": "Data",
                "label": "Grade Group",
                "read_only": 1,
                "fetch_from": "employee.grade_group"
            },
            {
                "fieldname": "supervisor_snapshot",
                "fieldtype": "Data",
                "label": "Supervisor",
                "read_only": 1
            },
            {
                "fieldname": "reviewer_snapshot",
                "fieldtype": "Data",
                "label": "Reviewer",
                "read_only": 1
            },
            {
                "fieldname": "plan_status",
                "fieldtype": "Select",
                "label": "Plan Status",
                "options": "Draft\nPending Supervisor Approval\nPending Reviewer Approval\nApproved\nRejected",
                "default": "Draft",
                "in_list_view": 1
            },
            {
                "fieldname": "workflow_state",
                "fieldtype": "Select",
                "label": "Workflow State",
                "options": "Planning Open\nMonitoring",
                "default": "Planning Open",
                "in_list_view": 1
            },
            {
                "fieldname": "plan_rejection_remark",
                "fieldtype": "Small Text",
                "label": "Plan Rejection Remark",
                "hidden": 1
            },
            {
                "fieldname": "targets",
                "fieldtype": "Table",
                "label": "Targets",
                "options": "PMS Target"
            },
            {
                "fieldname": "competencies",
                "fieldtype": "Table",
                "label": "Competencies",
                "options": "PMS Competency Score"
            }
        ],
        "permissions": [
            {
                "role": "System Manager",
                "read": 1, "write": 1, "create": 1, "delete": 1
            },
            {
                "role": "Employee",
                "read": 1, "write": 1, "create": 1
            },
            {
                "role": "Supervisor",
                "read": 1, "write": 1
            },
            {
                "role": "Reviewer",
                "read": 1, "write": 1
            }
        ]
    })
    doc.insert(ignore_permissions=True)
    print("Created PMS Appraisal")

def execute():
    create_pms_target()
    create_pms_competency_score()
    create_pms_appraisal()
    frappe.db.commit()
    print("Scaffold complete.")
