import frappe

PMS_ROLE_ROUTES = [
    ("HR Admin", "desk/pms-hr", "PMS HR"),
    ("Reviewer", "desk/pms-reviewer", "PMS Reviewer"),
    ("Supervisor 2", "desk/pms-supervisor-2", "PMS Supervisor 2"),
    ("Supervisor", "desk/pms-supervisor", "PMS Supervisor"),
    ("Employee", "desk/pms-employee", "PMS Employee"),
]

PMS_ALLOWED_WORKSPACES = {
    "HR Admin": ["PMS HR"],
    "Reviewer": ["PMS Reviewer", "PMS Employee"],
    "Supervisor 2": ["PMS Supervisor 2", "PMS Employee"],
    "Supervisor": ["PMS Supervisor", "PMS Employee"],
    "Employee": ["PMS Employee"],
}

def get_user_pms_info(user=None):
    if not user:
        user = frappe.session.user
    if not user or user in ("Guest", "Administrator"):
        return None

    roles = set(frappe.get_roles(user))
    
    # Do not restrict System Managers or Administrators
    if "System Manager" in roles or "Administrator" in roles:
        return None

    for role, route, ws_name in PMS_ROLE_ROUTES:
        if role in roles:
            return {
                "primary_role": role,
                "route": route,
                "slug": route.replace("desk/", "").replace("app/", ""),
                "workspace": ws_name,
                "roles": roles
            }
    return None

def on_session_creation(login_manager):
    """
    Sets redirect_after_login cache so frappe.auth.LoginManager directly
    redirects the user to their PMS workspace/dashboard after login.
    """
    try:
        user = login_manager.user
        info = get_user_pms_info(user)
        if info and info.get("route"):
            redirect_url = "/" + info["route"].lstrip("/")
            frappe.cache.hset("redirect_after_login", user, redirect_url)
            frappe.logger().info(f"[GDL PMS] Set login redirect for {user} -> {redirect_url}")
    except Exception as e:
        frappe.log_error(f"Error in GDL PMS on_session_creation: {str(e)}")

def boot_session(bootinfo):
    """
    Enriches and filters bootinfo for PMS users:
    - Sets home_page to the user's PMS dashboard/workspace.
    - Strips all extra non-PMS desktop icons (Organization, Accounting, Buying, etc.).
    - Filters workspace sidebar and allowed workspaces so extra modules don't appear.
    """
    try:
        user = frappe.session.user
        info = get_user_pms_info(user)
        if not info:
            return

        target_slug = info["slug"]
        bootinfo["home_page"] = target_slug

        # Determine allowed workspaces for this user
        allowed_ws = set()
        user_roles = info["roles"]
        for role, ws_list in PMS_ALLOWED_WORKSPACES.items():
            if role in user_roles:
                allowed_ws.update(ws_list)

        # 1. Filter desktop icons
        if "desktop_icons" in bootinfo and isinstance(bootinfo["desktop_icons"], list):
            filtered_icons = []
            for icon in bootinfo["desktop_icons"]:
                label = (icon.get("label") or "").strip()
                link_to = (icon.get("link_to") or "").strip()
                # Keep PMS icons
                if "PMS" in label or "PMS" in link_to or label in allowed_ws or link_to in allowed_ws:
                    filtered_icons.append(icon)
            
            # If no PMS icon exists in DB desktop icons yet, inject one
            if not filtered_icons:
                filtered_icons.append(frappe._dict({
                    "name": info["workspace"],
                    "label": info["workspace"],
                    "link": "/" + info["route"].lstrip("/"),
                    "link_type": "Workspace Sidebar",
                    "link_to": info["workspace"],
                    "icon_type": "Link",
                    "standard": 1,
                    "hidden": 0,
                    "bg_color": "blue"
                }))
            bootinfo["desktop_icons"] = filtered_icons

        # 2. Filter workspaces.pages & allowed_workspaces
        if "workspaces" in bootinfo and isinstance(bootinfo["workspaces"], dict) and "pages" in bootinfo["workspaces"]:
            bootinfo["workspaces"]["pages"] = [
                ws for ws in bootinfo["workspaces"]["pages"]
                if ws.get("name") in allowed_ws or ("PMS" not in (ws.get("name") or "") and "pms" not in (ws.get("name") or "").lower())
            ]

        if "allowed_workspaces" in bootinfo and isinstance(bootinfo["allowed_workspaces"], list):
            bootinfo["allowed_workspaces"] = [
                ws for ws in bootinfo["allowed_workspaces"]
                if ws.get("name") in allowed_ws or ("PMS" not in (ws.get("name") or "") and "pms" not in (ws.get("name") or "").lower())
            ]

        # 3. Filter workspace_sidebar_item
        if "workspace_sidebar_item" in bootinfo and isinstance(bootinfo["workspace_sidebar_item"], dict):
            pms_sidebar = {}
            for k, v in bootinfo["workspace_sidebar_item"].items():
                if any(w.lower() in k.lower() for w in allowed_ws):
                    pms_sidebar[k] = v
            # If there are PMS sidebars, restrict to them
            if pms_sidebar:
                bootinfo["workspace_sidebar_item"] = pms_sidebar

    except Exception as e:
        frappe.log_error(f"Error in GDL PMS boot_session: {str(e)}")

def set_user_default_workspace(doc, method=None):
    """
    Ensures that when a PMS User document is validated, default_workspace is set.
    """
    try:
        user_roles = [r.role for r in getattr(doc, "roles", [])]
        if "System Manager" in user_roles or "Administrator" in user_roles:
            return

        for role, route, ws_name in PMS_ROLE_ROUTES:
            if role in user_roles:
                if doc.default_workspace != ws_name:
                    doc.default_workspace = ws_name
                break
    except Exception as e:
        frappe.log_error(f"Error in GDL PMS set_user_default_workspace: {str(e)}")
