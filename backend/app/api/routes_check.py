import logging

from fastapi import APIRouter, Form, HTTPException, UploadFile

from app.checks.content_structure import (
    check_bullet_formatting,
    check_contact_info,
    check_date_formatting,
    check_file_name,
    check_length,
    check_section_headings,
)
from app.checks.formatting import (
    check_file_format,
    check_fonts,
    check_header_footer_contact,
    check_multi_column,
    check_tables_as_layout,
    check_text_boxes_images,
)
from app.checks.keyword_match import run_keyword_match
from app.checks.parseability import check_text_extraction
from app.db.supabase_client import save_report
from app.models.schemas import CheckResult
from app.parsing import UnsupportedFileType, parse_resume
from app.scoring.rubric import assemble_result

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = (".pdf", ".docx")
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


@router.post("/check", response_model=CheckResult)
async def check_resume(resume: UploadFile, job_description: str | None = Form(None)) -> CheckResult:
    filename = resume.filename or "resume"
    if not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Please upload a PDF or DOCX file.")

    data = await resume.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File is too large (max 10MB).")

    try:
        doc = parse_resume(data, filename)
    except UnsupportedFileType as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - surface a friendly message for any parser failure
        raise HTTPException(
            status_code=400,
            detail="Couldn't read this file. It may be corrupted, password-protected, or an unsupported format.",
        ) from exc

    parseability_format_issues = [
        check_file_format(filename),
        check_fonts(doc),
        check_text_extraction(doc),
    ]
    layout_structure_issues = [
        check_multi_column(doc),
        check_tables_as_layout(doc),
        check_text_boxes_images(doc),
        check_header_footer_contact(doc),
        check_section_headings(doc),
    ]
    content_completeness_issues = [
        check_contact_info(doc),
        check_length(doc),
        check_date_formatting(doc),
        check_bullet_formatting(doc),
        check_file_name(filename),
    ]

    jd_provided = bool(job_description and job_description.strip())
    keyword_issues = None
    keyword_details = None
    if jd_provided:
        keyword_issues, keyword_details = run_keyword_match(doc.raw_text, job_description)

    result = assemble_result(
        filename=filename,
        jd_provided=jd_provided,
        jd_text=job_description if jd_provided else None,
        parseability_format_issues=parseability_format_issues,
        layout_structure_issues=layout_structure_issues,
        content_completeness_issues=content_completeness_issues,
        keyword_match_issues=keyword_issues,
        keyword_details=keyword_details,
    )

    try:
        save_report(result)
    except Exception:  # noqa: BLE001 - persistence is best-effort, never block the response
        logger.exception("Failed to save report %s", result.id)

    return result
