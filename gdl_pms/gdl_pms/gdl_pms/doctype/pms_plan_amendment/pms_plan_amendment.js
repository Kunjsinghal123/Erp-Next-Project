frappe.ui.form.on("PMS Plan Amendment", {
    refresh: function(frm) {
        if (frm.is_new()) return;

        // Custom action buttons based on status
        if (frm.doc.status === "Draft" || frm.doc.status === "Rejected" || frm.doc.status === "Returned") {
            frm.add_custom_button(__("Submit for Approval"), function() {
                frappe.call({
                    method: "gdl_pms.gdl_pms.doctype.pms_plan_amendment.pms_plan_amendment.submit_amendment",
                    args: { docname: frm.doc.name },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(__("Amendment submitted for approval."));
                            frm.reload_doc();
                        }
                    }
                });
            }).addClass("btn-primary");
        }

        if (frm.doc.status === "Pending Supervisor Approval" || frm.doc.status === "Pending Reviewer Approval") {
            // Approve Button
            frm.add_custom_button(__("Approve Amendment"), function() {
                frappe.confirm(__("Are you sure you want to approve this target amendment?"), function() {
                    frappe.call({
                        method: "gdl_pms.gdl_pms.doctype.pms_plan_amendment.pms_plan_amendment.approve_amendment",
                        args: { docname: frm.doc.name },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint(__("Amendment Approved successfully."));
                                frm.reload_doc();
                            }
                        }
                    });
                });
            }).addClass("btn-success");

            // Return Button
            frm.add_custom_button(__("Return Amendment"), function() {
                frappe.prompt([
                    {
                        fieldname: "remark",
                        fieldtype: "Small Text",
                        label: __("Return Remark"),
                        reqd: 1
                    }
                ], function(values) {
                    frappe.call({
                        method: "gdl_pms.gdl_pms.doctype.pms_plan_amendment.pms_plan_amendment.reject_amendment",
                        args: {
                            docname: frm.doc.name,
                            remark: values.remark
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint(__("Amendment Returned."));
                                frm.reload_doc();
                            }
                        }
                    });
                }, __("Return Amendment"), __("Submit Return"));
            }).addClass("btn-danger");
        }

        // Set read-only state for revised_targets if not in Draft state
        if (frm.doc.status !== "Draft") {
            frm.set_df_property("revised_targets", "read_only", 1);
            frm.set_df_property("reason", "read_only", 1);
        } else {
            frm.set_df_property("revised_targets", "read_only", 0);
            frm.set_df_property("reason", "read_only", 0);
        }
    }
});
