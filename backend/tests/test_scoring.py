import os

import pytest

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
from app.parsing import parse_resume
from app.scoring.rubric import BASE_WEIGHTS_NO_JD, BASE_WEIGHTS_WITH_JD, SUB_WEIGHTS, assemble_result

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "..", "sample_resumes")


def load(name: str) -> bytes:
    with open(os.path.join(FIXTURES, name), "rb") as f:
        return f.read()


def test_base_weights_sum_to_one():
    assert pytest.approx(sum(BASE_WEIGHTS_WITH_JD.values()), rel=1e-6) == 1.0
    assert pytest.approx(sum(BASE_WEIGHTS_NO_JD.values()), rel=1e-6) == 1.0


def test_sub_weights_sum_to_one_per_category():
    for category, weights in SUB_WEIGHTS.items():
        assert pytest.approx(sum(weights.values()), rel=1e-6) == 1.0, category


def run_full_check(filename: str, jd_text: str | None = None):
    doc = parse_resume(load(filename), filename)
    parseability_issues = [check_file_format(filename), check_fonts(doc), check_text_extraction(doc)]
    layout_issues = [
        check_multi_column(doc),
        check_tables_as_layout(doc),
        check_text_boxes_images(doc),
        check_header_footer_contact(doc),
        check_section_headings(doc),
    ]
    content_issues = [
        check_contact_info(doc),
        check_length(doc),
        check_date_formatting(doc),
        check_bullet_formatting(doc),
        check_file_name(filename),
    ]
    jd_provided = bool(jd_text and jd_text.strip())
    keyword_issues = keyword_details = None
    if jd_provided:
        keyword_issues, keyword_details = run_keyword_match(doc.raw_text, jd_text)

    return assemble_result(
        filename=filename,
        jd_provided=jd_provided,
        jd_text=jd_text if jd_provided else None,
        parseability_format_issues=parseability_issues,
        layout_structure_issues=layout_issues,
        content_completeness_issues=content_issues,
        keyword_match_issues=keyword_issues,
        keyword_details=keyword_details,
    )


def test_clean_resume_scores_well_without_jd():
    result = run_full_check("clean_one_column.docx")
    assert result.jd_provided is False
    assert len(result.categories) == 3
    assert result.overall_score >= 70


def test_multi_column_resume_flagged_and_scores_lower():
    clean = run_full_check("clean_one_column.docx")
    multi = run_full_check("multi_column.docx")
    layout_clean = next(c for c in clean.categories if c.key == "layout_structure")
    layout_multi = next(c for c in multi.categories if c.key == "layout_structure")
    assert layout_multi.score < layout_clean.score

    multi_col_issue = next(i for i in layout_multi.issues if i.check == "multi_column")
    assert multi_col_issue.status == "fail"


def test_table_heavy_resume_fails_table_check():
    result = run_full_check("table_heavy.docx")
    layout = next(c for c in result.categories if c.key == "layout_structure")
    table_issue = next(i for i in layout.issues if i.check == "tables_as_layout")
    assert table_issue.status in ("warn", "fail")


def test_header_contact_only_flagged():
    result = run_full_check("header_contact_only.docx")
    layout = next(c for c in result.categories if c.key == "layout_structure")
    header_issue = next(i for i in layout.issues if i.check == "header_footer_contact")
    assert header_issue.status == "fail"


def test_scanned_image_pdf_fails_parseability():
    result = run_full_check("scanned_image_like.pdf")
    parse_cat = next(c for c in result.categories if c.key == "parseability_format")
    text_issue = next(i for i in parse_cat.issues if i.check == "text_extraction")
    assert text_issue.status == "fail"
    assert result.overall_score < 50


def test_jd_adds_keyword_match_category():
    jd = (
        "We are looking for a Software Engineering Intern with experience in Python, SQL, and AWS. "
        "The ideal candidate has strong communication skills and experience with React. "
        "Python and SQL experience are required. AWS knowledge is a plus."
    )
    result = run_full_check("clean_one_column.docx", jd_text=jd)
    assert result.jd_provided is True
    assert len(result.categories) == 4
    assert result.keyword_details is not None
    assert "python" in [k.lower() for k in result.keyword_details.matched]


def test_no_jd_excludes_keyword_category_and_rescales():
    result = run_full_check("clean_one_column.docx")
    assert result.jd_provided is False
    assert all(c.key != "keyword_match" for c in result.categories)
    total_weight = sum(c.weight for c in result.categories)
    assert pytest.approx(total_weight, rel=1e-6) == 1.0
