function update_grade_group_display(frm, emp_info) {
	let grade = frm.doc.grade_group || (emp_info && emp_info.grade_group) || "";
	if (!grade) {
		frm.dashboard.clear_headline();
		return;
	}

	let is_ps = (grade === "PS_CS");
	let is_os = (grade === "OS_ESP");
	let code = is_ps ? "PS" : (is_os ? "OS" : grade);
	let cat_title = is_ps ? "PS (Professional Staff)" : (is_os ? "OS (Operating Staff)" : grade);
	let badge_class = is_ps ? "blue" : "orange";
	let target_wt = is_ps ? 60 : 50;
	let comp_wt = is_ps ? 40 : 50;

	frm.set_df_property("grade_group", "hidden", 0);
	frm.set_df_property(
		"grade_group",
		"description",
		__("<span style='font-weight: 600; color: #1f2937;'>Category: {0}</span> &bull; Required Target Weight: <b>{1}%</b> | Competencies Weight: <b>{2}%</b>", [cat_title, target_wt, comp_wt])
	);

	frm.set_df_property(
		"targets",
		"description",
		__("For <b>{0}</b> category, total Target Weights must sum to exactly <b>{1}%</b>.", [code, target_wt])
	);

	// Dashboard headline banner
	frm.dashboard.clear_headline();
	frm.dashboard.set_headline(`
		<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; padding: 4px 0;">
			<div style="display: flex; align-items: center; gap: 10px;">
				<span class="indicator-pill ${badge_class} bold" style="font-size: 13px; padding: 4px 10px; border-radius: 6px;">
					Grade Group: ${grade} (${code})
				</span>
				<span style="font-size: 13px; font-weight: 600; color: var(--text-color);">
					Classification: ${cat_title}
				</span>
			</div>
			<div style="font-size: 12px; color: var(--text-muted); display: flex; gap: 16px;">
				<span>Required Targets Weight: <strong style="color: var(--text-color);">${target_wt}%</strong></span>
				<span>Competencies Weight: <strong style="color: var(--text-color);">${comp_wt}%</strong></span>
			</div>
		</div>
	`);
}

function render_appraisal_headline(frm) {
	let status = frm.doc.appraisal_status || "Self-Assessment Pending";
	let total_score = frm.doc.total_score != null ? flt(frm.doc.total_score, 2) : "--";
	let band = frm.doc.rating_band || "Unrated";
	let dispute = frm.doc.dispute_flag ? `<span class="indicator-pill red bold" style="margin-left: 6px;">Disputed</span>` : "";
	let locked = frm.doc.locked ? `<span class="indicator-pill green bold" style="margin-left: 6px;"><i class="fa fa-lock"></i> Locked</span>` : "";

	let badge_class = "blue";
	if (status === "Appraisal Accepted" || status === "Finalized & Locked") badge_class = "green";
	else if (status.includes("Dispute") || status.includes("PERC")) badge_class = "orange";
	else if (status.includes("Supervisor")) badge_class = "purple";

	let info_message = "";
	if (status === "Self-Assessment Pending") {
		info_message = __("Employee Self-Assessment is active. Enter self scores, remarks, upload supporting evidence, and submit.");
	} else if (status === "Pending Supervisor Review") {
		info_message = __("Awaiting Supervisor evaluation and scoring.");
	} else if (status === "Pending Employee Acceptance") {
		info_message = __("Supervisor evaluation completed. Employee must review and either Accept or Raise Dispute.");
	} else if (status === "Disputed - Pending Reviewer") {
		info_message = __("Dispute escalated to Reviewer ({0}). Reason: \"{1}\"", [frm.doc.reviewer_name || frm.doc.reviewer_snapshot, frm.doc.dispute_reason || ""]);
	} else if (status === "Reviewer Resolved - Pending Employee Decision") {
		info_message = __("Reviewer resolved the dispute. Employee can Accept the decision or Request PERC escalation.");
	} else if (status === "Under PERC Review") {
		info_message = __("Case submitted to Performance Evaluation Review Committee ({0}). Awaiting committee hearing & final score.", [frm.doc.perc_case || ""]);
	} else if (status === "Appraisal Accepted") {
		info_message = __("Appraisal evaluation accepted. Ready for HR Admin final lock.");
	} else if (status === "Finalized & Locked") {
		info_message = __("Appraisal finalized and permanently locked by HR Admin. Final Score: <b>{0}</b> ({1}).", [total_score, band]);
	}

	frm.dashboard.clear_headline();
	frm.dashboard.set_headline(`
		<div style="padding: 6px 0;">
			<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 8px;">
				<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
					<span class="indicator-pill ${badge_class} bold" style="font-size: 13px; padding: 4px 10px; border-radius: 6px;">
						${status}
					</span>
					${dispute}
					${locked}
					<span style="font-size: 13px; font-weight: 600; color: var(--text-color); margin-left: 6px;">
						Employee: ${frm.doc.employee_name} (${frm.doc.employee})
					</span>
				</div>
				<div style="display: flex; align-items: center; gap: 16px; font-size: 13px;">
					<span>Total Score: <strong style="color: #15803d; font-size: 15px;">${total_score}</strong></span>
					<span>Rating Band: <strong style="color: var(--text-color);">${band}</strong></span>
				</div>
			</div>
			<div style="font-size: 12.5px; color: var(--text-muted); background: rgba(0,0,0,0.02); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.05);">
				<i class="fa fa-info-circle text-info" style="margin-right: 6px;"></i> ${info_message}
			</div>
		</div>
	`);
}

function toggle_scoring_visibility(frm, is_appraisal) {
	const target_scoring_cols = [
		"self_score", "self_remark", "evidence",
		"supervisor_score", "supervisor_remark",
		"reviewer_score", "reviewer_remark"
	];
	const comp_scoring_cols = [
		"self_rating", "self_remark",
		"supervisor_rating", "supervisor_remark",
		"reviewer_rating", "reviewer_remark"
	];

	const parent_scoring_fields = [
		"appraisal_status", "total_score", "rating_band",
		"dispute_flag", "dispute_reason", "locked", "perc_case",
		"employee_overall_remarks", "supervisor_overall_remarks", "reviewer_overall_remarks"
	];

	if (!is_appraisal) {
		// HIDE ALL SCORING FIELDS IN PERFORMANCE PLAN MODE
		$('body').addClass('gdl-pms-plan-mode').removeClass('gdl-pms-appraisal-mode gdl-pms-self-assessment-stage');
		if (frm.page && frm.page.wrapper) {
			frm.page.wrapper.addClass('gdl-pms-plan-mode').removeClass('gdl-pms-appraisal-mode gdl-pms-self-assessment-stage');
		}

		parent_scoring_fields.forEach(f => {
			try {
				frm.set_df_property(f, "hidden", 1);
				frm.toggle_display(f, false);
			} catch(e){}
		});

		if (frm.fields_dict["targets"] && frm.fields_dict["targets"].grid) {
			let tg = frm.fields_dict["targets"].grid;
			try {
				tg.cannot_add_rows = false;
				tg.update_docfield_property("target_description", "read_only", 0);
				tg.update_docfield_property("weight", "read_only", 0);
				tg.update_docfield_property("remark", "hidden", 1);
				tg.update_docfield_property("self_remark", "hidden", 1);
				if (tg.set_column_disp_in_list_view) {
					tg.set_column_disp_in_list_view(["remark", ...target_scoring_cols], false);
				}
				tg.set_column_disp(["remark", ...target_scoring_cols], false);
			} catch(e){}
		}
		if (frm.fields_dict["competencies"] && frm.fields_dict["competencies"].grid) {
			let cg = frm.fields_dict["competencies"].grid;
			try {
				cg.cannot_add_rows = true;
				cg.update_docfield_property("self_remark", "hidden", 1);
				if (cg.set_column_disp_in_list_view) cg.set_column_disp_in_list_view(comp_scoring_cols, false);
				cg.set_column_disp(comp_scoring_cols, false);
			} catch(e){}
		}
	} else {
		// IN APPRAISAL MODE: SHOW SCORING FIELDS APPROPRIATE TO CURRENT STATE
		$('body').removeClass('gdl-pms-plan-mode').addClass('gdl-pms-appraisal-mode');
		if (frm.page && frm.page.wrapper) {
			frm.page.wrapper.removeClass('gdl-pms-plan-mode').addClass('gdl-pms-appraisal-mode');
		}

		let app_status = frm.doc.appraisal_status || "Self-Assessment Pending";
		let is_self = (app_status === "Self-Assessment Pending");

		if (is_self) {
			$('body').addClass('gdl-pms-self-assessment-stage');
			if (frm.page && frm.page.wrapper) {
				frm.page.wrapper.addClass('gdl-pms-self-assessment-stage');
			}
		} else {
			$('body').removeClass('gdl-pms-self-assessment-stage');
			if (frm.page && frm.page.wrapper) {
				frm.page.wrapper.removeClass('gdl-pms-self-assessment-stage');
			}
		}

		frm.set_df_property("appraisal_status", "hidden", 0);
		frm.toggle_display("appraisal_status", true);
		frm.set_df_property("total_score", "hidden", 0);
		frm.toggle_display("total_score", true);
		frm.set_df_property("rating_band", "hidden", 0);
		frm.toggle_display("rating_band", true);

		frm.set_df_property("employee_overall_remarks", "hidden", 0);
		frm.toggle_display("employee_overall_remarks", true);
		frm.set_df_property("supervisor_overall_remarks", "hidden", is_self ? 1 : 0);
		frm.toggle_display("supervisor_overall_remarks", !is_self);
		frm.set_df_property("reviewer_overall_remarks", "hidden", (is_self || app_status === "Pending Supervisor Review") ? 1 : 0);
		frm.toggle_display("reviewer_overall_remarks", (!is_self && app_status !== "Pending Supervisor Review"));

		let show_rev = (app_status.includes("Reviewer") || app_status.includes("PERC") || app_status === "Appraisal Accepted" || app_status === "Finalized & Locked");

		if (frm.fields_dict["targets"] && frm.fields_dict["targets"].grid) {
			let tg = frm.fields_dict["targets"].grid;
			let show_super = (!is_self);
			try {
				tg.cannot_add_rows = true;
				tg.update_docfield_property("remark", "hidden", 1);
				tg.update_docfield_property("self_remark", "hidden", 1);
				if (tg.set_column_disp_in_list_view) {
					tg.set_column_disp_in_list_view(["remark", "self_remark"], false);
					tg.set_column_disp_in_list_view(["self_score"], true);
					tg.set_column_disp_in_list_view(["supervisor_score", "supervisor_remark"], show_super);
					tg.set_column_disp_in_list_view(["reviewer_score"], show_rev);
				}
				tg.set_column_disp(["remark", "self_remark"], false);
				tg.set_column_disp(["self_score", "evidence"], true);
				tg.set_column_disp(["supervisor_score", "supervisor_remark"], show_super);
				tg.set_column_disp(["reviewer_score", "reviewer_remark"], show_rev);
			} catch(e){}
		}

		if (frm.fields_dict["competencies"] && frm.fields_dict["competencies"].grid) {
			let cg = frm.fields_dict["competencies"].grid;
			let show_super = (!is_self);
			try {
				cg.cannot_add_rows = true;
				cg.update_docfield_property("self_remark", "hidden", 1);
				if (cg.set_column_disp_in_list_view) {
					cg.set_column_disp_in_list_view(["self_remark"], false);
					cg.set_column_disp_in_list_view(["self_rating"], true);
					cg.set_column_disp_in_list_view(["supervisor_rating", "supervisor_remark"], show_super);
					cg.set_column_disp_in_list_view(["reviewer_rating"], show_rev);
				}
				cg.set_column_disp(["self_remark"], false);
				cg.set_column_disp(["self_rating"], true);
				cg.set_column_disp(["supervisor_rating", "supervisor_remark"], show_super);
				cg.set_column_disp(["reviewer_rating", "reviewer_remark"], show_rev);
			} catch(e){}
		}
	}
}

function apply_scoring_permissions(frm, app_status, is_supervisor, is_reviewer, is_employee, is_admin) {
	if (!frm.fields_dict["targets"] || !frm.fields_dict["targets"].grid) return;
	let tg = frm.fields_dict["targets"].grid;
	let cg = frm.fields_dict["competencies"] ? frm.fields_dict["competencies"].grid : null;

	let is_self_stage = (app_status === "Self-Assessment Pending");
	let is_sup_stage = (app_status === "Pending Supervisor Review");
	let is_rev_stage = (app_status === "Disputed - Pending Reviewer");

	let can_edit_self = (is_self_stage && (is_employee || is_admin));
	let can_edit_sup = (is_sup_stage && (is_supervisor || is_admin));
	let can_edit_rev = (is_rev_stage && (is_reviewer || is_admin));

	let target_ro = {
		target_description: 1,
		weight: 1,
		remark: 1,
		self_score: can_edit_self ? 0 : 1,
		self_remark: can_edit_self ? 0 : 1,
		evidence: can_edit_self ? 0 : 1,
		supervisor_score: can_edit_sup ? 0 : 1,
		supervisor_remark: can_edit_sup ? 0 : 1,
		reviewer_score: can_edit_rev ? 0 : 1,
		reviewer_remark: can_edit_rev ? 0 : 1
	};

	let comp_ro = {
		competency: 1,
		weight: 1,
		self_rating: can_edit_self ? 0 : 1,
		self_remark: can_edit_self ? 0 : 1,
		supervisor_rating: can_edit_sup ? 0 : 1,
		supervisor_remark: can_edit_sup ? 0 : 1,
		reviewer_rating: can_edit_rev ? 0 : 1,
		reviewer_remark: can_edit_rev ? 0 : 1
	};

	Object.keys(target_ro).forEach(fn => {
		let ro = target_ro[fn];
		try {
			if (tg.docfields) {
				let df = tg.docfields.find(d => d.fieldname === fn);
				if (df) df.read_only = ro;
			}
			if (frappe.meta.docfield_map["PMS Target"] && frappe.meta.docfield_map["PMS Target"][fn]) {
				frappe.meta.docfield_map["PMS Target"][fn].read_only = ro;
			}
			if (tg.visible_columns) {
				tg.visible_columns.forEach(col => {
					if (col[0] && col[0].fieldname === fn) col[0].read_only = ro;
				});
			}
			if (tg.grid_rows) {
				tg.grid_rows.forEach(row => {
					if (row.columns_list) {
						row.columns_list.forEach(c => {
							if (c.df && c.df.fieldname === fn) {
								c.df.read_only = ro;
								if (c.field && c.field.df) {
									c.field.df.read_only = ro;
									c.field.refresh && c.field.refresh();
								}
							}
						});
					}
					if (row.docfields) {
						let rdf = row.docfields.find(d => d.fieldname === fn);
						if (rdf) rdf.read_only = ro;
					}
				});
			}
		} catch(e) {}
	});

	if (cg) {
		Object.keys(comp_ro).forEach(fn => {
			let ro = comp_ro[fn];
			try {
				if (cg.docfields) {
					let df = cg.docfields.find(d => d.fieldname === fn);
					if (df) df.read_only = ro;
				}
				if (frappe.meta.docfield_map["PMS Competency Score"] && frappe.meta.docfield_map["PMS Competency Score"][fn]) {
					frappe.meta.docfield_map["PMS Competency Score"][fn].read_only = ro;
				}
				if (cg.visible_columns) {
					cg.visible_columns.forEach(col => {
						if (col[0] && col[0].fieldname === fn) col[0].read_only = ro;
					});
				}
				if (cg.grid_rows) {
					cg.grid_rows.forEach(row => {
						if (row.columns_list) {
							row.columns_list.forEach(c => {
								if (c.df && c.df.fieldname === fn) {
									c.df.read_only = ro;
									if (c.field && c.field.df) {
										c.field.df.read_only = ro;
										c.field.refresh && c.field.refresh();
									}
								}
							});
						}
						if (row.docfields) {
							let rdf = row.docfields.find(d => d.fieldname === fn);
							if (rdf) rdf.read_only = ro;
						}
					});
				}
			} catch(e) {}
		});
	}
}

function sync_employee_details(frm, employee, callback) {

	if (!employee) {
		frappe.call({
			method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.get_current_employee",
			callback: function(r) {
				if (r && r.message && r.message.name) {
					frm.set_value("employee", r.message.name).then(() => {
						apply_employee_data(frm, r.message, callback);
					});
				}
			}
		});
	} else {
		frappe.call({
			method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.get_employee_details",
			args: { employee: employee },
			callback: function(r) {
				if (r && r.message) {
					apply_employee_data(frm, r.message, callback);
				}
			}
		});
	}
}

function apply_employee_data(frm, data, callback) {
	let promises = [];
	if (data.employee_name && frm.doc.employee_name !== data.employee_name) {
		promises.push(frm.set_value("employee_name", data.employee_name));
	}
	if (data.grade_group && frm.doc.grade_group !== data.grade_group) {
		promises.push(frm.set_value("grade_group", data.grade_group));
	}
	if (data.reports_to && frm.doc.supervisor_snapshot !== data.reports_to) {
		promises.push(frm.set_value("supervisor_snapshot", data.reports_to));
	}
	if (data.reviewer && frm.doc.reviewer_snapshot !== data.reviewer) {
		promises.push(frm.set_value("reviewer_snapshot", data.reviewer));
	}
	if (data.supervisor_2 && frm.doc.supervisor_2_snapshot !== data.supervisor_2) {
		promises.push(frm.set_value("supervisor_2_snapshot", data.supervisor_2));
	}

	Promise.all(promises).then(() => {
		frm.refresh_field("employee_name");
		frm.refresh_field("grade_group");
		frm.refresh_field("supervisor_snapshot");
		frm.refresh_field("supervisor_name");
		frm.refresh_field("reviewer_snapshot");
		frm.refresh_field("reviewer_name");
		frm.refresh_field("supervisor_2_snapshot");
		frm.refresh_field("supervisor_2_name");

		if (data.supervisor_name) {
			frm.set_df_property("supervisor_snapshot", "description", `<b style="color: var(--text-color); font-size: 13px;">${data.supervisor_name}</b>`);
		}
		if (data.reviewer_name) {
			frm.set_df_property("reviewer_snapshot", "description", `<b style="color: var(--text-color); font-size: 13px;">${data.reviewer_name}</b>`);
		}
		if (data.supervisor_2_name) {
			frm.set_df_property("supervisor_2_snapshot", "description", `<b style="color: var(--text-color); font-size: 13px;">${data.supervisor_2_name}</b>`);
		}

		// Initialize default competencies if empty and new/draft
		if ((frm.is_new() || frm.doc.plan_status === "Draft") && (!frm.doc.competencies || frm.doc.competencies.length === 0)) {
			let weight = data.grade_group === "PS_CS" ? 8 : 10;
			let competencies = [
				"Job Knowledge & Skills",
				"Quality of Work",
				"Communication & Teamwork",
				"Initiative & Problem Solving",
				"Attendance & Punctuality"
			];
			frm.clear_table("competencies");
			competencies.forEach(comp => {
				let row = frm.add_child("competencies");
				row.competency = comp;
				row.weight = weight;
			});
			frm.refresh_field("competencies");
		}

		update_grade_group_display(frm, data);
		if (callback) callback();
	});
}

function build_plan_history_html(frm, history) {
	if (!history || history.length === 0) {
		return `
			<div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; text-align: center; color: #64748b; margin-top: 15px;">
				<i class="fa fa-info-circle" style="font-size: 24px; color: #94a3b8; margin-bottom: 8px;"></i>
				<div style="font-size: 14px; font-weight: 600; color: #334155;">No Plan History Recorded</div>
				<div style="font-size: 12px; margin-top: 4px;">History will appear here as the plan progresses through creation, reviews, approvals, re-edits, and amendments.</div>
			</div>
		`;
	}

	const color_map = {
		green: { border: "#bbf7d0", bg: "#f0fdf4", text: "#15803d", dot: "#16a34a" },
		red: { border: "#fecaca", bg: "#fef2f2", text: "#b91c1c", dot: "#dc2626" },
		orange: { border: "#fed7aa", bg: "#fff7ed", text: "#c2410c", dot: "#ea580c" },
		blue: { border: "#bae6fd", bg: "#f0f9ff", text: "#0369a1", dot: "#0284c7" },
		purple: { border: "#ddd6fe", bg: "#faf5ff", text: "#6d28d9", dot: "#7c3aed" },
		teal: { border: "#99f6e4", bg: "#f0fdfa", text: "#0f766e", dot: "#0d9488" },
		gray: { border: "#e2e8f0", bg: "#f8fafc", text: "#475569", dot: "#64748b" }
	};

	let items_html = "";
	history.forEach((ev, idx) => {
		let col = color_map[ev.badge_color] || color_map.gray;
		let is_last = (idx === history.length - 1);

		let comment_html = "";
		if (ev.comment) {
			let label = "Comment / Remark:";
			if (ev.event_type && (ev.event_type.includes("rejection") || ev.event_type.includes("return"))) label = "Return Reason / Remark:";
			else if (ev.event_type && ev.event_type.includes("re_edit")) label = "Revision Remark to Employee:";
			else if (ev.event_type && ev.event_type.includes("amendment")) label = "Amendment Reason / Remark:";

			comment_html = `
				<div style="background: ${col.bg}; border-left: 3px solid ${col.dot}; padding: 8px 12px; border-radius: 0 6px 6px 0; margin-top: 8px; font-size: 12.5px; color: #1e293b;">
					<div style="font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: ${col.dot}; margin-bottom: 2px;">
						${label}
					</div>
					<div style="font-style: italic; line-height: 1.4;">"${frappe.utils.escape_html(ev.comment)}"</div>
				</div>
			`;
		}

		let link_html = "";
		if (ev.link) {
			link_html = `
				<div style="margin-top: 8px;">
					<a href="${ev.link}" class="btn btn-xs btn-default" style="border-radius: 6px; font-size: 11.5px; padding: 3px 9px; display: inline-flex; align-items: center; gap: 5px; color: #1e293b; text-decoration: none; border: 1px solid #cbd5e1;">
						<i class="fa fa-external-link text-muted"></i> View Amendment Document
					</a>
				</div>
			`;
		}

		let details_html = "";
		if (ev.details && !ev.comment) {
			details_html = `<span style="font-size: 12px; color: #64748b;">&bull; ${frappe.utils.escape_html(ev.details)}</span>`;
		}

		items_html += `
			<div class="timeline-item" style="position: relative; margin-bottom: ${is_last ? '0px' : '20px'};">
				<!-- Timeline node circle -->
				<div style="position: absolute; left: -29px; top: 3px; width: 20px; height: 20px; border-radius: 50%; background: ${col.dot}; border: 3px solid #ffffff; box-shadow: 0 0 0 2px ${col.border}; display: flex; align-items: center; justify-content: center; color: #ffffff; font-size: 9px; z-index: 2;">
					<i class="fa ${ev.icon || 'fa-circle'}"></i>
				</div>

				<!-- Content Card -->
				<div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); transition: all 0.2s ease;">
					<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 6px;">
						<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
							<span style="font-weight: 700; font-size: 13.5px; color: #0f172a;">${frappe.utils.escape_html(ev.title)}</span>
							<span class="indicator-pill ${ev.badge_color} bold" style="font-size: 11px; padding: 2px 8px;">${frappe.utils.escape_html(ev.badge_text)}</span>
						</div>
						<div style="font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 4px;">
							<i class="fa fa-clock-o"></i> ${frappe.utils.escape_html(ev.formatted_date)}
						</div>
					</div>

					<div style="display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: #475569; flex-wrap: wrap;">
						<span style="display: inline-flex; align-items: center; gap: 4px; font-weight: 600; color: #334155;">
							<i class="fa fa-user-circle" style="color: #94a3b8;"></i> ${frappe.utils.escape_html(ev.actor_name || 'System')}
						</span>
						<span style="font-size: 11px; background: #f1f5f9; color: #475569; padding: 1px 6px; border-radius: 4px; font-weight: 600; border: 1px solid #e2e8f0;">
							${frappe.utils.escape_html(ev.actor_role || 'Employee')}
						</span>
						${details_html}
					</div>

					${comment_html}
					${link_html}
				</div>
			</div>
		`;
	});

	return `
		<div class="pms-history-card" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05); overflow: hidden; margin-top: 15px; margin-bottom: 25px;">
			<div style="display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-bottom: 1px solid #e2e8f0;">
				<div style="display: flex; align-items: center; gap: 10px;">
					<div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(21, 128, 61, 0.1); color: #15803d; display: flex; align-items: center; justify-content: center; font-size: 15px;">
						<i class="fa fa-history"></i>
					</div>
					<div>
						<div style="font-weight: 700; font-size: 14px; color: #0f172a; letter-spacing: -0.2px;">Performance Plan Lifecycle & Audit History</div>
						<div style="font-size: 11.5px; color: #64748b;">Complete chronological trail of submissions, approvals, returns, supervisor edits, and amendments</div>
					</div>
				</div>
				<div style="display: flex; align-items: center; gap: 8px;">
					<span class="indicator-pill blue bold" style="font-size: 11px;">${history.length} Event(s)</span>
					<button type="button" class="btn btn-xs btn-default btn-reload-plan-history" title="Refresh History" style="border-radius: 6px; padding: 4px 8px;">
						<i class="fa fa-refresh"></i> Refresh
					</button>
				</div>
			</div>
			
			<div style="padding: 20px 24px; background: #ffffff;">
				<div class="pms-timeline" style="position: relative; padding-left: 28px;">
					<!-- timeline vertical connecting line -->
					<div style="position: absolute; left: 9px; top: 12px; bottom: 12px; width: 2px; background: #e2e8f0; z-index: 1;"></div>
					${items_html}
				</div>
			</div>
		</div>
	`;
}

function render_plan_history(frm) {
	if (frm.is_new()) {
		try {
			frm.set_df_property("plan_history_section", "hidden", 1);
		} catch(e){}
		return;
	}

	try {
		frm.set_df_property("plan_history_section", "hidden", 0);
	} catch(e){}

	frappe.call({
		method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.get_plan_history",
		args: { docname: frm.doc.name },
		callback: function(r) {
			let history = (r && r.message) || [];
			let html = build_plan_history_html(frm, history);

			let rendered = false;
			if (frm.fields_dict["plan_history_html"] && frm.fields_dict["plan_history_html"].$wrapper) {
				frm.fields_dict["plan_history_html"].$wrapper.html(html);
				rendered = true;
			}

			if (!rendered || !$('#pms-plan-history-dynamic-wrapper').length) {
				let $anchor = (frm.fields_dict["competencies"] && frm.fields_dict["competencies"].$wrapper && frm.fields_dict["competencies"].$wrapper.is(':visible'))
					? frm.fields_dict["competencies"].$wrapper
					: (frm.fields_dict["targets"] ? frm.fields_dict["targets"].$wrapper : null);

				if ($anchor && $anchor.length && !rendered) {
					if (!$('#pms-plan-history-dynamic-wrapper').length) {
						$anchor.after('<div id="pms-plan-history-dynamic-wrapper" style="margin-top: 25px;"></div>');
					}
					$('#pms-plan-history-dynamic-wrapper').html(html);
				}
			}

			// Bind reload button
			$('.btn-reload-plan-history').off('click').on('click', function(e) {
				e.preventDefault();
				$(this).find('i').addClass('fa-spin');
				render_plan_history(frm);
			});
		}
	});
}

frappe.ui.form.on("PMS Appraisal", {
	setup: function(frm) {
		frm.add_fetch("employee", "employee_name", "employee_name");
		frm.set_query("cycle", function() {
			return {
				filters: {
					status: ["in", ["Active", "Planning Open", "Monitoring", "Self-Rating Open"]]
				}
			};
		});
	},

	onload: function(frm) {
		frm.set_query("cycle", function() {
			return {
				filters: {
					status: ["in", ["Active", "Planning Open", "Monitoring", "Self-Rating Open"]]
				}
			};
		});
		if (!frappe.user_roles.includes("HR Admin") && !frappe.user_roles.includes("System Manager")) {
			frm.set_df_property("employee", "read_only", 1);
		}
	},

	onload_post_render: function(frm) {
		toggle_scoring_visibility(frm, frm._is_appraisal_mode);
	},

	employee: function(frm) {
		if (frm.doc.employee) {
			sync_employee_details(frm, frm.doc.employee);
		}
	},

	refresh(frm) {
		if (frm.is_new() && !frm.doc.employee) {
			sync_employee_details(frm);
		} else if (frm.doc.employee) {
			if (!frm.doc.grade_group || !frm.doc.supervisor_name) {
				sync_employee_details(frm, frm.doc.employee);
			}
		}

		if (frm.doc.supervisor_name) {
			frm.set_df_property("supervisor_snapshot", "description", `<b style="color: var(--text-color); font-size: 13px;">${frm.doc.supervisor_name}</b>`);
		}
		if (frm.doc.reviewer_name) {
			frm.set_df_property("reviewer_snapshot", "description", `<b style="color: var(--text-color); font-size: 13px;">${frm.doc.reviewer_name}</b>`);
		}
		if (frm.doc.supervisor_2_name) {
			frm.set_df_property("supervisor_2_snapshot", "description", `<b style="color: var(--text-color); font-size: 13px;">${frm.doc.supervisor_2_name}</b>`);
		}

		let route_vm = (frappe.route_options && frappe.route_options.view_mode) || localStorage.getItem("pms_view_mode") || null;
		if (frappe.route_options && frappe.route_options.view_mode) {
			delete frappe.route_options.view_mode;
		}

		if (frm.is_new()) {
			frm._view_mode = "plan";
		} else if (route_vm) {
			frm._view_mode = route_vm;
		}

		let is_activated = (frm.doc.workflow_state === "Appraisal Open" || frm.doc.workflow_state === "Appraisal Completed" || (frm.doc.appraisal_status && frm.doc.appraisal_status !== "Not Activated"));

		// Performance Plan vs Appraisal Form resolution
		let is_appraisal = is_activated && (frm._view_mode === "appraisal" || (!frm._view_mode && is_activated));
		frm._is_appraisal_mode = is_appraisal;

		// Form Title & Scoring Field Visibility
		try {
			let title = is_appraisal ? __("PMS Appraisal Form") : (frm.is_new() ? __("New PMS Performance Plan") : __("PMS Performance Plan"));
			if (frm.set_title) {
				frm.set_title(title);
			} else if (frm.page && frm.page.set_title) {
				frm.page.set_title(title);
			}
		} catch (e) {
			console.log(e);
		}

		// Toggle scoring fields vs performance plan fields
		toggle_scoring_visibility(frm, is_appraisal);

		// Switcher button between Performance Plan and Appraisal Form
		if (!is_appraisal && is_activated) {
			frm.page.add_inner_button(__("Open Appraisal Form"), function() {
				frm._view_mode = "appraisal";
				localStorage.setItem("pms_view_mode", "appraisal");
				frm.refresh();
			}).addClass("btn-primary text-white").css("background", "linear-gradient(135deg, #15803d, #0d9488)");
		} else if (is_appraisal) {
			frm.page.add_inner_button(__("View Performance Plan"), function() {
				frm._view_mode = "plan";
				localStorage.setItem("pms_view_mode", "plan");
				frm.refresh();
			});
		}

		// Rejection & Revision Remarks visibility
		try {
			frm.set_df_property("plan_rejection_remark", "hidden", (frm.doc.plan_status === "Rejected" || frm.doc.plan_status === "Returned") ? 0 : 1);
			let show_revision = (!is_appraisal && (frm.doc.plan_revision_remark || frm.doc.plan_status === "Pending Supervisor Approval" || frm.doc.plan_status === "Pending Reviewer Approval"));
			frm.set_df_property("plan_revision_remark", "hidden", show_revision ? 0 : 1);
		} catch(e) { console.log(e); }

		// Render Performance Plan Lifecycle & History Timeline
		render_plan_history(frm);

		// Dynamic Evaluation of User Roles
		frappe.call({
			method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.get_current_employee",
			callback: function(r) {
				let current_emp = r && r.message && r.message.name;
				let is_my_doc = frm.is_new() || (current_emp && (current_emp === frm.doc.employee));
				let is_admin = frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("HR Admin") || frappe.user_roles.includes("HR Manager");
				let is_supervisor = (current_emp && current_emp === frm.doc.supervisor_snapshot) || is_admin;
				let is_reviewer = (current_emp && current_emp === frm.doc.reviewer_snapshot) || is_admin;
				let is_supervisor_2_only = frappe.user_roles.includes("Supervisor 2") && !is_admin && !frappe.user_roles.includes("Supervisor") && !frappe.user_roles.includes("Reviewer");
				let is_supervisor_2_for_this_doc = (current_emp && frm.doc.supervisor_2_snapshot === current_emp) && !is_my_doc && !is_admin;

				// Supervisor 2: Strict Read-Only Observer
				if (is_supervisor_2_only || is_supervisor_2_for_this_doc) {
					frm.disable_form();
					if (frm.disable_save) frm.disable_save();
					if (frm.page.btn_primary) frm.page.btn_primary.hide();
					if (is_appraisal) render_appraisal_headline(frm);
					else update_grade_group_display(frm);
					return;
				}

				// If Locked: Strict Permanent Lock
				if (frm.doc.locked) {
					frm.disable_form();
					if (frm.disable_save) frm.disable_save();
					if (frm.page.btn_primary) frm.page.btn_primary.hide();
					render_appraisal_headline(frm);
					return;
				}

				// =============================================================
				// CASE A: APPRAISAL PHASE ACTIVE
				// =============================================================
				if (is_appraisal) {
					render_appraisal_headline(frm);

					// In appraisal phase, target descriptions and weights are strictly locked
					frm.set_df_property("targets", "read_only", 0);
					frm.set_df_property("competencies", "read_only", 0);

					let app_status = frm.doc.appraisal_status || "Self-Assessment Pending";
					frm._current_emp = current_emp;
					apply_scoring_permissions(frm, app_status, is_supervisor, is_reviewer, is_my_doc, is_admin);

					// 1. Stage: Self-Assessment Pending
					if (app_status === "Self-Assessment Pending") {
						if (is_my_doc || is_admin) {
							frm.enable_save();
							frm.set_df_property("employee_overall_remarks", "read_only", 0);
							frm.set_df_property("supervisor_overall_remarks", "read_only", 1);
							frm.set_df_property("reviewer_overall_remarks", "read_only", 1);

							frm.page.add_inner_button(__("Submit Self-Appraisal"), function() {
								frappe.confirm(
									__("Are you sure you want to submit your Self-Appraisal to your Supervisor?"),
									function() {
										frappe.call({
											method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.submit_self_assessment",
											args: {
												docname: frm.doc.name,
												employee_remarks: frm.doc.employee_overall_remarks,
												target_data: frm.doc.targets,
												competency_data: frm.doc.competencies
											},
											callback: function(res) {
												if (!res.exc) {
													frappe.show_alert({message: __("Self-Appraisal submitted successfully."), indicator: "green"});
													frm.reload_doc();
												}
											}
										});
									}
								);
							}).addClass("btn-primary text-white").css("background-color", "#2490ef");
						} else {
							frm.disable_form();
						}
					}

					// 2. Stage: Pending Supervisor Review
					else if (app_status === "Pending Supervisor Review") {
						if (is_supervisor) {
							frm.enable_save();
							frm.set_df_property("employee_overall_remarks", "read_only", 1);
							frm.set_df_property("supervisor_overall_remarks", "read_only", 0);
							frm.set_df_property("reviewer_overall_remarks", "read_only", 1);

							frm.page.add_inner_button(__("Submit Supervisor Review"), function() {
								frappe.confirm(
									__("Submit your evaluation and score for this appraisal?"),
									function() {
										frappe.call({
											method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.submit_supervisor_review",
											args: {
												docname: frm.doc.name,
												supervisor_remarks: frm.doc.supervisor_overall_remarks,
												target_data: frm.doc.targets,
												competency_data: frm.doc.competencies
											},
											callback: function(res) {
												if (!res.exc) {
													frappe.show_alert({message: __("Supervisor review submitted."), indicator: "green"});
													frm.reload_doc();
												}
											}
										});
									}
								);
							}).addClass("btn-primary text-white").css("background-color", "#15803d");
						} else {
							frm.disable_form();
						}
					}

					// 3. Stage: Pending Employee Acceptance
					else if (app_status === "Pending Employee Acceptance") {
						frm.disable_form();
						if (is_my_doc || is_admin) {
							frm.page.add_inner_button(__("Accept Scores"), function() {
								frappe.confirm(
									__("Do you accept the supervisor's evaluation and scores?"),
									function() {
										frappe.call({
											method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.accept_supervisor_scores",
											args: { docname: frm.doc.name },
											callback: function(res) {
												if (!res.exc) {
													frappe.show_alert({message: __("Scores accepted."), indicator: "green"});
													frm.reload_doc();
												}
											}
										});
									}
								);
							}).addClass("btn-success text-white").css("background-color", "#28a745");

							frm.page.add_inner_button(__("Raise Dispute"), function() {
								frappe.prompt(
									{
										fieldtype: "Small Text",
										fieldname: "reason",
										label: __("Dispute Reason & Justification"),
										reqd: 1
									},
									function(values) {
										frappe.call({
											method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.raise_dispute",
											args: {
												docname: frm.doc.name,
												dispute_reason: values.reason
											},
											callback: function(res) {
												if (!res.exc) {
													frappe.show_alert({message: __("Dispute raised and forwarded to Reviewer."), indicator: "orange"});
													frm.reload_doc();
												}
											}
										});
									},
									__("Raise Appraisal Dispute"),
									__("Escalate to Reviewer")
								);
							}).addClass("btn-danger text-white").css("background-color", "#dc3545");
						}
					}

					// 4. Stage: Disputed - Pending Reviewer
					else if (app_status === "Disputed - Pending Reviewer") {
						if (is_reviewer) {
							frm.enable_save();
							frm.set_df_property("employee_overall_remarks", "read_only", 1);
							frm.set_df_property("supervisor_overall_remarks", "read_only", 1);
							frm.set_df_property("reviewer_overall_remarks", "read_only", 0);

							frm.page.add_inner_button(__("Submit Reviewer Decision"), function() {
								frappe.confirm(
									__("Submit your final dispute validation and scores?"),
									function() {
										frappe.call({
											method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.submit_reviewer_decision",
											args: {
												docname: frm.doc.name,
												reviewer_remarks: frm.doc.reviewer_overall_remarks,
												target_data: frm.doc.targets,
												competency_data: frm.doc.competencies
											},
											callback: function(res) {
												if (!res.exc) {
													frappe.show_alert({message: __("Reviewer decision submitted."), indicator: "green"});
													frm.reload_doc();
												}
											}
										});
									}
								);
							}).addClass("btn-primary text-white").css("background-color", "#15803d");
						} else {
							frm.disable_form();
						}
					}

					// 5. Stage: Reviewer Resolved - Pending Employee Decision
					else if (app_status === "Reviewer Resolved - Pending Employee Decision") {
						frm.disable_form();
						if (is_my_doc || is_admin) {
							frm.page.add_inner_button(__("Accept Reviewer Decision"), function() {
								frappe.confirm(
									__("Accept the Reviewer's final evaluation?"),
									function() {
										frappe.call({
											method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.accept_reviewer_decision",
											args: { docname: frm.doc.name },
											callback: function(res) {
												if (!res.exc) {
													frappe.show_alert({message: __("Reviewer decision accepted."), indicator: "green"});
													frm.reload_doc();
												}
											}
										});
									}
								);
							}).addClass("btn-success text-white").css("background-color", "#28a745");

							frm.page.add_inner_button(__("Request PERC Review"), function() {
								frappe.prompt(
									{
										fieldtype: "Small Text",
										fieldname: "justification",
										label: __("Grievance Justification for PERC Committee"),
										reqd: 1
									},
									function(values) {
										frappe.call({
											method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.request_perc_review",
											args: {
												docname: frm.doc.name,
												justification: values.justification
											},
											callback: function(res) {
												if (!res.exc) {
													frappe.show_alert({message: __("PERC Case opened successfully."), indicator: "orange"});
													frm.reload_doc();
												}
											}
										});
									},
									__("Request PERC Escalation"),
									__("Submit Request")
								);
							}).addClass("btn-warning text-dark");
						}
					}

					// 6. Stage: Under PERC Review
					else if (app_status === "Under PERC Review") {
						frm.disable_form();
					}

					// 7. Stage: Appraisal Accepted
					else if (app_status === "Appraisal Accepted") {
						frm.disable_form();
					}

					// Common Actions for HR Admin in Appraisal Phase
					if (is_admin) {
						if (["Appraisal Accepted", "Under PERC Review", "Reviewer Resolved - Pending Employee Decision"].includes(app_status)) {
							frm.page.add_inner_button(__("Lock Appraisal"), function() {
								frappe.prompt(
									{
										fieldtype: "Float",
										fieldname: "final_score",
										label: __("Confirmed Final Score (Optional Override)"),
										default: frm.doc.total_score || 0
									},
									function(values) {
										frappe.call({
											method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.lock_appraisal",
											args: {
												docname: frm.doc.name,
												final_score: values.final_score
											},
											callback: function(res) {
												if (!res.exc) {
													frappe.show_alert({message: __("Appraisal finalized and locked."), indicator: "green"});
													frm.reload_doc();
												}
											}
										});
									},
									__("Lock Appraisal"),
									__("Confirm & Lock")
								);
							}).addClass("btn-dark text-white");
						}

						if (frm.doc.perc_case) {
							frm.page.add_inner_button(__("View PERC Case"), function() {
								frappe.set_route("Form", "PERC Case", frm.doc.perc_case);
							});
						}
					}
					return;
				}

				// =============================================================
				// CASE B: PLANNING & MONITORING PHASE (Original Flow)
				// =============================================================
				update_grade_group_display(frm);

				// Lock form targets and competencies when Approved and in Monitoring stage
				if (frm.doc.plan_status === "Approved" && frm.doc.workflow_state === "Monitoring") {
					frm.set_df_property("targets", "read_only", 1);
					frm.set_df_property("competencies", "read_only", 1);
				}

				// 1. DRAFT or RETURNED stage
				if (frm.is_new() || frm.doc.plan_status === "Draft" || frm.doc.plan_status === "Rejected" || frm.doc.plan_status === "Returned") {
					if (frm.is_new() || is_my_doc || is_admin) {
						frm.set_df_property("targets", "read_only", 0);
						frm.set_df_property("competencies", "read_only", 0);
						frm.enable_save();

						if (frm.doc.plan_revision_remark) {
							frm.dashboard.clear_headline();
							update_grade_group_display(frm);
							frm.dashboard.set_headline_alert(`
								<div class="alert alert-warning" style="margin-bottom: 0px;">
									<b>Plan Returned for Analysis:</b> Modifications were made by <b>${frappe.utils.escape_html(frm.doc.revised_by_role || 'Supervisor/Reviewer')}</b>.<br>
									<i>"${frappe.utils.escape_html(frm.doc.plan_revision_remark)}"</i><br>
									Please review the updated tasks, weightages, and remarks. You can make adjustments and click <b>Send for Approval</b> when ready.
								</div>
							`);
						} else if ((frm.doc.plan_status === "Rejected" || frm.doc.plan_status === "Returned") && frm.doc.plan_rejection_remark) {
							frm.dashboard.clear_headline();
							update_grade_group_display(frm);
							frm.dashboard.set_headline_alert(`
								<div class="alert alert-warning" style="margin-bottom: 0px;">
									<b>Plan Returned:</b> Return Remark: <i>"${frappe.utils.escape_html(frm.doc.plan_rejection_remark)}"</i><br>
									Please review the remarks, make necessary adjustments, and click <b>Send for Approval</b> when ready.
								</div>
							`);
						}

						if (!frm.is_new()) {
							frm.page.add_inner_button(__("Send for Approval"), () => {
								frappe.call({
									method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.send_for_approval",
									args: { docname: frm.doc.name },
									callback: function(res) {
										if (!res.exc) {
											frappe.show_alert({message: __('Sent for Approval'), indicator: 'green'});
											frm.reload_doc();
										}
									}
								});
							}).addClass("btn-primary text-white").css("background-color", "#2490ef");
						}
					} else {
						frm.disable_form();
					}
					return;
				}

				// 2. PENDING SUPERVISOR APPROVAL stage
				if (frm.doc.plan_status === "Pending Supervisor Approval") {
					if (is_supervisor) {
						frm.set_df_property("targets", "read_only", 0);
						frm.set_df_property("plan_revision_remark", "read_only", 0);
						frm.set_df_property("plan_revision_remark", "hidden", 0);
						frm.set_df_property("competencies", "read_only", 1);
						frm.enable_save();

						frm.page.add_inner_button(__("Approve"), () => {
							frappe.prompt(
								{
									fieldtype: "Small Text",
									fieldname: "comment",
									label: __("Approval Comment / Remarks (Optional)")
								},
								function(values) {
									frappe.call({
										method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.approve_plan",
										args: { docname: frm.doc.name, comment: values.comment },
										callback: function(res) {
											if (!res.exc) {
												frappe.show_alert({message: __('Plan Approved'), indicator: 'green'});
												frm.reload_doc();
											}
										}
									});
								},
								__("Approve Performance Plan"),
								__("Approve")
							);
						}).addClass("btn-primary text-white").css("background-color", "#28a745");

						frm.page.add_inner_button(__("Return with Changes"), () => {
							frappe.prompt(
								{
									fieldtype: "Small Text",
									fieldname: "remark",
									label: __("Revision Remark to Employee (Optional)"),
									default: frm.doc.plan_revision_remark || ""
								},
								function(values) {
									frm.doc.plan_revision_remark = values.remark;
									frappe.call({
										method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.return_to_employee_with_edits",
										args: { docname: frm.doc.name, remark: values.remark },
										callback: function(res) {
											if (!res.exc) {
												frappe.show_alert({message: __('Plan returned to Employee for analysis'), indicator: 'blue'});
												frm.reload_doc();
											}
										}
									});
								},
								__("Return to Employee with Changes"),
								__("Return Plan")
							);
						}).addClass("btn-warning text-dark");

						frm.page.add_inner_button(__("Return"), () => {
							frappe.prompt(
								{ fieldtype: "Small Text", fieldname: "remark", label: __("Return Remark"), reqd: 1 },
								function(values) {
									frappe.call({
										method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.reject_plan",
										args: { docname: frm.doc.name, remark: values.remark },
										callback: function(res) {
											if (!res.exc) {
												frappe.show_alert({message: __('Returned'), indicator: 'orange'});
												frm.reload_doc();
											}
										}
									});
								},
								__("Return Plan"),
								__("Return")
							);
						}).addClass("btn-danger text-white").css("background-color", "#dc3545");
					} else {
						frm.disable_form();
					}
					return;
				}

				// 3. PENDING REVIEWER APPROVAL stage
				if (frm.doc.plan_status === "Pending Reviewer Approval") {
					if (is_reviewer) {
						frm.set_df_property("targets", "read_only", 0);
						frm.set_df_property("plan_revision_remark", "read_only", 0);
						frm.set_df_property("plan_revision_remark", "hidden", 0);
						frm.set_df_property("competencies", "read_only", 1);
						frm.enable_save();

						frm.page.add_inner_button(__("Approve"), () => {
							frappe.prompt(
								{
									fieldtype: "Small Text",
									fieldname: "comment",
									label: __("Approval Comment / Remarks (Optional)")
								},
								function(values) {
									frappe.call({
										method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.approve_plan",
										args: { docname: frm.doc.name, comment: values.comment },
										callback: function(res) {
											if (!res.exc) {
												frappe.show_alert({message: __('Plan Approved'), indicator: 'green'});
												frm.reload_doc();
											}
										}
									});
								},
								__("Approve Performance Plan"),
								__("Approve")
							);
						}).addClass("btn-primary text-white").css("background-color", "#28a745");

						frm.page.add_inner_button(__("Return with Changes"), () => {
							frappe.prompt(
								{
									fieldtype: "Small Text",
									fieldname: "remark",
									label: __("Revision Remark to Employee (Optional)"),
									default: frm.doc.plan_revision_remark || ""
								},
								function(values) {
									frm.doc.plan_revision_remark = values.remark;
									frappe.call({
										method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.return_to_employee_with_edits",
										args: { docname: frm.doc.name, remark: values.remark },
										callback: function(res) {
											if (!res.exc) {
												frappe.show_alert({message: __('Plan returned to Employee for analysis'), indicator: 'blue'});
												frm.reload_doc();
											}
										}
									});
								},
								__("Return to Employee with Changes"),
								__("Return Plan")
							);
						}).addClass("btn-warning text-dark");

						frm.page.add_inner_button(__("Return"), () => {
							frappe.prompt(
								{ fieldtype: "Small Text", fieldname: "remark", label: __("Return Remark"), reqd: 1 },
								function(values) {
									frappe.call({
										method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.reject_plan",
										args: { docname: frm.doc.name, remark: values.remark },
										callback: function(res) {
											if (!res.exc) {
												frappe.show_alert({message: __('Returned'), indicator: 'orange'});
												frm.reload_doc();
											}
										}
									});
								},
								__("Return Plan"),
								__("Return")
							);
						}).addClass("btn-danger text-white").css("background-color", "#dc3545");
					} else {
						frm.disable_form();
					}
					return;
				}

				// 4. APPROVED / MONITORING stage
				if (frm.doc.plan_status === "Approved") {
					frm.disable_form();
					if (frm.doc.workflow_state === "Monitoring") {
						// HR Admin Action: Activate Appraisal Phase
						if (is_admin) {
							frm.page.add_inner_button(__("Activate Appraisal Phase"), function() {
								frappe.confirm(
									__("Activate Appraisal Phase for this Performance Plan? Mapped competencies and scoring tables will become available for Employee Self-Assessment."),
									function() {
										frappe.call({
											method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.activate_appraisal_phase",
											args: { docname: frm.doc.name },
											callback: function(res) {
												if (!res.exc) {
													frappe.show_alert({message: __("Appraisal Phase Activated."), indicator: "green"});
													frm.reload_doc();
												}
											}
										});
									}
								);
							}).addClass("btn-success text-white").css("background-color", "#15803d");

							// Amendment Window Controls
							if (!frm.doc.amendment_window_open) {
								frm.page.add_inner_button(__("Open Amendment Window"), function() {
									frappe.call({
										method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.open_amendment_window",
										args: { docname: frm.doc.name },
										callback: function(res) {
											if (!res.exc) {
												frappe.show_alert({message: __("Amendment Window opened."), indicator: "green"});
												frm.reload_doc();
											}
										}
									});
								}).addClass("btn-warning text-dark");
							} else {
								frm.page.add_inner_button(__("Close Amendment Window"), function() {
									frappe.call({
										method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.close_amendment_window",
										args: { docname: frm.doc.name },
										callback: function(res) {
											if (!res.exc) {
												frappe.show_alert({message: __("Amendment Window closed."), indicator: "orange"});
												frm.reload_doc();
											}
										}
									});
								}).addClass("btn-danger text-white");
							}
						}

						// Employee action to Request Amendment when window is open
						if (frm.doc.amendment_window_open && (is_my_doc || is_admin)) {
							frm.page.add_inner_button(__("Request Amendment"), function() {
								frappe.call({
									method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.request_amendment",
									args: { docname: frm.doc.name },
									callback: function(res) {
										if (res && res.message) {
											frappe.show_alert({message: __("Amendment request created."), indicator: "green"});
											frappe.set_route("Form", "PMS Plan Amendment", res.message);
										}
									}
								});
							}).addClass("btn-primary text-white").css("background-color", "#2490ef");
						}
					}
					return;
				}
			}
		});
	}
});

frappe.ui.form.on("PMS Target", {
	form_render: function(frm, cdt, cdn) {
		let is_app = frm._is_appraisal_mode;
		let grid_row = frm.fields_dict["targets"] && frm.fields_dict["targets"].grid.grid_rows_by_docname[cdn];
		if (!grid_row) return;

		const scoring_cols = ["self_score", "self_remark", "evidence", "supervisor_score", "supervisor_remark", "reviewer_score", "reviewer_remark"];
		grid_row.toggle_display("remark", false);
		grid_row.toggle_display("self_remark", false);

		if (!is_app) {
			scoring_cols.forEach(f => grid_row.toggle_display(f, false));
			grid_row.toggle_enable("target_description", true);
			grid_row.toggle_enable("weight", true);
		} else {
			let app_status = frm.doc.appraisal_status || "Self-Assessment Pending";
			let is_self_stage = (app_status === "Self-Assessment Pending");
			let is_sup_stage = (app_status === "Pending Supervisor Review");
			let is_rev_stage = (app_status === "Disputed - Pending Reviewer");

			let is_admin = frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("HR Admin") || frappe.user_roles.includes("HR Manager");
			let current_emp = frm._current_emp;
			let is_supervisor = (current_emp && current_emp === frm.doc.supervisor_snapshot) || is_admin;
			let is_reviewer = (current_emp && current_emp === frm.doc.reviewer_snapshot) || is_admin;
			let is_employee = (current_emp && current_emp === frm.doc.employee) || is_admin;

			grid_row.toggle_enable("target_description", false);
			grid_row.toggle_enable("weight", false);

			// Self scoring
			grid_row.toggle_display("self_score", true);
			grid_row.toggle_display("evidence", true);
			let can_edit_self = is_self_stage && is_employee;
			grid_row.toggle_enable("self_score", can_edit_self);
			grid_row.toggle_enable("evidence", can_edit_self);

			// Supervisor scoring
			let show_super = (!is_self_stage);
			grid_row.toggle_display("supervisor_score", show_super);
			grid_row.toggle_display("supervisor_remark", show_super);
			let can_edit_sup = is_sup_stage && is_supervisor;
			grid_row.toggle_enable("supervisor_score", can_edit_sup);
			grid_row.toggle_enable("supervisor_remark", can_edit_sup);

			// Reviewer scoring
			let show_rev = (is_rev_stage || app_status.includes("Reviewer") || app_status.includes("PERC") || app_status === "Appraisal Accepted" || app_status === "Finalized & Locked");
			grid_row.toggle_display("reviewer_score", show_rev);
			grid_row.toggle_display("reviewer_remark", show_rev);
			let can_edit_rev = is_rev_stage && is_reviewer;
			grid_row.toggle_enable("reviewer_score", can_edit_rev);
			grid_row.toggle_enable("reviewer_remark", can_edit_rev);
		}
	},
	reviewer_score: function(frm, cdt, cdn) {
		let app_status = frm.doc.appraisal_status;
		let is_admin = frappe.user_roles.includes("System Manager");
		if (app_status !== "Disputed - Pending Reviewer" && !is_admin) {
			frappe.model.set_value(cdt, cdn, "reviewer_score", 0);
			frappe.msgprint({
				title: __("Not Allowed"),
				indicator: "red",
				message: __("Supervisor cannot enter or edit Reviewer Score. Only the assigned Reviewer can evaluate during dispute review.")
			});
		}
	},
	reviewer_remark: function(frm, cdt, cdn) {
		let app_status = frm.doc.appraisal_status;
		let is_admin = frappe.user_roles.includes("System Manager");
		if (app_status !== "Disputed - Pending Reviewer" && !is_admin) {
			frappe.model.set_value(cdt, cdn, "reviewer_remark", "");
			frappe.msgprint({
				title: __("Not Allowed"),
				indicator: "red",
				message: __("Supervisor cannot enter or edit Reviewer Remark.")
			});
		}
	},
	self_score: function(frm, cdt, cdn) {
		let app_status = frm.doc.appraisal_status;
		let is_admin = frappe.user_roles.includes("System Manager");
		if (app_status !== "Self-Assessment Pending" && !is_admin) {
			frappe.msgprint({
				title: __("Not Allowed"),
				indicator: "red",
				message: __("Self-Assessment score cannot be edited at this stage.")
			});
			frm.reload_doc();
		}
	}
});

frappe.ui.form.on("PMS Competency Score", {
	form_render: function(frm, cdt, cdn) {
		let is_app = frm._is_appraisal_mode;
		let grid_row = frm.fields_dict["competencies"] && frm.fields_dict["competencies"].grid.grid_rows_by_docname[cdn];
		if (!grid_row) return;

		const scoring_cols = ["self_rating", "self_remark", "supervisor_rating", "supervisor_remark", "reviewer_rating", "reviewer_remark"];
		grid_row.toggle_display("self_remark", false);

		if (!is_app) {
			scoring_cols.forEach(f => grid_row.toggle_display(f, false));
			grid_row.toggle_enable("competency", false);
			grid_row.toggle_enable("weight", false);
		} else {
			let app_status = frm.doc.appraisal_status || "Self-Assessment Pending";
			let is_self_stage = (app_status === "Self-Assessment Pending");
			let is_sup_stage = (app_status === "Pending Supervisor Review");
			let is_rev_stage = (app_status === "Disputed - Pending Reviewer");

			let is_admin = frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("HR Admin") || frappe.user_roles.includes("HR Manager");
			let current_emp = frm._current_emp;
			let is_supervisor = (current_emp && current_emp === frm.doc.supervisor_snapshot) || is_admin;
			let is_reviewer = (current_emp && current_emp === frm.doc.reviewer_snapshot) || is_admin;
			let is_employee = (current_emp && current_emp === frm.doc.employee) || is_admin;

			grid_row.toggle_enable("competency", false);
			grid_row.toggle_enable("weight", false);

			// Self rating
			grid_row.toggle_display("self_rating", true);
			let can_edit_self = is_self_stage && is_employee;
			grid_row.toggle_enable("self_rating", can_edit_self);

			// Supervisor rating
			let show_super = (!is_self_stage);
			grid_row.toggle_display("supervisor_rating", show_super);
			grid_row.toggle_display("supervisor_remark", show_super);
			let can_edit_sup = is_sup_stage && is_supervisor;
			grid_row.toggle_enable("supervisor_rating", can_edit_sup);
			grid_row.toggle_enable("supervisor_remark", can_edit_sup);

			// Reviewer rating
			let show_rev = (is_rev_stage || app_status.includes("Reviewer") || app_status.includes("PERC") || app_status === "Appraisal Accepted" || app_status === "Finalized & Locked");
			grid_row.toggle_display("reviewer_rating", show_rev);
			grid_row.toggle_display("reviewer_remark", show_rev);
			let can_edit_rev = is_rev_stage && is_reviewer;
			grid_row.toggle_enable("reviewer_rating", can_edit_rev);
			grid_row.toggle_enable("reviewer_remark", can_edit_rev);
		}
	},
	reviewer_rating: function(frm, cdt, cdn) {
		let app_status = frm.doc.appraisal_status;
		let is_admin = frappe.user_roles.includes("System Manager");
		if (app_status !== "Disputed - Pending Reviewer" && !is_admin) {
			frappe.model.set_value(cdt, cdn, "reviewer_rating", 0);
			frappe.msgprint({
				title: __("Not Allowed"),
				indicator: "red",
				message: __("Supervisor cannot enter or edit Reviewer Rating. Only the assigned Reviewer can evaluate during dispute review.")
			});
		}
	},
	reviewer_remark: function(frm, cdt, cdn) {
		let app_status = frm.doc.appraisal_status;
		let is_admin = frappe.user_roles.includes("System Manager");
		if (app_status !== "Disputed - Pending Reviewer" && !is_admin) {
			frappe.model.set_value(cdt, cdn, "reviewer_remark", "");
			frappe.msgprint({
				title: __("Not Allowed"),
				indicator: "red",
				message: __("Supervisor cannot enter or edit Reviewer Remark.")
			});
		}
	},
	self_rating: function(frm, cdt, cdn) {
		let app_status = frm.doc.appraisal_status;
		let is_admin = frappe.user_roles.includes("System Manager");
		if (app_status !== "Self-Assessment Pending" && !is_admin) {
			frappe.msgprint({
				title: __("Not Allowed"),
				indicator: "red",
				message: __("Self-Assessment rating cannot be edited at this stage.")
			});
			frm.reload_doc();
		}
	}
});

