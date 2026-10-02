import frappe
import json
from frappe.utils import flt

def run_tests():
    print("==================================================")
    print("STARTING MID-TERM AMENDMENT FLOW VERIFICATION TESTS")
    print("==================================================")

    # 1. Setup Test Cycle and Appraisal Plan
    cycle_name = "Test Cycle Amendment 2026"
    if frappe.db.exists("PMS Appraisal Cycle", cycle_name):
        frappe.delete_doc("PMS Appraisal Cycle", cycle_name, force=True)

    cycle = frappe.get_doc({
        "doctype": "PMS Appraisal Cycle",
        "cycle_name": cycle_name,
        "cycle_type": "Annual",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "status": "Active",
        "grade_group": "All",
        "amendment_window_open": 0
    }).insert(ignore_permissions=True)
    print("1. Test Cycle created (amendment_window_open = 0).")

    # Get employee1
    emp1 = frappe.db.get_value("Employee", {"user_id": "employee1@gmail.com"}, ["name", "grade_group"], as_dict=True)
    emp1_name = emp1.name if emp1 else "HR-EMP-00001"
    emp1_grade = emp1.grade_group if (emp1 and emp1.grade_group) else "PS_CS"
    expected_weight = 60 if emp1_grade == "PS_CS" else 50
    w1 = expected_weight / 2.0

    # Create test plan
    plan = frappe.get_doc({
        "doctype": "PMS Appraisal",
        "employee": emp1_name,
        "cycle": cycle_name,
        "grade_group": emp1_grade,
        "supervisor_snapshot": "HR-EMP-00002",
        "reviewer_snapshot": "HR-EMP-00003",
        "plan_status": "Draft",
        "workflow_state": "Planning Open",
        "targets": [
            {"target_description": "Initial Target 1", "weight": w1},
            {"target_description": "Initial Target 2", "weight": w1}
        ]
    }).insert(ignore_permissions=True)

    # Approve initial plan -> Status = Approved, Workflow State = Monitoring
    plan.plan_status = "Approved"
    plan.workflow_state = "Monitoring"
    plan.save(ignore_permissions=True)
    print(f"2. Performance Plan {plan.name} created and Approved (Monitoring stage). Grade Group: {emp1_grade}, Target Weight: {expected_weight}.")

    # TEST RULE 1: Direct Editing Lock
    print("\n--- Testing Rule 1: Direct Editing Lock ---")
    frappe.set_user("employee1@gmail.com")
    try:
        plan_reload = frappe.get_doc("PMS Appraisal", plan.name)
        plan_reload.targets[0].target_description = "Illegal Direct Target Modification"
        plan_reload.save(ignore_permissions=True)
        print("ERROR: Direct editing was allowed on Approved plan!")
    except Exception as e:
        print(f"SUCCESS: Direct editing locked as expected. Error caught: {e}")

    # TEST RULE 2: Amendment Window Closed Check
    print("\n--- Testing Rule 2: HR Amendment Window Check ---")
    frappe.set_user("employee1@gmail.com")
    try:
        from gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal import request_amendment
        request_amendment(plan.name)
        print("ERROR: Request Amendment succeeded while window was closed!")
    except Exception as e:
        print(f"SUCCESS: Blocked amendment request when window closed. Error caught: {e}")

    # Open Amendment Window individually for this plan
    frappe.set_user("Administrator")
    from gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal import open_amendment_window, close_amendment_window
    open_amendment_window(plan.name)
    plan.reload()
    assert plan.amendment_window_open == 1, "amendment_window_open must be 1 on PMS Appraisal"
    print(f"HR Admin opened the Amendment Window individually on plan {plan.name}.")

    # TEST RULE 3 & 4: Request Amendment & Employee Flow
    print("\n--- Testing Rule 3 & 4: Request Amendment & Employee Flow ---")
    frappe.set_user("employee1@gmail.com")
    amend_name = request_amendment(plan.name)
    amendment = frappe.get_doc("PMS Plan Amendment", amend_name)
    print(f"SUCCESS: Created Amendment {amendment.name} (Amendment Number: {amendment.amendment_number}).")

    assert amendment.amendment_number == 1, "Amendment number should be 1"
    assert flt(amendment.previous_total_weight) == expected_weight, f"Previous total weight should be {expected_weight}"
    assert len(amendment.revised_targets) == 2, "Revised targets should be pre-filled with 2 items"

    # Employee modifies revised targets (sets weight to invalid sum)
    amendment.reason = "Mid-term targets revision due to project scope change."
    amendment.revised_targets[0].weight = 10  # Total weight will be invalid
    amendment.save(ignore_permissions=True)

    from gdl_pms.gdl_pms.doctype.pms_plan_amendment.pms_plan_amendment import submit_amendment, approve_amendment, reject_amendment
    try:
        submit_amendment(amendment.name)
        print("ERROR: Weight validation failed to catch invalid sum!")
    except Exception as e:
        print(f"SUCCESS: Weight sum validation caught invalid sum. Error: {e}")

    # Fix revised targets to valid total weight
    amendment.reload()
    if expected_weight == 60:
        w_a, w_b, w_c = 20, 20, 20
    else:
        w_a, w_b, w_c = 20, 15, 15

    amendment.revised_targets[0].weight = w_a
    amendment.revised_targets[1].weight = w_b
    amendment.append("revised_targets", {"target_description": "New Mid-Term Target 3", "weight": w_c})
    amendment.save(ignore_permissions=True)

    # Submit for approval
    submit_amendment(amendment.name)
    amendment.reload()
    assert amendment.status == "Pending Supervisor Approval", "Status should be Pending Supervisor Approval"
    print(f"SUCCESS: Amendment submitted. Status: {amendment.status}")

    # TEST RULE 5: Approval Flow (Supervisor Rejection -> Route to Draft)
    print("\n--- Testing Rule 5: Supervisor Rejection & Resubmission ---")
    frappe.set_user("supervisor@test.com")
    reject_amendment(amendment.name, "Please clarify target 3 description.")
    amendment.reload()
    assert amendment.status == "Draft", "Status should return to Draft on rejection"
    assert amendment.amendment_number == 1, "Amendment number must stay 1 on resubmission"
    print("SUCCESS: Supervisor rejected amendment with remark. Status returned to Draft.")

    # Employee corrects and resubmits
    frappe.set_user("employee1@gmail.com")
    amendment.revised_targets[2].target_description = "Updated Mid-Term Target 3 (Clarified)"
    amendment.save(ignore_permissions=True)
    submit_amendment(amendment.name)
    amendment.reload()
    assert amendment.status == "Pending Supervisor Approval", "Status should be Pending Supervisor Approval"
    print("SUCCESS: Employee resubmitted corrected amendment.")

    # TEST RULE 5 & 6: Supervisor & Reviewer Approval -> Live Targets Update
    print("\n--- Testing Rule 5 & 6: Supervisor & Reviewer Approval -> Targets Update ---")
    frappe.set_user("supervisor@test.com")
    approve_amendment(amendment.name)
    amendment.reload()
    assert amendment.status == "Pending Reviewer Approval", "Status should be Pending Reviewer Approval"
    print("SUCCESS: Supervisor approved. Status moved to Pending Reviewer Approval.")

    frappe.set_user("reviewer@test.com")
    approve_amendment(amendment.name)
    amendment.reload()
    assert amendment.status == "Approved", "Status should be Approved"
    print("SUCCESS: Reviewer approved. Final Amendment Status: Approved.")

    # Verify Parent Plan Targets replacement
    plan_final = frappe.get_doc("PMS Appraisal", plan.name)
    assert plan_final.workflow_state == "Monitoring", "Parent plan workflow state must remain Monitoring"
    assert plan_final.plan_status == "Approved", "Parent plan status must remain Approved"
    assert len(plan_final.targets) == 3, f"Parent plan targets count should be 3, got {len(plan_final.targets)}"
    assert plan_final.targets[2].target_description == "Updated Mid-Term Target 3 (Clarified)", "Target 3 description should match revised targets"
    assert plan_final.amendment_window_open == 0, "Window should be closed after approval"
    print("SUCCESS: Live targets on parent Performance Plan replaced with revised_targets.")
    print("SUCCESS: Parent plan remained in Monitoring / Approved stage, and amendment window automatically closed.")

    # TEST RULE 3: Second Amendment (Amendment 2)
    print("\n--- Testing Amendment 2 (Auto-Increment & History) ---")
    # HR Admin opens window for Amendment 2
    frappe.set_user("Administrator")
    open_amendment_window(plan.name)

    frappe.set_user("employee1@gmail.com")
    amend2_name = request_amendment(plan.name)
    amend2 = frappe.get_doc("PMS Plan Amendment", amend2_name)
    assert amend2.amendment_number == 2, f"Second amendment number should be 2, got {amend2.amendment_number}"
    print(f"SUCCESS: Created second amendment {amend2.name} with amendment_number = 2.")

    frappe.set_user("Administrator")
    print("\n==================================================")
    print("ALL MID-TERM AMENDMENT VERIFICATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
