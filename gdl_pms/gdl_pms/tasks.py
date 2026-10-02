import frappe
from frappe.utils import getdate, add_days

def send_pending_action_reminders():
    frappe.logger().info("Executing daily pending action reminders for PMS")
    # Open appraisals
    appraisals = frappe.get_all("PMS Appraisal", filters={"docstatus": 0}, fields=["name", "employee", "workflow_state"])
    
    for app in appraisals:
        state = app.workflow_state
        recipient = None
        message = ""
        
        if state == "Planning Open":
            # notify employee
            emp = frappe.get_doc("Employee", app.employee)
            if emp.user_id:
                recipient = emp.user_id
                message = f"Please complete your planning for Appraisal {app.name}."
        elif state == "Pending Supervisor Approval":
            # notify supervisor
            emp_doc = frappe.get_doc("Employee", app.employee)
            if emp_doc.reports_to:
                sup = frappe.get_doc("Employee", emp_doc.reports_to)
                if sup.user_id:
                    recipient = sup.user_id
                    message = f"Pending supervisor approval for {app.employee}'s Appraisal: {app.name}."
        elif state == "Pending Reviewer Approval":
            # notify reviewer
            emp_doc = frappe.get_doc("Employee", app.employee)
            if emp_doc.reviewer:
                rev = frappe.get_doc("Employee", emp_doc.reviewer)
                if rev.user_id:
                    recipient = rev.user_id
                    message = f"Pending reviewer approval for {app.employee}'s Appraisal: {app.name}."
        
        if recipient and message:
            try:
                from gdl_pms.email_service import send_pms_email
                send_pms_email(
                    recipients=recipient,
                    subject=f"Action Required: PMS Appraisal ({app.name})",
                    title="Action Required: PMS Appraisal",
                    message=f"<p>{message}</p>",
                    details={
                        "Appraisal": app.name,
                        "Employee": app.employee,
                        "Current Phase": state,
                        "Status": "Pending Action"
                    }
                )
            except Exception as e:
                frappe.logger().error(f"Failed sending pending reminder for {app.name}: {str(e)}")

def auto_transition_cycle_states():
    frappe.logger().info("Executing cron for auto-transitioning cycle states")
    cycles = frappe.get_all("PMS Appraisal Cycle", filters={"status": ["in", ["Draft", "Planning Open", "Monitoring"]]}, fields=["name", "status", "start_date"])
    
    today = getdate()
    for cycle in cycles:
        current_status = cycle.status
        if not cycle.start_date: continue
        start = getdate(cycle.start_date)
        
        # Logical progression based on dates since specific phase dates aren't in doctype
        new_status = current_status
        if current_status == "Draft" and today >= start:
            new_status = "Planning Open"
        elif current_status == "Planning Open" and today >= add_days(start, 30):
            new_status = "Monitoring"
        elif current_status == "Monitoring" and today >= add_days(start, 180):
            new_status = "Self-Rating Open"
            
        if new_status != current_status:
            frappe.db.set_value("PMS Appraisal Cycle", cycle.name, "status", new_status)
            frappe.logger().info(f"Transitioned cycle {cycle.name} to {new_status}")
