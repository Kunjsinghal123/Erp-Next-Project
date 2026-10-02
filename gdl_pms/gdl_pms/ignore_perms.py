import frappe
def execute():
    for f in ['employee', 'supervisor_snapshot', 'reviewer_snapshot']:
        frappe.db.set_value('DocField', {'parent': 'PMS Appraisal', 'fieldname': f}, 'ignore_user_permissions', 1)
    frappe.db.commit()
    print("Done")
