import frappe
from gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal import (
    approve_plan, reject_plan, send_for_approval, request_amendment
)
from gdl_pms.dashboard_api import get_supervisor_2_dashboard_data

def run_tests():
    print("=== STARTING SUPERVISOR 2 TEST SUITE ===")

    # 1. Verify custom field
    assert frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "supervisor_2"}), "Custom Field 'supervisor_2' missing on Employee"
    print("[PASS] 1. Custom field 'supervisor_2' exists on Employee")

    # 2. Setup test users and employees
    s2_user_email = "test_s2_monitor@gdltest.com"
    sub_user_email = "test_s2_subordinate@gdltest.com"
    unrelated_user_email = "test_s2_unrelated@gdltest.com"

    for email, fname in [
        (s2_user_email, "S2 Monitor"),
        (sub_user_email, "S2 Subordinate"),
        (unrelated_user_email, "S2 Unrelated")
    ]:
        if not frappe.db.exists("User", email):
            u = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": fname,
                "enabled": 1,
                "send_welcome_email": 0
            })
            u.insert(ignore_permissions=True)

    def get_or_create_emp(email, name):
        emp_name = frappe.db.get_value("Employee", {"user_id": email}, "name")
        if not emp_name:
            company = frappe.db.get_value("Company", {}, "name") or "DrukSmart Private Limited"
            emp = frappe.get_doc({
                "doctype": "Employee",
                "first_name": name,
                "user_id": email,
                "status": "Active",
                "gender": "Male",
                "date_of_birth": "1990-01-01",
                "date_of_joining": "2026-01-01",
                "company": company,
                "grade_group": "OS_ESP"
            })
            emp.insert(ignore_permissions=True)
            emp_name = emp.name
        return emp_name

    s2_emp = get_or_create_emp(s2_user_email, "S2 Monitor")
    sub_emp = get_or_create_emp(sub_user_email, "S2 Subordinate")
    unrelated_emp = get_or_create_emp(unrelated_user_email, "S2 Unrelated")

    # 3. Test Auto Role & User Permission assignment
    sub_doc = frappe.get_doc("Employee", sub_emp)
    sub_doc.supervisor_2 = s2_emp
    sub_doc.save(ignore_permissions=True)
    frappe.db.commit()

    # Verify role was granted to s2_user
    assert frappe.db.exists("Has Role", {"parent": s2_user_email, "role": "Supervisor 2"}), "Role 'Supervisor 2' was not auto-assigned"
    print("[PASS] 2. 'Supervisor 2' role auto-assigned to S2 user")

    # Verify User Permission was granted
    user_perm = frappe.db.exists("User Permission", {
        "user": s2_user_email,
        "allow": "Employee",
        "for_value": sub_emp,
        "applicable_for": "PMS Appraisal"
    })
    assert user_perm, "User Permission scoping PMS Appraisal was not created for S2 user"
    print("[PASS] 3. User Permission for S2 user scoping PMS Appraisal to subordinate created")

    # 4. Test Snapshot field auto-population on PMS Appraisal
    # Get active cycle
    cycle = frappe.db.get_value("PMS Appraisal Cycle", {"status": "Active"}, "name")
    if not cycle:
        cycle = frappe.db.get_value("PMS Appraisal Cycle", {}, "name")

    # Create appraisal for subordinate
    test_plan = frappe.get_doc({
        "doctype": "PMS Appraisal",
        "employee": sub_emp,
        "cycle": cycle,
        "targets": [
            {"target_description": "Target 1", "weight": 25},
            {"target_description": "Target 2", "weight": 25}
        ]
    })
    test_plan.insert(ignore_permissions=True)
    frappe.db.commit()

    assert test_plan.supervisor_2_snapshot == s2_emp, f"supervisor_2_snapshot not auto-populated! Expected {s2_emp}, got {test_plan.supervisor_2_snapshot}"
    print(f"[PASS] 4. supervisor_2_snapshot auto-populated accurately: {test_plan.supervisor_2_snapshot}")

    # Create appraisal for unrelated employee without supervisor_2
    unrelated_plan = frappe.get_doc({
        "doctype": "PMS Appraisal",
        "employee": unrelated_emp,
        "cycle": cycle,
        "targets": [
            {"target_description": "Target 1", "weight": 25},
            {"target_description": "Target 2", "weight": 25}
        ]
    })
    unrelated_plan.insert(ignore_permissions=True)
    frappe.db.commit()

    # 5. Test Permissions & Scoping as S2 user
    frappe.set_user(s2_user_email)

    # Read permission on assigned subordinate plan -> True
    read_perm = frappe.has_permission("PMS Appraisal", "read", test_plan, user=s2_user_email)
    assert read_perm is True, "S2 user cannot read subordinate's plan"
    print("[PASS] 5. S2 user has read permission on monitored plan")

    # Write permission on assigned subordinate plan -> False
    write_perm = frappe.has_permission("PMS Appraisal", "write", test_plan, user=s2_user_email)
    assert write_perm is False, "S2 user unexpectedly has write permission on monitored plan"
    print("[PASS] 6. S2 user has NO write permission (has_permission check returns False)")

    # Read permission on unrelated plan -> False
    unrelated_read = frappe.has_permission("PMS Appraisal", "read", unrelated_plan, user=s2_user_email)
    assert unrelated_read is False, "S2 user unexpectedly has read permission on unrelated plan"
    print("[PASS] 7. S2 user CANNOT read unrelated plan")

    # 6. Test Document-level safety net (saving / editing plan as S2 user)
    blocked_save = False
    try:
        plan_as_s2 = frappe.get_doc("PMS Appraisal", test_plan.name)
        plan_as_s2.targets[0].target_description = "Hacked by S2"
        plan_as_s2.save()
    except frappe.PermissionError as pe:
        blocked_save = True
    except Exception as e:
        if "read-only" in str(e).lower() or "not permitted" in str(e).lower():
            blocked_save = True
        else:
            print(f"Exception on save: {type(e)} {e}")

    assert blocked_save, "Save attempt by S2 user was NOT blocked by document-level safety net!"
    print("[PASS] 8. Document-level write attempt by S2 user blocked by safety net")

    # 7. Test Workflow action blocking for S2 user
    # Send for Approval
    blocked_action = False
    try:
        send_for_approval(test_plan.name)
    except Exception:
        blocked_action = True
    assert blocked_action, "send_for_approval was not blocked for S2 user"
    print("[PASS] 9. send_for_approval blocked for S2 user")

    # Approve Plan
    blocked_action = False
    try:
        approve_plan(test_plan.name)
    except Exception:
        blocked_action = True
    assert blocked_action, "approve_plan was not blocked for S2 user"
    print("[PASS] 10. approve_plan blocked for S2 user")

    # Reject Plan
    blocked_action = False
    try:
        reject_plan(test_plan.name, "Rejected by S2")
    except Exception:
        blocked_action = True
    assert blocked_action, "reject_plan was not blocked for S2 user"
    print("[PASS] 11. reject_plan blocked for S2 user")

    # Request Amendment
    blocked_action = False
    try:
        request_amendment(test_plan.name)
    except Exception:
        blocked_action = True
    assert blocked_action, "request_amendment was not blocked for S2 user"
    print("[PASS] 12. request_amendment blocked for S2 user")

    # 8. Test Dashboard API
    dash_data = get_supervisor_2_dashboard_data()
    assert dash_data["counts"]["total_monitored"] >= 1, "Dashboard API did not return monitored plans"
    plan_names = [p["name"] for p in dash_data["plans"]]
    assert test_plan.name in plan_names, "Assigned plan missing from S2 dashboard data"
    assert unrelated_plan.name not in plan_names, "Unrelated plan leaked into S2 dashboard data"
    print(f"[PASS] 13. Dashboard API returned {len(dash_data['plans'])} monitored plans accurately scoped")

    # Clean up test user session
    frappe.set_user("Administrator")
    print("=== ALL SUPERVISOR 2 TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
