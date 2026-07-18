from uuid import uuid4

from app.models.schemas import Issue
from app.parsing.common import ParsedDocument
from app.scoring.rubric import sub_weight

CATEGORY = "parseability_format"
MIN_WORD_COUNT = 60


def _issue(check: str, status: str, title: str, detail: str, fix: str, score: float) -> Issue:
    return Issue(
        id=str(uuid4()),
        category=CATEGORY,
        check=check,
        status=status,
        title=title,
        detail=detail,
        fix=fix,
        weight=sub_weight(CATEGORY, check),
        score=score,
    )


def check_text_extraction(doc: ParsedDocument) -> Issue:
    if doc.is_scanned_image:
        return _issue(
            "text_extraction", "fail",
            "Resume appears to be a scanned image",
            "Almost no selectable text was found even though the document has pages. This usually means "
            "the resume is a scanned image or a picture pasted into the document — ATS systems can't read "
            "any of the text at all, so the resume is effectively invisible to them.",
            "Export your resume directly from a word processor (Word, Google Docs) as a PDF rather than "
            "scanning or photographing a printed copy.",
            0,
        )

    if doc.word_count < MIN_WORD_COUNT:
        return _issue(
            "text_extraction", "warn",
            "Very little extractable text",
            f"Only about {doc.word_count} words were extracted, which is low for a resume. Some content "
            "may be trapped in images, text boxes, or an unusual layout that text extraction can't reach.",
            "Make sure all resume content — including skills and experience — is regular selectable text.",
            50,
        )

    return _issue(
        "text_extraction", "pass",
        "Full text extracts cleanly",
        f"{doc.word_count} words of text were extracted in reading order, which is what an ATS relies on.",
        "",
        100,
    )
