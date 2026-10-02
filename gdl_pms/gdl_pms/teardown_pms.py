import frappe

def execute():
    doctypes_to_delete = ["PMS Appraisal", "PMS Target", "PMS Competency Score"]
    
    # 1. Delete all records first
    for dt in doctypes_to_delete:
        if frappe.db.exists("DocType", dt):
            records = frappe.get_all(dt)
            for r in records:
                try:
                    frappe.delete_doc(dt, r.name, force=1, ignore_permissions=1)
                except Exception as e:
                    pass
    
    frappe.db.commit()

    # 2. Delete the DocTypes themselves
    for dt in doctypes_to_delete:
        if frappe.db.exists("DocType", dt):
            try:
                frappe.delete_doc("DocType", dt, force=1, ignore_permissions=1)
                print(f"Deleted DocType: {dt}")
            except Exception as e:
                print(f"Failed to delete {dt}: {e}")
    
    # 3. Delete Translation
    trans = frappe.get_all("Translation", filters={"source_text": "PMS Appraisal"})
    for t in trans:
        frappe.delete_doc("Translation", t.name, force=1, ignore_permissions=1)
        print("Deleted Translation")

    # 4. Delete associated Client Scripts / Server Scripts if they exist generically
    for dt in doctypes_to_delete:
        cs = frappe.get_all("Client Script", filters={"dt": dt})
        for c in cs:
            frappe.delete_doc("Client Script", c.name, force=1, ignore_permissions=1)
        
        ss = frappe.get_all("Server Script", filters={"reference_doctype": dt})
        for s in ss:
            frappe.delete_doc("Server Script", s.name, force=1, ignore_permissions=1)

    frappe.db.commit()
    print("Teardown complete.")
