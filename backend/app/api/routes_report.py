import logging

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.db.supabase_client import attach_email_to_report, get_report, save_email_subscriber
from app.email.sender import send_report_email
from app.models.schemas import CheckResult, EmailCaptureRequest

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/report/{report_id}", response_model=CheckResult)
async def get_report_by_id(report_id: str) -> CheckResult:
    if not settings.db_configured:
        raise HTTPException(status_code=503, detail="Report storage isn't configured on this server.")
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.post("/report/{report_id}/email")
async def email_report(report_id: str, payload: EmailCaptureRequest) -> dict:
    if not settings.db_configured:
        raise HTTPException(status_code=503, detail="Report storage isn't configured on this server.")
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    try:
        save_email_subscriber(payload.email, report_id)
        attach_email_to_report(report_id, payload.email)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to save email subscriber for report %s", report_id)

    if not settings.email_configured:
        return {"saved": True, "sent": False, "message": "Email saved. Delivery isn't configured yet."}

    report.email = payload.email
    sent = send_report_email(payload.email, report)
    return {"saved": True, "sent": sent}
