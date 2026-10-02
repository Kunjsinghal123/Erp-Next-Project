frappe.query_reports["PMS Score Analysis"] = {
	"filters": [
		{
			"fieldname": "cycle",
			"label": __("Appraisal Cycle"),
			"fieldtype": "Link",
			"options": "PMS Appraisal Cycle"
		},
		{
			"fieldname": "department",
			"label": __("Office"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "grade_group",
			"label": __("Grade Group"),
			"fieldtype": "Select",
			"options": "\nPS_CS\nOS_ESP"
		}
	]
};
