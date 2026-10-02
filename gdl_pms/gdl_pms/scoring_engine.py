import frappe
from frappe.utils import flt

GRADE_WEIGHTS = {
    "PS_CS": {"work": 60, "competency": 40},
    "OS_ESP": {"work": 50, "competency": 50},
}

RATING_BANDS = [
    (90, 100, "Outstanding Performance"),
    (80, 89.99, "Exceeds Expectations"),
    (70, 79.99, "Meets Expectations"),
    (60, 69.99, "Needs Improvement"),
    (0, 59.99, "Unsatisfactory Performance"),
]

def get_band(total):
    total = flt(total, 2)
    for lo, hi, label in RATING_BANDS:
        if lo <= total <= hi:
            return label
    if total > 100:
        return "Outstanding Performance"
    return "Unrated"

def compute_final_score(appraisal):
    """
    Computes provisional or final score based on stage:
    - If in Reviewer phase or Disputed, uses reviewer scores (falling back to supervisor scores).
    - Otherwise (Supervisor evaluation), uses supervisor scores.
    """
    is_reviewer_phase = (
        appraisal.appraisal_status in [
            "Reviewer Resolved - Pending Employee Decision",
            "Under PERC Review"
        ]
        or getattr(appraisal, "dispute_flag", 0) == 1
    )

    work_score = 0.0
    for t in appraisal.targets:
        if is_reviewer_phase and (t.reviewer_score is not None and flt(t.reviewer_score) > 0):
            work_score += flt(t.reviewer_score)
        else:
            work_score += flt(t.supervisor_score or 0)
            
    comp_score = 0.0
    for c in appraisal.competencies:
        if is_reviewer_phase and (c.reviewer_rating is not None and flt(c.reviewer_rating) > 0):
            comp_score += flt(c.reviewer_rating)
        else:
            comp_score += flt(c.supervisor_rating or 0)
            
    total = flt(work_score + comp_score, 2)
    appraisal.total_score = total
    appraisal.rating_band = get_band(total)
    
    if total < 70:
        trigger_pip(appraisal.employee)
        
    return total

def trigger_pip(employee):
    frappe.logger().info(f"PIP triggered for employee {employee}")

def apply_perc_override(appraisal_name, final_score):
    """Called from PERC Case when a case is Resolved."""
    doc = frappe.get_doc("PMS Appraisal", appraisal_name)
    doc.total_score = flt(final_score, 2)
    doc.rating_band = get_band(doc.total_score)
    doc.appraisal_status = "Appraisal Accepted"
    doc.add_comment("Comment", f"PERC Committee determined final score: {doc.total_score} ({doc.rating_band}).")
    doc.save(ignore_permissions=True)
    frappe.db.commit()
