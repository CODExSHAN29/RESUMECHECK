from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    file_type: str  # "pdf" | "docx"
    filename: str
    raw_text: str
    lines: list[str]
    body_text: str  # raw_text minus header/footer regions
    page_count: int
    char_count: int
    word_count: int
    fonts: set[str] = field(default_factory=set)
    has_tables: bool = False
    table_count: int = 0
    multi_column_pages: int = 0
    header_footer_text: str = ""
    image_count: int = 0
    text_box_count: int = 0
    is_scanned_image: bool = False


class UnsupportedFileType(Exception):
    pass
