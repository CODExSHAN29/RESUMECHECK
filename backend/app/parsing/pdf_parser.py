import io

import pdfplumber

from .common import ParsedDocument

HEADER_FOOTER_MARGIN = 0.08  # top/bottom 8% of page treated as header/footer
COLUMN_GAP_PT = 20  # min horizontal gap between two char clusters to count as separate columns
MULTI_COLUMN_LINE_FRACTION = 0.25  # fraction of a page's text lines that must show a column split


def _line_groups(chars: list[dict]) -> dict[int, list[dict]]:
    groups: dict[int, list[dict]] = {}
    for c in chars:
        key = round(c["top"])
        groups.setdefault(key, []).append(c)
    return groups


def _page_is_multi_column(chars: list[dict], page_width: float) -> bool:
    if not chars:
        return False
    mid = page_width / 2
    lines = _line_groups(chars)
    split_lines = 0
    counted_lines = 0
    for line_chars in lines.values():
        text_chars = [c for c in line_chars if c["text"].strip()]
        if len(text_chars) < 6:
            continue
        counted_lines += 1
        left = [c for c in text_chars if c["x0"] < mid]
        right = [c for c in text_chars if c["x0"] >= mid]
        if len(left) >= 3 and len(right) >= 3:
            gap = min(c["x0"] for c in right) - max(c["x1"] for c in left)
            if gap >= COLUMN_GAP_PT:
                split_lines += 1
    if counted_lines == 0:
        return False
    return (split_lines / counted_lines) >= MULTI_COLUMN_LINE_FRACTION


def parse_pdf(data: bytes, filename: str) -> ParsedDocument:
    fonts: set[str] = set()
    all_lines: list[str] = []
    body_lines: list[str] = []
    header_footer_lines: list[str] = []
    table_count = 0
    multi_column_pages = 0
    image_count = 0
    text_box_count = 0
    char_count = 0

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            chars = page.chars
            char_count += len(chars)
            for c in chars:
                if c.get("fontname"):
                    fonts.add(c["fontname"])

            text = page.extract_text() or ""
            page_lines = [ln for ln in text.split("\n") if ln.strip()]
            all_lines.extend(page_lines)

            header_cut = page.height * HEADER_FOOTER_MARGIN
            footer_cut = page.height * (1 - HEADER_FOOTER_MARGIN)
            region_chars = [c for c in chars if c["top"] < header_cut or c["bottom"] > footer_cut]
            if region_chars:
                region_groups = _line_groups(region_chars)
                for line_chars in region_groups.values():
                    line_text = "".join(c["text"] for c in sorted(line_chars, key=lambda c: c["x0"])).strip()
                    if line_text:
                        header_footer_lines.append(line_text)

            try:
                body_page_text = page.crop((0, header_cut, page.width, footer_cut)).extract_text() or ""
            except Exception:
                body_page_text = ""
            body_lines.extend(ln for ln in body_page_text.split("\n") if ln.strip())

            try:
                tables = page.find_tables()
            except Exception:
                tables = []
            table_count += len(tables)

            try:
                rects = page.rects
            except Exception:
                rects = []
            text_box_count += len([r for r in rects if r.get("width", 0) > 20 and r.get("height", 0) > 10])

            image_count += len(page.images)

            if _page_is_multi_column(chars, page.width):
                multi_column_pages += 1

    raw_text = "\n".join(all_lines)
    word_count = len(raw_text.split())
    is_scanned_image = char_count < 20 and page_count >= 1

    return ParsedDocument(
        file_type="pdf",
        filename=filename,
        raw_text=raw_text,
        lines=all_lines,
        body_text="\n".join(body_lines),
        page_count=page_count,
        char_count=char_count,
        word_count=word_count,
        fonts=fonts,
        has_tables=table_count > 0,
        table_count=table_count,
        multi_column_pages=multi_column_pages,
        header_footer_text="\n".join(header_footer_lines),
        image_count=image_count,
        text_box_count=text_box_count,
        is_scanned_image=is_scanned_image,
    )
