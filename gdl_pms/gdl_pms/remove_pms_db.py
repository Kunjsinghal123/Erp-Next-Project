import frappe
import json

def run():
    installed_apps = frappe.db.get_global("installed_apps")
    if installed_apps:
        try:
            apps_list = json.loads(installed_apps)
            if "pms" in apps_list:
                apps_list.remove("pms")
                frappe.db.set_global("installed_apps", json.dumps(apps_list))
                frappe.db.commit()
                print("Removed pms from DB")
            else:
                print("pms not in DB list:", apps_list)
        except Exception as e:
            print("Error parsing installed_apps:", e)
    else:
        print("installed_apps not found in DB")
