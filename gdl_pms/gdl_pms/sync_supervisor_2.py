import frappe

def sync_existing():
    # 1. Update tabPMS Appraisal where employee has supervisor_2 set on Employee
    updated_appraisals = frappe.db.sql("""
        UPDATE `tabPMS Appraisal` a
        INNER JOIN `tabEmployee` e ON a.employee = e.name
        SET a.supervisor_2_snapshot = e.supervisor_2
        WHERE e.supervisor_2 IS NOT NULL 
          AND e.supervisor_2 != ''
          AND (a.supervisor_2_snapshot IS NULL OR a.supervisor_2_snapshot = '' OR a.supervisor_2_snapshot != e.supervisor_2)
    """)
    print(f"Synced supervisor_2_snapshot on existing PMS Appraisals")

    # 2. Update tabPMS Plan Amendment
    updated_amendments = frappe.db.sql("""
        UPDATE `tabPMS Plan Amendment` a
        INNER JOIN `tabEmployee` e ON a.employee = e.name
        SET a.supervisor_2_snapshot = e.supervisor_2
        WHERE e.supervisor_2 IS NOT NULL 
          AND e.supervisor_2 != ''
          AND (a.supervisor_2_snapshot IS NULL OR a.supervisor_2_snapshot = '' OR a.supervisor_2_snapshot != e.supervisor_2)
    """)
    print(f"Synced supervisor_2_snapshot on existing PMS Plan Amendments")

    frappe.db.commit()
    print("Sync complete.")

if __name__ == "__main__":
    sync_existing()
