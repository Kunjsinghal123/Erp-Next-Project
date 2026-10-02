import frappe

def maybe_create_increment(appraisal):
    """
    Creates a draft Additional Salary record for a Performance Increment
    if the employee's total score is > 80.
    """
    if appraisal.total_score and appraisal.total_score > 80:
        frappe.get_doc({
            "doctype": "Additional Salary",
            "employee": appraisal.employee,
            "salary_component": "Performance Increment",
            "amount": 0,  # HR fills in the actual figure per GDL's increment matrix
            "docstatus": 0,
            "payroll_date": frappe.utils.today()
        }).insert(ignore_permissions=True)
        frappe.logger().info(f"Draft Additional Salary created for Employee: {appraisal.employee}")
