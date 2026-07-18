import json
from functools import lru_cache

from supabase import Client, create_client

from app.config import settings
from app.models.schemas import CheckResult


@lru_cache
def get_client() -> Client | None:
    if not settings.db_configured:
        return None
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def save_report(result: CheckResult) -> None:
    client = get_client()
    if client is None:
        return
    payload = json.loads(result.model_dump_json())
    client.table("reports").insert(
        {
            "id": payload["id"],
            "created_at": payload["created_at"],
            "filename": payload["filename"],
            "overall_score": payload["overall_score"],
            "category_scores": payload["categories"],
            "issues": [issue for cat in payload["categories"] for issue in cat["issues"]],
            "jd_text": payload["jd_text"],
            "email": payload["email"],
            "report_json": payload,
        }
    ).execute()


def get_report(report_id: str) -> CheckResult | None:
    client = get_client()
    if client is None:
        return None
    resp = client.table("reports").select("report_json").eq("id", report_id).limit(1).execute()
    if not resp.data:
        return None
    return CheckResult.model_validate(resp.data[0]["report_json"])


def attach_email_to_report(report_id: str, email: str) -> None:
    client = get_client()
    if client is None:
        return
    existing = get_report(report_id)
    report_json = None
    if existing is not None:
        existing.email = email
        report_json = json.loads(existing.model_dump_json())
    update = {"email": email}
    if report_json is not None:
        update["report_json"] = report_json
    client.table("reports").update(update).eq("id", report_id).execute()


def save_email_subscriber(email: str, report_id: str) -> None:
    client = get_client()
    if client is None:
        return
    # returning="minimal" — the anon role has insert-only access to this table
    # (no select policy, so collected emails can't be read back publicly).
    client.table("email_subscribers").insert(
        {"email": email, "report_id": report_id}, returning="minimal"
    ).execute()
