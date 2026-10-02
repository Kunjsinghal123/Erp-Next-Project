"""
GDL Performance Management System - Central Email Service
================================================================================
You can switch email providers at any time just by changing `ACTIVE_PROVIDER`.

Supported Providers:
  - "resend"         : Send via Resend REST API (Recommended - fast, modern, reliable)
  - "postmark"       : Send via Postmark REST API
  - "smtp"           : Direct SMTP (Gmail, Brevo, SendGrid, custom company mail server)
  - "frappe_default" : Native Frappe Desk Email Account (frappe.sendmail)
================================================================================
"""

import os
import json
import urllib.request
import urllib.error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Try importing frappe if running within Frappe runtime
try:
    import frappe
except ImportError:
    frappe = None


# ==============================================================================
# 1. CENTRAL CONFIGURATION (CHANGE SERVICE HERE)
# ==============================================================================

# Choose one: "resend" | "postmark" | "smtp" | "frappe_default"
ACTIVE_PROVIDER = os.environ.get("PMS_EMAIL_PROVIDER", "resend")

# Default Sender Display & Address
# Note: For Resend free testing, use "onboarding@resend.dev". In production, use your verified domain (e.g. "pms@gdl.bt").
DEFAULT_FROM_EMAIL = os.environ.get("PMS_FROM_EMAIL", "GDL PMS <onboarding@resend.dev>")

# Provider Specific Credentials & Settings
PROVIDER_SETTINGS = {
    # Resend: https://resend.com
    "resend": {
        "api_key": os.environ.get("RESEND_API_KEY", "re_your_api_key_here"),
        "from_email": DEFAULT_FROM_EMAIL,
    },
    
    # Postmark: https://postmarkapp.com
    "postmark": {
        "server_token": os.environ.get("POSTMARK_SERVER_TOKEN", "your_postmark_token_here"),
        "from_email": DEFAULT_FROM_EMAIL,
    },
    
    # Generic SMTP (Gmail / Brevo / Custom Corporate Server)
    "smtp": {
        "host": os.environ.get("SMTP_HOST", "smtp.resend.com"),
        "port": int(os.environ.get("SMTP_PORT", 587)),
        "use_tls": os.environ.get("SMTP_USE_TLS", "True").lower() in ("true", "1", "yes"),
        "username": os.environ.get("SMTP_USER", "resend"),
        "password": os.environ.get("SMTP_PASSWORD", "your_smtp_password_here"),
        "from_email": DEFAULT_FROM_EMAIL,
    },
    
    # Native Frappe Desk Email Account (Configured in Desk -> Settings -> Email Account)
    "frappe_default": {
        "from_email": None,  # Frappe uses default outgoing email account
    }
}


# ==============================================================================
# 2. HTML EMAIL TEMPLATE BUILDER
# ==============================================================================

def build_pms_email_html(title, recipient_name, message, details=None, cta_url=None, cta_text="View in PMS Portal"):
    """
    Builds a responsive, high-aesthetic HTML email template for GDL PMS.
    """
    recipient_display = recipient_name or "Colleague"
    
    # Render details table if provided
    details_html = ""
    if details and isinstance(details, dict):
        rows = ""
        for key, value in details.items():
            if value:
                rows += f"""
                <tr>
                    <td style="padding: 9px 14px; font-size: 13px; color: #64748b; font-weight: 600; border-bottom: 1px solid #f1f5f9; width: 38%;">{key}</td>
                    <td style="padding: 9px 14px; font-size: 13px; color: #1e293b; font-weight: 500; border-bottom: 1px solid #f1f5f9;">{value}</td>
                </tr>
                """
        if rows:
            details_html = f"""
            <table style="width: 100%; border-collapse: separate; border-spacing: 0; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; margin: 20px 0;">
                {rows}
            </table>
            """

    # Call to action button
    cta_html = ""
    if cta_url:
        cta_html = f"""
        <div style="text-align: center; margin: 28px 0 16px;">
            <a href="{cta_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 600; display: inline-block; box-shadow: 0 2px 4px rgba(37,99,235,0.2);">
                {cta_text} &rarr;
            </a>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body style="margin: 0; padding: 24px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; color: #334155;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
            <!-- Header -->
            <tr>
                <td style="padding: 24px 32px; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8; font-weight: 700; margin-bottom: 4px;">GDL Performance Management System</div>
                    <div style="font-size: 20px; font-weight: 700; color: #ffffff;">{title}</div>
                </td>
            </tr>

            <!-- Body -->
            <tr>
                <td style="padding: 32px;">
                    <p style="margin: 0 0 16px; font-size: 15px; color: #1e293b; font-weight: 600;">Dear {recipient_display},</p>
                    <div style="font-size: 14px; line-height: 1.6; color: #475569;">
                        {message}
                    </div>

                    {details_html}
                    {cta_html}

                    <p style="margin: 24px 0 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                        This is an automated notification from the GDL PMS Portal. Please do not reply directly to this email.
                    </p>
                </td>
            </tr>

            <!-- Footer -->
            <tr>
                <td style="padding: 16px 32px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center;">
                    &copy; GDL Performance Management System &bull; Confidential &bull; All rights reserved.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html


# ==============================================================================
# 3. LOW-LEVEL PROVIDER DISPATCHERS
# ==============================================================================

def _send_via_resend(from_email, recipients, subject, html_content, text_content=None):
    """Sends email using Resend REST API (Zero external dependencies)."""
    settings = PROVIDER_SETTINGS.get("resend", {})
    api_key = settings.get("api_key")
    
    if not api_key or "your_api_key_here" in api_key:
        msg = f"[Resend Demo Mode] RESEND_API_KEY is not set. Skipped actual delivery to {recipients}. Subject: {subject}"
        _log(msg, level="warning")
        return {"success": False, "simulated": True, "error": "RESEND_API_KEY not configured"}

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "User-Agent": "GDL-PMS/1.0"
    }
    
    payload = {
        "from": from_email or settings.get("from_email") or DEFAULT_FROM_EMAIL,
        "to": recipients if isinstance(recipients, list) else [recipients],
        "subject": subject,
        "html": html_content
    }
    if text_content:
        payload["text"] = text_content

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            _log(f"Email successfully sent via Resend to {recipients}. ID: {result.get('id')}")
            return {"success": True, "provider": "resend", "data": result}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        _log(f"Resend HTTP error ({e.code}): {err_msg}", level="error")
        return {"success": False, "provider": "resend", "error": err_msg, "code": e.code}
    except Exception as e:
        _log(f"Resend send failed: {str(e)}", level="error")
        return {"success": False, "provider": "resend", "error": str(e)}


def _send_via_postmark(from_email, recipients, subject, html_content, text_content=None):
    """Sends email using Postmark REST API."""
    settings = PROVIDER_SETTINGS.get("postmark", {})
    token = settings.get("server_token")
    
    if not token or "your_postmark_token" in token:
        _log(f"[Postmark Demo Mode] Token not set. Skipped delivery to {recipients}.", level="warning")
        return {"success": False, "simulated": True, "error": "Postmark token not configured"}

    url = "https://api.postmarkapp.com/email"
    headers = {
        "X-Postmark-Server-Token": token.strip(),
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    to_str = ", ".join(recipients) if isinstance(recipients, list) else recipients
    payload = {
        "From": from_email or settings.get("from_email") or DEFAULT_FROM_EMAIL,
        "To": to_str,
        "Subject": subject,
        "HtmlBody": html_content,
        "TextBody": text_content or message_to_plain_text(html_content)
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            _log(f"Email sent via Postmark to {recipients}.")
            return {"success": True, "provider": "postmark", "data": result}
    except Exception as e:
        _log(f"Postmark send failed: {str(e)}", level="error")
        return {"success": False, "provider": "postmark", "error": str(e)}


def _send_via_smtp(from_email, recipients, subject, html_content, text_content=None):
    """Sends email via standard SMTP (Gmail, Brevo, SendGrid, etc.)."""
    settings = PROVIDER_SETTINGS.get("smtp", {})
    host = settings.get("host")
    port = settings.get("port", 587)
    username = settings.get("username")
    password = settings.get("password")
    use_tls = settings.get("use_tls", True)
    sender = from_email or settings.get("from_email") or DEFAULT_FROM_EMAIL

    to_list = recipients if isinstance(recipients, list) else [recipients]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(to_list)

    if text_content:
        msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(host, port, timeout=10)
        if use_tls:
            server.starttls()
        if username and password and "your_smtp_password" not in password:
            server.login(username, password)
        server.sendmail(sender, to_list, msg.as_string())
        server.quit()
        _log(f"Email successfully sent via SMTP ({host}) to {to_list}")
        return {"success": True, "provider": "smtp"}
    except Exception as e:
        _log(f"SMTP send failed: {str(e)}", level="error")
        return {"success": False, "provider": "smtp", "error": str(e)}


def _send_via_frappe_default(from_email, recipients, subject, html_content, text_content=None):
    """Sends email using native Frappe Desk Email Account."""
    if not frappe:
        return {"success": False, "error": "Frappe runtime is not available"}
        
    try:
        frappe.sendmail(
            recipients=recipients if isinstance(recipients, list) else [recipients],
            sender=from_email,
            subject=subject,
            message=html_content,
            now=False
        )
        _log(f"Queued email in Frappe Email Queue to {recipients}")
        return {"success": True, "provider": "frappe_default"}
    except Exception as e:
        _log(f"Frappe sendmail failed: {str(e)}", level="error")
        return {"success": False, "provider": "frappe_default", "error": str(e)}


# ==============================================================================
# 4. UNIFIED PUBLIC SEND FUNCTION
# ==============================================================================

def send_pms_email(recipients, subject, message, title=None, details=None, cta_url=None, cta_text="View in PMS Portal", from_email=None):
    """
    Main unified function to send emails in PMS.
    Automatically respects ACTIVE_PROVIDER.
    """
    if not recipients:
        _log("send_pms_email skipped: no recipients provided.", level="warning")
        return {"success": False, "error": "No recipients"}

    if isinstance(recipients, str):
        recipients = [recipients.strip()]

    # Filter out empty or test invalid strings
    valid_recipients = [r for r in recipients if r and "@" in r]
    if not valid_recipients:
        _log(f"No valid email addresses in recipients list: {recipients}", level="warning")
        return {"success": False, "error": "No valid email addresses"}

    # Generate beautiful HTML
    html_title = title or subject
    html_content = build_pms_email_html(
        title=html_title,
        recipient_name="",
        message=message,
        details=details,
        cta_url=cta_url,
        cta_text=cta_text
    )

    provider = (ACTIVE_PROVIDER or "resend").lower().strip()

    if provider == "resend":
        return _send_via_resend(from_email, valid_recipients, subject, html_content, text_content=message)
    elif provider == "postmark":
        return _send_via_postmark(from_email, valid_recipients, subject, html_content, text_content=message)
    elif provider == "smtp":
        return _send_via_smtp(from_email, valid_recipients, subject, html_content, text_content=message)
    elif provider == "frappe_default":
        return _send_via_frappe_default(from_email, valid_recipients, subject, html_content, text_content=message)
    else:
        # Fallback to resend
        _log(f"Unknown email provider '{provider}', falling back to Resend.", level="warning")
        return _send_via_resend(from_email, valid_recipients, subject, html_content, text_content=message)


# ==============================================================================
# 5. SPECIFIC PMS WORKFLOW EMAIL HELPERS
# ==============================================================================

def notify_plan_submitted(appraisal_doc, supervisor_email):
    """Triggered when Employee submits targets for approval."""
    emp_name = appraisal_doc.get("employee_name") or appraisal_doc.get("employee")
    details = {
        "Appraisal ID": appraisal_doc.name,
        "Employee": f"{emp_name} ({appraisal_doc.get('employee')})",
        "Cycle": appraisal_doc.get("cycle_name") or appraisal_doc.get("appraisal_cycle") or "Current Cycle",
        "Action Required": "Please review and approve or return the performance targets"
    }
    msg = f"<p><strong>{emp_name}</strong> has submitted their Performance Plan for your review and approval.</p>"
    return send_pms_email(
        recipients=supervisor_email,
        subject=f"Action Required: Performance Plan Submitted by {emp_name}",
        title="Performance Plan Approval Pending",
        message=msg,
        details=details
    )


def notify_plan_returned(appraisal_doc, employee_email, remark, returned_by_role="Supervisor"):
    """Triggered when Supervisor/Reviewer returns targets for revision."""
    details = {
        "Appraisal ID": appraisal_doc.name,
        "Returned By": returned_by_role,
        "Reason / Remarks": remark or "Please review the notes and adjust your targets.",
        "Action Required": "Update your targets and re-submit for approval"
    }
    msg = f"<p>Your Performance Plan has been returned by your {returned_by_role} with revision remarks.</p>"
    return send_pms_email(
        recipients=employee_email,
        subject=f"Revision Required: Performance Plan ({appraisal_doc.name})",
        title="Performance Plan Returned for Revision",
        message=msg,
        details=details
    )


def notify_plan_approved(appraisal_doc, employee_email):
    """Triggered when Performance Plan is finally approved."""
    details = {
        "Appraisal ID": appraisal_doc.name,
        "Status": "Approved (Monitoring Phase Active)",
        "Next Phase": "Mid-Year Monitoring & Target Progress Tracking"
    }
    msg = "<p>Congratulations! Your Performance Plan has been reviewed and officially approved.</p>"
    return send_pms_email(
        recipients=employee_email,
        subject=f"Approved: Performance Plan ({appraisal_doc.name})",
        title="Performance Plan Approved",
        message=msg,
        details=details
    )


def notify_self_assessment_submitted(appraisal_doc, supervisor_email):
    """Triggered when Employee submits their Self-Assessment."""
    emp_name = appraisal_doc.get("employee_name") or appraisal_doc.get("employee")
    details = {
        "Appraisal ID": appraisal_doc.name,
        "Employee": f"{emp_name} ({appraisal_doc.get('employee')})",
        "Action Required": "Complete Supervisor Evaluation & Scoring"
    }
    msg = f"<p><strong>{emp_name}</strong> has completed their Self-Assessment for the current appraisal cycle. Your evaluation is now required.</p>"
    return send_pms_email(
        recipients=supervisor_email,
        subject=f"Action Required: Self-Assessment Submitted by {emp_name}",
        title="Self-Assessment Evaluation Pending",
        message=msg,
        details=details
    )


def notify_supervisor_scores_submitted(appraisal_doc, employee_email):
    """Triggered when Supervisor completes evaluation scores."""
    details = {
        "Appraisal ID": appraisal_doc.name,
        "Action Required": "Log in to review scores and either Accept or Dispute"
    }
    msg = "<p>Your supervisor has completed their appraisal evaluation and submitted your scores. Please log in to review the feedback and accept or dispute the outcome.</p>"
    return send_pms_email(
        recipients=employee_email,
        subject=f"Review Ready: Supervisor Evaluation Completed ({appraisal_doc.name})",
        title="Supervisor Evaluation Scores Ready",
        message=msg,
        details=details
    )


def notify_dispute_raised(appraisal_doc, reviewer_email, reason):
    """Triggered when Employee raises a dispute."""
    emp_name = appraisal_doc.get("employee_name") or appraisal_doc.get("employee")
    details = {
        "Appraisal ID": appraisal_doc.name,
        "Employee": f"{emp_name} ({appraisal_doc.get('employee')})",
        "Dispute Reason": reason or "Disagreed with supervisor scores",
        "Action Required": "Review dispute and submit 2nd-level decision"
    }
    msg = f"<p><strong>{emp_name}</strong> has raised a dispute regarding their supervisor's appraisal scoring. Your intervention as Reviewer is required.</p>"
    return send_pms_email(
        recipients=reviewer_email,
        subject=f"Dispute Alert: Appraisal Score Disputed by {emp_name}",
        title="Appraisal Scoring Dispute Raised",
        message=msg,
        details=details
    )


def notify_appraisal_locked(appraisal_doc, employee_email, final_score):
    """Triggered when Appraisal is finalized and locked."""
    details = {
        "Appraisal ID": appraisal_doc.name,
        "Final Score": f"{final_score:.2f}" if final_score is not None else "Finalized",
        "Status": "Locked & Complete"
    }
    msg = "<p>Your performance appraisal cycle has been officially finalized, verified, and locked.</p>"
    return send_pms_email(
        recipients=employee_email,
        subject=f"Completed: Appraisal Finalized ({appraisal_doc.name})",
        title="Appraisal Finalized & Locked",
        message=msg,
        details=details
    )


# ==============================================================================
# 6. INTERNAL UTILITIES
# ==============================================================================

def message_to_plain_text(html_text):
    """Simple plain-text converter fallback."""
    import re
    clean = re.sub(r"<[^>]+>", " ", html_text or "")
    return " ".join(clean.split())


def _log(msg, level="info"):
    """Logs to frappe logger if present, or stdout."""
    if frappe:
        logger = frappe.logger("gdl_pms_email")
        if level == "error":
            logger.error(msg)
        elif level == "warning":
            logger.warning(msg)
        else:
            logger.info(msg)
    else:
        print(f"[{level.upper()}] {msg}")
