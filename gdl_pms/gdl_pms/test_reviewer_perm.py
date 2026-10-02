import frappe

def test():
    user = "reviewer2@test.com"
    docname = "PMS-2026-09-00008"
    
    frappe.set_user(user)
    doc = frappe.get_doc("PMS Appraisal", docname)
    
    print(f"User: {user}")
    print(f"Doc Employee: {doc.employee}")
    print(f"Doc Supervisor: {doc.supervisor_snapshot}")
    print(f"Doc Reviewer: {doc.reviewer_snapshot}")
    print(f"User Roles: {frappe.get_roles(user)}")
    
    has_perm = frappe.has_permission("PMS Appraisal", "read", doc, user=user)
    print(f"has_permission result: {has_perm}")
    
    # Check user permissions for user
    user_perms = frappe.get_all("User Permission", filters={"user": user}, fields=["allow", "for_value", "applicable_for"])
    print(f"User Permissions: {user_perms}")

if __name__ == "__main__":
    test()
