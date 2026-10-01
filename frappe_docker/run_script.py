import sys, os
sys.path.insert(0, '/workspace/development/frappe-bench/apps/frappe')
import frappe
frappe.init(site="gdl.bt")
frappe.connect()
import create_supervisor_user
create_supervisor_user.execute()
