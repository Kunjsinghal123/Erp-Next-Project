import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def run():
    frappe.logger().info("Setting up Grade Group derivation...")
    
    # 1. Create Custom Field on Employee if not exists
    create_custom_field("Employee", {
        "fieldname": "grade_group",
        "label": "Grade Group",
        "fieldtype": "Select",
        "options": "PS_CS\nOS_ESP",
        "insert_after": "department",
        "reqd": 1,
        "in_list_view": 1
    })
    frappe.logger().info("Created/Updated custom field 'grade_group' on Employee")
    
    # 2. Make 'grade_group' on PMS Appraisal read-only
    make_property_setter("PMS Appraisal", "grade_group", "read_only", 1, "Check")
    frappe.logger().info("Set 'grade_group' on PMS Appraisal to read-only")
    
    frappe.db.commit()
    print("Grade group setup completed.")
