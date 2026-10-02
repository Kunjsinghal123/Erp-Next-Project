import frappe

def execute(filters=None):
    columns = [
        {"fieldname": "description", "label": "Target Description", "fieldtype": "Text", "width": 300},
        {"fieldname": "weight", "label": "Weight", "fieldtype": "Float", "width": 100},
        {"fieldname": "self_score", "label": "Self Score", "fieldtype": "Float", "width": 100},
        {"fieldname": "supervisor_score", "label": "Supervisor Score", "fieldtype": "Float", "width": 120},
        {"fieldname": "reviewer_score", "label": "Reviewer Score", "fieldtype": "Float", "width": 120}
    ]
    
    conditions = "1=1"
    if filters and filters.get("employee"):
        conditions += f" AND a.employee = '{filters.get('employee')}'"
    if filters and filters.get("cycle"):
        conditions += f" AND a.cycle = '{filters.get('cycle')}'"
        
    query = f"""
        SELECT 
            t.description,
            t.weight,
            t.self_score,
            t.supervisor_score,
            t.reviewer_score
        FROM `tabPMS Target` t
        LEFT JOIN `tabPMS Appraisal` a ON t.parent = a.name
        WHERE {conditions}
    """
    
    data = frappe.db.sql(query, as_dict=True)
    return columns, data
