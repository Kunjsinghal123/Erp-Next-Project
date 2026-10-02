import frappe

def execute():
    doc = frappe.get_doc("DocType", "PMS Appraisal")
    for field in doc.fields:
        if field.fieldname in ["plan_status", "workflow_state"]:
            field.read_only = 1
            if field.fieldname == "plan_status" and "Monitoring" not in field.options:
                field.options += "\nMonitoring"
    doc.save()
    frappe.db.commit()
    print("Updated PMS Appraisal")
