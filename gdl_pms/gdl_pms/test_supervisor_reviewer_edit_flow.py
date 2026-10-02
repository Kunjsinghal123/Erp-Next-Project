import frappe
from frappe.utils import flt
from gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal import (
    send_for_approval,
    approve_plan,
    reject_plan,
    return_to_employee_with_edits,
)

def run_tests():
    print("================================================================")
    print("STARTING SUPERVISOR & REVIEWER EDIT AND RETURN FLOW TESTS")
    print("================================================================")

    frappe.set_user("Administrator")

    # 1. Setup Active Cycle
    cycle_name = "Test Cycle Edit Flow 2026"
    if frappe.db.exists("PMS Appraisal Cycle", cycle_name):
        frappe.delete_doc("PMS Appraisal Cycle", cycle_name, force=True)

    cycle = frappe.get_doc({
        "doctype": "PMS Appraisal Cycle",
        "cycle_name": cycle_name,
        "cycle_type": "Annual",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "status": "Active",
        "grade_group": "All"
    }).insert(ignore_permissions=True)
    print("1. Active Appraisal Cycle created.")

    # 2. Setup Employees
    emp_user = "dechen.peldon@gdl.bt"
    sup_user = "karma.wangchuk@gdl.bt"
    rev_user = "sonam.tobgay@gdl.bt"

    emp_name = frappe.db.get_value("Employee", {"user_id": emp_user}, "name")
    sup_name = frappe.db.get_value("Employee", {"user_id": sup_user}, "name")
    rev_name = frappe.db.get_value("Employee", {"user_id": rev_user}, "name")

    assert emp_name, f"Employee for {emp_user} not found"
    assert sup_name, f"Employee for {sup_user} not found"
    assert rev_name, f"Employee for {rev_user} not found"

    # Clean up old test appraisals for this employee in this cycle
    old_plans = frappe.get_all("PMS Appraisal", filters={"employee": emp_name, "cycle": cycle_name}, pluck="name")
    for op in old_plans:
        frappe.delete_doc("PMS Appraisal", op, force=True)

    # 3. Create Draft Plan as Employee
    frappe.set_user(emp_user)
    plan = frappe.get_doc({
        "doctype": "PMS Appraisal",
        "employee": emp_name,
        "cycle": cycle_name,
        "grade_group": "OS_ESP",
        "supervisor_snapshot": sup_name,
        "reviewer_snapshot": rev_name,
        "plan_status": "Draft",
        "workflow_state": "Planning Open",
        "targets": [
            {"target_description": "Initial Task 1", "weight": 25.0, "remark": "Initial target"},
            {"target_description": "Initial Task 2", "weight": 25.0}
        ]
    }).insert(ignore_permissions=True)
    print(f"2. Plan {plan.name} created as Draft. Total weight = 50.")

    # 4. Employee sends for approval
    send_for_approval(plan.name)
    plan.reload()
    assert plan.plan_status == "Pending Supervisor Approval", f"Expected Pending Supervisor Approval, got {plan.plan_status}"
    print("3. Plan successfully sent for Supervisor Approval.")

    # 5. Supervisor edits the tasks (adds Task 3, updates weights, adds remarks)
    frappe.set_user(sup_user)
    plan_sup = frappe.get_doc("PMS Appraisal", plan.name)
    plan_sup.targets[0].weight = 20.0
    plan_sup.targets[1].weight = 20.0
    plan_sup.append("targets", {
        "target_description": "Task 3 (Added by Supervisor)",
        "weight": 10.0,
        "remark": "Priority project for department"
    })
    plan_sup.plan_revision_remark = "Added Task 3 and re-balanced weights to 20/20/10."
    plan_sup.save()
    print("4. Supervisor saved edits to targets and weights.")

    # 6. Verify plan automatically reverted to Draft for Employee analysis
    plan.reload()
    assert plan.plan_status == "Draft", f"Expected Draft after Supervisor edit, got {plan.plan_status}"
    assert plan.revised_by_role == "Supervisor", f"Expected revised_by_role = Supervisor, got {plan.revised_by_role}"
    assert len(plan.targets) == 3, f"Expected 3 targets, got {len(plan.targets)}"
    assert flt(sum(t.weight for t in plan.targets)) == 50.0, "Target weights must sum to 50"
    print("5. SUCCESS: Plan automatically returned to Draft status with revised_by_role='Supervisor'!")

    # Verify timeline comment exists
    comments = frappe.get_all("Comment", filters={"reference_doctype": "PMS Appraisal", "reference_name": plan.name}, pluck="content")
    assert any("modified by Supervisor" in c for c in comments), "Comment for supervisor revision not found"
    print("6. SUCCESS: Timeline comment logged.")

    # 7. Employee reviews changes and re-submits for approval
    frappe.set_user(emp_user)
    send_for_approval(plan.name)
    plan.reload()
    assert plan.plan_status == "Pending Supervisor Approval", f"Expected Pending Supervisor Approval, got {plan.plan_status}"
    assert plan.plan_revision_remark is None, "Expected plan_revision_remark to be cleared on resubmit"
    print("7. SUCCESS: Employee analyzed changes and successfully re-submitted for approval.")

    # 8. Supervisor approves without edits
    frappe.set_user(sup_user)
    approve_plan(plan.name)
    plan.reload()
    assert plan.plan_status == "Pending Reviewer Approval", f"Expected Pending Reviewer Approval, got {plan.plan_status}"
    print("8. SUCCESS: Supervisor approved plan -> moved to Pending Reviewer Approval.")

    # 9. Reviewer edits the tasks using return_to_employee_with_edits
    frappe.set_user(rev_user)
    plan_rev = frappe.get_doc("PMS Appraisal", plan.name)
    # Reviewer modifies weightage: 20 -> 15 on Task 1, 10 -> 15 on Task 3
    plan_rev.targets[0].weight = 15.0
    plan_rev.targets[2].weight = 15.0
    plan_rev.targets[2].remark = "Increased weight from 10 to 15 per review"
    plan_rev.save()

    plan.reload()
    assert plan.plan_status == "Draft", f"Expected Draft after Reviewer edit, got {plan.plan_status}"
    assert plan.revised_by_role == "Reviewer", f"Expected revised_by_role = Reviewer, got {plan.revised_by_role}"
    print("9. SUCCESS: Reviewer edit automatically returned plan to Draft for Employee analysis!")

    # 10. Employee re-submits
    frappe.set_user(emp_user)
    send_for_approval(plan.name)
    plan.reload()
    assert plan.plan_status == "Pending Supervisor Approval"

    # 11. Supervisor approves
    frappe.set_user(sup_user)
    approve_plan(plan.name)
    plan.reload()
    assert plan.plan_status == "Pending Reviewer Approval"

    # 12. Reviewer approves
    frappe.set_user(rev_user)
    approve_plan(plan.name)
    plan.reload()
    assert plan.plan_status == "Approved", f"Expected Approved, got {plan.plan_status}"
    assert plan.workflow_state == "Monitoring", f"Expected Monitoring, got {plan.workflow_state}"
    print("10. SUCCESS: Plan approved through full chain and is in Monitoring stage!")

    print("\n================================================================")
    print("ALL SUPERVISOR & REVIEWER EDIT AND RETURN FLOW TESTS PASSED!")
    print("================================================================")
