# Copyright (c) 2026, GDL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PMSAppraisalCycle(Document):
	def onload(self):
		user = frappe.session.user
		if user != "Administrator":
			roles = frappe.get_roles(user)
			if not any(r in roles for r in ["HR Admin", "System Manager", "HR Manager"]):
				self.set("applicable_employees", [])

	def validate(self):
		if not self.cycle_type:
			self.cycle_type = "Annual"

		if self.cycle_type == "Probation":
			if self.calendar_year and not self.start_date:
				self.start_date = f"{self.calendar_year}-01-01"
			if self.start_date and not self.end_date:
				self.end_date = frappe.utils.add_days(frappe.utils.add_months(self.start_date, 3), -1)
		else:
			if self.calendar_year:
				if not self.start_date:
					self.start_date = f"{self.calendar_year}-01-01"
				if not self.end_date:
					self.end_date = f"{self.calendar_year}-12-31"

		# Auto-populate applicable employees on save if empty or if requested
		if not self.applicable_employees or getattr(self.flags, "sync_employees", False):
			self.populate_applicable_employees()

	def populate_applicable_employees(self):
		data = _get_applicable_employees_internal(self.grade_group, self.name, self.cycle_type)
		self.applicable_employees = []
		for emp in data.get("employees", []):
			self.append("applicable_employees", {
				"employee": emp["employee"],
				"employee_name": emp["employee_name"],
				"employment_type": emp.get("employment_type"),
				"grade_group": emp.get("grade_group"),
				"department": emp.get("department"),
				"designation": emp.get("designation"),
				"supervisor": emp.get("supervisor"),
				"supervisor_name": emp.get("supervisor_name"),
				"reviewer": emp.get("reviewer"),
				"reviewer_name": emp.get("reviewer_name"),
				"appraisal_status": emp.get("appraisal_status") or "Not Created",
			})


def check_hr_admin_permission():
	user = frappe.session.user
	if user == "Administrator":
		return
	roles = frappe.get_roles(user)
	if not any(r in roles for r in ["HR Admin", "System Manager", "HR Manager"]):
		frappe.throw(
			_("Only HR Admin is permitted to access cycle employee reporting hierarchy."),
			frappe.PermissionError
		)


@frappe.whitelist()
def get_applicable_employees_list(grade_group=None, cycle_name=None, cycle_type=None):
	"""
	Fetch all active employees applicable for the given grade group along with
	supervisor and reviewer hierarchy details.
	Restricted strictly to HR Admin / System Manager.
	"""
	check_hr_admin_permission()
	return _get_applicable_employees_internal(grade_group, cycle_name, cycle_type)


def _get_applicable_employees_internal(grade_group=None, cycle_name=None, cycle_type=None):
	if cycle_name:
		cycle_doc = frappe.db.get_value("PMS Appraisal Cycle", cycle_name, ["grade_group", "cycle_type"], as_dict=True)
		if cycle_doc:
			if not grade_group:
				grade_group = cycle_doc.grade_group
			if not cycle_type:
				cycle_type = cycle_doc.cycle_type

	grade_group = grade_group or "All"
	cycle_type = cycle_type or "Annual"

	filters = {"status": "Active"}
	if grade_group != "All":
		filters["grade_group"] = grade_group

	employees = frappe.get_all(
		"Employee",
		filters=filters,
		fields=[
			"name", "employee_name", "grade_group", "department",
			"designation", "reports_to", "reviewer",
			"final_confirmation_date", "contract_end_date"
		],
		order_by="employee_name asc"
	)

	# Filter employees based on Cycle Type:
	# - Probation: Only unconfirmed and non-contract employees (final_confirmation_date is not set and contract_end_date is not set)
	# - Annual: Regular (final_confirmation_date is set) and Contract (contract_end_date is set) employees
	if cycle_type == "Probation":
		employees = [
			e for e in employees
			if not e.get("final_confirmation_date") and not e.get("contract_end_date")
		]
	else:
		employees = [
			e for e in employees
			if e.get("final_confirmation_date") or e.get("contract_end_date")
		]

	# Collect supervisor and reviewer IDs to fetch their names in batch
	supervisor_ids = {e["reports_to"] for e in employees if e.get("reports_to")}
	reviewer_ids = {e["reviewer"] for e in employees if e.get("reviewer")}
	all_lead_ids = supervisor_ids.union(reviewer_ids)

	lead_names_map = {}
	if all_lead_ids:
		lead_records = frappe.get_all(
			"Employee",
			filters={"name": ["in", list(all_lead_ids)]},
			fields=["name", "employee_name"]
		)
		lead_names_map = {r["name"]: r["employee_name"] for r in lead_records}

	# Check existing PMS Appraisals if cycle_name is provided
	appraisal_status_map = {}
	if cycle_name:
		existing_appraisals = frappe.get_all(
			"PMS Appraisal",
			filters={"cycle": cycle_name},
			fields=["employee", "plan_status", "workflow_state", "name"]
		)
		appraisal_status_map = {a["employee"]: a["plan_status"] or "Draft" for a in existing_appraisals}

	result_list = []
	with_sup_count = 0
	with_rev_count = 0
	missing_hierarchy_list = []

	for emp in employees:
		sup_id = emp.get("reports_to")
		sup_name = lead_names_map.get(sup_id) if sup_id else None

		rev_id = emp.get("reviewer")
		rev_name = lead_names_map.get(rev_id) if rev_id else None

		if sup_id:
			with_sup_count += 1
		if rev_id:
			with_rev_count += 1

		if not sup_id or not rev_id:
			missing_reasons = []
			if not sup_id: missing_reasons.append("Supervisor")
			if not rev_id: missing_reasons.append("Reviewer")
			missing_hierarchy_list.append({
				"employee": emp["name"],
				"employee_name": emp["employee_name"],
				"missing": ", ".join(missing_reasons)
			})

		plan_status = appraisal_status_map.get(emp["name"], "Not Created")
		emp_type = "Contract" if emp.get("contract_end_date") else ("Regular" if emp.get("final_confirmation_date") else "Probation")

		result_list.append({
			"employee": emp["name"],
			"employee_name": emp["employee_name"],
			"employment_type": emp_type,
			"grade_group": emp.get("grade_group"),
			"department": emp.get("department"),
			"designation": emp.get("designation"),
			"supervisor": sup_id,
			"supervisor_name": sup_name or "Not Assigned",
			"reviewer": rev_id,
			"reviewer_name": rev_name or "Not Assigned",
			"appraisal_status": plan_status
		})

	total_emp = len(employees)
	stats = {
		"total": total_emp,
		"with_supervisor": with_sup_count,
		"with_reviewer": with_rev_count,
		"missing_supervisor": total_emp - with_sup_count,
		"missing_reviewer": total_emp - with_rev_count,
		"missing_any_count": len(missing_hierarchy_list),
		"missing_hierarchy_list": missing_hierarchy_list
	}

	return {
		"employees": result_list,
		"stats": stats
	}


@frappe.whitelist()
def sync_cycle_employees(cycle_name):
	"""
	Whitelisted method for HR Admin to re-sync employees on an existing cycle.
	"""
	check_hr_admin_permission()
	doc = frappe.get_doc("PMS Appraisal Cycle", cycle_name)
	doc.flags.sync_employees = True
	doc.populate_applicable_employees()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return get_applicable_employees_list(doc.grade_group, doc.name, doc.cycle_type)


def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	if user == "Administrator": return ""
	
	roles = frappe.get_roles(user)
	if "HR Admin" in roles or "System Manager" in roles:
		return ""
	
	# Allow all authenticated employees, supervisors, reviewers, and supervisor 2 to view draft and active/published cycles
	allowed_roles = {"Employee", "Supervisor", "Reviewer", "Supervisor 2"}
	if any(r in allowed_roles for r in roles):
		return "`tabPMS Appraisal Cycle`.status IN ('Draft', 'Active', 'Planning Open', 'Monitoring', 'Self-Rating Open', 'Closed')"
		
	return "1=0"


def has_permission(doc, ptype="read", user=None):
	if not user: user = frappe.session.user
	if user == "Administrator": return True
	
	roles = frappe.get_roles(user)
	if "HR Admin" in roles or "System Manager" in roles:
		return True
		
	if ptype == "read":
		allowed_roles = {"Employee", "Supervisor", "Reviewer", "Supervisor 2"}
		if any(r in allowed_roles for r in roles):
			return True
	
	return False
