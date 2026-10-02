import frappe

def get_base_html(title, is_final):
    score_cols = ""
    if is_final:
        score_cols = """
            <th>Self Score</th>
            <th>Supervisor Score</th>
            <th>Reviewer Score</th>
        """
        
    score_cells_target = ""
    if is_final:
        score_cells_target = """
            <td>{{ t.self_score or "" }}</td>
            <td>{{ t.supervisor_score or "" }}</td>
            <td>{{ t.reviewer_score or "" }}</td>
        """
        
    score_cells_comp = ""
    if is_final:
        score_cells_comp = """
            <td>{{ c.self_rating or "" }}</td>
            <td>{{ c.supervisor_rating or "" }}</td>
            <td>{{ c.reviewer_rating or "" }}</td>
        """
        
    final_scores = ""
    if is_final:
        final_scores = """
        <div class="row" style="margin-top: 30px;">
            <div class="col-xs-12">
                <h4>Final Scoring</h4>
                <table class="table table-bordered">
                    <tr>
                        <th width="30%">Total Score</th>
                        <td>{{ doc.total_score or "" }}</td>
                    </tr>
                    <tr>
                        <th>Rating Band</th>
                        <td>{{ doc.rating_band or "" }}</td>
                    </tr>
                </table>
            </div>
        </div>
        """

    html = f"""
    <style>
        .pms-header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #ccc; padding-bottom: 10px; }}
        .pms-table th {{ background-color: #f8f9fa; }}
        .signature-box {{ margin-top: 50px; text-align: center; }}
        .sig-line {{ border-top: 1px solid #000; margin-top: 50px; width: 80%; margin-left: auto; margin-right: auto; }}
    </style>
    
    <div class="pms-header">
        <h2>GreenDigital Limited (GDL)</h2>
        <h3>{title}</h3>
        <h4>Cycle: {{{{ doc.cycle }}}} | Grade Group: {{{{ doc.grade_group }}}}</h4>
    </div>
    
    <div class="row">
        <div class="col-xs-6">
            <strong>Employee:</strong> {{{{ doc.employee }}}}<br>
        </div>
        <div class="col-xs-6 text-right">
            <strong>Date:</strong> {{{{ frappe.utils.formatdate(doc.modified) }}}}<br>
        </div>
    </div>
    
    <div class="row" style="margin-top: 20px;">
        <div class="col-xs-12">
            <h4>Part A: Work Targets</h4>
            <table class="table table-bordered pms-table">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Weight</th>
                        {score_cols}
                    </tr>
                </thead>
                <tbody>
                    {{% for t in doc.targets %}}
                    <tr>
                        <td>{{{{ t.description }}}}</td>
                        <td>{{{{ t.weight }}}}</td>
                        {score_cells_target}
                    </tr>
                    {{% endfor %}}
                </tbody>
            </table>
        </div>
    </div>
    
    <div class="row" style="margin-top: 20px;">
        <div class="col-xs-12">
            <h4>Part B: Core Competencies</h4>
            <table class="table table-bordered pms-table">
                <thead>
                    <tr>
                        <th>Competency</th>
                        <th>Weight</th>
                        {score_cols}
                    </tr>
                </thead>
                <tbody>
                    {{% for c in doc.competencies %}}
                    <tr>
                        <td>{{{{ c.competency }}}}</td>
                        <td>{{{{ c.weight }}}}</td>
                        {score_cells_comp}
                    </tr>
                    {{% endfor %}}
                </tbody>
            </table>
        </div>
    </div>
    
    {final_scores}
    
    <div class="row signature-box">
        <div class="col-xs-4">
            <div class="sig-line"></div>
            Employee Signature
        </div>
        <div class="col-xs-4">
            <div class="sig-line"></div>
            Supervisor Signature
        </div>
        <div class="col-xs-4">
            <div class="sig-line"></div>
            Reviewer Signature
        </div>
    </div>
    """
    
    return html

def run():
    frappe.logger().info("Creating Print Formats for PMS...")
    
    formats = [
        {"name": "Annexure 5.1 (Planning Phase - PS_CS)", "title": "Performance Appraisal - Planning Phase", "final": False},
        {"name": "Annexure 5.2 (Planning Phase - OS_ESP)", "title": "Performance Appraisal - Planning Phase", "final": False},
        {"name": "Annexure 5.3 (Final Appraisal - PS_CS)", "title": "Final Performance Appraisal", "final": True},
        {"name": "Annexure 5.4 (Final Appraisal - OS_ESP)", "title": "Final Performance Appraisal", "final": True},
    ]
    
    for fmt in formats:
        if not frappe.db.exists("Print Format", fmt["name"]):
            doc = frappe.get_doc({
                "doctype": "Print Format",
                "name": fmt["name"],
                "doc_type": "PMS Appraisal",
                "custom_format": 1,
                "print_format_builder": 0,
                "html": get_base_html(fmt["title"], fmt["final"]),
                "module": "Gdl Pms"
            })
            doc.insert(ignore_permissions=True)
            frappe.logger().info(f"Created Print Format: {fmt['name']}")
        else:
            frappe.logger().info(f"Print Format {fmt['name']} already exists.")
            
    frappe.db.commit()
    print("Successfully created Print Formats.")
