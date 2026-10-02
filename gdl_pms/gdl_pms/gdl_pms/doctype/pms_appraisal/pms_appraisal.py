import frappe
from frappe.model.document import Document
from frappe.utils import flt
import json
from gdl_pms import scoring_engine

class PMSAppraisal(Document):
    def before_insert(self):
        # Auto-fetch supervisor/reviewer snapshots and employee_name if employee is selected
        if self.employee:
            emp = frappe.get_doc("Employee", self.employee)
            self.employee_name = emp.employee_name
            self.supervisor_snapshot = emp.reports_to
            self.supervisor_name = frappe.db.get_value("Employee", emp.reports_to, "employee_name") if emp.reports_to else ""
            self.reviewer_snapshot = emp.reviewer
            self.reviewer_name = frappe.db.get_value("Employee", emp.reviewer, "employee_name") if emp.reviewer else ""
            self.supervisor_2_snapshot = emp.get("supervisor_2")
            self.supervisor_2_name = frappe.db.get_value("Employee", emp.get("supervisor_2"), "employee_name") if emp.get("supervisor_2") else ""
            if not self.grade_group:
                self.grade_group = emp.grade_group or "OS_ESP"

    def onload(self):
        if self.employee:
            if not self.grade_group:
                self.grade_group = frappe.db.get_value("Employee", self.employee, "grade_group") or "OS_ESP"
            if not self.employee_name:
                self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
            if self.supervisor_snapshot and not getattr(self, "supervisor_name", None):
                self.supervisor_name = frappe.db.get_value("Employee", self.supervisor_snapshot, "employee_name")
            if self.reviewer_snapshot and not getattr(self, "reviewer_name", None):
                self.reviewer_name = frappe.db.get_value("Employee", self.reviewer_snapshot, "employee_name")
            if self.supervisor_2_snapshot and not getattr(self, "supervisor_2_name", None):
                self.supervisor_2_name = frappe.db.get_value("Employee", self.supervisor_2_snapshot, "employee_name")

    def validate(self):
        if self.employee:
            if not self.grade_group:
                self.grade_group = frappe.db.get_value("Employee", self.employee, "grade_group") or "OS_ESP"
            if not self.employee_name:
                self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
            if self.supervisor_snapshot and not getattr(self, "supervisor_name", None):
                self.supervisor_name = frappe.db.get_value("Employee", self.supervisor_snapshot, "employee_name")
            if self.reviewer_snapshot and not getattr(self, "reviewer_name", None):
                self.reviewer_name = frappe.db.get_value("Employee", self.reviewer_snapshot, "employee_name")
            if self.supervisor_2_snapshot and not getattr(self, "supervisor_2_name", None):
                self.supervisor_2_name = frappe.db.get_value("Employee", self.supervisor_2_snapshot, "employee_name")

        # 1. Lock Protection: Prevent any modification if locked
        if not self.is_new() and self.db_get("locked"):
            if not getattr(self, "_allow_unlock", False):
                frappe.throw("This Appraisal is Finalized & Locked and cannot be modified.")

        # 2. Document-level permission safety net: Supervisor 2 is strictly read-only
        user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        roles = frappe.get_roles()
        is_admin = any(r in roles for r in ["Administrator", "System Manager", "HR Manager", "HR Admin"])
        if not is_admin and user_emp:
            if self.supervisor_2_snapshot == user_emp and user_emp not in [self.employee, self.supervisor_snapshot, self.reviewer_snapshot]:
                frappe.throw("Supervisor 2 has read-only access and cannot edit or modify Performance Plans or Appraisals.", frappe.PermissionError)
            elif "Supervisor 2" in roles and user_emp not in [self.employee, self.supervisor_snapshot, self.reviewer_snapshot]:
                frappe.throw("Supervisor 2 has read-only access and cannot edit or modify Performance Plans or Appraisals.", frappe.PermissionError)

        # 3. Prevent direct editing of targets when plan was ALREADY Approved & Monitoring in DB
        if not self.is_new() and self.db_get("plan_status") == "Approved" and self.db_get("workflow_state") == "Monitoring":
            if not getattr(self, "_allow_target_update", False) and "System Manager" not in frappe.get_roles():
                db_targets = frappe.get_all("PMS Target", filters={"parent": self.name}, fields=["target_description", "weight", "remark"], order_by="idx asc")
                current_targets = [{"target_description": t.target_description, "weight": flt(t.weight, 2), "remark": getattr(t, "remark", None)} for t in self.targets]
                db_targets_formatted = [{"target_description": t.target_description, "weight": flt(t.weight, 2), "remark": getattr(t, "remark", None)} for t in db_targets]
                if current_targets != db_targets_formatted:
                    frappe.throw("Direct editing of targets is locked for Approved Performance Plans. Please use the 'Request Amendment' action.")

        # 4. Automatic revert to Draft when Supervisor or Reviewer edits tasks/weightages/remarks during planning approval stage
        if not self.is_new() and self.workflow_state == "Planning Open":
            db_status = self.db_get("plan_status")
            if db_status in ["Pending Supervisor Approval", "Pending Reviewer Approval"]:
                db_targets = frappe.get_all("PMS Target", filters={"parent": self.name}, fields=["target_description", "weight", "remark"], order_by="idx asc")
                current_targets = [
                    {
                        "target_description": (t.target_description or "").strip(),
                        "weight": flt(t.weight, 2),
                        "remark": (getattr(t, "remark", None) or "").strip()
                    }
                    for t in self.targets
                ]
                db_targets_formatted = [
                    {
                        "target_description": (t.target_description or "").strip(),
                        "weight": flt(t.weight, 2),
                        "remark": (getattr(t, "remark", None) or "").strip()
                    }
                    for t in db_targets
                ]

                targets_changed = (current_targets != db_targets_formatted)
                db_rev_remark = (self.db_get("plan_revision_remark") or "").strip()
                curr_rev_remark = (getattr(self, "plan_revision_remark", None) or "").strip()
                remark_changed = (db_rev_remark != curr_rev_remark)

                if targets_changed or remark_changed or getattr(self, "_return_to_employee", False):
                    editor_role = "Supervisor" if db_status == "Pending Supervisor Approval" else "Reviewer"
                    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
                    is_sys_mgr = "System Manager" in frappe.get_roles()
                    if is_sys_mgr and user_emp not in [self.supervisor_snapshot, self.reviewer_snapshot]:
                        editor_role = f"System Manager ({editor_role} Stage)"

                    self.plan_status = "Draft"
                    self.workflow_state = "Planning Open"
                    self.revised_by_role = editor_role
                    self.plan_rejection_remark = None

                    note_suffix = f": \"{curr_rev_remark}\"" if curr_rev_remark else ""
                    self.add_comment(
                        "Comment",
                        f"Performance Plan targets/weights were modified by {editor_role} ({frappe.session.user}){note_suffix}. Returned to employee ({self.employee_name}) for analysis."
                    )
                    frappe.msgprint(
                        f"Edits detected from {editor_role}. Performance Plan has been returned to {self.employee_name} for analysis.",
                        indicator="blue",
                        alert=True
                    )

        # 5. Validate that Performance Plan can only be created for an Active / Planning Open cycle
        if self.is_new() and self.cycle:
            cycle_status = frappe.db.get_value("PMS Appraisal Cycle", self.cycle, "status")
            if cycle_status not in ["Active", "Planning Open", "Monitoring", "Self-Rating Open"]:
                frappe.throw(f"Performance Plans can only be created for Active Appraisal Cycles. Selected cycle '{self.cycle}' is currently in '{cycle_status}' status.")

        # 6. Validate target weights on save
        expected_weight = 60 if self.grade_group == "PS_CS" else 50
        total_weight = sum(flt(t.weight) for t in self.targets)
        if flt(total_weight, 2) != flt(expected_weight, 2):
            frappe.throw(f"Total target weight must be exactly {expected_weight}. Current sum is {flt(total_weight, 2)}.")

        # 7. Validate score limits for Appraisal Phase
        for t in self.targets:
            w = flt(t.weight)
            if t.self_score is not None and t.self_score != "":
                if flt(t.self_score) < 0 or flt(t.self_score) > w:
                    frappe.throw(f"Target '{t.target_description}': Self Score ({t.self_score}) cannot exceed row weight ({w}) or be negative.")
            if t.supervisor_score is not None and t.supervisor_score != "":
                if flt(t.supervisor_score) < 0 or flt(t.supervisor_score) > w:
                    frappe.throw(f"Target '{t.target_description}': Supervisor Score ({t.supervisor_score}) cannot exceed row weight ({w}) or be negative.")
            if t.reviewer_score is not None and t.reviewer_score != "":
                if flt(t.reviewer_score) < 0 or flt(t.reviewer_score) > w:
                    frappe.throw(f"Target '{t.target_description}': Reviewer Score ({t.reviewer_score}) cannot exceed row weight ({w}) or be negative.")

        for c in self.competencies:
            cw = flt(c.weight)
            if c.self_rating is not None and c.self_rating != "":
                if flt(c.self_rating) < 0 or flt(c.self_rating) > cw:
                    frappe.throw(f"Competency '{c.competency}': Self Rating ({c.self_rating}) cannot exceed weight ({cw}) or be negative.")
            if c.supervisor_rating is not None and c.supervisor_rating != "":
                if flt(c.supervisor_rating) < 0 or flt(c.supervisor_rating) > cw:
                    frappe.throw(f"Competency '{c.competency}': Supervisor Rating ({c.supervisor_rating}) cannot exceed weight ({cw}) or be negative.")
            if c.reviewer_rating is not None and c.reviewer_rating != "":
                if flt(c.reviewer_rating) < 0 or flt(c.reviewer_rating) > cw:
                    frappe.throw(f"Competency '{c.competency}': Reviewer Rating ({c.reviewer_rating}) cannot exceed weight ({cw}) or be negative.")

        # 8. Strict Role-Based Score Validation during Appraisal Phase
        if not self.is_new() and self.appraisal_status and self.appraisal_status != "Not Activated":
            roles = frappe.get_roles()
            is_admin = any(r in roles for r in ["Administrator", "System Manager"])
            user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")

            if not is_admin:
                is_supervisor_user = (user_emp and user_emp == self.supervisor_snapshot)
                is_reviewer_user = (user_emp and user_emp == self.reviewer_snapshot)
                is_employee_user = (user_emp and user_emp == self.employee)

                db_targets = {
                    t.name: t for t in frappe.get_all(
                        "PMS Target",
                        filters={"parent": self.name},
                        fields=["name", "self_score", "self_remark", "supervisor_score", "supervisor_remark", "reviewer_score", "reviewer_remark", "target_description", "weight"]
                    )
                }
                db_comps = {
                    c.name: c for c in frappe.get_all(
                        "PMS Competency Score",
                        filters={"parent": self.name},
                        fields=["name", "self_rating", "self_remark", "supervisor_rating", "supervisor_remark", "reviewer_rating", "reviewer_remark"]
                    )
                }

                for t in self.targets:
                    db_t = db_targets.get(t.name)
                    if db_t:
                        # Target Description and Weight cannot be modified in Appraisal phase
                        if (t.target_description or "").strip() != (db_t.target_description or "").strip() or flt(t.weight) != flt(db_t.weight):
                            frappe.throw("Target description and weight are locked and cannot be modified during appraisal phase.")

                        # Reviewer score/remark can ONLY be modified by assigned Reviewer
                        if flt(t.reviewer_score) != flt(db_t.reviewer_score) or (t.reviewer_remark or "") != (db_t.reviewer_remark or ""):
                            if not is_reviewer_user:
                                frappe.throw("Only the assigned Reviewer can enter or edit Reviewer scores and remarks.", frappe.PermissionError)
                            elif self.appraisal_status not in ["Disputed - Pending Reviewer", "Under PERC Review"]:
                                frappe.throw(f"Reviewer scores cannot be edited in '{self.appraisal_status}' stage.", frappe.PermissionError)

                        # Supervisor score/remark can ONLY be modified by assigned Supervisor
                        if flt(t.supervisor_score) != flt(db_t.supervisor_score) or (t.supervisor_remark or "") != (db_t.supervisor_remark or ""):
                            if not is_supervisor_user:
                                frappe.throw("Only the assigned Supervisor can enter or edit Supervisor scores and remarks.", frappe.PermissionError)
                            elif self.appraisal_status != "Pending Supervisor Review":
                                frappe.throw("Supervisor scores cannot be edited outside of the 'Pending Supervisor Review' stage.", frappe.PermissionError)

                        # Self score/remark can ONLY be modified by assigned Employee
                        if flt(t.self_score) != flt(db_t.self_score) or (t.self_remark or "") != (db_t.self_remark or ""):
                            if not is_employee_user:
                                frappe.throw("Only the Employee can enter or edit Self Assessment scores and remarks.", frappe.PermissionError)
                            elif self.appraisal_status != "Self-Assessment Pending":
                                frappe.throw("Self Assessment scores cannot be edited after submission.", frappe.PermissionError)

                for c in self.competencies:
                    db_c = db_comps.get(c.name)
                    if db_c:
                        # Reviewer rating/remark can ONLY be modified by assigned Reviewer
                        if flt(c.reviewer_rating) != flt(db_c.reviewer_rating) or (c.reviewer_remark or "") != (db_c.reviewer_remark or ""):
                            if not is_reviewer_user:
                                frappe.throw("Only the assigned Reviewer can enter or edit Reviewer rating and remarks.", frappe.PermissionError)
                            elif self.appraisal_status not in ["Disputed - Pending Reviewer", "Under PERC Review"]:
                                frappe.throw(f"Reviewer ratings cannot be edited in '{self.appraisal_status}' stage.", frappe.PermissionError)

                        # Supervisor rating/remark can ONLY be modified by assigned Supervisor
                        if flt(c.supervisor_rating) != flt(db_c.supervisor_rating) or (c.supervisor_remark or "") != (db_c.supervisor_remark or ""):
                            if not is_supervisor_user:
                                frappe.throw("Only the assigned Supervisor can enter or edit Supervisor rating and remarks.", frappe.PermissionError)
                            elif self.appraisal_status != "Pending Supervisor Review":
                                frappe.throw("Supervisor ratings cannot be edited outside of the 'Pending Supervisor Review' stage.", frappe.PermissionError)

                        # Self rating/remark can ONLY be modified by assigned Employee
                        if flt(c.self_rating) != flt(db_c.self_rating) or (c.self_remark or "") != (db_c.self_remark or ""):
                            if not is_employee_user:
                                frappe.throw("Only the Employee can enter or edit Self Rating and remarks.", frappe.PermissionError)
                            elif self.appraisal_status != "Self-Assessment Pending":
                                frappe.throw("Self Rating cannot be edited after submission.", frappe.PermissionError)


# ==============================================================================
# APPRAISAL PHASE LIFECYCLE APIS
# ==============================================================================

@frappe.whitelist()
def activate_appraisal_phase(docname):
    """
    Triggered by HR Admin on an Approved Performance Plan in Monitoring stage.
    Transitions plan into the Appraisal Phase with mapped Competencies.
    """
    roles = frappe.get_roles()
    is_hr = any(r in roles for r in ["Administrator", "System Manager", "HR Admin", "HR Manager"])
    if not is_hr:
        frappe.throw("Only HR Admin or System Manager can activate the Appraisal Phase.")

    doc = frappe.get_doc("PMS Appraisal", docname)
    if doc.plan_status != "Approved" or doc.workflow_state != "Monitoring":
        frappe.throw("Appraisal Phase can only be activated for Approved Performance Plans in Monitoring stage.")

    # Ensure mapped competencies based on Grade Group
    expected_comp_weight = 8 if doc.grade_group == "PS_CS" else 10
    standard_competencies = [
        "Job Knowledge & Skills",
        "Quality of Work",
        "Communication & Teamwork",
        "Initiative & Problem Solving",
        "Attendance & Punctuality"
    ]

    if not doc.competencies or len(doc.competencies) == 0:
        doc.competencies = []
        for comp in standard_competencies:
            doc.append("competencies", {
                "competency": comp,
                "weight": expected_comp_weight
            })
    else:
        # Validate or sync competency weights
        for c in doc.competencies:
            c.weight = expected_comp_weight

    doc.workflow_state = "Appraisal Open"
    doc.appraisal_status = "Self-Assessment Pending"
    doc.add_comment("Comment", f"Appraisal Phase activated by HR Admin ({frappe.session.user}).")
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return "Appraisal Phase Activated"


@frappe.whitelist()
def submit_self_assessment(docname, employee_remarks=None, target_data=None, competency_data=None):
    """
    Stage 1: Employee enters self-scores, remarks, and evidence, then submits to Supervisor.
    """
    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_admin = any(r in frappe.get_roles() for r in ["Administrator", "System Manager"])

    if doc.employee != user_emp and not is_admin:
        frappe.throw("Only the assigned Employee can submit their Self-Assessment.")

    if doc.appraisal_status != "Self-Assessment Pending":
        frappe.throw(f"Self-Assessment cannot be submitted in status '{doc.appraisal_status}'.")

    # Update targets if passed
    if target_data:
        if isinstance(target_data, str):
            target_data = json.loads(target_data)
        for idx, t_in in enumerate(target_data):
            if idx < len(doc.targets):
                if "self_score" in t_in and t_in["self_score"] is not None and t_in["self_score"] != "":
                    doc.targets[idx].self_score = flt(t_in["self_score"])
                if "self_remark" in t_in:
                    doc.targets[idx].self_remark = t_in["self_remark"]
                if "evidence" in t_in:
                    doc.targets[idx].evidence = t_in["evidence"]

    # Update competencies if passed
    if competency_data:
        if isinstance(competency_data, str):
            competency_data = json.loads(competency_data)
        for idx, c_in in enumerate(competency_data):
            if idx < len(doc.competencies):
                if "self_rating" in c_in and c_in["self_rating"] is not None and c_in["self_rating"] != "":
                    doc.competencies[idx].self_rating = flt(c_in["self_rating"])
                if "self_remark" in c_in:
                    doc.competencies[idx].self_remark = c_in["self_remark"]

    if employee_remarks:
        doc.employee_overall_remarks = employee_remarks

    doc.add_comment("Comment", f"Self-Assessment submitted by {doc.employee_name}.")
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    try:
        from gdl_pms.email_service import notify_self_assessment_submitted
        sup_email = _get_employee_email(doc.supervisor_snapshot)
        if sup_email:
            notify_self_assessment_submitted(doc, sup_email)
    except Exception as e:
        frappe.logger().error(f"Failed sending self-assessment email: {str(e)}")

    return "Self-Assessment Submitted"


@frappe.whitelist()
def submit_supervisor_review(docname, supervisor_remarks=None, target_data=None, competency_data=None):
    """
    Stage 2: Supervisor enters scores and remarks, computes provisional score, and submits to Employee.
    """
    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_admin = any(r in frappe.get_roles() for r in ["Administrator", "System Manager"])

    if doc.supervisor_snapshot != user_emp and not is_admin:
        frappe.throw("Only the assigned Supervisor can submit this appraisal evaluation.")

    if doc.appraisal_status != "Pending Supervisor Review":
        frappe.throw(f"Supervisor evaluation cannot be submitted in status '{doc.appraisal_status}'.")

    if target_data:
        if isinstance(target_data, str):
            target_data = json.loads(target_data)
        for idx, t_in in enumerate(target_data):
            if idx < len(doc.targets):
                if "supervisor_score" in t_in and t_in["supervisor_score"] is not None and t_in["supervisor_score"] != "":
                    doc.targets[idx].supervisor_score = flt(t_in["supervisor_score"])
                if "supervisor_remark" in t_in:
                    doc.targets[idx].supervisor_remark = t_in["supervisor_remark"]

    if competency_data:
        if isinstance(competency_data, str):
            competency_data = json.loads(competency_data)
        for idx, c_in in enumerate(competency_data):
            if idx < len(doc.competencies):
                if "supervisor_rating" in c_in and c_in["supervisor_rating"] is not None and c_in["supervisor_rating"] != "":
                    doc.competencies[idx].supervisor_rating = flt(c_in["supervisor_rating"])
                if "supervisor_remark" in c_in:
                    doc.competencies[idx].supervisor_remark = c_in["supervisor_remark"]

    if supervisor_remarks:
        doc.supervisor_overall_remarks = supervisor_remarks

    # Compute provisional total score & rating band
    work_score = sum(flt(t.supervisor_score or 0) for t in doc.targets)
    comp_score = sum(flt(c.supervisor_rating or 0) for c in doc.competencies)
    doc.total_score = flt(work_score + comp_score, 2)
    doc.rating_band = scoring_engine.get_band(doc.total_score)

    doc.appraisal_status = "Pending Employee Acceptance"
    doc.add_comment("Comment", f"Supervisor evaluation submitted by {frappe.session.user}. Provisional Score: {doc.total_score} ({doc.rating_band}).")
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    try:
        from gdl_pms.email_service import notify_supervisor_scores_submitted
        emp_email = _get_employee_email(doc.employee)
        if emp_email:
            notify_supervisor_scores_submitted(doc, emp_email)
    except Exception as e:
        frappe.logger().error(f"Failed sending supervisor review email: {str(e)}")

    return "Supervisor Assessment Submitted"


@frappe.whitelist()
def accept_supervisor_scores(docname):
    """
    Stage 3A: Employee accepts Supervisor's evaluation.
    """
    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_admin = any(r in frappe.get_roles() for r in ["Administrator", "System Manager"])

    if doc.employee != user_emp and not is_admin:
        frappe.throw("Only the assigned Employee can accept their appraisal.")

    if doc.appraisal_status != "Pending Employee Acceptance":
        frappe.throw(f"Action not valid in status '{doc.appraisal_status}'.")

    doc.appraisal_status = "Appraisal Accepted"
    doc.add_comment("Comment", f"Supervisor evaluation accepted by employee {doc.employee_name}.")
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return "Appraisal Accepted"


@frappe.whitelist()
def raise_dispute(docname, dispute_reason):
    """
    Stage 3B: Employee raises a dispute against Supervisor's evaluation, sending case to Reviewer.
    """
    if not dispute_reason or not str(dispute_reason).strip():
        frappe.throw("Dispute reason is mandatory.")

    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_admin = any(r in frappe.get_roles() for r in ["Administrator", "System Manager"])

    if doc.employee != user_emp and not is_admin:
        frappe.throw("Only the assigned Employee can raise a dispute.")

    if doc.appraisal_status != "Pending Employee Acceptance":
        frappe.throw(f"Dispute cannot be raised in status '{doc.appraisal_status}'.")

    doc.dispute_flag = 1
    doc.dispute_reason = dispute_reason
    doc.appraisal_status = "Disputed - Pending Reviewer"
    doc.add_comment("Comment", f"Dispute raised by employee {doc.employee_name}: \"{dispute_reason}\". Escalated to Reviewer ({doc.reviewer_name or doc.reviewer_snapshot}).")
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    try:
        from gdl_pms.email_service import notify_dispute_raised
        rev_email = _get_employee_email(doc.reviewer_snapshot)
        if rev_email:
            notify_dispute_raised(doc, rev_email, dispute_reason)
    except Exception as e:
        frappe.logger().error(f"Failed sending dispute email: {str(e)}")

    return "Dispute Raised & Escalated to Reviewer"


@frappe.whitelist()
def submit_reviewer_decision(docname, reviewer_remarks=None, target_data=None, competency_data=None):
    """
    Stage 4: Reviewer evaluates disputed appraisal, submits score validations/overrides.
    """
    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_admin = any(r in frappe.get_roles() for r in ["Administrator", "System Manager"])

    if doc.reviewer_snapshot != user_emp and not is_admin:
        frappe.throw("Only the assigned Reviewer can resolve this dispute.")

    if doc.appraisal_status != "Disputed - Pending Reviewer":
        frappe.throw(f"Reviewer decision cannot be submitted in status '{doc.appraisal_status}'.")

    if target_data:
        if isinstance(target_data, str):
            target_data = json.loads(target_data)
        for idx, t_in in enumerate(target_data):
            if idx < len(doc.targets):
                if "reviewer_score" in t_in and t_in["reviewer_score"] is not None and t_in["reviewer_score"] != "":
                    doc.targets[idx].reviewer_score = flt(t_in["reviewer_score"])
                if "reviewer_remark" in t_in:
                    doc.targets[idx].reviewer_remark = t_in["reviewer_remark"]

    if competency_data:
        if isinstance(competency_data, str):
            competency_data = json.loads(competency_data)
        for idx, c_in in enumerate(competency_data):
            if idx < len(doc.competencies):
                if "reviewer_rating" in c_in and c_in["reviewer_rating"] is not None and c_in["reviewer_rating"] != "":
                    doc.competencies[idx].reviewer_rating = flt(c_in["reviewer_rating"])
                if "reviewer_remark" in c_in:
                    doc.competencies[idx].reviewer_remark = c_in["reviewer_remark"]

    if reviewer_remarks:
        doc.reviewer_overall_remarks = reviewer_remarks

    # Re-compute total score based on reviewer decisions
    work_score = sum(flt(t.reviewer_score) if (t.reviewer_score is not None and t.reviewer_score != "" and flt(t.reviewer_score) > 0) else flt(t.supervisor_score or 0) for t in doc.targets)
    comp_score = sum(flt(c.reviewer_rating) if (c.reviewer_rating is not None and c.reviewer_rating != "" and flt(c.reviewer_rating) > 0) else flt(c.supervisor_rating or 0) for c in doc.competencies)
    doc.total_score = flt(work_score + comp_score, 2)
    doc.rating_band = scoring_engine.get_band(doc.total_score)

    doc.appraisal_status = "Reviewer Resolved - Pending Employee Decision"
    doc.add_comment("Comment", f"Reviewer dispute resolution submitted by {frappe.session.user}. Validated Score: {doc.total_score} ({doc.rating_band}).")
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return "Reviewer Decision Submitted"


@frappe.whitelist()
def accept_reviewer_decision(docname):
    """
    Stage 5A: Employee accepts Reviewer's dispute decision.
    """
    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_admin = any(r in frappe.get_roles() for r in ["Administrator", "System Manager"])

    if doc.employee != user_emp and not is_admin:
        frappe.throw("Only the assigned Employee can accept the reviewer decision.")

    if doc.appraisal_status != "Reviewer Resolved - Pending Employee Decision":
        frappe.throw(f"Action not valid in status '{doc.appraisal_status}'.")

    doc.appraisal_status = "Appraisal Accepted"
    doc.add_comment("Comment", f"Reviewer decision accepted by employee {doc.employee_name}.")
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return "Reviewer Decision Accepted"


@frappe.whitelist()
def request_perc_review(docname, justification):
    """
    Stage 5B: Employee disagrees with Reviewer and requests formal PERC escalation.
    Creates a linked PERC Case record.
    """
    if not justification or not str(justification).strip():
        frappe.throw("Justification for PERC request is mandatory.")

    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_admin = any(r in frappe.get_roles() for r in ["Administrator", "System Manager"])

    if doc.employee != user_emp and not is_admin:
        frappe.throw("Only the assigned Employee can request a PERC review.")

    if doc.appraisal_status != "Reviewer Resolved - Pending Employee Decision":
        frappe.throw(f"PERC request cannot be raised in status '{doc.appraisal_status}'.")

    # Check or create PERC Case
    existing_perc = frappe.db.get_value("PERC Case", {"appraisal": docname}, "name")
    if not existing_perc:
        perc = frappe.get_doc({
            "doctype": "PERC Case",
            "appraisal": doc.name,
            "raised_by": doc.employee,
            "justification": justification,
            "status": "Open"
        }).insert(ignore_permissions=True)
        doc.perc_case = perc.name
    else:
        doc.perc_case = existing_perc

    doc.appraisal_status = "Under PERC Review"
    doc.add_comment("Comment", f"PERC Review requested by employee {doc.employee_name}. Case {doc.perc_case} opened. Justification: \"{justification}\".")
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return doc.perc_case


@frappe.whitelist()
def lock_appraisal(docname, final_score=None):
    """
    Stage 6: HR Admin reviews appraisal (post-acceptance or post-PERC), updates final score if needed, and locks it permanently.
    """
    roles = frappe.get_roles()
    is_hr = any(r in roles for r in ["Administrator", "System Manager", "HR Admin", "HR Manager"])
    if not is_hr:
        frappe.throw("Only HR Admin or System Manager can lock appraisals.")

    doc = frappe.get_doc("PMS Appraisal", docname)
    if doc.appraisal_status not in ["Appraisal Accepted", "Under PERC Review", "Reviewer Resolved - Pending Employee Decision"]:
        frappe.throw(f"Cannot lock appraisal in status '{doc.appraisal_status}'.")

    if final_score is not None and final_score != "":
        doc.total_score = flt(final_score, 2)
        doc.rating_band = scoring_engine.get_band(doc.total_score)

    doc.locked = 1
    doc.workflow_state = "Appraisal Completed"
    doc.appraisal_status = "Finalized & Locked"
    doc.add_comment("Comment", f"Appraisal finalized and locked by HR Admin ({frappe.session.user}). Final Score: {doc.total_score} ({doc.rating_band}).")
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    try:
        from gdl_pms.email_service import notify_appraisal_locked
        emp_email = _get_employee_email(doc.employee)
        if emp_email:
            notify_appraisal_locked(doc, emp_email, doc.total_score)
    except Exception as e:
        frappe.logger().error(f"Failed sending appraisal locked email: {str(e)}")

    return "Appraisal Finalized & Locked"


# ==============================================================================
# PLANNING & AMENDMENT METHODS (Preserved & Maintained)
# ==============================================================================

@frappe.whitelist()
def open_amendment_window(docname):
    roles = frappe.get_roles()
    is_hr = any(r in roles for r in ["Administrator", "System Manager", "HR Admin", "HR Manager"])
    if not is_hr:
        frappe.throw("Only HR Admin or System Manager can open the Amendment Window.")

    doc = frappe.get_doc("PMS Appraisal", docname)
    if doc.plan_status != "Approved" or doc.workflow_state != "Monitoring":
        frappe.throw("Amendment Window can only be opened for Approved Performance Plans in Monitoring stage.")

    doc.amendment_window_open = 1
    doc.save(ignore_permissions=True)
    doc.add_comment("Comment", f"Amendment Window opened by {frappe.session.user} (HR Admin).")
    return "Amendment Window Opened"


@frappe.whitelist()
def close_amendment_window(docname):
    roles = frappe.get_roles()
    is_hr = any(r in roles for r in ["Administrator", "System Manager", "HR Admin", "HR Manager"])
    if not is_hr:
        frappe.throw("Only HR Admin or System Manager can close the Amendment Window.")

    doc = frappe.get_doc("PMS Appraisal", docname)
    doc.amendment_window_open = 0
    doc.save(ignore_permissions=True)
    doc.add_comment("Comment", f"Amendment Window closed by {frappe.session.user} (HR Admin).")
    return "Amendment Window Closed"


@frappe.whitelist()
def request_amendment(docname):
    doc = frappe.get_doc("PMS Appraisal", docname)

    if doc.plan_status != "Approved" or doc.workflow_state != "Monitoring":
        frappe.throw("Amendments can only be requested for Approved plans in Monitoring stage.")

    is_hr = any(r in frappe.get_roles() for r in ["Administrator", "System Manager", "HR Admin"])
    if not doc.amendment_window_open and not is_hr:
        frappe.throw("The Amendment Window for this Performance Plan is currently closed by HR Admin.")

    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if doc.employee != user_emp and not is_hr:
        frappe.throw("Only the assigned Employee can request an amendment.")

    existing_pending = frappe.db.exists("PMS Plan Amendment", {
        "performance_plan": doc.name,
        "status": ["in", ["Draft", "Pending Supervisor Approval", "Pending Reviewer Approval"]]
    })
    if existing_pending:
        frappe.throw(f"An active amendment request ({existing_pending}) already exists for this Performance Plan.")

    amendment = frappe.get_doc({
        "doctype": "PMS Plan Amendment",
        "performance_plan": doc.name
    })
    amendment.insert(ignore_permissions=True)
    frappe.db.commit()
    return amendment.name


def _get_employee_email(emp_id):
    """Helper to fetch user_id/email for an employee"""
    if not emp_id:
        return None
    return frappe.db.get_value("Employee", emp_id, "user_id") or frappe.db.get_value("Employee", emp_id, "company_email")


@frappe.whitelist()
def get_employee_details(employee=None):
    if not employee:
        employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if not employee:
        return None
        
    emp_data = frappe.db.get_value(
        "Employee",
        employee,
        ["name", "employee_name", "grade_group", "reports_to", "reviewer", "supervisor_2"],
        as_dict=True
    )
    if emp_data:
        grade = emp_data.get("grade_group") or "OS_ESP"
        emp_data["grade_group"] = grade
        emp_data["is_ps"] = (grade == "PS_CS")
        emp_data["is_os"] = (grade == "OS_ESP")
        emp_data["category_code"] = "PS" if grade == "PS_CS" else "OS"
        emp_data["category_name"] = "PS (Professional Staff)" if grade == "PS_CS" else "OS (Operating Staff)"
        emp_data["target_weight"] = 60 if grade == "PS_CS" else 50
        emp_data["competency_weight"] = 40 if grade == "PS_CS" else 50
        emp_data["comp_per_row"] = 8 if grade == "PS_CS" else 10
        emp_data["supervisor_name"] = frappe.db.get_value("Employee", emp_data.get("reports_to"), "employee_name") if emp_data.get("reports_to") else ""
        emp_data["reviewer_name"] = frappe.db.get_value("Employee", emp_data.get("reviewer"), "employee_name") if emp_data.get("reviewer") else ""
        emp_data["supervisor_2_name"] = frappe.db.get_value("Employee", emp_data.get("supervisor_2"), "employee_name") if emp_data.get("supervisor_2") else ""
    return emp_data

@frappe.whitelist()
def get_current_employee():
    return get_employee_details()

@frappe.whitelist()
def is_authorized_to_approve(docname):
    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_sys_mgr = "System Manager" in frappe.get_roles()
    
    if doc.plan_status == "Pending Supervisor Approval":
        return bool(doc.supervisor_snapshot == user_emp or is_sys_mgr)
    elif doc.plan_status == "Pending Reviewer Approval":
        return bool(doc.reviewer_snapshot == user_emp or is_sys_mgr)
        
    return False


@frappe.whitelist()
def send_for_approval(docname):
    doc = frappe.get_doc("PMS Appraisal", docname)
    
    if doc.plan_status not in ["Draft", "Rejected", "Returned"]:
        frappe.throw("Only Draft or Returned plans can be sent for approval.")
        
    expected_weight = 60 if doc.grade_group == "PS_CS" else 50
    total_weight = sum(flt(t.weight) for t in doc.targets)
    if flt(total_weight, 2) != flt(expected_weight, 2):
        frappe.throw(f"Total target weight must be exactly {expected_weight}. Current sum is {flt(total_weight, 2)}.")

    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if doc.employee != user_emp and "System Manager" not in frappe.get_roles():
        frappe.throw("Not authorized.")

    if doc.plan_revision_remark:
        doc.add_comment("Comment", f"Employee {doc.employee_name or doc.employee} reviewed the revisions and submitted the plan for approval.")
        doc.plan_revision_remark = None
        doc.revised_by_role = None
    elif doc.plan_status in ["Rejected", "Returned"]:
        doc.add_comment("Comment", f"Employee {doc.employee_name or doc.employee} updated and re-submitted the plan after return.")
    else:
        doc.add_comment("Comment", f"Performance Plan submitted for approval by Employee ({doc.employee_name or doc.employee}).")

    doc.plan_status = "Pending Supervisor Approval"
    doc.workflow_state = "Planning Open"
    doc.plan_rejection_remark = None
    doc.save(ignore_permissions=True)

    try:
        from gdl_pms.email_service import notify_plan_submitted
        sup_email = _get_employee_email(doc.supervisor_snapshot)
        if sup_email:
            notify_plan_submitted(doc, sup_email)
    except Exception as e:
        frappe.logger().error(f"Failed sending plan submission email: {str(e)}")

    return "Sent for Supervisor Approval"


@frappe.whitelist()
def return_to_employee_with_edits(docname, remark=None):
    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_sys_mgr = "System Manager" in frappe.get_roles()

    if doc.plan_status == "Pending Supervisor Approval":
        if doc.supervisor_snapshot != user_emp and not is_sys_mgr:
            frappe.throw("Only the assigned Supervisor can perform this action.")
    elif doc.plan_status == "Pending Reviewer Approval":
        if doc.reviewer_snapshot != user_emp and not is_sys_mgr:
            frappe.throw("Only the assigned Reviewer can perform this action.")
    else:
        frappe.throw("Plan is not pending your approval.")

    if remark:
        doc.plan_revision_remark = remark
    doc._return_to_employee = True
    doc.save()

    try:
        from gdl_pms.email_service import notify_plan_returned
        emp_email = _get_employee_email(doc.employee)
        if emp_email:
            editor_role = "Supervisor" if doc.plan_status == "Pending Supervisor Approval" else "Reviewer"
            notify_plan_returned(doc, emp_email, remark, returned_by_role=editor_role)
    except Exception as e:
        frappe.logger().error(f"Failed sending plan return email: {str(e)}")

    return "Plan returned to Employee for analysis"


@frappe.whitelist()
def approve_plan(docname, comment=None):
    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_sys_mgr = "System Manager" in frappe.get_roles()

    approver_name = frappe.db.get_value("Employee", user_emp, "employee_name") if user_emp else frappe.session.user
    comment_suffix = f': "{comment}"' if comment else ""

    if doc.plan_status == "Pending Supervisor Approval":
        if doc.supervisor_snapshot != user_emp and not is_sys_mgr:
            frappe.throw("Only the assigned Supervisor can approve this plan.")
        if doc.reviewer_snapshot:
            doc.plan_status = "Pending Reviewer Approval"
            doc.workflow_state = "Planning Open"
            doc.add_comment("Comment", f"Performance Plan approved by Supervisor {approver_name} ({frappe.session.user}){comment_suffix}. Forwarded for Reviewer Approval.")
        else:
            doc.plan_status = "Approved"
            doc.workflow_state = "Monitoring"
            doc.add_comment("Comment", f"Performance Plan approved by Supervisor {approver_name} ({frappe.session.user}){comment_suffix}. Plan is now Approved & Active.")
            
    elif doc.plan_status == "Pending Reviewer Approval":
        if doc.reviewer_snapshot != user_emp and not is_sys_mgr:
            frappe.throw("Only the assigned Reviewer can approve this plan.")
        doc.plan_status = "Approved"
        doc.workflow_state = "Monitoring"
        doc.add_comment("Comment", f"Performance Plan approved by Reviewer {approver_name} ({frappe.session.user}){comment_suffix}. Plan is now Approved & Active.")
    else:
        frappe.throw("Plan is not pending your approval.")

    doc.save(ignore_permissions=True)

    try:
        from gdl_pms.email_service import notify_plan_approved, notify_plan_submitted
        if doc.plan_status == "Pending Reviewer Approval":
            rev_email = _get_employee_email(doc.reviewer_snapshot)
            if rev_email:
                notify_plan_submitted(doc, rev_email)
        elif doc.plan_status == "Approved":
            emp_email = _get_employee_email(doc.employee)
            if emp_email:
                notify_plan_approved(doc, emp_email)
    except Exception as e:
        frappe.logger().error(f"Failed sending plan approval email: {str(e)}")

    return "Plan Approved"


@frappe.whitelist()
def reject_plan(docname, remark):
    if not remark:
        frappe.throw("Return remark is mandatory.")
        
    doc = frappe.get_doc("PMS Appraisal", docname)
    user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    is_sys_mgr = "System Manager" in frappe.get_roles()

    if doc.plan_status == "Pending Supervisor Approval":
        if doc.supervisor_snapshot != user_emp and not is_sys_mgr:
            frappe.throw("Only the assigned Supervisor can return this plan.")
        role_label = "Supervisor"
    elif doc.plan_status == "Pending Reviewer Approval":
        if doc.reviewer_snapshot != user_emp and not is_sys_mgr:
            frappe.throw("Only the assigned Reviewer can return this plan.")
        role_label = "Reviewer"
    else:
        frappe.throw("Plan is not pending your approval.")

    rejector_name = frappe.db.get_value("Employee", user_emp, "employee_name") if user_emp else frappe.session.user
    doc.plan_status = "Returned"
    doc.workflow_state = "Planning Open"
    doc.plan_rejection_remark = remark
    doc.add_comment(
        "Comment",
        f"Performance Plan returned by {role_label} {rejector_name} ({frappe.session.user}). Return Reason: \"{remark}\""
    )
    doc.save(ignore_permissions=True)

    try:
        from gdl_pms.email_service import notify_plan_returned
        emp_email = _get_employee_email(doc.employee)
        if emp_email:
            notify_plan_returned(doc, emp_email, remark, returned_by_role=role_label)
    except Exception as e:
        frappe.logger().error(f"Failed sending plan return email: {str(e)}")

    return "Plan Returned"


@frappe.whitelist()
def return_plan(docname, remark):
    return reject_plan(docname, remark)


@frappe.whitelist()
def bulk_approve_plan(docnames):
    if isinstance(docnames, str):
        docnames = json.loads(docnames)
    
    approved_count = 0
    for docname in docnames:
        try:
            approve_plan(docname)
            approved_count += 1
        except Exception as e:
            frappe.log_error(f"Failed to bulk approve {docname}: {str(e)}")
            
    if approved_count > 0:
        frappe.db.commit()
    return f"Approved {approved_count} plans."


@frappe.whitelist()
def bulk_reject_plan(docnames, remark):
    if isinstance(docnames, str):
        docnames = json.loads(docnames)
        
    rejected_count = 0
    for docname in docnames:
        try:
            reject_plan(docname, remark)
            rejected_count += 1
        except Exception as e:
            frappe.log_error(f"Failed to bulk return {docname}: {str(e)}")
            
    if rejected_count > 0:
        frappe.db.commit()
    return f"Returned {rejected_count} plans."


@frappe.whitelist()
def bulk_return_plan(docnames, remark):
    return bulk_reject_plan(docnames, remark)


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    if user == "Administrator" or "System Manager" in frappe.get_roles(user) or "HR Manager" in frappe.get_roles(user) or "HR Admin" in frappe.get_roles(user):
        return ""

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        return "1=2"

    return f"""(`tabPMS Appraisal`.employee = '{employee}' or `tabPMS Appraisal`.supervisor_snapshot = '{employee}' or `tabPMS Appraisal`.reviewer_snapshot = '{employee}' or `tabPMS Appraisal`.supervisor_2_snapshot = '{employee}' or `tabPMS Appraisal`.employee in (select name from `tabEmployee` where supervisor_2 = '{employee}'))"""


def has_permission(doc, ptype="read", user=None):
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)
    if user == "Administrator" or "System Manager" in roles or "HR Manager" in roles or "HR Admin" in roles:
        return True

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        return False

    is_supervisor_2 = (doc.supervisor_2_snapshot == employee or frappe.db.get_value("Employee", doc.employee, "supervisor_2") == employee)
    is_primary_party = (doc.employee == employee or doc.supervisor_snapshot == employee or doc.reviewer_snapshot == employee)

    if ptype == "read":
        if is_primary_party or is_supervisor_2:
            return True
        return False
    else:
        # Non-read permissions (write, delete, create, submit, etc.)
        if is_supervisor_2 and not is_primary_party:
            return False
        if is_primary_party:
            return True
        return False


@frappe.whitelist()
def get_plan_history(docname):
    """
    Returns complete chronological audit history for a PMS Appraisal Performance Plan:
    1. Plan Creation & Initial Draft
    2. Employee Submissions for Approval
    3. Supervisor / Reviewer Re-edits / Analysis returns (Rule 4) with revision remarks
    4. Plan Approvals (Supervisor & Reviewer) with comments
    5. Plan Rejections (Supervisor & Reviewer) with rejection remarks
    6. Amendments (PMS Plan Amendment):
       - Creation / request date & reason
       - Supervisor & Reviewer amendment approval / rejection logs & remarks
       - Date applied to parent plan
    """
    if not docname or not frappe.db.exists("PMS Appraisal", docname):
        return []

    doc = frappe.get_doc("PMS Appraisal", docname)
    history = []

    def get_full_name(user_id):
        if not user_id:
            return ""
        full_name = frappe.db.get_value("User", user_id, "full_name")
        return full_name or user_id

    # 1. Plan Creation Event
    creator_name = get_full_name(doc.owner) or doc.employee_name or doc.employee
    history.append({
        "timestamp": str(doc.creation),
        "formatted_date": frappe.utils.format_datetime(doc.creation, "dd MMM yyyy, hh:mm a"),
        "event_type": "creation",
        "title": "Performance Plan Created",
        "actor_name": creator_name,
        "actor_role": "Employee",
        "badge_text": "Draft Created",
        "badge_color": "gray",
        "comment": "",
        "details": "Performance Plan initialized in Draft status.",
        "icon": "fa-file-text-o"
    })

    # 2. Extract Events from tabComment
    comments = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": "PMS Appraisal",
            "reference_name": docname
        },
        fields=["name", "content", "comment_by", "comment_email", "creation"],
        order_by="creation asc"
    )

    seen_approval_supervisor = False
    seen_approval_reviewer = False
    seen_rejection = False
    seen_re_edit = False

    for c in comments:
        content = (c.content or "").strip()
        if not content:
            continue

        c_time = str(c.creation)
        formatted_c_time = frappe.utils.format_datetime(c.creation, "dd MMM yyyy, hh:mm a")
        author_name = c.comment_by or get_full_name(c.comment_email) or c.comment_email or ""

        # A: Targets/weights modified by Supervisor or Reviewer (Rule 4)
        if "targets/weights were modified by" in content or "Returned to employee" in content or "Plan returned to Employee" in content:
            role = "Supervisor" if "Supervisor" in content else ("Reviewer" if "Reviewer" in content else "Supervisor")
            note = ""
            if '": "' in content:
                parts = content.split('": "', 1)
                note = parts[1].rsplit('"', 1)[0]
            elif 'Reason: "' in content:
                parts = content.split('Reason: "', 1)
                note = parts[1].rsplit('"', 1)[0]
            elif ': "' in content:
                parts = content.split(': "', 1)
                note = parts[1].rsplit('"', 1)[0]

            seen_re_edit = True
            history.append({
                "timestamp": c_time,
                "formatted_date": formatted_c_time,
                "event_type": "re_edit",
                "title": f"Plan Re-edited / Returned by {role}",
                "actor_name": author_name,
                "actor_role": role,
                "badge_text": f"Re-edited by {role}",
                "badge_color": "orange",
                "comment": note,
                "details": content,
                "icon": "fa-pencil-square-o"
            })

        # B: Submissions for Approval
        elif "submitted the plan for approval" in content or "submitted for approval" in content or "re-submitted the plan" in content:
            history.append({
                "timestamp": c_time,
                "formatted_date": formatted_c_time,
                "event_type": "submission",
                "title": "Submitted for Approval",
                "actor_name": author_name or doc.employee_name or doc.employee,
                "actor_role": "Employee",
                "badge_text": "Submitted",
                "badge_color": "blue",
                "comment": "",
                "details": content,
                "icon": "fa-paper-plane-o"
            })

        # C: Approvals
        elif "approved by Supervisor" in content:
            seen_approval_supervisor = True
            comment_text = ""
            if 'Comment: "' in content:
                comment_text = content.split('Comment: "', 1)[1].rsplit('"', 1)[0]
            elif ': "' in content:
                comment_text = content.split(': "', 1)[1].rsplit('"', 1)[0]

            history.append({
                "timestamp": c_time,
                "formatted_date": formatted_c_time,
                "event_type": "supervisor_approval",
                "title": "Plan Approved by Supervisor",
                "actor_name": author_name or doc.supervisor_name or doc.supervisor_snapshot,
                "actor_role": "Supervisor",
                "badge_text": "Supervisor Approved",
                "badge_color": "green",
                "comment": comment_text,
                "details": content,
                "icon": "fa-check-circle-o"
            })

        elif "approved by Reviewer" in content:
            seen_approval_reviewer = True
            comment_text = ""
            if 'Comment: "' in content:
                comment_text = content.split('Comment: "', 1)[1].rsplit('"', 1)[0]
            elif ': "' in content:
                comment_text = content.split(': "', 1)[1].rsplit('"', 1)[0]

            history.append({
                "timestamp": c_time,
                "formatted_date": formatted_c_time,
                "event_type": "reviewer_approval",
                "title": "Plan Approved by Reviewer",
                "actor_name": author_name or doc.reviewer_name or doc.reviewer_snapshot,
                "actor_role": "Reviewer",
                "badge_text": "Reviewer Approved",
                "badge_color": "green",
                "comment": comment_text,
                "details": content,
                "icon": "fa-check-circle"
            })

        # D: Returns / Rejections
        elif "rejected by" in content or "Plan rejected" in content or "returned by" in content or "Plan returned" in content:
            role = "Reviewer" if "Reviewer" in content else "Supervisor"
            seen_rejection = True
            rejection_reason = ""
            if 'Reason: "' in content:
                rejection_reason = content.split('Reason: "', 1)[1].rsplit('"', 1)[0]
            elif 'Remark: "' in content:
                rejection_reason = content.split('Remark: "', 1)[1].rsplit('"', 1)[0]
            elif ': "' in content:
                rejection_reason = content.split(': "', 1)[1].rsplit('"', 1)[0]

            history.append({
                "timestamp": c_time,
                "formatted_date": formatted_c_time,
                "event_type": "rejection",
                "title": f"Plan Returned by {role}",
                "actor_name": author_name,
                "actor_role": role,
                "badge_text": f"Returned by {role}",
                "badge_color": "orange",
                "comment": rejection_reason or content,
                "details": content,
                "icon": "fa-undo"
            })

        # E: Amendment applied comment
        elif "Plan Amendment #" in content:
            history.append({
                "timestamp": c_time,
                "formatted_date": formatted_c_time,
                "event_type": "amendment_applied",
                "title": "Plan Amendment Applied",
                "actor_name": author_name or "System",
                "actor_role": "System",
                "badge_text": "Amendment Applied",
                "badge_color": "teal",
                "comment": "",
                "details": content,
                "icon": "fa-refresh"
            })

    # 3. Amendments from tabPMS Plan Amendment & Child Logs
    amendments = frappe.get_all(
        "PMS Plan Amendment",
        filters={"performance_plan": docname},
        fields=["name", "amendment_number", "revision_date", "reason", "status", "supervisor_remark", "reviewer_remark", "creation", "owner"],
        order_by="amendment_number asc"
    )

    for amd in amendments:
        logs = frappe.get_all(
            "PMS Amendment Log",
            filters={"parent": amd.name},
            fields=["name", "action", "user", "role", "timestamp", "status", "remark"],
            order_by="timestamp asc"
        )

        if logs:
            for l in logs:
                l_time = str(l.timestamp or amd.creation)
                formatted_l_time = frappe.utils.format_datetime(l.timestamp or amd.creation, "dd MMM yyyy, hh:mm a")
                u_name = get_full_name(l.user) or l.user or ""
                act = l.action or ""
                b_color = "purple"
                b_text = f"Amendment #{amd.amendment_number}"
                icon = "fa-pencil"

                if "Approved" in act:
                    b_color = "green"
                    b_text = f"Amendment #{amd.amendment_number} Approved"
                    icon = "fa-check"
                elif "Rejected" in act or "Returned" in act:
                    b_color = "orange"
                    b_text = f"Amendment #{amd.amendment_number} Returned"
                    icon = "fa-undo"
                elif "Submitted" in act:
                    b_color = "purple"
                    b_text = f"Amendment #{amd.amendment_number} Requested"
                    icon = "fa-file-text"

                history.append({
                    "timestamp": l_time,
                    "formatted_date": formatted_l_time,
                    "event_type": "amendment_log",
                    "title": f"Plan Amendment #{amd.amendment_number} ({amd.name}): {act}",
                    "actor_name": u_name,
                    "actor_role": l.role or "Employee",
                    "badge_text": b_text,
                    "badge_color": b_color,
                    "comment": l.remark or "",
                    "details": f"Reason: {amd.reason}" if amd.reason else "",
                    "link": f"/app/pms-plan-amendment/{amd.name}",
                    "icon": icon
                })
        else:
            # Fallback if no child logs
            amd_time = str(amd.creation)
            formatted_amd_time = frappe.utils.format_datetime(amd.creation, "dd MMM yyyy, hh:mm a")
            creator = get_full_name(amd.owner) or amd.owner
            history.append({
                "timestamp": amd_time,
                "formatted_date": formatted_amd_time,
                "event_type": "amendment",
                "title": f"Plan Amendment #{amd.amendment_number} ({amd.name})",
                "actor_name": creator,
                "actor_role": "Employee",
                "badge_text": f"Amendment: {amd.status}",
                "badge_color": "green" if amd.status == "Approved" else ("red" if amd.status == "Rejected" else "purple"),
                "comment": amd.reason or "",
                "details": f"Supervisor Remark: {amd.supervisor_remark or 'None'} | Reviewer Remark: {amd.reviewer_remark or 'None'}",
                "link": f"/app/pms-plan-amendment/{amd.name}",
                "icon": "fa-file-text-o"
            })

    # 4. State Fallbacks for Older Records
    if doc.plan_status in ["Approved", "Monitoring", "Appraisal Open", "Appraisal Completed"]:
        if not seen_approval_supervisor:
            history.append({
                "timestamp": str(doc.modified or doc.creation),
                "formatted_date": frappe.utils.format_datetime(doc.modified or doc.creation, "dd MMM yyyy, hh:mm a"),
                "event_type": "supervisor_approval",
                "title": "Plan Approved by Supervisor",
                "actor_name": doc.supervisor_name or doc.supervisor_snapshot or "Supervisor",
                "actor_role": "Supervisor",
                "badge_text": "Supervisor Approved",
                "badge_color": "green",
                "comment": "",
                "details": "Performance Plan approved by Supervisor.",
                "icon": "fa-check-circle-o"
            })
        if doc.reviewer_snapshot and not seen_approval_reviewer:
            history.append({
                "timestamp": str(doc.modified or doc.creation),
                "formatted_date": frappe.utils.format_datetime(doc.modified or doc.creation, "dd MMM yyyy, hh:mm a"),
                "event_type": "reviewer_approval",
                "title": "Plan Approved by Reviewer",
                "actor_name": doc.reviewer_name or doc.reviewer_snapshot or "Reviewer",
                "actor_role": "Reviewer",
                "badge_text": "Reviewer Approved",
                "badge_color": "green",
                "comment": "",
                "details": "Performance Plan approved by Reviewer. Plan Activated.",
                "icon": "fa-check-circle"
            })

    if doc.plan_status in ["Rejected", "Returned"] and not seen_rejection:
        history.append({
            "timestamp": str(doc.modified or doc.creation),
            "formatted_date": frappe.utils.format_datetime(doc.modified or doc.creation, "dd MMM yyyy, hh:mm a"),
            "event_type": "rejection",
            "title": "Plan Returned",
            "actor_name": doc.supervisor_name or doc.reviewer_name or "Approver",
            "actor_role": "Supervisor/Reviewer",
            "badge_text": "Plan Returned",
            "badge_color": "orange",
            "comment": doc.plan_rejection_remark or "Return remark not recorded",
            "details": doc.plan_rejection_remark or "",
            "icon": "fa-undo"
        })

    if doc.plan_status == "Draft" and doc.plan_revision_remark and not seen_re_edit:
        history.append({
            "timestamp": str(doc.modified or doc.creation),
            "formatted_date": frappe.utils.format_datetime(doc.modified or doc.creation, "dd MMM yyyy, hh:mm a"),
            "event_type": "re_edit",
            "title": f"Plan Re-edited / Returned by {doc.revised_by_role or 'Supervisor'}",
            "actor_name": doc.supervisor_name or doc.reviewer_name or (doc.revised_by_role or "Supervisor"),
            "actor_role": doc.revised_by_role or "Supervisor",
            "badge_text": f"Re-edited by {doc.revised_by_role or 'Supervisor'}",
            "badge_color": "orange",
            "comment": doc.plan_revision_remark,
            "details": "Targets/weights adjusted and returned to Employee for analysis.",
            "icon": "fa-pencil-square-o"
        })

    # 5. Sort chronologically (oldest to newest)
    history.sort(key=lambda x: str(x.get("timestamp") or ""))
    return history
