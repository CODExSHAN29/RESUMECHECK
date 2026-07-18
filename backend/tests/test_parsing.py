import os

import pytest

from app.parsing import parse_resume

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "..", "sample_resumes")


def load(name: str) -> bytes:
    with open(os.path.join(FIXTURES, name), "rb") as f:
        return f.read()


def test_clean_docx_parses_single_column_no_tables():
    doc = parse_resume(load("clean_one_column.docx"), "clean_one_column.docx")
    assert doc.file_type == "docx"
    assert doc.multi_column_pages == 0
    assert doc.table_count == 0
    assert "jordan.lee@email.com" in doc.raw_text.lower()
    assert doc.word_count > 30


def test_multi_column_docx_detected():
    doc = parse_resume(load("multi_column.docx"), "multi_column.docx")
    assert doc.multi_column_pages >= 1


def test_table_heavy_docx_detected():
    doc = parse_resume(load("table_heavy.docx"), "table_heavy.docx")
    assert doc.table_count >= 1
    assert doc.has_tables is True


def test_header_contact_docx_only_in_header():
    doc = parse_resume(load("header_contact_only.docx"), "header_contact_only.docx")
    assert "casey.nguyen@email.com" in doc.header_footer_text.lower()
    assert "casey.nguyen@email.com" not in doc.raw_text.lower()


def test_clean_pdf_parses_single_column():
    doc = parse_resume(load("clean_resume.pdf"), "clean_resume.pdf")
    assert doc.file_type == "pdf"
    assert doc.multi_column_pages == 0
    assert "alex.rivera@email.com" in doc.raw_text.lower()
    assert doc.page_count == 1


def test_multi_column_pdf_detected():
    doc = parse_resume(load("multi_column.pdf"), "multi_column.pdf")
    assert doc.multi_column_pages >= 1


def test_table_heavy_pdf_detected():
    doc = parse_resume(load("table_heavy.pdf"), "table_heavy.pdf")
    assert doc.table_count >= 1


def test_scanned_image_pdf_detected():
    doc = parse_resume(load("scanned_image_like.pdf"), "scanned_image_like.pdf")
    assert doc.is_scanned_image is True
    assert doc.char_count < 20


def test_header_contact_pdf_only_in_header_region():
    doc = parse_resume(load("header_contact_only.pdf"), "header_contact_only.pdf")
    assert "jamie.wong@email.com" in doc.header_footer_text.lower()
    # raw_text is the full linear extraction (includes header/footer);
    # body_text is what's left once the header/footer region is excluded.
    assert "jamie.wong@email.com" in doc.raw_text.lower()
    assert "jamie.wong@email.com" not in doc.body_text.lower()


def test_unsupported_extension_raises():
    from app.parsing import UnsupportedFileType

    with pytest.raises(UnsupportedFileType):
        parse_resume(b"not a real file", "resume.txt")
