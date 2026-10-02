# Copyright (c) 2026, GDL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class PMSCalendar(Document):
	def validate(self):
		self.validate_permissions()
		self.validate_dates()

	def validate_permissions(self):
		user = frappe.session.user
		if user == "Administrator":
			return
		roles = frappe.get_roles(user)
		if not any(r in roles for r in ["HR Admin", "System Manager", "HR Manager"]):
			frappe.throw(
				_("Only HR Admin / System Manager can create or modify PMS Calendar."),
				frappe.PermissionError
			)

	def validate_dates(self):
		# Performance plan dates validation
		if self.employee_submission_deadline and self.supervisor_approval_deadline:
			if getdate(self.employee_submission_deadline) > getdate(self.supervisor_approval_deadline):
				frappe.throw(_("Employee Submission End Date ({0}) cannot be after Supervisor Approval End Date ({1})").format(
					self.employee_submission_deadline, self.supervisor_approval_deadline
				))

		if self.supervisor_approval_deadline and self.reviewer_approval_deadline:
			if getdate(self.supervisor_approval_deadline) > getdate(self.reviewer_approval_deadline):
				frappe.throw(_("Supervisor Approval End Date ({0}) cannot be after Reviewer Approval End Date ({1})").format(
					self.supervisor_approval_deadline, self.reviewer_approval_deadline
				))

		# Appraisal dates validation if enabled
		if self.enable_appraisal_timeline:
			if self.self_scoring_start_date and self.self_scoring_end_date:
				if getdate(self.self_scoring_start_date) > getdate(self.self_scoring_end_date):
					frappe.throw(_("Self-Scoring Start Date ({0}) cannot be after Self-Scoring End Date ({1})").format(
						self.self_scoring_start_date, self.self_scoring_end_date
					))

			if self.self_scoring_end_date and self.supervisor_appraisal_end_date:
				if getdate(self.self_scoring_end_date) > getdate(self.supervisor_appraisal_end_date):
					frappe.throw(_("Self-Scoring End Date ({0}) cannot be after Supervisor Appraisal Review End Date ({1})").format(
						self.self_scoring_end_date, self.supervisor_appraisal_end_date
					))

			if self.supervisor_appraisal_end_date and self.reviewer_appraisal_end_date:
				if getdate(self.supervisor_appraisal_end_date) > getdate(self.reviewer_appraisal_end_date):
					frappe.throw(_("Supervisor Appraisal Review End Date ({0}) cannot be after Reviewer Appraisal Review End Date ({1})").format(
						self.supervisor_appraisal_end_date, self.reviewer_appraisal_end_date
					))


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return ""

	roles = frappe.get_roles(user)
	if "HR Admin" in roles or "System Manager" in roles or "HR Manager" in roles:
		return ""

	# Restrict access exclusively for non-HR users
	return "1=0"


def has_permission(doc, ptype="read", user=None):
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True

	roles = frappe.get_roles(user)
	if "HR Admin" in roles or "System Manager" in roles or "HR Manager" in roles:
		return True

	return False
