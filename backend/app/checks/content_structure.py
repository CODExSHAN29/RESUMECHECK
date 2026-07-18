import os
import re
from uuid import uuid4

from rapidfuzz import fuzz

from app.models.schemas import Issue
from app.parsing.common import ParsedDocument
from app.scoring.rubric import sub_weight

from .patterns import (
    BULLET_CHARS,
    DATE_PATTERNS,
    EMAIL_RE,
    GENERIC_FILENAME_RE,
    LOCATION_HINT_RE,
    PHONE_RE,
)

LAYOUT_CATEGORY = "layout_structure"
CONTENT_CATEGORY = "content_completeness"

CORE_HEADING_GROUPS = {
    "experience": ["experience", "work experience", "professional experience", "employment history"],
    "education": ["education", "academic background"],
    "skills": ["skills", "technical skills", "core competencies"],
}

FUZZY_MATCH_THRESHOLD = 85


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


def _line_matches_any(line: str, candidates: list[str]) -> bool:
    clean = line.strip().lower().rstrip(":")
    if len(clean) > 40:
        return False
    for candidate in candidates:
        if fuzz.ratio(clean, candidate) >= FUZZY_MATCH_THRESHOLD:
            return True
    return False


def check_section_headings(doc: ParsedDocument) -> Issue:
    found_groups = set()
    for line in doc.lines:
        for group, variants in CORE_HEADING_GROUPS.items():
            if group in found_groups:
                continue
            if _line_matches_any(line, variants):
                found_groups.add(group)

    missing = [g for g in CORE_HEADING_GROUPS if g not in found_groups]

    if not missing:
        return _issue(
            LAYOUT_CATEGORY, "section_headings", "pass",
            "Standard section headings found",
            "Experience, Education, and Skills sections were all found with recognizable headings, "
            "which ATS systems map directly to their internal schema.",
            "",
            100,
        )
    if len(missing) == 1:
        return _issue(
            LAYOUT_CATEGORY, "section_headings", "warn",
            f"Missing a standard '{missing[0].title()}' heading",
            "ATS systems look for standard, literal section headings to categorize your content. "
            "A missing or non-standard heading for a core section may mean that content isn't mapped at all.",
            f"Add a clearly labeled '{missing[0].title()}' heading above that section.",
            60,
        )
    return _issue(
        LAYOUT_CATEGORY, "section_headings", "fail",
        "Standard section headings not detected",
        "None of the core section headings (Experience, Education, Skills) were recognized. ATS systems "
        "rely on standard headings to file your content into the right fields — creative or missing "
        "headings often mean that content is dropped from the parsed profile.",
        "Use plain, standard headings: 'Experience', 'Education', 'Skills' (avoid creative alternatives "
        "like 'What I've Done' or icon-only headers).",
        0,
    )


def check_contact_info(doc: ParsedDocument) -> Issue:
    text = doc.raw_text
    has_email = bool(EMAIL_RE.search(text))
    has_phone = bool(PHONE_RE.search(text))
    has_location = bool(LOCATION_HINT_RE.search(text))

    first_line = next((ln.strip() for ln in doc.lines if ln.strip()), "")
    words = first_line.split()
    has_name = (
        1 < len(words) <= 4
        and all(w[0:1].isupper() for w in words if w[0:1].isalpha())
        and not EMAIL_RE.search(first_line)
        and not any(ch.isdigit() for ch in first_line)
    )

    present = [has_name, has_email, has_phone, has_location]
    count = sum(present)
    score = round((count / 4) * 100)

    if count == 4:
        status, title = "pass", "Name, email, phone, and location all detected"
        detail = "All core contact details are present as plain text an ATS can read."
        fix = ""
    elif count == 3:
        status, title = "warn", "One contact detail may be missing"
        missing = [
            n for n, v in zip(["name", "email", "phone", "location"], present) if not v
        ]
        detail = f"Couldn't clearly detect: {', '.join(missing)}."
        fix = "Double-check that your " + " and ".join(missing) + " appear as plain text near the top of the resume."
    else:
        status, title = "fail", "Missing key contact details"
        missing = [
            n for n, v in zip(["name", "email", "phone", "location"], present) if not v
        ]
        detail = f"Couldn't detect: {', '.join(missing)}. If these exist, they may be inside an image, icon, or header that ATS parsers skip."
        fix = "Add your " + ", ".join(missing) + " as plain text near the top of the resume body."

    return _issue(CONTENT_CATEGORY, "contact_info", status, title, detail, fix, score)


def check_length(doc: ParsedDocument) -> Issue:
    pages = doc.page_count
    if pages <= 1:
        return _issue(
            CONTENT_CATEGORY, "length", "pass",
            "1-page resume",
            "A single page is the expected length for students and early-career applicants.",
            "",
            100,
        )
    if pages == 2:
        return _issue(
            CONTENT_CATEGORY, "length", "warn",
            "2-page resume",
            "Two pages can work for experienced candidates, but recruiters and ATS keyword scans "
            "for early-career roles typically expect one page.",
            "Trim to the most relevant experience and aim for a single page.",
            60,
        )
    return _issue(
        CONTENT_CATEGORY, "length", "fail",
        f"{pages}-page resume",
        "Resumes this long are unusual for early-career applicants and often signal unfocused content.",
        "Cut down to one page, keeping only the most relevant and recent experience.",
        20,
    )


_STYLE_NAMES = ["month_name", "numeric_slash", "year_range", "year_present"]


def check_date_formatting(doc: ParsedDocument) -> Issue:
    text = doc.raw_text
    matched_styles = set()
    total_matches = 0
    for idx, pattern in enumerate(DATE_PATTERNS):
        matches = pattern.findall(text)
        if matches:
            matched_styles.add(_STYLE_NAMES[idx])
            total_matches += len(matches)

    if total_matches == 0:
        return _issue(
            CONTENT_CATEGORY, "date_formatting", "warn",
            "No clear dates detected",
            "Couldn't find recognizable dates for work/education entries. If your resume has dates, an "
            "unusual format may prevent an ATS from placing your experience on a timeline.",
            "Use a clear, consistent format like 'Jan 2022 - Present' for each role or degree.",
            50,
        )

    if len(matched_styles) == 1:
        return _issue(
            CONTENT_CATEGORY, "date_formatting", "pass",
            "Consistent date formatting",
            "Dates use one consistent format throughout, which ATS date parsers handle reliably.",
            "",
            100,
        )

    return _issue(
        CONTENT_CATEGORY, "date_formatting", "warn",
        "Inconsistent date formats",
        "Multiple different date formats were detected (e.g. 'Jan 2022' mixed with '01/2022'). "
        "Inconsistent formats can confuse ATS date parsing and look unpolished to reviewers.",
        "Pick one date format (e.g. 'Jan 2022 - Present') and use it for every entry.",
        50,
    )


def check_bullet_formatting(doc: ParsedDocument) -> Issue:
    bullet_lines = sum(1 for ln in doc.lines if ln.strip()[:1] in BULLET_CHARS)

    if bullet_lines >= 5:
        return _issue(
            CONTENT_CATEGORY, "bullet_formatting", "pass",
            "Real bullet points used",
            "Achievements are broken into bullet points, which ATS and human reviewers both parse well.",
            "",
            100,
        )
    if bullet_lines >= 1:
        return _issue(
            CONTENT_CATEGORY, "bullet_formatting", "warn",
            "Few bullet points detected",
            "Only a handful of bulleted lines were found. Dense paragraphs are harder for both ATS "
            "keyword extraction and human skimming.",
            "Break experience/project descriptions into 3-5 bullet points per role, one achievement each.",
            60,
        )
    return _issue(
        CONTENT_CATEGORY, "bullet_formatting", "warn",
        "No bullet points detected",
        "No standard bullet characters were found. If achievements are written as paragraphs, key "
        "phrases can get buried.",
        "Use a standard bullet character (•, -, or a real Word/Docs bullet list) for each achievement.",
        50,
    )


def check_file_name(filename: str) -> Issue:
    stem = os.path.splitext(filename)[0].strip()
    if GENERIC_FILENAME_RE.match(stem):
        return _issue(
            CONTENT_CATEGORY, "file_name", "fail",
            f"Generic file name ('{filename}')",
            "Recruiters and some ATS systems display the file name directly. A generic name like "
            "'resume.pdf' looks unpolished and makes your file hard to find later.",
            "Rename the file to something like 'FirstName-LastName-Resume.pdf'.",
            30,
        )
    return _issue(
        CONTENT_CATEGORY, "file_name", "pass",
        "Descriptive file name",
        f"'{filename}' is a clear, specific file name.",
        "",
        100,
    )
