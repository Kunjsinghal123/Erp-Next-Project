import frappe

def execute(filters=None):
    columns = [
        {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 160},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 180},
        {"fieldname": "work_score", "label": "Work Score", "fieldtype": "Float", "width": 120},
        {"fieldname": "comp_score", "label": "Competency Score", "fieldtype": "Float", "width": 140},
        {"fieldname": "total_score", "label": "Total Score", "fieldtype": "Float", "width": 120},
        {"fieldname": "rating_band", "label": "Rating Band", "fieldtype": "Data", "width": 200}
    ]
    
    conditions = "1=1"
    if filters and filters.get("cycle"):
        conditions += f" AND a.cycle = '{filters.get('cycle')}'"
    if filters and filters.get("department"):
        conditions += f" AND e.department = '{filters.get('department')}'"
    if filters and filters.get("grade_group"):
        conditions += f" AND a.grade_group = '{filters.get('grade_group')}'"
        
    appraisals = frappe.db.sql(f"""
        SELECT a.name, a.employee, e.employee_name, a.total_score, a.rating_band
        FROM `tabPMS Appraisal` a
        LEFT JOIN `tabEmployee` e ON a.employee = e.name
        WHERE {conditions}
    """, as_dict=True)
    
    data = []
    for app in appraisals:
        # Calculate work score
        targets = frappe.get_all("PMS Target", filters={"parent": app.name}, fields=["reviewer_score", "supervisor_score"])
        work_score = sum((t.reviewer_score or t.supervisor_score or 0) for t in targets)
        
        # Calculate comp score
        comps = frappe.get_all("PMS Competency Score", filters={"parent": app.name}, fields=["reviewer_rating", "supervisor_rating"])
        comp_score = sum((c.reviewer_rating or c.supervisor_rating or 0) for c in comps)
        
        data.append({
            "employee": app.employee,
            "employee_name": app.employee_name,
            "work_score": work_score,
            "comp_score": comp_score,
            "total_score": app.total_score,
            "rating_band": app.rating_band
        })
        
    return columns, data
