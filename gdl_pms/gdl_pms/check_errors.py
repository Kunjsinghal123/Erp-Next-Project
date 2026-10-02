import frappe

def run():
    errors = frappe.get_all("Error Log", fields=["method", "error"], limit_page_length=3, order_by="creation desc")
    for e in errors:
        print(f"ERROR: {e.method}")
        print(e.error)
        print("-" * 50)
