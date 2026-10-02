frappe.query_reports["PMS Office Report"] = {
	"filters": [
		{
			"fieldname": "department",
			"label": __("Office"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "cycle",
			"label": __("Appraisal Cycle"),
			"fieldtype": "Link",
			"options": "PMS Appraisal Cycle"
		}
	]
};
