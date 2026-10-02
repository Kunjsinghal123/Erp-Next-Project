import frappe

def execute(filters=None):
    columns = [
        {"fieldname": "department", "label": "Office", "fieldtype": "Link", "options": "Department", "width": 200},
        {"fieldname": "avg_score", "label": "Average Total Score", "fieldtype": "Float", "width": 150},
        {"fieldname": "outstanding", "label": "Outstanding Count", "fieldtype": "Int", "width": 130},
        {"fieldname": "exceeds", "label": "Exceeds Count", "fieldtype": "Int", "width": 120},
        {"fieldname": "meets", "label": "Meets Count", "fieldtype": "Int", "width": 100},
        {"fieldname": "needs_improvement", "label": "Needs Improvement", "fieldtype": "Int", "width": 150},
        {"fieldname": "unsatisfactory", "label": "Unsatisfactory", "fieldtype": "Int", "width": 120}
    ]
    
    conditions = "1=1"
    if filters and filters.get("department"):
        conditions += f" AND e.department = '{filters.get('department')}'"
    if filters and filters.get("cycle"):
        conditions += f" AND a.cycle = '{filters.get('cycle')}'"
        
    query = f"""
        SELECT 
            e.department,
            AVG(a.total_score) as avg_score,
            SUM(CASE WHEN a.rating_band LIKE 'Outstanding%' THEN 1 ELSE 0 END) as outstanding,
            SUM(CASE WHEN a.rating_band LIKE 'Exceeds%' THEN 1 ELSE 0 END) as exceeds,
            SUM(CASE WHEN a.rating_band LIKE 'Meets%' THEN 1 ELSE 0 END) as meets,
            SUM(CASE WHEN a.rating_band LIKE 'Needs Improvement%' THEN 1 ELSE 0 END) as needs_improvement,
            SUM(CASE WHEN a.rating_band LIKE 'Unsatisfactory%' THEN 1 ELSE 0 END) as unsatisfactory
        FROM `tabPMS Appraisal` a
        LEFT JOIN `tabEmployee` e ON a.employee = e.name
        WHERE {conditions}
        GROUP BY e.department
    """
    
    data = frappe.db.sql(query, as_dict=True)
    return columns, data
