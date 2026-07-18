import re

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
LOCATION_HINT_RE = re.compile(
    r"\b([A-Z][a-zA-Z.]+,\s?[A-Z]{2}\b|[A-Z][a-zA-Z.]+,\s?[A-Z][a-zA-Z]+\b)"
)

STANDARD_HEADINGS = [
    "experience", "work experience", "professional experience", "employment history",
    "education", "academic background",
    "skills", "technical skills", "core competencies",
    "projects", "personal projects", "academic projects",
    "summary", "professional summary", "objective",
    "certifications", "certificates",
    "awards", "honors",
    "publications",
    "volunteer experience", "leadership",
]

BULLET_CHARS = {"•", "●", "▪", "◦", "-", "*", "⁃", "‣"}

MONTH_NAMES = (
    "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    "january|february|march|april|june|july|august|september|october|november|december"
)
DATE_PATTERNS = [
    re.compile(rf"\b({MONTH_NAMES})\.?\s+\d{{4}}\b", re.IGNORECASE),  # Jan 2022 / January 2022
    re.compile(r"\b\d{1,2}/\d{4}\b"),  # 01/2022
    re.compile(r"\b\d{4}\s?-\s?\d{4}\b"),  # 2020-2022
    re.compile(r"\b\d{4}\s?-\s?(present|current)\b", re.IGNORECASE),
]

SENIORITY_WORDS = ["intern", "internship", "junior", "entry level", "entry-level", "associate",
                    "mid-level", "senior", "sr.", "lead", "staff", "principal", "manager", "director"]

GENERIC_FILENAME_RE = re.compile(
    r"^(resume|cv|my\s*resume|untitled|document\d*|new\s*resume|final|draft)\b",
    re.IGNORECASE,
)
