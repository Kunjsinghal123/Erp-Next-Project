frappe.query_reports["PMS Employee Report"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "cycle",
			"label": __("Appraisal Cycle"),
			"fieldtype": "Link",
			"options": "PMS Appraisal Cycle"
		}
	]
};
