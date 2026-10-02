import frappe

def inspect_all():
    workspaces = frappe.get_all("Workspace", fields=["name", "title", "module", "public", "for_user"])
    print("--- WORKSPACES ---")
    for ws in workspaces:
        roles = [r.role for r in frappe.get_all("Has Role", filters={"parent": ws.name}, fields=["role"])]
        print(f"WS: {ws.name} | Title: {ws.title} | Module: {ws.module} | Roles: {roles}")
        
def test_verification():
    from frappe.boot import get_bootinfo
    from frappe.website.utils import get_home_page
    from gdl_pms.auth_hooks import boot_session, get_user_pms_info

    test_users = [
        "hr.admin@gdl.bt",
        "priya.patel@gdl.bt",
        "rahul.sharma@gdl.bt",
        "amit.verma@gdl.bt",
        "rajesh.kumar@gdl.bt",
        "Administrator"
    ]

    for u in test_users:
        frappe.set_user(u)
        frappe.cache.hdel("desktop_icons", u)
        boot = get_bootinfo()
        pms_info = get_user_pms_info(u)
        home_page = get_home_page()
        icon_labels = [i.label for i in boot.get("desktop_icons", [])]
        print(f"\nUser: {u} (PMS Info: {pms_info['primary_role'] if pms_info else 'Non-PMS/Admin'})")
        print(f"  get_home_page(): {home_page}")
        print(f"  bootinfo['home_page']: {boot.get('home_page')}")
        print(f"  Desktop Icons ({len(icon_labels)}): {icon_labels}")












