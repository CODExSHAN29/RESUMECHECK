from uuid import uuid4

from app.models.schemas import Issue
from app.parsing.common import ParsedDocument
from app.scoring.rubric import sub_weight

from .patterns import EMAIL_RE, PHONE_RE

CATEGORY = "layout_structure"
FORMAT_CATEGORY = "parseability_format"

ACCEPTABLE_EXTENSIONS = (".pdf", ".docx")

# Font names that indicate the document embeds a subset/custom font, which
# some ATS text extractors render as garbled or missing characters.
SUSPICIOUS_FONT_MARKERS = ("subset", "+", "custom", "embedded")


def _issue(category: str, check: str, status: str, title: str, detail: str, fix: str, score: float) -> Issue:
    return Issue(
        id=str(uuid4()),
        category=category,
        check=check,
        status=status,
        title=title,
        detail=detail,
        fix=fix,
        weight=sub_weight(category, check),
        score=score,
    )


def check_file_format(filename: str) -> Issue:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _issue(
            FORMAT_CATEGORY, "file_format", "pass",
            "PDF format",
            "PDF is well-supported by modern ATS platforms when the text is selectable.",
            "",
            100,
        )
    if lower.endswith(".docx"):
        return _issue(
            FORMAT_CATEGORY, "file_format", "pass",
            "DOCX format",
            "DOCX is natively supported by most ATS systems (Workday, Greenhouse, Lever).",
            "",
            100,
        )
    return _issue(
        FORMAT_CATEGORY, "file_format", "fail",
        "Unsupported file format",
        "ATS systems expect PDF or DOCX. Other formats (images, .pages, .odt) are often rejected or fail to parse.",
        "Re-save your resume as a PDF (text-based, not scanned) or a .docx file.",
        0,
    )


def check_fonts(doc: ParsedDocument) -> Issue:
    fonts = doc.fonts
    if not fonts:
        return _issue(
            FORMAT_CATEGORY, "fonts", "warn",
            "Could not determine fonts used",
            "Font information wasn't detectable, which can happen with unusual document encodings.",
            "Use a standard font like Arial, Calibri, or Times New Roman to be safe.",
            60,
        )

    suspicious = [f for f in fonts if any(marker in f.lower() for marker in SUSPICIOUS_FONT_MARKERS)]
    if suspicious:
        return _issue(
            FORMAT_CATEGORY, "fonts", "warn",
            "Embedded or subset fonts detected",
            "Fonts like " + ", ".join(sorted(suspicious)[:3]) + " are embedded/subset fonts. Some ATS "
            "text extractors render these as garbled or missing characters.",
            "Switch to a standard system font (Arial, Calibri, Helvetica, Georgia, Times New Roman).",
            60,
        )

    if len(fonts) > 4:
        return _issue(
            FORMAT_CATEGORY, "fonts", "warn",
            f"{len(fonts)} different fonts detected",
            "Using many different fonts increases the chance one of them doesn't extract cleanly, "
            "and looks inconsistent to a human reviewer too.",
            "Stick to 1-2 standard fonts throughout the resume.",
            70,
        )

    return _issue(
        FORMAT_CATEGORY, "fonts", "pass",
        "Standard, consistent fonts",
        "Your resume uses a small number of standard fonts, which parse reliably.",
        "",
        100,
    )


def check_multi_column(doc: ParsedDocument) -> Issue:
    if doc.multi_column_pages == 0:
        return _issue(
            CATEGORY, "multi_column", "pass",
            "Single-column layout",
            "Single-column resumes are read top-to-bottom correctly by ATS text extractors.",
            "",
            100,
        )
    return _issue(
        CATEGORY, "multi_column", "fail",
        "Multi-column layout detected",
        "ATS parsers read left-to-right, top-to-bottom in a single pass. Multi-column layouts often get "
        "scrambled — text from both columns gets interleaved into nonsense.",
        "Switch to a single-column layout. Use bold section headers instead of side columns for skills/dates.",
        0,
    )


def check_tables_as_layout(doc: ParsedDocument) -> Issue:
    if not doc.has_tables:
        return _issue(
            CATEGORY, "tables_as_layout", "pass",
            "No layout tables detected",
            "Avoiding tables means your content extracts as plain, ordered text.",
            "",
            100,
        )
    if doc.table_count <= 1:
        return _issue(
            CATEGORY, "tables_as_layout", "warn",
            "One table detected",
            "Tables can extract out of order or merge cell text unpredictably in many ATS parsers.",
            "If this table holds skills or dates, consider converting it to plain bulleted lines.",
            50,
        )
    return _issue(
        CATEGORY, "tables_as_layout", "fail",
        f"{doc.table_count} tables detected",
        "Multiple tables strongly suggest the resume uses tables for layout/alignment. ATS parsers "
        "frequently extract table content out of order or drop it entirely.",
        "Rebuild the resume using plain paragraphs and bullet lists instead of tables.",
        0,
    )


def check_text_boxes_images(doc: ParsedDocument) -> Issue:
    problems = []
    if doc.text_box_count > 0:
        problems.append(f"{doc.text_box_count} text box(es)")
    if doc.image_count > 0:
        problems.append(f"{doc.image_count} image(s)/icon(s)")

    if not problems:
        return _issue(
            CATEGORY, "text_boxes_images", "pass",
            "No text boxes or icon graphics",
            "All content is regular flowing text, which ATS systems extract reliably.",
            "",
            100,
        )

    status = "fail" if doc.text_box_count > 0 else "warn"
    score = 20 if status == "fail" else 60
    return _issue(
        CATEGORY, "text_boxes_images", status,
        "Text boxes or icon graphics detected (" + ", ".join(problems) + ")",
        "Text inside a text box or an icon standing in for a word (e.g. a phone icon instead of 'Phone:') "
        "is often skipped entirely by ATS text extraction, since it's not part of the main text flow.",
        "Move any text-box content into the main body text, and replace icons with plain text labels.",
        score,
    )


def check_header_footer_contact(doc: ParsedDocument) -> Issue:
    header_footer_has_contact = bool(
        EMAIL_RE.search(doc.header_footer_text) or PHONE_RE.search(doc.header_footer_text)
    )
    body_has_contact = bool(EMAIL_RE.search(doc.body_text) or PHONE_RE.search(doc.body_text))

    if not header_footer_has_contact:
        return _issue(
            CATEGORY, "header_footer_contact", "pass",
            "Contact info is not locked in a header/footer",
            "Contact info in the main body text is reliably picked up by ATS parsers.",
            "",
            100,
        )

    if body_has_contact:
        return _issue(
            CATEGORY, "header_footer_contact", "warn",
            "Contact info also appears in a header/footer",
            "Many ATS parsers strip header/footer content entirely before indexing a resume.",
            "Keep your contact info in the main document body as well, not only in the header/footer.",
            60,
        )

    return _issue(
        CATEGORY, "header_footer_contact", "fail",
        "Contact info found only in a header/footer",
        "Many ATS parsers strip headers and footers before indexing, which means your email/phone "
        "may never reach the recruiter's system.",
        "Move your name, email, and phone number out of the header/footer and into the top of the "
        "main document body.",
        0,
    )
