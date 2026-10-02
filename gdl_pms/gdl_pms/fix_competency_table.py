import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def run():
    frappe.logger().info("Locking competency table rows...")
    
    # Disable adding/deleting rows in the competencies child table
    make_property_setter("PMS Appraisal", "competencies", "cannot_add_rows", 1, "Check")
    make_property_setter("PMS Appraisal", "competencies", "cannot_delete_rows", 1, "Check")
    
    frappe.logger().info("Competency table is now locked from manual additions/deletions.")
    frappe.db.commit()
    print("Competencies table locked.")
