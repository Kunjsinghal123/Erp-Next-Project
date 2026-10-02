function update_pms_sidebar_active(mode) {
	setTimeout(function() {
		var $sidebar = $('.body-sidebar, .desk-sidebar');
		if (!$sidebar.length) return;
		var $planItem = $sidebar.find('.sidebar-item-container[item-name="PMS Performance Plan"] .standard-sidebar-item');
		var $appraisalItem = $sidebar.find('.sidebar-item-container[item-name="PMS Appraisal Form"] .standard-sidebar-item');
		if (mode === "appraisal") {
			$planItem.removeClass('active-sidebar selected');
			$appraisalItem.addClass('active-sidebar selected');
		} else {
			$appraisalItem.removeClass('active-sidebar selected');
			$planItem.addClass('active-sidebar selected');
		}
	}, 100);
}

frappe.listview_settings['PMS Appraisal'] = {
	add_fields: ["employee", "employee_name", "cycle", "plan_status", "workflow_state", "appraisal_status", "total_score", "rating_band"],
	
	formatters: {
		employee_name(val, df, doc) {
			if (val) {
				return `<span style="font-weight: 600; color: var(--text-color);">${frappe.utils.escape_html(val)}</span>`;
			}
			return val;
		},
		appraisal_status(val, df, doc) {
			if (!val || val === "Not Activated") {
				return `<span class="text-muted small">Not Activated</span>`;
			}
			let color = "blue";
			if (val === "Appraisal Accepted" || val === "Finalized & Locked") color = "green";
			else if (val.includes("Dispute") || val.includes("PERC")) color = "orange";
			else if (val.includes("Supervisor")) color = "purple";
			return `<span class="indicator-pill ${color} small">${frappe.utils.escape_html(val)}</span>`;
		},
		total_score(val, df, doc) {
			if (val != null && doc.appraisal_status && doc.appraisal_status !== "Not Activated") {
				return `<strong style="color: #15803d;">${flt(val, 2)}</strong>`;
			}
			return "--";
		}
	},

	onload: function(listview) {
		listview.apply_pms_view_mode = function(mode, force_reload, extra_filters) {
			if (!mode) mode = "plan";
			listview._current_view_mode = mode;
			localStorage.setItem("pms_view_mode", mode);
			let is_appraisal = (mode === "appraisal");

			// 1. Update Title
			if (listview.page && listview.page.set_title) {
				listview.page.set_title(is_appraisal ? __("PMS Appraisal Form") : __("PMS Performance Plan"));
			}

			// 2. Update In-page Tab Buttons
			let $tabs = listview.$page.find('.pms-view-mode-tabs');
			if ($tabs.length) {
				if (is_appraisal) {
					$tabs.find('.tab-plans').removeClass('btn-primary text-white').addClass('btn-default');
					$tabs.find('.tab-appraisals').removeClass('btn-default').addClass('btn-primary text-white');
				} else {
					$tabs.find('.tab-plans').removeClass('btn-default').addClass('btn-primary text-white');
					$tabs.find('.tab-appraisals').removeClass('btn-primary text-white').addClass('btn-default');
				}
			}

			// 3. Update Primary Action Button
			let is_supervisor_2_only = frappe.user_roles && frappe.user_roles.includes("Supervisor 2") &&
				!frappe.user_roles.includes("System Manager") &&
				!frappe.user_roles.includes("HR Admin") &&
				!frappe.user_roles.includes("HR Manager") &&
				!frappe.user_roles.includes("Employee") &&
				!frappe.user_roles.includes("Supervisor") &&
				!frappe.user_roles.includes("Reviewer");

			if (listview.page && listview.page.btn_primary) {
				if (is_appraisal || is_supervisor_2_only) {
					listview.page.btn_primary.hide();
				} else {
					listview.page.btn_primary.show();
					listview.page.set_primary_action(__("Add PMS Performance Plan"), function() {
						frappe.new_doc("PMS Appraisal");
					});
				}
			}

			// 4. Update Sidebar Active Item
			update_pms_sidebar_active(mode);

			// 5. Update Filters
			if (listview.filter_area) {
				let filter_cond = is_appraisal ? "!=" : "=";
				let filters_to_add = [
					["PMS Appraisal", "appraisal_status", filter_cond, "Not Activated", false]
				];
				if (extra_filters && Array.isArray(extra_filters)) {
					filters_to_add = filters_to_add.concat(extra_filters);
				}

				let clear_p = (listview.filter_area.clear) ? listview.filter_area.clear(false) : Promise.resolve();
				if (clear_p && clear_p.then) {
					clear_p.then(() => {
						listview.filter_area.add(filters_to_add, true);
					});
				} else {
					listview.filter_area.add(filters_to_add, true);
				}
			} else if (force_reload) {
				listview.refresh();
			}
		};

		let view_mode = "plan";
		if (frappe.route_options && frappe.route_options.view_mode) {
			view_mode = frappe.route_options.view_mode;
			delete frappe.route_options.view_mode;
			localStorage.setItem("pms_view_mode", view_mode);
		} else if (localStorage.getItem("pms_view_mode")) {
			view_mode = localStorage.getItem("pms_view_mode");
		}

		let extra_filters = [];
		if (frappe.route_options && typeof frappe.route_options.plan_status === "string" && frappe.route_options.plan_status.includes('["in"')) {
			try {
				let parsed = JSON.parse(frappe.route_options.plan_status);
				delete frappe.route_options.plan_status;
				extra_filters.push(["PMS Appraisal", "plan_status", "in", parsed[1], false]);
				view_mode = "plan";
				localStorage.setItem("pms_view_mode", "plan");
			} catch(e) {}
		}

		listview.apply_pms_view_mode(view_mode, false, extra_filters);

		// Ensure row clicks remember the current view mode
		$(listview.wrapper).on('click', '.list-row, .list-subject a, .list-row-container', function() {
			localStorage.setItem("pms_view_mode", listview._current_view_mode || "plan");
		});
	},

	refresh: function(listview) {
		// Ensure apply_pms_view_mode is defined on listview
		if (!listview.apply_pms_view_mode) {
			listview.apply_pms_view_mode = function(mode, force_reload, extra_filters) {
				if (!mode) mode = "plan";
				listview._current_view_mode = mode;
				localStorage.setItem("pms_view_mode", mode);
				let is_appraisal = (mode === "appraisal");

				if (listview.page && listview.page.set_title) {
					listview.page.set_title(is_appraisal ? __("PMS Appraisal Form") : __("PMS Performance Plan"));
				}

				let $tabs = listview.$page.find('.pms-view-mode-tabs');
				if ($tabs.length) {
					if (is_appraisal) {
						$tabs.find('.tab-plans').removeClass('btn-primary text-white').addClass('btn-default');
						$tabs.find('.tab-appraisals').removeClass('btn-default').addClass('btn-primary text-white');
					} else {
						$tabs.find('.tab-plans').removeClass('btn-default').addClass('btn-primary text-white');
						$tabs.find('.tab-appraisals').removeClass('btn-primary text-white').addClass('btn-default');
					}
				}

				let is_supervisor_2_only = frappe.user_roles && frappe.user_roles.includes("Supervisor 2") &&
					!frappe.user_roles.includes("System Manager") &&
					!frappe.user_roles.includes("HR Admin") &&
					!frappe.user_roles.includes("HR Manager") &&
					!frappe.user_roles.includes("Employee") &&
					!frappe.user_roles.includes("Supervisor") &&
					!frappe.user_roles.includes("Reviewer");

				if (listview.page && listview.page.btn_primary) {
					if (is_appraisal || is_supervisor_2_only) {
						listview.page.btn_primary.hide();
					} else {
						listview.page.btn_primary.show();
						listview.page.set_primary_action(__("Add PMS Performance Plan"), function() {
							frappe.new_doc("PMS Appraisal");
						});
					}
				}

				update_pms_sidebar_active(mode);

				if (listview.filter_area) {
					let filter_cond = is_appraisal ? "!=" : "=";
					let filters_to_add = [
						["PMS Appraisal", "appraisal_status", filter_cond, "Not Activated", false]
					];
					if (extra_filters && Array.isArray(extra_filters)) {
						filters_to_add = filters_to_add.concat(extra_filters);
					}

					let clear_p = (listview.filter_area.clear) ? listview.filter_area.clear(false) : Promise.resolve();
					if (clear_p && clear_p.then) {
						clear_p.then(() => {
							listview.filter_area.add(filters_to_add, true);
						});
					} else {
						listview.filter_area.add(filters_to_add, true);
					}
				} else if (force_reload) {
					listview.refresh();
				}
			};
		}

		// Render Tab Switcher (Performance Plans vs Appraisals)
		if (!listview.$page.find('.pms-view-mode-tabs').length) {
			let $tabs = $(`
				<div class="pms-view-mode-tabs btn-group" style="margin-right: 12px; display: inline-flex;">
					<button class="btn btn-sm btn-default tab-plans font-weight-bold" type="button">
						<i class="fa fa-clipboard" style="margin-right: 4px;"></i> ${__("Performance Plans")}
					</button>
					<button class="btn btn-sm btn-default tab-appraisals font-weight-bold" type="button">
						<i class="fa fa-check-circle" style="margin-right: 4px;"></i> ${__("Appraisals")}
					</button>
				</div>
			`);

			listview.page.page_actions.prepend($tabs);

			$tabs.find('.tab-plans').on('click', function() {
				listview.apply_pms_view_mode("plan", true);
			});

			$tabs.find('.tab-appraisals').on('click', function() {
				listview.apply_pms_view_mode("appraisal", true);
			});
		}

		// Check if a specific view mode was requested via route_options or localStorage
		let target_mode = null;
		if (frappe.route_options && frappe.route_options.view_mode) {
			target_mode = frappe.route_options.view_mode;
			delete frappe.route_options.view_mode;
		} else if (localStorage.getItem("pms_view_mode")) {
			target_mode = localStorage.getItem("pms_view_mode");
		} else {
			target_mode = listview._current_view_mode || "plan";
		}

		if (target_mode !== listview._current_view_mode) {
			listview.apply_pms_view_mode(target_mode, true);
			return;
		}

		let is_appraisal_mode = (listview._current_view_mode === "appraisal");

		// Set title based on current view mode
		listview.page.set_title(is_appraisal_mode ? __("PMS Appraisal Form") : __("PMS Performance Plan"));

		// Update tab active classes
		let $tabs = listview.$page.find('.pms-view-mode-tabs');
		if ($tabs.length) {
			if (is_appraisal_mode) {
				$tabs.find('.tab-plans').removeClass('btn-primary text-white').addClass('btn-default');
				$tabs.find('.tab-appraisals').removeClass('btn-default').addClass('btn-primary text-white');
			} else {
				$tabs.find('.tab-plans').removeClass('btn-default').addClass('btn-primary text-white');
				$tabs.find('.tab-appraisals').removeClass('btn-primary text-white').addClass('btn-default');
			}
		}

		// Primary Action Button
		let is_supervisor_2_only = frappe.user_roles && frappe.user_roles.includes("Supervisor 2") &&
			!frappe.user_roles.includes("System Manager") &&
			!frappe.user_roles.includes("HR Admin") &&
			!frappe.user_roles.includes("HR Manager") &&
			!frappe.user_roles.includes("Employee") &&
			!frappe.user_roles.includes("Supervisor") &&
			!frappe.user_roles.includes("Reviewer");

		if (listview.page.btn_primary) {
			if (is_appraisal_mode || is_supervisor_2_only) {
				listview.page.btn_primary.hide();
			} else {
				listview.page.btn_primary.show();
				listview.page.set_primary_action(__("Add PMS Performance Plan"), function() {
					frappe.new_doc("PMS Appraisal");
				});
			}
		}

		update_pms_sidebar_active(listview._current_view_mode || "plan");

		// Bulk Approve & Reject Actions for Supervisors/Reviewers on Plans
		let can_approve = frappe.user_roles && (frappe.user_roles.includes("Supervisor") ||
			frappe.user_roles.includes("Reviewer") ||
			frappe.user_roles.includes("System Manager"));

		if (can_approve && !is_appraisal_mode) {
			if (!listview._bulk_actions_added) {
				listview._bulk_actions_added = true;
				listview.page.add_actions_menu_item(__("Approve Selected Plans"), () => {
					let docnames = listview.get_checked_items().map(d => d.name);
					if (docnames.length === 0) return;
					
					frappe.call({
						method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.bulk_approve_plan",
						args: { docnames: docnames },
						callback: function(r) {
							if (!r.exc) {
								frappe.show_alert({message: __('Successfully Approved'), indicator: 'green'});
								listview.refresh();
							}
						}
					});
				});

				listview.page.add_actions_menu_item(__("Return Selected Plans"), () => {
					let docnames = listview.get_checked_items().map(d => d.name);
					if (docnames.length === 0) return;
					
					frappe.prompt(
						{ fieldtype: "Small Text", fieldname: "remark", label: __("Return Remark"), reqd: 1 },
						function(values) {
							frappe.call({
								method: "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.bulk_reject_plan",
								args: { docnames: docnames, remark: values.remark },
								callback: function(res) {
									if (!res.exc) {
										frappe.show_alert({message: __('Successfully Returned'), indicator: 'orange'});
										listview.refresh();
									}
								}
							});
						},
						__("Return Plans"),
						__("Return")
					);
				});
			}
		}
	}
};
