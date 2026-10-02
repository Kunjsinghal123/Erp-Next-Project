frappe.listview_settings['PMS Plan Amendment'] = {
	add_fields: ["employee", "employee_name", "performance_plan", "status"],
	formatters: {
		employee(val, df, doc) {
			if (doc && doc.employee_name) {
				return `<span style="font-weight: 600; color: var(--text-color);">${frappe.utils.escape_html(doc.employee_name)}</span> <span class="text-muted small">(${frappe.utils.escape_html(val)})</span>`;
			}
			return val;
		},
		employee_name(val, df, doc) {
			if (val) {
				return `<span style="font-weight: 600; color: var(--text-color);">${frappe.utils.escape_html(val)}</span>`;
			}
			return val;
		}
	}
};
