import frappe
from frappe.utils import now_datetime, pretty_date, format_datetime, formatdate

def get_active_appraisal_cycles():
    cycles_list = frappe.db.get_list(
        "PMS Appraisal Cycle",
        filters={"status": ["in", ["Draft", "Active", "Planning Open", "Monitoring", "Self-Rating Open"]]},
        fields=["name", "cycle_name", "status", "start_date", "end_date", "creation"],
        order_by="creation desc",
        limit=10
    )
    if not cycles_list:
        cycles_list = frappe.db.get_list(
            "PMS Appraisal Cycle",
            fields=["name", "cycle_name", "status", "start_date", "end_date", "creation"],
            order_by="creation desc",
            limit=10
        )

    cycles = []
    for c in cycles_list:
        date_str = ""
        if c.get("start_date") and c.get("end_date"):
            date_str = f" • {formatdate(c.start_date, 'dd MMM yyyy')} - {formatdate(c.end_date, 'dd MMM yyyy')}"
        status_val = c.get("status") or "Draft"
        if status_val == "Active":
            badge_class = "badge-approved"
        elif status_val in ["Planning Open", "Monitoring", "Self-Rating Open"]:
            badge_class = "badge-pending"
        elif status_val == "Draft":
            badge_class = "badge-draft"
        else:
            badge_class = "badge-inprogress"

        cycles.append({
            "name": c.name,
            "title": c.cycle_name or c.name,
            "status": status_val,
            "badge_class": badge_class,
            "subtitle": f"Status: {status_val}{date_str}"
        })
    return cycles

@frappe.whitelist()
def get_employee_dashboard_data():
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    
    # Try to find linked Employee
    employee = frappe.db.get_value(
        "Employee", 
        {"user_id": user}, 
        ["name", "employee_name", "first_name", "user_id"], 
        as_dict=True
    )
    
    if not employee:
        # Fallback search by email
        employee = frappe.db.get_value(
            "Employee", 
            {"prefered_email": user}, 
            ["name", "employee_name", "first_name", "user_id"], 
            as_dict=True
        ) or frappe.db.get_value(
            "Employee", 
            {"company_email": user}, 
            ["name", "employee_name", "first_name", "user_id"], 
            as_dict=True
        )

    employee_id = employee.get("name") if employee else None
    if employee:
        display_name = employee.get("first_name") or employee.get("employee_name") or (user_doc.first_name if user_doc else "Employee")
    else:
        display_name = (user_doc.first_name if user_doc else None) or "Employee"

    # Determine time of day greeting
    now_hour = now_datetime().hour
    if now_hour < 12:
        greeting_prefix = "Good Morning"
    elif now_hour < 17:
        greeting_prefix = "Good Afternoon"
    else:
        greeting_prefix = "Good Evening"

    greeting = f"{greeting_prefix}, {display_name}"

    # Counts logic
    emp_filters = []
    if employee_id:
        emp_filters.append(["employee", "=", employee_id])
    else:
        emp_filters.append(["owner", "=", user])

    # 1. Performance Plans Count
    my_plans_count = frappe.db.count("PMS Appraisal", filters=emp_filters)

    # 2. Plan Amendments Count
    amendment_filters = list(emp_filters)
    amendments_count = frappe.db.count("PMS Plan Amendment", filters=amendment_filters)

    # 3. Approval History Count
    approval_history_filters = list(emp_filters)
    approval_history_filters.append(["plan_status", "in", ["Approved", "Rejected", "Returned"]])
    approval_history_count = frappe.db.count("PMS Appraisal", filters=approval_history_filters)

    # Recent Activity
    appraisals = frappe.db.get_list(
        "PMS Appraisal",
        filters=emp_filters,
        fields=["name", "cycle", "plan_status", "creation", "modified"],
        order_by="modified desc",
        limit=5
    )

    amendment_list = frappe.db.get_list(
        "PMS Plan Amendment",
        filters=emp_filters,
        fields=["name", "performance_plan", "status", "creation", "modified"],
        order_by="modified desc",
        limit=5
    )

    activities = []
    for app in appraisals:
        activities.append({
            "id": app.name,
            "title": f"Performance Plan ({app.cycle})" if app.cycle else f"Performance Plan {app.name}",
            "doctype": "PMS Appraisal",
            "name": app.name,
            "status": app.plan_status or "Draft",
            "badge_class": get_badge_class(app.plan_status),
            "date_str": f"Updated on {format_datetime(app.modified, 'dd MMM yyyy, hh:mm a')}",
            "timestamp": app.modified
        })

    for amd in amendment_list:
        activities.append({
            "id": amd.name,
            "title": f"Amendment Request ({amd.performance_plan or amd.name})",
            "doctype": "PMS Plan Amendment",
            "name": amd.name,
            "status": amd.status or "Pending",
            "badge_class": get_badge_class(amd.status),
            "date_str": f"Submitted on {format_datetime(amd.modified, 'dd MMM yyyy, hh:mm a')}",
            "timestamp": amd.modified
        })

    # Sort activities by modified timestamp descending
    activities.sort(key=lambda x: str(x["timestamp"]), reverse=True)
    recent_activities = activities[:4]

    # Appraisal Cycles for dropdown & dashboard card
    cycles = get_active_appraisal_cycles()

    return {
        "greeting": greeting,
        "user_email": user_doc.email,
        "display_name": display_name,
        "counts": {
            "my_plans": my_plans_count,
            "active_cycles": len(cycles),
            "amendments": amendments_count,
            "approval_history": approval_history_count
        },
        "recent_activities": recent_activities,
        "cycles": cycles
    }

@frappe.whitelist()
def get_supervisor_dashboard_data():
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    
    employee = frappe.db.get_value(
        "Employee", 
        {"user_id": user}, 
        ["name", "employee_name", "first_name"], 
        as_dict=True
    )
    
    if employee:
        display_name = employee.get("first_name") or employee.get("employee_name") or (user_doc.first_name if user_doc else "Supervisor")
    else:
        display_name = (user_doc.first_name if user_doc else None) or "Supervisor"

    now_hour = now_datetime().hour
    greeting_prefix = "Good Morning" if now_hour < 12 else ("Good Afternoon" if now_hour < 17 else "Good Evening")
    greeting = f"{greeting_prefix}, {display_name}"

    # Supervisor Counts
    pending_appraisals = frappe.db.count("PMS Appraisal", filters={"plan_status": "Pending Supervisor Approval"})
    pending_amendments = frappe.db.count("PMS Plan Amendment", filters={"status": "Pending Supervisor Approval"})
    pending_evaluations = frappe.db.count("PMS Appraisal", filters={"appraisal_status": "Pending Supervisor Review"})
    total_pending = pending_appraisals + pending_amendments + pending_evaluations

    total_team_plans = frappe.db.count("PMS Appraisal")
    approved_plans = frappe.db.count("PMS Appraisal", filters={"plan_status": "Approved"})

    # Pending Team Actions List
    pending_appraisal_list = frappe.db.get_list(
        "PMS Appraisal",
        filters={"plan_status": "Pending Supervisor Approval"},
        fields=["name", "employee", "cycle", "plan_status", "modified"],
        order_by="modified desc",
        limit=5
    )

    pending_evaluations_list = frappe.db.get_list(
        "PMS Appraisal",
        filters={"appraisal_status": "Pending Supervisor Review"},
        fields=["name", "employee", "cycle", "appraisal_status", "modified"],
        order_by="modified desc",
        limit=5
    )

    pending_amendments_list = frappe.db.get_list(
        "PMS Plan Amendment",
        filters={"status": "Pending Supervisor Approval"},
        fields=["name", "performance_plan", "employee", "status", "modified"],
        order_by="modified desc",
        limit=5
    )

    pending_items = []
    for app in pending_evaluations_list:
        emp_name = frappe.db.get_value("Employee", app.employee, "employee_name") if app.employee else "Team Member"
        pending_items.append({
            "id": app.name,
            "title": f"Appraisal Evaluation: {emp_name}",
            "subtitle": f"Cycle: {app.cycle or 'Current'} • Self-Assessment Submitted {format_datetime(app.modified, 'dd MMM, hh:mm a')}",
            "doctype": "PMS Appraisal",
            "name": app.name,
            "status": "Pending Evaluation",
            "badge_class": "badge-pending",
            "timestamp": app.modified
        })

    for app in pending_appraisal_list:
        emp_name = frappe.db.get_value("Employee", app.employee, "employee_name") if app.employee else "Team Member"
        pending_items.append({
            "id": app.name,
            "title": f"Plan Review: {emp_name}",
            "subtitle": f"Cycle: {app.cycle or 'Current'} • Submitted {format_datetime(app.modified, 'dd MMM, hh:mm a')}",
            "doctype": "PMS Appraisal",
            "name": app.name,
            "status": "Pending Approval",
            "badge_class": "badge-pending",
            "timestamp": app.modified
        })

    for amd in pending_amendments_list:
        emp_name = frappe.db.get_value("Employee", amd.employee, "employee_name") if amd.employee else "Team Member"
        pending_items.append({
            "id": amd.name,
            "title": f"Amendment Request: {emp_name}",
            "subtitle": f"Plan: {amd.performance_plan or amd.name} • Submitted {format_datetime(amd.modified, 'dd MMM, hh:mm a')}",
            "doctype": "PMS Plan Amendment",
            "name": amd.name,
            "status": "Pending Amendment",
            "badge_class": "badge-pending",
            "timestamp": amd.modified
        })

    pending_items.sort(key=lambda x: str(x["timestamp"]), reverse=True)

    cycles = get_active_appraisal_cycles()

    return {
        "greeting": greeting,
        "user_email": user_doc.email,
        "display_name": display_name,
        "counts": {
            "pending_approvals": total_pending,
            "team_plans": total_team_plans,
            "active_cycles": len(cycles),
            "approved_plans": approved_plans
        },
        "pending_items": pending_items[:5],
        "cycles": cycles
    }

@frappe.whitelist()
def get_reviewer_dashboard_data():
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    
    employee = frappe.db.get_value(
        "Employee", 
        {"user_id": user}, 
        ["name", "employee_name", "first_name"], 
        as_dict=True
    )
    
    if employee:
        display_name = employee.get("first_name") or employee.get("employee_name") or (user_doc.first_name if user_doc else "Reviewer")
    else:
        display_name = (user_doc.first_name if user_doc else None) or "Reviewer"

    now_hour = now_datetime().hour
    greeting_prefix = "Good Morning" if now_hour < 12 else ("Good Afternoon" if now_hour < 17 else "Good Evening")
    greeting = f"{greeting_prefix}, {display_name}"

    # Reviewer Counts
    pending_appraisals = frappe.db.count("PMS Appraisal", filters={"plan_status": "Pending Reviewer Approval"})
    pending_amendments = frappe.db.count("PMS Plan Amendment", filters={"status": "Pending Reviewer Approval"})
    pending_disputes = frappe.db.count("PMS Appraisal", filters={"appraisal_status": "Disputed - Pending Reviewer"})
    total_pending = pending_appraisals + pending_amendments + pending_disputes

    total_dept_plans = frappe.db.count("PMS Appraisal")
    finalized_plans = frappe.db.count("PMS Appraisal", filters={"plan_status": "Approved"})

    # Pending Review Queue
    pending_disputes_list = frappe.db.get_list(
        "PMS Appraisal",
        filters={"appraisal_status": "Disputed - Pending Reviewer"},
        fields=["name", "employee", "cycle", "dispute_reason", "modified"],
        order_by="modified desc",
        limit=5
    )

    pending_appraisal_list = frappe.db.get_list(
        "PMS Appraisal",
        filters={"plan_status": "Pending Reviewer Approval"},
        fields=["name", "employee", "cycle", "plan_status", "modified"],
        order_by="modified desc",
        limit=5
    )

    pending_amendments_list = frappe.db.get_list(
        "PMS Plan Amendment",
        filters={"status": "Pending Reviewer Approval"},
        fields=["name", "performance_plan", "employee", "status", "modified"],
        order_by="modified desc",
        limit=5
    )

    pending_reviews = []
    for app in pending_disputes_list:
        emp_name = frappe.db.get_value("Employee", app.employee, "employee_name") if app.employee else "Employee"
        pending_reviews.append({
            "id": app.name,
            "title": f"Dispute Resolution: {emp_name}",
            "subtitle": f"Reason: \"{app.dispute_reason or 'Score Dispute'}\" • Action Required",
            "doctype": "PMS Appraisal",
            "name": app.name,
            "status": "Disputed",
            "badge_class": "badge-rejected",
            "timestamp": app.modified
        })

    for app in pending_appraisal_list:
        emp_name = frappe.db.get_value("Employee", app.employee, "employee_name") if app.employee else "Employee"
        pending_reviews.append({
            "id": app.name,
            "title": f"Final Review: {emp_name}",
            "subtitle": f"Cycle: {app.cycle or 'Current'} • Waiting Sign-off",
            "doctype": "PMS Appraisal",
            "name": app.name,
            "status": "Pending Reviewer",
            "badge_class": "badge-purple",
            "timestamp": app.modified
        })

    for amd in pending_amendments_list:
        emp_name = frappe.db.get_value("Employee", amd.employee, "employee_name") if amd.employee else "Employee"
        pending_reviews.append({
            "id": amd.name,
            "title": f"Reviewer Amendment: {emp_name}",
            "subtitle": f"Plan: {amd.performance_plan or amd.name} • Waiting Sign-off",
            "doctype": "PMS Plan Amendment",
            "name": amd.name,
            "status": "Pending Reviewer",
            "badge_class": "badge-purple",
            "timestamp": amd.modified
        })

    pending_reviews.sort(key=lambda x: str(x["timestamp"]), reverse=True)

    cycles = get_active_appraisal_cycles()

    return {
        "greeting": greeting,
        "user_email": user_doc.email,
        "display_name": display_name,
        "counts": {
            "pending_reviews": total_pending,
            "dept_plans": total_dept_plans,
            "active_cycles": len(cycles),
            "finalized_plans": finalized_plans
        },
        "pending_reviews": pending_reviews[:5],
        "cycles": cycles
    }

@frappe.whitelist()
def get_hr_dashboard_data():
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    
    employee = frappe.db.get_value(
        "Employee", 
        {"user_id": user}, 
        ["name", "employee_name", "first_name"], 
        as_dict=True
    )
    
    if employee:
        display_name = employee.get("first_name") or employee.get("employee_name") or (user_doc.first_name if user_doc else "HR Admin")
    else:
        display_name = (user_doc.first_name if user_doc else None) or "HR Admin"

    now_hour = now_datetime().hour
    greeting_prefix = "Good Morning" if now_hour < 12 else ("Good Afternoon" if now_hour < 17 else "Good Evening")
    greeting = f"{greeting_prefix}, {display_name}"

    # HR Counts
    active_employees = frappe.db.count("Employee", filters={"status": "Active"}) if frappe.db.exists("DocType", "Employee") else 0
    total_appraisals = frappe.db.count("PMS Appraisal")
    active_cycles_count = frappe.db.count("PMS Appraisal Cycle", filters={"status": ["in", ["Draft", "Active", "Monitoring", "Planning Open", "Self-Rating Open"]]})
    
    pending_perc_count = 0
    if frappe.db.exists("DocType", "PERC Case"):
        pending_perc_count = frappe.db.count("PERC Case", filters={"status": ["in", ["Open", "Pending"]]})

    # Active Cycles List
    cycles = get_active_appraisal_cycles()

    # Recent PERC cases
    perc_cases = []
    if frappe.db.exists("DocType", "PERC Case"):
        raw_cases = frappe.db.get_list(
            "PERC Case",
            fields=["name", "raised_by", "status", "creation"],
            order_by="creation desc",
            limit=5
        )
        for pc in raw_cases:
            emp_name = frappe.db.get_value("Employee", pc.raised_by, "employee_name") if pc.get("raised_by") else "Employee"
            perc_cases.append({
                "name": pc.name,
                "title": f"PERC Case: {emp_name}",
                "subtitle": f"Case ID: {pc.name} • Status: {pc.status or 'Open'}",
                "status": pc.status or "Open",
                "badge_class": "badge-rejected" if pc.status == "Open" else "badge-approved"
            })

    return {
        "greeting": greeting,
        "user_email": user_doc.email,
        "display_name": display_name,
        "counts": {
            "active_employees": active_employees,
            "total_appraisals": total_appraisals,
            "active_cycles": active_cycles_count,
            "pending_perc": pending_perc_count
        },
        "cycles": cycles,
        "perc_cases": perc_cases
    }

def get_badge_class(status):
    if not status:
        return "badge-draft"
    status_lower = status.lower()
    if "approved" in status_lower:
        return "badge-approved"
    elif "pending" in status_lower or "in progress" in status_lower:
        return "badge-pending"
    elif "monitoring" in status_lower or "active" in status_lower:
        return "badge-inprogress"
    elif "rejected" in status_lower or "returned" in status_lower:
        return "badge-returned"
    else:
        return "badge-draft"

@frappe.whitelist()
def get_cycle_employees(cycle=None):
    filters = {}
    if cycle:
        filters["cycle"] = cycle

    appraisals = frappe.db.get_all(
        "PMS Appraisal",
        filters=filters,
        fields=["name", "employee", "cycle", "plan_status", "workflow_state", "supervisor_snapshot", "reviewer_snapshot", "modified"],
        order_by="modified desc"
    )

    emp_docs = frappe.db.get_all("Employee", fields=["name", "employee_name", "reports_to", "department", "designation"])
    emp_map = {e.name: e for e in emp_docs}

    result = []
    for app in appraisals:
        emp_id = app.employee
        emp_info = emp_map.get(emp_id, {})
        emp_name = emp_info.get("employee_name") or emp_id or "Unknown Employee"

        sup_id = app.supervisor_snapshot or emp_info.get("reports_to")
        sup_info = emp_map.get(sup_id, {}) if sup_id else {}
        sup_name = sup_info.get("employee_name") or sup_id or "Not Assigned"

        rev_id = app.reviewer_snapshot
        rev_info = emp_map.get(rev_id, {}) if rev_id else {}
        rev_name = rev_info.get("employee_name") or rev_id or "Not Assigned"

        result.append({
            "appraisal_name": app.name,
            "cycle": app.cycle or "General Cycle",
            "employee_id": emp_id,
            "employee_name": emp_name,
            "department": emp_info.get("department") or "N/A",
            "designation": emp_info.get("designation") or "N/A",
            "supervisor_id": sup_id or "",
            "supervisor_name": sup_name,
            "reviewer_id": rev_id or "",
            "reviewer_name": rev_name,
            "plan_status": app.plan_status or "Draft",
            "badge_class": get_badge_class(app.plan_status)
        })

    return result

@frappe.whitelist()
def get_supervisor_2_dashboard_data():
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["name", "employee_name", "first_name"],
        as_dict=True
    )
    if not employee:
        employee = frappe.db.get_value(
            "Employee",
            {"prefered_email": user},
            ["name", "employee_name", "first_name"],
            as_dict=True
        ) or frappe.db.get_value(
            "Employee",
            {"company_email": user},
            ["name", "employee_name", "first_name"],
            as_dict=True
        )

    employee_id = employee.get("name") if employee else None
    display_name = (employee.get("first_name") or employee.get("employee_name") if employee else None) or (user_doc.first_name if user_doc else "Supervisor 2")

    now_hour = now_datetime().hour
    greeting_prefix = "Good Morning" if now_hour < 12 else ("Good Afternoon" if now_hour < 17 else "Good Evening")
    greeting = f"{greeting_prefix}, {display_name}"

    monitored_emps = []
    if employee_id:
        monitored_emps = frappe.db.get_all("Employee", filters={"supervisor_2": employee_id}, pluck="name")

    if employee_id and "System Manager" not in frappe.get_roles() and "Administrator" != user:
        conditions = ["`tabPMS Appraisal`.supervisor_2_snapshot = %(emp)s"]
        params = {"emp": employee_id}
        if monitored_emps:
            conditions.append("`tabPMS Appraisal`.employee IN %(monitored_emps)s")
            params["monitored_emps"] = tuple(monitored_emps)
        where_clause = " OR ".join(conditions)
        appraisals = frappe.db.sql(f"""
            SELECT name, employee, cycle, grade_group, plan_status, workflow_state,
                   supervisor_snapshot, reviewer_snapshot, supervisor_2_snapshot, modified
            FROM `tabPMS Appraisal`
            WHERE ({where_clause})
            ORDER BY modified desc
        """, params, as_dict=True)
    else:
        appraisals = frappe.db.get_all(
            "PMS Appraisal",
            fields=["name", "employee", "cycle", "grade_group", "plan_status", "workflow_state", "supervisor_snapshot", "reviewer_snapshot", "supervisor_2_snapshot", "modified"],
            order_by="modified desc"
        )

    emp_ids = [a.employee for a in appraisals if a.employee]
    emp_map = {}
    if emp_ids:
        emp_docs = frappe.db.get_all("Employee", filters={"name": ["in", list(set(emp_ids))]}, fields=["name", "employee_name", "department", "designation"])
        emp_map = {e.name: e for e in emp_docs}

    monitored_plans = []
    for app in appraisals:
        emp_info = emp_map.get(app.employee, {})
        emp_name = emp_info.get("employee_name") or app.employee or "Unknown Employee"

        monitored_plans.append({
            "name": app.name,
            "employee_id": app.employee,
            "employee_name": emp_name,
            "department": emp_info.get("department") or "N/A",
            "designation": emp_info.get("designation") or "N/A",
            "cycle": app.cycle or "N/A",
            "grade_group": app.grade_group or "N/A",
            "plan_status": app.plan_status or "Draft",
            "workflow_state": app.workflow_state or "Planning Open",
            "badge_class": get_badge_class(app.plan_status),
            "modified": format_datetime(app.modified, "dd MMM yyyy, hh:mm a") if app.modified else ""
        })

    total_monitored_plans = len(monitored_plans)
    unique_monitored_emps = len(set(emp_ids + list(monitored_emps)))
    approved_count = sum(1 for p in monitored_plans if p["plan_status"] == "Approved")
    draft_count = sum(1 for p in monitored_plans if p["plan_status"] == "Draft")

    active_cycle_doc = frappe.db.get_value(
        "PMS Appraisal Cycle",
        {"status": "Active"},
        ["name", "cycle_name", "start_date", "end_date"],
        as_dict=True
    )
    active_cycle_title = (active_cycle_doc.get("cycle_name") or active_cycle_doc.get("name")) if active_cycle_doc else "No Active Cycle"

    return {
        "greeting": greeting,
        "display_name": display_name,
        "counts": {
            "total_monitored": total_monitored_plans,
            "unique_employees": unique_monitored_emps,
            "approved": approved_count,
            "draft": draft_count,
            "active_cycle": active_cycle_title
        },
        "plans": monitored_plans,
        "cycles": get_active_appraisal_cycles()
    }



