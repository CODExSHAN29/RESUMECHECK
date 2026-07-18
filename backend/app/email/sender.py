import logging

import httpx

from app.config import settings
from app.models.schemas import CheckResult

RESEND_URL = "https://api.resend.com/emails"
logger = logging.getLogger(__name__)


def _render_html(report: CheckResult) -> str:
    rows = []
    for cat in report.categories:
        rows.append(
            f"<tr><td style='padding:6px 12px;border-bottom:1px solid #eee;'>{cat.label}</td>"
            f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:right;'>{cat.score:.0f}/100</td></tr>"
        )
    top_fixes = [
        issue for cat in report.categories for issue in cat.issues if issue.status in ("fail", "warn")
    ][:5]
    fixes_html = "".join(f"<li style='margin-bottom:8px;'><b>{i.title}</b> — {i.fix or i.detail}</li>" for i in top_fixes)

    return f"""
    <div style="font-family: -apple-system, Arial, sans-serif; max-width: 560px; margin: 0 auto;">
      <h2>Your ResumeCheck Report</h2>
      <p style="font-size: 40px; font-weight: 700; margin: 8px 0;">{report.overall_score}/100</p>
      <table style="width:100%; border-collapse: collapse; margin: 16px 0;">{''.join(rows)}</table>
      <h3>Top things to fix</h3>
      <ul>{fixes_html}</ul>
      <p style="color:#888; font-size: 12px;">ResumeCheck — free ATS resume checker</p>
    </div>
    """


def send_report_email(to_email: str, report: CheckResult) -> bool:
    if not settings.email_configured:
        return False

    response = httpx.post(
        RESEND_URL,
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        json={
            "from": settings.resend_from_email,
            "to": [to_email],
            "subject": f"Your ResumeCheck report — {report.overall_score}/100",
            "html": _render_html(report),
        },
        timeout=10,
    )
    if response.status_code >= 300:
        logger.error("Resend send failed (%s): %s", response.status_code, response.text)
        return False
    return True
