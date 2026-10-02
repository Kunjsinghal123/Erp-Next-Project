import frappe

def run():
    frappe.logger().info("Creating Script Reports for PMS...")
    reports = [
        "PMS Completion Report",
        "PMS Score Analysis",
        "PMS Employee Report",
        "PMS Office Report"
    ]
    
    if frappe.db.exists("Report", "PMS Department Report"):
        frappe.rename_doc("Report", "PMS Department Report", "PMS Office Report", force=True)

    
    for r in reports:
        if not frappe.db.exists("Report", r):
            doc = frappe.get_doc({
                "doctype": "Report",
                "report_name": r,
                "ref_doctype": "PMS Appraisal",
                "report_type": "Script Report",
                "is_standard": "Yes",
                "module": "GDL PMS",
                "roles": [
                    {"role": "HR Admin"},
                    {"role": "System Manager"}
                ]
            })
            doc.insert(ignore_permissions=True)
            frappe.logger().info(f"Created report: {r}")
        else:
            doc = frappe.get_doc("Report", r)
            doc.roles = []
            doc.append("roles", {"role": "HR Admin"})
            doc.append("roles", {"role": "System Manager"})
            doc.save(ignore_permissions=True)
            frappe.logger().info(f"Updated permissions for report: {r}")
            
    frappe.db.commit()
    print("Successfully configured Script Reports permissions.")
    
