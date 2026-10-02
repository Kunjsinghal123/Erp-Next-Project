import frappe

def update():
    doc = frappe.get_doc("DocType", "PMS Appraisal")
    f = doc.get("fields", {"fieldname": "grade_group"})[0]
    f.fetch_from = "employee.grade_group"
    doc.save()
    frappe.db.commit()
    print("Updated fetch_from")
