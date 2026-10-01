import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def create_task_list_docx(filename):
    doc = docx.Document()
    
    # Page Setup - Standard Margins (1 inch)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("List of Tasks Performed:")
    title_run.font.name = "Arial"
    title_run.font.size = Pt(16)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)
    
    # Add spacing after title
    title_p.paragraph_format.space_after = Pt(18)

    # Task Data
    tasks = [
        "Reviewed full e-Recruitment and PMS (Performance Management System) requirement documents across Public, Applicant, Employee, Supervisor, Reviewer, and HR portal sections.",
        "Mapped functional and technical requirements against standard Frappe HRMS and ERPNext modules to identify standard features vs. custom gap areas.",
        "Identified customization areas requiring custom app development (appraisal scoring engine, mid-cycle amendments, PERC committee review, portal dashboards).",
        "Structured findings into phases (Foundation -> Setup -> Goal Setting -> Self Assessment -> Supervisor Evaluation -> Reviewer Review -> PERC Committee -> Deployment).",
        "Broke down each phase into granular technical sub-tasks and implementation milestones.",
        "Built Requirement-Gap-Feasibility tracker and architectural documentation.",
        "Set up local development environment with Frappe Bench, Frappe Framework, ERPNext, and HRMS app; configured MariaDB, Redis, and Node dependencies.",
        "Created new site and installed HRMS on local bench for testing standard appraisal and employee doctypes.",
        "Scaffolded custom app 'gdl_pms', set up module structure, hooks.py, git repository, and folder conventions for DocTypes and custom assets.",
        "Designed solution architecture for Multi-tier Appraisal Workflow and custom dashboards layout (Employee, Supervisor, Reviewer, HR Admin).",
        "Defined custom data model for PMS: PMS Appraisal Cycle, PMS Appraisal, PMS Target, PMS Competency Score, PMS Plan Amendment, PMS Amendment Log, PERC Case, and PERC Committee Member.",
        "Implemented scoring calculation engine (scoring_engine.py) for automated computation of target completion percentages, weighted competency scores, and overall grades.",
        "Configured multi-level workflow states, transition rules, and validation checks across evaluation phases.",
        "Configured role-based permission control (RBAC) scripts (fix_permissions.py, setup_employee_perms.py, employee_hooks.py) for strict user data isolation.",
        "Created custom Desk Workspaces (pms_reviewer.json, etc.) and styled theme bundle (gdl_pms_theme.bundle.css) for consistent branding and visual badges.",
        "Built custom query/script reports: PMS Completion Report, PMS Employee Report, and PMS Score Analysis.",
        "Configured custom PDF Print Formats (setup_print_formats.py) for exporting completed appraisals, scorecards, and committee decision letters.",
        "Created automated demo user creation scripts and hierarchy linking (create_indian_demo_users.py, setup_supervisor_2.py).",
        "Verified bench/app/site setup, added API endpoints (dashboard_api.py), and completed workflow end-to-end testing (test_amendment_flow.py, test_supervisor_2_flow.py)."
    ]

    # Create Table: 2 columns
    table = doc.add_table(rows=1 + len(tasks), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Define Column Widths: Project = 2.0 inches, Task = 4.5 inches
    col_widths = [Inches(2.0), Inches(4.5)]

    # Style Header Row
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Project"
    hdr_cells[1].text = "Task"

    # Header Styling
    header_bg_color = "4F81BD"  # Professional steel blue
    for i, cell in enumerate(hdr_cells):
        cell.width = col_widths[i]
        
        # Shading
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{header_bg_color}"/>')
        cell._tc.get_or_add_tcPr().append(shading)
        
        # Alignment & Padding
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            for r in p.runs:
                r.font.name = "Arial"
                r.font.size = Pt(11)
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Set repeat header on every page
    trPr = table.rows[0]._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

    # Populate Data Rows
    project_name = "DrukSmart ERPNext"

    for idx, task_text in enumerate(tasks, start=1):
        row_cells = table.rows[idx].cells
        
        # Row height / spacing
        row_cells[0].width = col_widths[0]
        row_cells[1].width = col_widths[1]

        row_cells[0].text = project_name
        row_cells[1].text = task_text

        # Alternating background shading (light blue tint vs white)
        if idx % 2 == 0:
            bg_color = "F2F5F9"
            for cell in row_cells:
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_color}"/>')
                cell._tc.get_or_add_tcPr().append(shading)

        # Style Project Cell
        p0 = row_cells[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p0.paragraph_format.space_before = Pt(4)
        p0.paragraph_format.space_after = Pt(4)
        if len(p0.runs) > 0:
            p0.runs[0].font.name = "Arial"
            p0.runs[0].font.size = Pt(10)
            p0.runs[0].font.bold = True
            p0.runs[0].font.color.rgb = RGBColor(0x33, 0x33, 0x33)

        # Style Task Cell
        p1 = row_cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p1.paragraph_format.space_before = Pt(4)
        p1.paragraph_format.space_after = Pt(4)
        if len(p1.runs) > 0:
            p1.runs[0].font.name = "Arial"
            p1.runs[0].font.size = Pt(10)
            p1.runs[0].font.color.rgb = RGBColor(0x22, 0x22, 0x22)

        # Vertical Alignment
        row_cells[0].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        row_cells[1].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # Apply Borders (Thin grey table grid)
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="D3D3D3"/>\n'
        f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="D3D3D3"/>\n'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>\n'
        f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>\n'
        f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="D3D3D3"/>\n'
        f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="D3D3D3"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

    doc.save(filename)
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    create_task_list_docx("/Users/imprabhav/Projects/erp-next project/List_of_Tasks_Completed.docx")
