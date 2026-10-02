# Copyright (c) 2026, GDL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class PERCCase(Document):
    def validate(self):
        if self.status == "Resolved" and (self.final_score is None or self.final_score == ""):
            frappe.throw("Final Score is mandatory when resolving a PERC Case.")

    def on_update(self):
        if self.status == "Resolved" and self.final_score is not None and self.appraisal:
            from gdl_pms.scoring_engine import apply_perc_override
            apply_perc_override(self.appraisal, flt(self.final_score))
