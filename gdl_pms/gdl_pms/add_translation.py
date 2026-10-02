import frappe

def execute():
    if not frappe.db.exists("Translation", {"source_text": "PMS Appraisal", "translated_text": "PMS Performance Plan"}):
        doc = frappe.get_doc({
            "doctype": "Translation",
            "language": "en",
            "source_text": "PMS Appraisal",
            "translated_text": "PMS Performance Plan"
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Translation added.")
    else:
        print("Translation already exists.")
