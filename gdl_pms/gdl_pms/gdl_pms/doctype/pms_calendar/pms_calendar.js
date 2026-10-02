// Copyright (c) 2026, GDL and contributors
// For license information, please see license.txt

frappe.ui.form.on("PMS Calendar", {
	refresh: function(frm) {
		render_timeline_overview(frm);

		if (!frm.is_new() && frm.doc.calendar_year) {
			frm.page.add_inner_button(__("View Appraisal Cycles ({0})", [frm.doc.calendar_year]), function() {
				frappe.set_route("List", "PMS Appraisal Cycle", {
					calendar_year: frm.doc.calendar_year
				});
			}, __("Actions"));

			frm.page.add_inner_button(__("Create Appraisal Cycle"), function() {
				frappe.new_doc("PMS Appraisal Cycle", {
					calendar_year: frm.doc.calendar_year,
					cycle_name: "PMS Appraisal Cycle " + frm.doc.calendar_year,
					start_date: frm.doc.calendar_year + "-01-01",
					end_date: frm.doc.calendar_year + "-12-31"
				});
			}, __("Actions")).addClass("btn-primary text-white");
		}
	},

	calendar_year: function(frm) {
		render_timeline_overview(frm);
	},

	employee_submission_deadline: function(frm) {
		render_timeline_overview(frm);
	},

	supervisor_approval_deadline: function(frm) {
		render_timeline_overview(frm);
	},

	reviewer_approval_deadline: function(frm) {
		render_timeline_overview(frm);
	},

	enable_appraisal_timeline: function(frm) {
		render_timeline_overview(frm);
	},

	self_scoring_start_date: function(frm) {
		render_timeline_overview(frm);
	},

	self_scoring_end_date: function(frm) {
		render_timeline_overview(frm);
	}
});

function render_timeline_overview(frm) {
	if (!frm.fields_dict.timeline_summary_html || !frm.fields_dict.timeline_summary_html.$wrapper) return;

	var year = frm.doc.calendar_year || "---";
	var emp_sub = frm.doc.employee_submission_deadline ? frappe.datetime.str_to_user(frm.doc.employee_submission_deadline) : "Not Set";
	var sup_app = frm.doc.supervisor_approval_deadline ? frappe.datetime.str_to_user(frm.doc.supervisor_approval_deadline) : "Not Set";
	var rev_app = frm.doc.reviewer_approval_deadline ? frappe.datetime.str_to_user(frm.doc.reviewer_approval_deadline) : "Not Set";

	var has_appr = frm.doc.enable_appraisal_timeline;
	var self_start = frm.doc.self_scoring_start_date ? frappe.datetime.str_to_user(frm.doc.self_scoring_start_date) : "Not Set";
	var self_end = frm.doc.self_scoring_end_date ? frappe.datetime.str_to_user(frm.doc.self_scoring_end_date) : "Not Set";

	var html = `
		<div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px;">
			<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
				<div style="font-weight: 700; font-size: 15px; color: #0f172a; display: flex; align-items: center; gap: 8px;">
				  Performance Management Calendar & Timelines: <span style="color: #2563eb; font-weight: 800;">${frappe.utils.escape_html(year)}</span>
				</div>
				<span style="background: #e0e7ff; color: #3730a3; font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 6px;">
					Annual Period: 01-Jan-${frappe.utils.escape_html(year)} to 31-Dec-${frappe.utils.escape_html(year)}
				</span>
			</div>

			<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;">
				<!-- Plan Milestone 1 -->
				<div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #0284c7; border-radius: 8px; padding: 10px 14px;">
					<div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Employee Plan Submission</div>
					<div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-top: 3px;">${emp_sub}</div>
					<div style="font-size: 11px; color: #0284c7;">Final date for employee submission</div>
				</div>

				<!-- Plan Milestone 2 -->
				<div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #16a34a; border-radius: 8px; padding: 10px 14px;">
					<div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Supervisor Approval</div>
					<div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-top: 3px;">${sup_app}</div>
					<div style="font-size: 11px; color: #16a34a;">Final date for supervisor review</div>
				</div>

				<!-- Plan Milestone 3 -->
				<div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #9333ea; border-radius: 8px; padding: 10px 14px;">
					<div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Reviewer Approval</div>
					<div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-top: 3px;">${rev_app}</div>
					<div style="font-size: 11px; color: #9333ea;">Final date for reviewer approval</div>
				</div>

				<!-- Appraisal Milestone -->
				${has_appr ? `
				<div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #ea580c; border-radius: 8px; padding: 10px 14px;">
					<div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;">Self-Scoring Window</div>
					<div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-top: 3px;">${self_start} &rarr; ${self_end}</div>
					<div style="font-size: 11px; color: #ea580c;">Employee self-assessment timeline</div>
				</div>
				` : ''}
			</div>
		</div>
	`;

	frm.fields_dict.timeline_summary_html.$wrapper.html(html);
}
