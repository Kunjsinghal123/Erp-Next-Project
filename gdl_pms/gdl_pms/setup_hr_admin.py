import frappe

def run():
    frappe.logger().info("Starting HR Admin Setup...")
    
    # 1. Create Role
    role_name = "HR Admin"
    if not frappe.db.exists("Role", role_name):
        doc = frappe.get_doc({
            "doctype": "Role",
            "role_name": role_name,
            "desk_access": 1
        })
        doc.insert(ignore_permissions=True)
        frappe.logger().info(f"Created Role: {role_name}")
    else:
        frappe.logger().info(f"Role {role_name} already exists.")
        
    # 2. Add DocPerms
    doctypes_to_grant = [
        "PMS Appraisal Cycle",
        "PMS Appraisal",
        "PERC Case",
        "Employee"
    ]
    
    # Need to get all DocTypes to check if they are submittable
    for dt_name in doctypes_to_grant:
        if frappe.db.exists("DocType", dt_name):
            dt = frappe.get_doc("DocType", dt_name)
            
            # Check if perm already exists
            if not frappe.db.exists("DocPerm", {"parent": dt_name, "role": role_name}):
                perm = frappe.get_doc({
                    "doctype": "DocPerm",
                    "parent": dt_name,
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": role_name,
                    "permlevel": 0,
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "report": 1,
                    "export": 1,
                    "share": 1,
                    "amend": 1 if dt.is_submittable else 0,
                    "submit": 1 if dt.is_submittable else 0,
                    "cancel": 1 if dt.is_submittable else 0
                })
                perm.insert(ignore_permissions=True)
                frappe.logger().info(f"Granted {role_name} permissions on {dt_name}")
            else:
                frappe.logger().info(f"Permissions for {role_name} on {dt_name} already exist.")
        else:
            frappe.logger().info(f"DocType {dt_name} not found! Skipping permissions.")
            
    # 3. Create User
    user_email = "hr.admin@gdl.bt"
    if not frappe.db.exists("User", user_email):
        user = frappe.get_doc({
            "doctype": "User",
            "email": user_email,
            "first_name": "HR",
            "last_name": "Admin",
            "send_welcome_email": 0,
            "user_type": "System User",
            "roles": [{"role": role_name}]
        })
        user.insert(ignore_permissions=True)
        # Set a default password
        from frappe.utils.password import update_password
        update_password(user=user_email, pwd="admin")
        frappe.logger().info(f"Created user {user_email}")
    else:
        user = frappe.get_doc("User", user_email)
        # Check if role is assigned
        has_role = False
        for r in user.roles:
            if r.role == role_name:
                has_role = True
                break
        if not has_role:
            user.append("roles", {"role": role_name})
            user.save(ignore_permissions=True)
            frappe.logger().info(f"Assigned {role_name} to {user_email}")
        frappe.logger().info(f"User {user_email} already exists.")
        
    frappe.db.commit()
    frappe.logger().info("HR Admin Setup Complete!")
    print("Successfully completed HR Admin setup.")
