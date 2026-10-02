import frappe

def run():
    # Delete existing test records to avoid unique/reqd constraints
    frappe.db.sql("DELETE FROM `tabPMS Appraisal Cycle`")
    frappe.db.commit()
    
    dt = frappe.get_doc("DocType", "PMS Appraisal Cycle")
    
    has_cycle_name = False
    for f in dt.fields:
        if f.fieldname == "cycle_name":
            has_cycle_name = True
            break
            
    if not has_cycle_name:
        dt.append("fields", {
            "fieldname": "cycle_name",
            "fieldtype": "Data",
            "label": "Cycle Name",
            "reqd": 1,
            "in_list_view": 1,
            "unique": 1
        })
        cycle_field = dt.fields[-1]
        dt.fields.remove(cycle_field)
        dt.fields.insert(0, cycle_field)
        for i, f in enumerate(dt.fields):
            f.idx = i + 1
            
    dt.autoname = "field:cycle_name"
    dt.show_title_field_in_link = 1
    dt.title_field = "cycle_name"
    
    # Update field order explicitly
    if getattr(dt, 'field_order', None):
        if "cycle_name" not in dt.field_order:
            dt.field_order = ["cycle_name"] + [f for f in dt.field_order if f != "cycle_name"]
    
    dt.save(ignore_permissions=True)
    frappe.db.commit()
    print("Added cycle_name to PMS Appraisal Cycle")
