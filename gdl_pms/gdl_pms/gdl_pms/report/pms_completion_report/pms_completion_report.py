import frappe

def execute(filters=None):
    columns = [
        {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 160},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 180},
        {"fieldname": "department", "label": "Office", "fieldtype": "Link", "options": "Department", "width": 150},
        {"fieldname": "workflow_state", "label": "Current Stage", "fieldtype": "Data", "width": 160}
    ]
    
    filters = filters or {}
    conditions = ["e.status = 'Active'"]
    values = {}
    
    if filters.get("department"):
        conditions.append("e.department = %(department)s")
        values["department"] = filters.get("department")
        
    cycle_join = ""
    if filters.get("cycle"):
        cycle_join = "AND a.cycle = %(cycle)s"
        values["cycle"] = filters.get("cycle")
        
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            e.name AS employee,
            e.employee_name,
            e.department,
            CASE
                WHEN a.name IS NULL THEN 'Not Started'
                ELSE COALESCE(a.workflow_state, 'Draft')
            END AS workflow_state
        FROM `tabEmployee` e
        LEFT JOIN `tabPMS Appraisal` a ON a.employee = e.name AND a.docstatus != 2 {cycle_join}
        WHERE {where_clause}
        ORDER BY e.name ASC
    """
    
    data = frappe.db.sql(query, values=values, as_dict=True)
    return columns, data
