from .common import ParsedDocument, UnsupportedFileType
from .docx_parser import parse_docx
from .pdf_parser import parse_pdf


def parse_resume(data: bytes, filename: str) -> ParsedDocument:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return parse_pdf(data, filename)
    if lower.endswith(".docx"):
        return parse_docx(data, filename)
    raise UnsupportedFileType(f"Unsupported file type: {filename}")


__all__ = ["ParsedDocument", "UnsupportedFileType", "parse_resume"]
