"""
Email service using Resend for transactional emails.
"""

import resend
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.email')


def send_report_email(to_email: str, user_name: str, project_name: str, project_id: str, markdown_content: str = None):
    """
    Send the completed prediction report to the user's email.
    """
    if not Config.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email")
        return None

    resend.api_key = Config.RESEND_API_KEY

    workspace_url = f"{Config.FRONTEND_URL}/workspace/{project_id}"

    # Build HTML email
    report_preview = ""
    if markdown_content:
        # Take first ~500 chars as preview
        preview_text = markdown_content[:500]
        if len(markdown_content) > 500:
            preview_text += "..."
        # Simple markdown to text for preview
        preview_text = preview_text.replace("**", "").replace("*", "").replace("###", "").replace("##", "").replace("#", "")
        report_preview = f"""
        <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 24px 0; border-left: 4px solid #4f46e5;">
          <p style="color: #464555; font-size: 14px; line-height: 1.7; margin: 0; white-space: pre-wrap;">{preview_text}</p>
        </div>
        """

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background: #f7f9fb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
        <!-- Header -->
        <div style="text-align: center; margin-bottom: 32px;">
          <h1 style="font-size: 20px; font-weight: 700; color: #4f46e5; letter-spacing: -0.04em; margin: 0;">AUGUR</h1>
          <p style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.2em; color: #777587; margin: 4px 0 0;">AI Prediction Engine</p>
        </div>

        <!-- Card -->
        <div style="background: #fff; border-radius: 16px; padding: 40px 32px; box-shadow: 0 4px 24px rgba(79, 70, 229, 0.06);">
          <h2 style="font-size: 24px; font-weight: 700; color: #191c1e; margin: 0 0 8px; letter-spacing: -0.02em;">Your Prediction Report is Ready</h2>
          <p style="font-size: 15px; color: #464555; line-height: 1.6; margin: 0 0 24px;">
            Hi{(' ' + user_name) if user_name else ''}, the swarm intelligence analysis for <strong>{project_name}</strong> has completed.
          </p>

          {report_preview}

          <!-- CTA Button -->
          <div style="text-align: center; margin: 32px 0 16px;">
            <a href="{workspace_url}"
               style="display: inline-block; padding: 14px 32px; background: #4f46e5; color: #fff; text-decoration: none; border-radius: 10px; font-size: 15px; font-weight: 600; letter-spacing: -0.01em;">
              View Full Report
            </a>
          </div>
          <p style="text-align: center; font-size: 13px; color: #777587; margin: 0;">
            You can also chat with simulated agents and explore the knowledge graph in your workspace.
          </p>
        </div>

        <!-- Footer -->
        <div style="text-align: center; margin-top: 32px;">
          <p style="font-size: 12px; color: #999; margin: 0;">
            Sent by Augur AI Prediction Engine
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    try:
        result = resend.Emails.send({
            "from": Config.EMAIL_FROM,
            "to": [to_email],
            "subject": f"Your prediction report is ready: {project_name[:60]}",
            "html": html_body,
        })
        logger.info(f"Report email sent to {to_email}, id={result.get('id', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Failed to send report email to {to_email}: {e}")
        return None
