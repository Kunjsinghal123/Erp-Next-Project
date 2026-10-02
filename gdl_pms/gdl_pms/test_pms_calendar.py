import frappe
from gdl_pms.gdl_pms.doctype.pms_calendar.pms_calendar import get_permission_query_conditions, has_permission

def test_pms_calendar():
    print("--- Starting PMS Calendar Verification ---")

    # 1. Verify PMS Calendar 2026 doc
    assert frappe.db.exists("PMS Calendar", "2026"), "PMS Calendar 2026 does not exist!"
    cal_2026 = frappe.get_doc("PMS Calendar", "2026")
    print(f"Verified PMS Calendar 2026: Year={cal_2026.calendar_year}, Submission Deadline={cal_2026.employee_submission_deadline}, Supervisor Approval={cal_2026.supervisor_approval_deadline}, Reviewer Approval={cal_2026.reviewer_approval_deadline}")
    assert str(cal_2026.employee_submission_deadline) == "2026-03-31"
    assert str(cal_2026.supervisor_approval_deadline) == "2026-04-15"
    assert str(cal_2026.reviewer_approval_deadline) == "2026-04-30"

    # 2. Verify Date Validation (Negative tests)
    bad_cal = frappe.new_doc("PMS Calendar")
    bad_cal.calendar_year = "2027"
    bad_cal.employee_submission_deadline = "2027-05-01"
    bad_cal.supervisor_approval_deadline = "2027-04-01" # Earlier than employee!
    try:
        bad_cal.validate_dates()
        assert False, "Should have thrown error for submission date after supervisor date"
    except frappe.ValidationError:
        print("Verified validation: Correctly rejected employee deadline after supervisor deadline")

    # 3. Verify PMS Appraisal Cycle calendar year automation
    test_cycle_name = "Test PMS Cycle 2027"
    if frappe.db.exists("PMS Appraisal Cycle", test_cycle_name):
        frappe.delete_doc("PMS Appraisal Cycle", test_cycle_name, force=True)

    cycle = frappe.new_doc("PMS Appraisal Cycle")
    cycle.cycle_name = test_cycle_name
    cycle.calendar_year = "2027"
    cycle.cycle_type = "Annual"
    cycle.grade_group = "All"
    cycle.save(ignore_permissions=True)

    cycle.reload()
    print(f"Verified Appraisal Cycle 2027 dates: Start={cycle.start_date}, End={cycle.end_date}")
    assert str(cycle.start_date) == "2027-01-01", f"Expected start_date 2027-01-01, got {cycle.start_date}"
    assert str(cycle.end_date) == "2027-12-31", f"Expected end_date 2027-12-31, got {cycle.end_date}"
    print("Verified: Selecting calendar year in PMS Appraisal Cycle automatically populates 01-Jan and 31-Dec dates!")

    # Clean up test cycle
    frappe.delete_doc("PMS Appraisal Cycle", test_cycle_name, force=True)

    # 4. Verify Permissions
    # HR Admin user
    hr_cond = get_permission_query_conditions("hr.admin@gdl.bt")
    assert hr_cond == "", f"HR Admin should have full query access, got {hr_cond}"
    assert has_permission(cal_2026, user="hr.admin@gdl.bt") is True, "HR Admin should have permission"
    print("Verified: HR Admin has full access to PMS Calendar")

    # Employee user
    emp_users = frappe.get_all("User", filters={"email": ["like", "emp%@gdl.bt"]}, limit=1)
    if emp_users:
        emp_user = emp_users[0].name
        emp_cond = get_permission_query_conditions(emp_user)
        assert emp_cond == "1=0", f"Employee should get '1=0' query condition, got {emp_cond}"
        assert has_permission(cal_2026, user=emp_user) is False, "Employee must not have access to PMS Calendar"
        print(f"Verified: Employee ({emp_user}) is strictly denied access (1=0 condition, has_permission=False)")

    # Supervisor user
    sup_users = frappe.get_all("User", filters={"email": ["like", "sup%@gdl.bt"]}, limit=1)
    if sup_users:
        sup_user = sup_users[0].name
        sup_cond = get_permission_query_conditions(sup_user)
        assert sup_cond == "1=0", f"Supervisor should get '1=0' query condition, got {sup_cond}"
        assert has_permission(cal_2026, user=sup_user) is False, "Supervisor must not have access to PMS Calendar"
        print(f"Verified: Supervisor ({sup_user}) is strictly denied access")

    # 5. Verify Workspace Sidebar
    sidebar = frappe.get_doc("Workspace Sidebar", "GDL PMS")
    sidebar_items = [i.label for i in sidebar.items]
    assert "PMS Calendar" in sidebar_items, "PMS Calendar not found in Workspace Sidebar items!"
    print(f"Verified: 'PMS Calendar' is present in Workspace Sidebar items: {sidebar_items}")

    print("ALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_pms_calendar()
