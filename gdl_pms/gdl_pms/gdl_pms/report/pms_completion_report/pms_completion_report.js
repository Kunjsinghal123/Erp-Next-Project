frappe.query_reports["PMS Completion Report"] = {
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
		}
	]
};
