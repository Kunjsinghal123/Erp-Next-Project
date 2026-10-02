import frappe
from gdl_pms.employee_hooks import auto_assign_roles

def sync_all():
    print("Syncing Supervisor & Reviewer roles for all employees...")
    employees = frappe.get_all("Employee", fields=["name", "employee_name", "user_id", "reports_to", "reviewer"])
    
    for emp in employees:
        emp_doc = frappe.get_doc("Employee", emp.name)
        auto_assign_roles(emp_doc, None)
        
    frappe.db.commit()
    print("Done syncing roles!")

if __name__ == "__main__":
    sync_all()
