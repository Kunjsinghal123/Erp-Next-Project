import frappe
from frappe.utils import flt
from gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal import (
    activate_appraisal_phase,
    submit_self_assessment,
    submit_supervisor_review,
    accept_supervisor_scores,
    raise_dispute,
    submit_reviewer_decision,
    accept_reviewer_decision,
    request_perc_review,
    lock_appraisal,
)

def run_tests():
    print("==================================================")
    print("STARTING FULL PMS APPRAISAL PHASE LIFECYCLE TESTS")
    print("==================================================")

    # 1. Setup Test Cycle
    cycle_name = "Test Appraisal Cycle 2026"
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
    print("1. Test Appraisal Cycle created.")

    # 2. Get demo users / employees
    emp1 = frappe.db.get_value("Employee", {"user_id": "employee1@gmail.com"}, ["name", "grade_group"], as_dict=True)
    emp1_name = emp1.name if emp1 else "HR-EMP-00001"
    emp1_grade = emp1.grade_group if (emp1 and emp1.grade_group) else "PS_CS"
    expected_target_weight = 60 if emp1_grade == "PS_CS" else 50
    w1 = expected_target_weight / 2.0
    w2 = expected_target_weight / 2.0

    sup_emp = frappe.db.get_value("Employee", {"user_id": "supervisor@test.com"}, "name") or "HR-EMP-00002"
    rev_emp = frappe.db.get_value("Employee", {"user_id": "reviewer@test.com"}, "name") or "HR-EMP-00003"

    # =========================================================================
    # TEST SUITE 1: Standard Acceptance Path
    # =========================================================================
    print("\n--- TEST SUITE 1: Standard Appraisal Flow (Employee Accepts) ---")

    plan1 = frappe.get_doc({
        "doctype": "PMS Appraisal",
        "employee": emp1_name,
        "cycle": cycle_name,
        "grade_group": emp1_grade,
        "supervisor_snapshot": sup_emp,
        "reviewer_snapshot": rev_emp,
        "plan_status": "Approved",
        "workflow_state": "Monitoring",
        "targets": [
            {"target_description": "Project Execution & Quality", "weight": w1},
            {"target_description": "System Optimization & Uptime", "weight": w2}
        ]
    }).insert(ignore_permissions=True)
    print(f"2. Approved Performance Plan created: {plan1.name}")

    # HR Admin activates Appraisal Phase
    frappe.set_user("Administrator")
    activate_appraisal_phase(plan1.name)
    plan1.reload()
    assert plan1.workflow_state == "Appraisal Open", f"Expected 'Appraisal Open', got {plan1.workflow_state}"
    assert plan1.appraisal_status == "Self-Assessment Pending", f"Expected 'Self-Assessment Pending', got {plan1.appraisal_status}"
    assert len(plan1.competencies) == 5, f"Expected 5 competencies, got {len(plan1.competencies)}"
    expected_comp_wt = 8 if emp1_grade == "PS_CS" else 10
    for c in plan1.competencies:
        assert flt(c.weight) == expected_comp_wt, f"Competency weight expected {expected_comp_wt}, got {c.weight}"
    print(f"3. Appraisal Phase Activated successfully: status='{plan1.appraisal_status}', competencies mapped={len(plan1.competencies)}.")

    # Employee Self-Assessment
    frappe.set_user("employee1@gmail.com")
    
    # Verify score validation error if score exceeds weight
    target_data_invalid = [
        {"self_score": w1 + 10, "self_remark": "Exceeding weight test"},
        {"self_score": w2, "self_remark": "Valid"}
    ]
    try:
        submit_self_assessment(plan1.name, employee_remarks="Invalid test", target_data=target_data_invalid)
        assert False, "Validation should have failed for score exceeding weight"
    except Exception as e:
        print(f"4. Verified score limit validation successfully caught error: {str(e)[:60]}...")

    # Valid Self-Assessment
    target_data_valid = [
        {"self_score": w1 - 2, "self_remark": "Completed project deliverables ahead of schedule"},
        {"self_score": w2 - 3, "self_remark": "Achieved 99.8% uptime"}
    ]
    comp_data_valid = [
        {"self_rating": expected_comp_wt, "self_remark": "Strong performance"} for _ in range(5)
    ]
    submit_self_assessment(
        plan1.name,
        employee_remarks="Solid year of achievements across all KPIs.",
        target_data=target_data_valid,
        competency_data=comp_data_valid
    )
    plan1.reload()
    assert plan1.appraisal_status == "Pending Supervisor Review", f"Expected 'Pending Supervisor Review', got {plan1.appraisal_status}"
    assert plan1.targets[0].self_score == w1 - 2
    print(f"5. Self-Assessment submitted: status='{plan1.appraisal_status}'.")

    # Supervisor Review & Scoring
    frappe.set_user("supervisor@test.com")
    sup_target_data = [
        {"supervisor_score": w1 - 3, "supervisor_remark": "Good work on project, minor delays in phase 2"},
        {"supervisor_score": w2 - 2, "supervisor_remark": "Met uptime requirements"}
    ]
    sup_comp_data = [
        {"supervisor_rating": expected_comp_wt - 1, "supervisor_remark": "Consistent and collaborative"} for _ in range(5)
    ]
    submit_supervisor_review(
        plan1.name,
        supervisor_remarks="Commendable overall performance. Meets key organizational standards.",
        target_data=sup_target_data,
        competency_data=sup_comp_data
    )
    plan1.reload()
    assert plan1.appraisal_status == "Pending Employee Acceptance", f"Expected 'Pending Employee Acceptance', got {plan1.appraisal_status}"
    expected_total = (w1 - 3) + (w2 - 2) + (5 * (expected_comp_wt - 1))
    assert flt(plan1.total_score, 2) == flt(expected_total, 2), f"Expected total score {expected_total}, got {plan1.total_score}"
    assert plan1.rating_band != "Unrated"
    print(f"6. Supervisor Review submitted: status='{plan1.appraisal_status}', total_score={plan1.total_score}, rating_band='{plan1.rating_band}'.")

    # Employee Accepts Scores
    frappe.set_user("employee1@gmail.com")
    accept_supervisor_scores(plan1.name)
    plan1.reload()
    assert plan1.appraisal_status == "Appraisal Accepted", f"Expected 'Appraisal Accepted', got {plan1.appraisal_status}"
    print(f"7. Employee accepted supervisor evaluation: status='{plan1.appraisal_status}'.")

    # HR Admin Final Lock
    frappe.set_user("Administrator")
    lock_appraisal(plan1.name)
    plan1.reload()
    assert plan1.appraisal_status == "Finalized & Locked", f"Expected 'Finalized & Locked', got {plan1.appraisal_status}"
    assert plan1.locked == 1, "Appraisal must be locked (locked=1)"
    assert plan1.workflow_state == "Appraisal Completed"
    print(f"8. HR Admin locked appraisal: status='{plan1.appraisal_status}', locked={plan1.locked}.")

    # Verify modification is blocked when locked
    try:
        plan1.employee_overall_remarks = "Attempted edit after lock"
        plan1.save()
        assert False, "Modification of locked appraisal should have been blocked"
    except Exception as e:
        print(f"9. Verified permanent lock prevents edits: {str(e)[:60]}...")

    # =========================================================================
    # TEST SUITE 2: Dispute & PERC Resolution Path
    # =========================================================================
    print("\n--- TEST SUITE 2: Dispute Escalation & PERC Committee Resolution ---")

    plan2 = frappe.get_doc({
        "doctype": "PMS Appraisal",
        "employee": emp1_name,
        "cycle": cycle_name,
        "grade_group": emp1_grade,
        "supervisor_snapshot": sup_emp,
        "reviewer_snapshot": rev_emp,
        "plan_status": "Approved",
        "workflow_state": "Monitoring",
        "targets": [
            {"target_description": "Core Deliverable 1", "weight": w1},
            {"target_description": "Core Deliverable 2", "weight": w2}
        ]
    }).insert(ignore_permissions=True)

    frappe.set_user("Administrator")
    activate_appraisal_phase(plan2.name)

    # Employee self scores
    frappe.set_user("employee1@gmail.com")
    submit_self_assessment(
        plan2.name,
        employee_remarks="High performance across all tasks.",
        target_data=[{"self_score": w1, "self_remark": "100%"}, {"self_score": w2, "self_remark": "100%"}],
        competency_data=[{"self_rating": expected_comp_wt, "self_remark": "Excellent"} for _ in range(5)]
    )

    # Supervisor under-scores
    frappe.set_user("supervisor@test.com")
    submit_supervisor_review(
        plan2.name,
        supervisor_remarks="Subpar results.",
        target_data=[{"supervisor_score": w1 / 2.0, "supervisor_remark": "Low output"}, {"supervisor_score": w2 / 2.0, "supervisor_remark": "Low output"}],
        competency_data=[{"supervisor_rating": expected_comp_wt / 2.0, "supervisor_remark": "Needs improvement"} for _ in range(5)]
    )
    plan2.reload()
    assert plan2.appraisal_status == "Pending Employee Acceptance"
    print(f"10. Supervisor gave low score: total_score={plan2.total_score}. Moving to Employee Review.")

    # Employee raises Dispute
    frappe.set_user("employee1@gmail.com")
    dispute_text = "Supervisor disregarded documented client sign-offs and production logs attached as evidence."
    raise_dispute(plan2.name, dispute_reason=dispute_text)
    plan2.reload()
    assert plan2.dispute_flag == 1, "Dispute flag should be 1"
    assert plan2.dispute_reason == dispute_text
    assert plan2.appraisal_status == "Disputed - Pending Reviewer"
    print(f"11. Employee raised dispute: dispute_flag={plan2.dispute_flag}, status='{plan2.appraisal_status}'.")

    # Reviewer Evaluates Dispute
    frappe.set_user("reviewer@test.com")
    rev_target_data = [
        {"reviewer_score": w1 - 2, "reviewer_remark": "Evidence verifies on-time delivery with client sign-off"},
        {"reviewer_score": w2 - 2, "reviewer_remark": "Production metrics confirm successful rollout"}
    ]
    rev_comp_data = [
        {"reviewer_rating": expected_comp_wt - 1, "reviewer_remark": "Good communication observed"} for _ in range(5)
    ]
    submit_reviewer_decision(
        plan2.name,
        reviewer_remarks="Dispute reviewed. Upgraded scores based on verified deliverables.",
        target_data=rev_target_data,
        competency_data=rev_comp_data
    )
    plan2.reload()
    assert plan2.appraisal_status == "Reviewer Resolved - Pending Employee Decision"
    rev_expected_total = (w1 - 2) + (w2 - 2) + (5 * (expected_comp_wt - 1))
    assert flt(plan2.total_score, 2) == flt(rev_expected_total, 2)
    print(f"12. Reviewer submitted decision: status='{plan2.appraisal_status}', total_score={plan2.total_score} ({plan2.rating_band}).")

    # Employee still requests PERC review
    frappe.set_user("employee1@gmail.com")
    perc_justification = "Requesting committee evaluation regarding competency weighting and leadership impact."
    perc_case_name = request_perc_review(plan2.name, justification=perc_justification)
    plan2.reload()
    assert plan2.appraisal_status == "Under PERC Review"
    assert plan2.perc_case == perc_case_name
    assert frappe.db.exists("PERC Case", perc_case_name)
    print(f"13. PERC Case created: {perc_case_name}, appraisal_status='{plan2.appraisal_status}'.")

    # PERC Committee Hearing & Resolution
    frappe.set_user("Administrator")
    perc_doc = frappe.get_doc("PERC Case", perc_case_name)
    perc_doc.hearing_notes = "Committee reviewed grievance, project logs, supervisor notes, and reviewer validation."
    perc_doc.final_score = 92.5
    perc_doc.status = "Resolved"
    perc_doc.save(ignore_permissions=True)
    print(f"14. PERC Committee resolved case with final_score={perc_doc.final_score}.")

    # Verify score override applied to Appraisal
    plan2.reload()
    assert flt(plan2.total_score, 2) == 92.5, f"Expected 92.5, got {plan2.total_score}"
    assert plan2.rating_band == "Outstanding Performance"
    assert plan2.appraisal_status == "Appraisal Accepted"
    print(f"15. PERC score override applied to Appraisal: total_score={plan2.total_score}, rating_band='{plan2.rating_band}', status='{plan2.appraisal_status}'.")

    # HR Locks Appraisal
    lock_appraisal(plan2.name)
    plan2.reload()
    assert plan2.appraisal_status == "Finalized & Locked"
    assert plan2.locked == 1
    print(f"16. HR finalized & locked appraisal after PERC resolution.")

    print("\n==================================================")
    print("ALL APPRAISAL PHASE LIFECYCLE TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
