import frappe
import json
from frappe.model.document import Document
from frappe.utils import flt, today, now_datetime

class PMSPlanAmendment(Document):
    def before_insert(self):
        # 1. Auto-increment amendment_number per performance_plan
        if self.performance_plan:
            max_num = frappe.db.sql("""
                SELECT MAX(amendment_number) FROM `tabPMS Plan Amendment`
                WHERE performance_plan = %s
            """, (self.performance_plan,))[0][0]
            self.amendment_number = (max_num or 0) + 1

        self.revision_date = today()

        # 2. Auto-fetch details from parent PMS Appraisal if missing
        if self.performance_plan:
            plan = frappe.get_doc("PMS Appraisal", self.performance_plan)
            self.employee = plan.employee
            self.employee_name = getattr(plan, "employee_name", None) or frappe.db.get_value("Employee", plan.employee, "employee_name")
            self.cycle = plan.cycle
            self.grade_group = plan.grade_group
            self.supervisor_snapshot = plan.supervisor_snapshot
            self.reviewer_snapshot = plan.reviewer_snapshot
            self.supervisor_2_snapshot = getattr(plan, "supervisor_2_snapshot", None)

            # 3. Snapshot current targets into previous_targets
            if not self.previous_targets:
                prev_targets_list = []
                for t in plan.targets:
                    prev_targets_list.append({
                        "target_description": t.target_description,
                        "weight": flt(t.weight)
                    })
                self.previous_targets = json.dumps(prev_targets_list, indent=2)

            # 4. Pre-fill revised_targets if empty
            if not self.revised_targets:
                for t in plan.targets:
                    self.append("revised_targets", {
                        "target_description": t.target_description,
                        "weight": flt(t.weight)
                    })

    def validate(self):
        if self.employee and not getattr(self, "employee_name", None):
            self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")

        # Compute weight totals
        if self.previous_targets:
            try:
                prev_list = json.loads(self.previous_targets)
                self.previous_total_weight = sum(flt(t.get("weight", 0)) for t in prev_list)
            except Exception:
                self.previous_total_weight = 0
        else:
            self.previous_total_weight = 0

        self.revised_total_weight = sum(flt(t.weight) for t in self.revised_targets)


@frappe.whitelist()
def submit_amendment(docname):
    doc = frappe.get_doc("PMS Plan Amendment", docname)
    
    if doc.status not in ["Draft", "Rejected", "Returned"]:
        frappe.throw("Only Draft or Returned amendments can be submitted for approval.")

    if not doc.reason or not doc.reason.strip():
        frappe.throw("Reason for Amendment is mandatory before submission.")

    # Check amendment window open on performance plan
    plan_window_open = frappe.db.get_value("PMS Appraisal", doc.performance_plan, "amendment_window_open")
    is_hr = any(r in frappe.get_roles() for r in ["Administrator", "System Manager", "HR Admin"])
    if not plan_window_open and not is_hr:
        frappe.throw("The Amendment Window for this Performance Plan is currently closed by HR Admin.")

    # Validate weight sum against grade group
    expected_weight = 60 if doc.grade_group == "PS_CS" else 50
    total_weight = sum(flt(t.weight) for t in doc.revised_targets)
    if flt(total_weight, 2) != flt(expected_weight, 2):
        frappe.throw(f"Total weight of revised targets must equal {expected_weight}. Current sum is {flt(total_weight, 2)}.")

    # Validate user is the employee or System Manager
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if doc.employee != user_emp and "System Manager" not in frappe.get_roles():
        frappe.throw("Only the assigned Employee can submit this amendment request.")

    doc.status = "Pending Supervisor Approval"
    doc.append("approval_history", {
        "action": "Submitted for Approval",
        "user": frappe.session.user,
        "role": "Employee",
        "timestamp": now_datetime(),
        "status": "Pending Supervisor Approval",
        "remark": doc.reason
    })
    doc.save(ignore_permissions=True)
    return "Amendment submitted for Supervisor Approval"


@frappe.whitelist()
def approve_amendment(docname):
    doc = frappe.get_doc("PMS Plan Amendment", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_sys_mgr = "System Manager" in frappe.get_roles()

    if doc.status == "Pending Supervisor Approval":
        if doc.supervisor_snapshot != user_emp and not is_sys_mgr:
            frappe.throw("Only the assigned Supervisor can approve this amendment.")
            
        doc.append("approval_history", {
            "action": "Approved by Supervisor",
            "user": frappe.session.user,
            "role": "Supervisor",
            "timestamp": now_datetime(),
            "status": "Approved" if not doc.reviewer_snapshot else "Pending Reviewer Approval",
            "remark": doc.supervisor_remark or "Approved"
        })

        if doc.reviewer_snapshot:
            doc.status = "Pending Reviewer Approval"
        else:
            doc.status = "Approved"
            apply_amendment_to_plan(doc)

    elif doc.status == "Pending Reviewer Approval":
        if doc.reviewer_snapshot != user_emp and not is_sys_mgr:
            frappe.throw("Only the assigned Reviewer can approve this amendment.")

        doc.status = "Approved"
        doc.append("approval_history", {
            "action": "Approved by Reviewer",
            "user": frappe.session.user,
            "role": "Reviewer",
            "timestamp": now_datetime(),
            "status": "Approved",
            "remark": doc.reviewer_remark or "Approved"
        })
        apply_amendment_to_plan(doc)
    else:
        frappe.throw("This amendment is not pending your approval.")

    doc.save(ignore_permissions=True)
    return f"Amendment {doc.status}"


@frappe.whitelist()
def reject_amendment(docname, remark):
    if not remark or not remark.strip():
        frappe.throw("Return remark is mandatory.")

    doc = frappe.get_doc("PMS Plan Amendment", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_sys_mgr = "System Manager" in frappe.get_roles()

    if doc.status == "Pending Supervisor Approval":
        if doc.supervisor_snapshot != user_emp and not is_sys_mgr:
            frappe.throw("Only the assigned Supervisor can return this amendment.")
        doc.supervisor_remark = remark
        role_label = "Supervisor"
    elif doc.status == "Pending Reviewer Approval":
        if doc.reviewer_snapshot != user_emp and not is_sys_mgr:
            frappe.throw("Only the assigned Reviewer can return this amendment.")
        doc.reviewer_remark = remark
        role_label = "Reviewer"
    else:
        frappe.throw("This amendment is not pending your approval.")

    doc.status = "Draft"
    doc.append("approval_history", {
        "action": f"Returned by {role_label}",
        "user": frappe.session.user,
        "role": role_label,
        "timestamp": now_datetime(),
        "status": "Draft",
        "remark": remark
    })
    doc.save(ignore_permissions=True)
    return "Amendment Returned and routed back to Employee (Draft)"


@frappe.whitelist()
def return_amendment(docname, remark):
    return reject_amendment(docname, remark)


def apply_amendment_to_plan(doc):
    """
    On final approval of an amendment:
    Replace live targets on parent PMS Appraisal with revised_targets.
    Keep workflow_state = 'Monitoring' and plan_status = 'Approved'.
    """
    plan = frappe.get_doc("PMS Appraisal", doc.performance_plan)
    plan._allow_target_update = True
    plan.targets = []
    for t in doc.revised_targets:
        plan.append("targets", {
            "target_description": t.target_description,
            "weight": flt(t.weight),
            "remark": getattr(t, "remark", None)
        })
    # Ensure parent stays in Monitoring and Approved state, and close the amendment window
    plan.plan_status = "Approved"
    plan.workflow_state = "Monitoring"
    plan.amendment_window_open = 0
    plan.add_comment(
        "Comment",
        f"Plan Amendment #{doc.amendment_number} ({doc.name}) applied. Revision Date: {doc.revision_date}. Reason: \"{doc.reason}\"."
    )
    plan.save(ignore_permissions=True)
    frappe.logger().info(f"Successfully applied Amendment {doc.name} targets to Performance Plan {plan.name}")


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    if user == "Administrator" or "System Manager" in frappe.get_roles(user) or "HR Manager" in frappe.get_roles(user) or "HR Admin" in frappe.get_roles(user):
        return ""

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        return "1=2"

    return f"""(`tabPMS Plan Amendment`.employee = '{employee}' or `tabPMS Plan Amendment`.supervisor_snapshot = '{employee}' or `tabPMS Plan Amendment`.reviewer_snapshot = '{employee}' or `tabPMS Plan Amendment`.supervisor_2_snapshot = '{employee}' or `tabPMS Plan Amendment`.employee in (select name from `tabEmployee` where supervisor_2 = '{employee}'))"""


def has_permission(doc, ptype="read", user=None):
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)
    if user == "Administrator" or "System Manager" in roles or "HR Manager" in roles or "HR Admin" in roles:
        return True

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        return False

    is_supervisor_2 = (getattr(doc, "supervisor_2_snapshot", None) == employee or frappe.db.get_value("Employee", doc.employee, "supervisor_2") == employee)
    is_primary_party = (doc.employee == employee or doc.supervisor_snapshot == employee or doc.reviewer_snapshot == employee)

    if ptype == "read":
        if is_primary_party or is_supervisor_2:
            return True
        return False
    else:
        if is_supervisor_2 and not is_primary_party:
            return False
        if is_primary_party:
            return True
        return False
