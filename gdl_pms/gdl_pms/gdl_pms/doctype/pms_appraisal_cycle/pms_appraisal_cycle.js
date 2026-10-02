// Copyright (c) 2026, GDL and contributors
// For license information, please see license.txt

frappe.ui.form.on("PMS Appraisal Cycle", {
	onload: function(frm) {
		if (!is_hr_admin_user()) {
			hide_employee_hierarchy_section(frm);
			return;
		}
		show_employee_hierarchy_section(frm);
		if (frm.is_new()) {
			fetch_and_render_employees(frm, true);
		}
	},

	refresh: function(frm) {
		if (!is_hr_admin_user()) {
			hide_employee_hierarchy_section(frm);
			return;
		}
		show_employee_hierarchy_section(frm);

		// Render employees and summary on refresh
		if (frm.is_new()) {
			fetch_and_render_employees(frm, true);
			return;
		}

		// Existing record: render summary and add Sync button for HR Admin
		render_existing_summary(frm);

		frm.page.add_inner_button(__("Sync Employees List"), function() {
			frappe.confirm(__("This will refresh the applicable employees list with their current supervisor and reviewer details from Employee masters. Continue?"), function() {
				frappe.call({
					method: "gdl_pms.gdl_pms.doctype.pms_appraisal_cycle.pms_appraisal_cycle.sync_cycle_employees",
					args: {
						cycle_name: frm.doc.name
					},
					freeze: true,
					freeze_message: __("Updating employee hierarchy..."),
					callback: function(r) {
						if (r.message) {
							frm.reload_doc();
							frappe.show_alert({
								message: __("Applicable employees list updated successfully!"),
								indicator: "green"
							});
						}
					}
				});
			});
		}, __("Actions"));

		// HR Quick Action Buttons to Open/Close Amendment Window
		if (!frm.doc.amendment_window_open) {
			frm.page.add_inner_button(__("Open Amendment Window"), function() {
				frm.set_value("amendment_window_open", 1).then(() => {
					frm.save().then(() => {
						frappe.show_alert({message: __("Amendment Window Opened for Employees."), indicator: "green"});
					});
				});
			}, __("Actions")).addClass("btn-primary text-white").css("background-color", "#15803d");
		} else {
			frm.page.add_inner_button(__("Close Amendment Window"), function() {
				frm.set_value("amendment_window_open", 0).then(() => {
					frm.save().then(() => {
						frappe.show_alert({message: __("Amendment Window Closed."), indicator: "red"});
					});
				});
			}, __("Actions")).addClass("btn-danger text-white");
		}
	},

	grade_group: function(frm) {
		if (!is_hr_admin_user()) return;
		// When creating or updating Grade Group, dynamically fetch and update employee list
		fetch_and_render_employees(frm, true);
	},

	calendar_year: function(frm) {
		sync_cycle_dates(frm, "calendar_year");
		if (is_hr_admin_user()) {
			fetch_and_render_employees(frm, true);
		}
	},

	start_date: function(frm) {
		sync_cycle_dates(frm, "start_date");
	},

	cycle_type: function(frm) {
		sync_cycle_dates(frm, "cycle_type");
		if (is_hr_admin_user()) {
			fetch_and_render_employees(frm, true);
		}
	}
});

function parse_date_to_moment(val) {
	if (!val) return null;
	if (val instanceof Date) return moment(val);
	let str_val = String(val).trim();
	// Check for DD-MM-YYYY format
	if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(str_val)) {
		let parts = str_val.split("-");
		return moment(`${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`, "YYYY-MM-DD");
	}
	let m = moment(str_val, ["YYYY-MM-DD", "YYYY/MM/DD", "DD-MM-YYYY", "MM-DD-YYYY"]);
	if (!m.isValid()) {
		m = moment(str_val);
	}
	return m.isValid() ? m : null;
}

function calculate_3_months_end(start_date_val) {
	let m = parse_date_to_moment(start_date_val);
	if (!m) return "";
	return m.clone().add(3, "months").subtract(1, "days").format("YYYY-MM-DD");
}

function sync_cycle_dates(frm, source_field) {
	let cycle_type = frm.doc.cycle_type || "Annual";

	if (cycle_type === "Probation") {
		if (frm.doc.start_date) {
			let end_d = calculate_3_months_end(frm.doc.start_date);
			if (end_d && frm.doc.end_date !== end_d) {
				frm.set_value("end_date", end_d);
				frappe.show_alert({
					message: __("Probation Cycle: End Date set to 3 months ({0})", [end_d]),
					indicator: "blue"
				});
			}
		} else if (frm.doc.calendar_year) {
			let year = frm.doc.calendar_year;
			frm.set_value("start_date", year + "-01-01");
			frm.set_value("end_date", year + "-03-31");
		}

		if (frm.is_new() && (!frm.doc.cycle_name || frm.doc.cycle_name.includes("PMS Appraisal Cycle"))) {
			frm.set_value("cycle_name", "Probation Appraisal Cycle " + (frm.doc.calendar_year || moment().year()));
		}
	} else if (cycle_type === "Annual") {
		if (frm.doc.calendar_year) {
			let year = frm.doc.calendar_year;
			if (!frm.doc.start_date || source_field === "calendar_year" || source_field === "cycle_type") {
				frm.set_value("start_date", year + "-01-01");
			}
			frm.set_value("end_date", year + "-12-31");
		}

		if (frm.is_new() && (!frm.doc.cycle_name || frm.doc.cycle_name.includes("Probation Appraisal Cycle"))) {
			frm.set_value("cycle_name", "PMS Appraisal Cycle " + (frm.doc.calendar_year || moment().year()));
		}
	}
}

function fetch_and_render_employees(frm, populate_table) {
	var grade_group = frm.doc.grade_group || "All";
	var cycle_name = frm.is_new() ? null : frm.doc.name;
	var cycle_type = frm.doc.cycle_type || "Annual";

	frappe.call({
		method: "gdl_pms.gdl_pms.doctype.pms_appraisal_cycle.pms_appraisal_cycle.get_applicable_employees_list",
		args: {
			grade_group: grade_group,
			cycle_name: cycle_name,
			cycle_type: cycle_type
		},
		callback: function(r) {
			if (r.message) {
				var data = r.message;
				var employees = data.employees || [];
				var stats = data.stats || {};

				// Populate child table if requested
				if (populate_table) {
					frm.clear_table("applicable_employees");
					employees.forEach(function(emp) {
						var row = frm.add_child("applicable_employees");
						row.employee = emp.employee;
						row.employee_name = emp.employee_name;
						row.employment_type = emp.employment_type || (cycle_type === "Probation" ? "Probation" : "Regular");
						row.grade_group = emp.grade_group;
						row.department = emp.department;
						row.designation = emp.designation;
						row.supervisor = emp.supervisor;
						row.supervisor_name = emp.supervisor_name;
						row.reviewer = emp.reviewer;
						row.reviewer_name = emp.reviewer_name;
						row.appraisal_status = emp.appraisal_status || "Not Created";
					});
					frm.refresh_field("applicable_employees");
				}

				// Render Summary Card Banner with employee chips
				render_summary_banner(frm, stats, grade_group, cycle_type, employees);
			}
		}
	});
}

function render_existing_summary(frm) {
	var employees = frm.doc.applicable_employees || [];
	if (!employees.length) {
		fetch_and_render_employees(frm, true);
		return;
	}

	var total = employees.length;
	var with_sup = 0;
	var with_rev = 0;
	var missing_list = [];

	employees.forEach(function(row) {
		var has_sup = row.supervisor && row.supervisor_name !== "Not Assigned";
		var has_rev = row.reviewer && row.reviewer_name !== "Not Assigned";

		if (has_sup) with_sup++;
		if (has_rev) with_rev++;

		if (!has_sup || !has_rev) {
			var reasons = [];
			if (!has_sup) reasons.push("Supervisor");
			if (!has_rev) reasons.push("Reviewer");
			missing_list.push({
				employee: row.employee,
				employee_name: row.employee_name,
				missing: reasons.join(", ")
			});
		}
	});

	var stats = {
		total: total,
		with_supervisor: with_sup,
		with_reviewer: with_rev,
		missing_supervisor: total - with_sup,
		missing_reviewer: total - with_rev,
		missing_any_count: missing_list.length,
		missing_hierarchy_list: missing_list
	};

	render_summary_banner(frm, stats, frm.doc.grade_group || "All", frm.doc.cycle_type || "Annual", employees);
}

function render_summary_banner(frm, stats, grade_group, cycle_type, employees_list) {
	if (!frm.fields_dict.employee_summary_html || !frm.fields_dict.employee_summary_html.$wrapper) return;

	cycle_type = cycle_type || frm.doc.cycle_type || "Annual";
	var total = stats.total || 0;
	var with_sup = stats.with_supervisor || 0;
	var with_rev = stats.with_reviewer || 0;
	var missing_count = stats.missing_any_count || 0;
	var missing_list = stats.missing_hierarchy_list || [];

	var is_probation = cycle_type === "Probation";
	var type_badge = is_probation
		? `<span style="background: #fef3c7; color: #b45309; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; border: 1px solid #fcd34d;">Probation Cycle (Probation Employees Only)</span>`
		: `<span style="background: #e0f2fe; color: #0369a1; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; border: 1px solid #bae6fd;">Annual Cycle (Regular & Contract)</span>`;

	var missing_alert_html = '';
	if (missing_count > 0) {
		var names_preview = missing_list.slice(0, 3).map(function(m) {
			return `${frappe.utils.escape_html(m.employee_name)} (Missing: ${m.missing})`;
		}).join("; ");

		if (missing_list.length > 3) {
			names_preview += ` +${missing_list.length - 3} more`;
		}

		missing_alert_html = `
			<div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 10px 14px; margin-top: 12px; display: flex; align-items: center; justify-content: space-between; gap: 10px;">
				<div style="display: flex; align-items: center; gap: 8px;">
					<div>
						<strong style="color: #b45309; font-size: 13px;">Reporting Hierarchy Incomplete:</strong>
						<span style="color: #92400e; font-size: 12px; margin-left: 4px;">${names_preview}</span>
					</div>
				</div>
				<span style="background: #fef3c7; color: #b45309; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 12px; white-space: nowrap; border: 1px solid #fcd34d;">
					${missing_count} Action Needed
				</span>
			</div>
		`;
	} else if (total > 0) {
		missing_alert_html = `
			<div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 8px 12px; margin-top: 10px; display: flex; align-items: center; gap: 8px;">
				<span style="font-size: 15px;">✅</span>
				<span style="color: #15803d; font-size: 12px; font-weight: 600;">All ${total} eligible employees have Supervisor & Reviewer assigned. Ready for appraisal rollout.</span>
			</div>
		`;
	}

	var employee_chips_html = '';
	if (employees_list && employees_list.length) {
		employee_chips_html = employees_list.map(function(e) {
			var emp_name = e.employee_name || e.employee;
			var emp_t = e.employment_type || (is_probation ? 'Probation' : 'Regular');
			var badge_color = emp_t === 'Probation' ? '#b45309' : (emp_t === 'Contract' ? '#6b21a8' : '#15803d');
			var badge_bg = emp_t === 'Probation' ? '#fef3c7' : (emp_t === 'Contract' ? '#f3e8ff' : '#dcfce7');
			var sup_text = e.supervisor_name && e.supervisor_name !== 'Not Assigned' ? ` • Sup: ${frappe.utils.escape_html(e.supervisor_name)}` : ' • <span style="color:#dc2626;">No Sup</span>';
			return `
				<div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px 8px; font-size: 11px; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
					<span style="font-weight: 600; color: #1e293b;">${frappe.utils.escape_html(emp_name)}</span>
					<span style="background: ${badge_bg}; color: ${badge_color}; font-size: 10px; font-weight: 700; padding: 1px 5px; border-radius: 4px;">${emp_t}</span>
					<span style="color: #64748b; font-size: 10px;">${sup_text}</span>
				</div>
			`;
		}).join('');
	} else {
		employee_chips_html = `<span style="font-size: 12px; color: #94a3b8; font-style: italic;">No active employees found matching criteria.</span>`;
	}

	var html = `
		<div class="pms-cycle-emp-summary-box" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
			<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
				<div style="font-weight: 700; font-size: 14px; color: #0f172a; display: flex; align-items: center; gap: 6px;">
					<span></span> Cycle Coverage & Reporting Hierarchy
				</div>
				<div style="display: flex; gap: 8px; align-items: center;">
					${type_badge}
					<span style="background: #f1f5f9; color: #475569; font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 6px;">
						Grade Group: ${frappe.utils.escape_html(grade_group)}
					</span>
				</div>
			</div>
			<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
				<!-- Card 1 -->
				<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 14px; border-left: 4px solid #15803d;">
					<div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase;">Total Eligible</div>
					<div style="font-size: 22px; font-weight: 700; color: #0f172a; margin-top: 2px;">${total}</div>
					<div style="font-size: 11px; color: #15803d;">${is_probation ? "Probation Employees" : "Regular & Contract"}</div>
				</div>
				<!-- Card 2 -->
				<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 14px; border-left: 4px solid #2563eb;">
					<div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase;">With Supervisor</div>
					<div style="font-size: 22px; font-weight: 700; color: #1e40af; margin-top: 2px;">${with_sup} <span style="font-size: 13px; font-weight: 500; color: #64748b;">/ ${total}</span></div>
					<div style="font-size: 11px; color: #2563eb;">Supervisor Assigned</div>
				</div>
				<!-- Card 3 -->
				<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 14px; border-left: 4px solid #7c3aed;">
					<div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase;">With Reviewer</div>
					<div style="font-size: 22px; font-weight: 700; color: #6b21a8; margin-top: 2px;">${with_rev} <span style="font-size: 13px; font-weight: 500; color: #64748b;">/ ${total}</span></div>
					<div style="font-size: 11px; color: #7c3aed;">Reviewer Assigned</div>
				</div>
			</div>
			${missing_alert_html}

			<!-- Eligible Employees Chips Preview -->
			<div style="margin-top: 14px; border-top: 1px solid #f1f5f9; padding-top: 10px;">
				<div style="font-size: 12px; font-weight: 700; color: #334155; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
					<span>${is_probation ? "Probation Employees Included in this Cycle" : "Regular & Contract Employees Included in this Cycle"} (${total}):</span>
					<span style="font-size: 11px; color: #64748b; font-weight: normal;">(Edit reporting details in table below)</span>
				</div>
				<div style="display: flex; flex-wrap: wrap; gap: 6px; max-height: 120px; overflow-y: auto; padding: 4px 2px;">
					${employee_chips_html}
				</div>
			</div>
		</div>
	`;

	frm.fields_dict.employee_summary_html.$wrapper.html(html);
}

function is_hr_admin_user() {
	if (frappe.session && (frappe.session.user === "Administrator" || frappe.session.user === "hr.admin@gdl.bt")) return true;
	var allowed_roles = ["HR Admin", "HR Manager", "System Manager", "Administrator"];
	return allowed_roles.some(function(r) {
		return (frappe.user && typeof frappe.user.has_role === "function" && frappe.user.has_role(r))
			|| (frappe.boot && frappe.boot.user && frappe.boot.user.roles && frappe.boot.user.roles.includes(r))
			|| (frappe.user_roles && frappe.user_roles.includes(r));
	});
}

function show_employee_hierarchy_section(frm) {
	frm.toggle_display("applicable_employees_section", true);
	frm.toggle_display("employee_summary_html", true);
	frm.toggle_display("applicable_employees", true);
	frm.set_df_property("applicable_employees_section", "hidden", 0);
	frm.set_df_property("employee_summary_html", "hidden", 0);
	frm.set_df_property("applicable_employees", "hidden", 0);
}

function hide_employee_hierarchy_section(frm) {
	frm.toggle_display("applicable_employees_section", false);
	frm.toggle_display("employee_summary_html", false);
	frm.toggle_display("applicable_employees", false);
	frm.set_df_property("applicable_employees_section", "hidden", 1);
	frm.set_df_property("employee_summary_html", "hidden", 1);
	frm.set_df_property("applicable_employees", "hidden", 1);
	if (frm.fields_dict.employee_summary_html && frm.fields_dict.employee_summary_html.$wrapper) {
		frm.fields_dict.employee_summary_html.$wrapper.empty();
	}
}
