import frappe

def test_search():
    frappe.set_user("employee1@gmail.com")
    try:
        res = frappe.desk.search.search_link("Employee", "", "PMS Appraisal", "employee")
        print(f"Search Link Result: {res}")
    except Exception as e:
        print(f"Error: {e}")
