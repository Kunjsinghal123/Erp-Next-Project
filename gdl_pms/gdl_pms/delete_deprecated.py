import frappe

def delete_deprecated():
    doctype_name = "PMS Supervisor Reviewer Mapping"
    
    if frappe.db.exists("DocType", doctype_name):
        frappe.delete_doc("DocType", doctype_name, ignore_missing=True, force=True)
        print(f"Deleted DocType: {doctype_name}")
        
    # Also delete any Workspace shortcuts that might be pointing to it
    shortcuts = frappe.get_all("Workspace Shortcut", filters={"link_to": doctype_name})
    for s in shortcuts:
        # Actually workspace shortcuts are child tables of Workspace, so we need to delete from the Workspace
        ws_name = frappe.db.get_value("Workspace Shortcut", s.name, "parent")
        if ws_name:
            ws = frappe.get_doc("Workspace", ws_name)
            ws.shortcuts = [x for x in ws.shortcuts if x.link_to != doctype_name]
            ws.save(ignore_permissions=True)
            print(f"Removed shortcut from Workspace: {ws_name}")

    frappe.db.commit()

delete_deprecated()
