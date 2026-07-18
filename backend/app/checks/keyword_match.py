import re
from collections import Counter
from uuid import uuid4

from rapidfuzz import fuzz

from app.models.schemas import Issue, KeywordDetails
from app.scoring.rubric import sub_weight

from .skills_lexicon import HARD_SKILLS
from .stopwords import STOPWORDS

CATEGORY = "keyword_match"
MAX_GENERAL_KEYWORDS = 15
FUZZY_MATCH_THRESHOLD = 90

ENTRY_WORDS = ["intern", "internship", "entry level", "entry-level", "junior"]
MID_WORDS = ["associate", "mid-level", "mid level"]
SENIOR_WORDS = ["senior", "sr.", "lead", "staff", "principal", "director", "manager", "vp", "head of"]


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


def _contains_term(haystack_lower: str, term: str) -> bool:
    if re.match(r"^[a-z0-9\s]+$", term):
        return re.search(rf"\b{re.escape(term)}\b", haystack_lower) is not None
    return term in haystack_lower


def _match_terms(keywords: list[str], resume_lower: str) -> tuple[list[str], list[str]]:
    matched, missing = [], []
    for kw in keywords:
        if _contains_term(resume_lower, kw) or fuzz.partial_ratio(kw, resume_lower) >= FUZZY_MATCH_THRESHOLD:
            matched.append(kw)
        else:
            missing.append(kw)
    return matched, missing


_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#]*(?:[.-][a-zA-Z0-9+#]+)*")


def _rank_phrases_by_frequency(text: str) -> list[str]:
    """Simple frequency-based phrase ranking: count unigrams and bigrams,
    skip stopwords, rank by how often each phrase recurs in the JD. This
    intentionally avoids a heavy ML dependency per the brief ("start simple")."""
    words = [w.lower() for w in _WORD_RE.findall(text)]
    counts: Counter[str] = Counter()

    for word in words:
        if len(word) > 2 and word not in STOPWORDS:
            counts[word] += 1

    for a, b in zip(words, words[1:]):
        if a not in STOPWORDS and b not in STOPWORDS and len(a) > 2 and len(b) > 2:
            counts[f"{a} {b}"] += 1

    # Only keep phrases that recur, or the resume/JD is too short to have
    # meaningful repetition signal — a phrase appearing once is noise.
    ranked = [phrase for phrase, count in counts.most_common() if count >= 2]
    return ranked


def extract_keywords(jd_text: str) -> tuple[list[str], list[str]]:
    jd_lower = jd_text.lower()
    hard_skills_found = sorted(s for s in HARD_SKILLS if _contains_term(jd_lower, s))

    general_keywords: list[str] = []
    for term in _rank_phrases_by_frequency(jd_text):
        if any(term in hs or hs in term for hs in hard_skills_found):
            continue
        general_keywords.append(term)
        if len(general_keywords) >= MAX_GENERAL_KEYWORDS:
            break

    return hard_skills_found, general_keywords


def _seniority_level(text_lower: str) -> str | None:
    if any(w in text_lower for w in SENIOR_WORDS):
        return "senior"
    if any(w in text_lower for w in MID_WORDS):
        return "mid"
    if any(w in text_lower for w in ENTRY_WORDS):
        return "entry"
    return None


def check_keyword_coverage(matched: list[str], missing: list[str]) -> Issue:
    total = len(matched) + len(missing)
    if total == 0:
        return _issue(
            "keyword_coverage", "pass",
            "No specific keywords extracted from the job description",
            "The job description was too short or generic to extract meaningful keywords.",
            "Paste a fuller job description with specific responsibilities and requirements.",
            100,
        )
    score = round((len(matched) / total) * 100)
    if score >= 75:
        status, title = "pass", f"Strong keyword match ({len(matched)}/{total})"
        detail = "Most of the key terms from the job description also appear in your resume."
        fix = ""
    elif score >= 40:
        status, title = "warn", f"Partial keyword match ({len(matched)}/{total})"
        detail = "A meaningful chunk of the job description's key terms are missing from your resume."
        fix = "Review the missing keywords checklist and add the ones that genuinely apply to your experience."
    else:
        status, title = "fail", f"Weak keyword match ({len(matched)}/{total})"
        detail = "Most of the job description's key terms don't appear in your resume, which will likely "
        detail += "score low in an ATS keyword scan."
        fix = "Rework your resume to naturally include the missing keywords you actually have experience with."
    return _issue("keyword_coverage", status, title, detail, fix, score)


def check_hard_skill_gap(matched_hard: list[str], missing_hard: list[str]) -> Issue:
    total = len(matched_hard) + len(missing_hard)
    if total == 0:
        return _issue(
            "hard_skill_gap", "pass",
            "No specific hard skills detected in the job description",
            "No tools/technologies from our lexicon were detected in the job description.",
            "",
            100,
        )
    score = round((len(matched_hard) / total) * 100)
    if score >= 75:
        status, title = "pass", "Most required hard skills are present"
        detail = "Your resume mentions most of the specific tools/technologies the job description calls for."
        fix = ""
    elif score >= 40:
        status, title = "warn", f"{len(missing_hard)} hard skill(s) missing"
        detail = "Some specific tools/technologies from the job description aren't mentioned in your resume."
        fix = "Add the missing tools/technologies you have real experience with: " + ", ".join(missing_hard[:8])
    else:
        status, title = "fail", f"{len(missing_hard)} hard skill(s) missing"
        detail = "Most of the specific tools/technologies the job description asks for are absent from your resume."
        fix = "Add the missing tools/technologies you have real experience with: " + ", ".join(missing_hard[:8])
    return _issue("hard_skill_gap", status, title, detail, fix, score)


def check_seniority_alignment(jd_text: str, resume_text: str) -> Issue:
    jd_level = _seniority_level(jd_text.lower())
    resume_level = _seniority_level(resume_text.lower())

    if jd_level is None:
        return _issue(
            "seniority_alignment", "pass",
            "No explicit seniority level detected in the job description",
            "The job description didn't contain clear seniority signals (e.g. 'Senior', 'Intern').",
            "",
            100,
        )
    if resume_level is None:
        return _issue(
            "seniority_alignment", "warn",
            f"Resume doesn't clearly signal a level matching the job's '{jd_level}' framing",
            "The job description reads as a specific seniority level, but your resume doesn't use "
            "matching language (titles, years of experience) to signal it.",
            f"Make sure your titles/summary reflect the level you're applying at ('{jd_level}').",
            60,
        )

    rank = {"entry": 0, "mid": 1, "senior": 2}
    distance = abs(rank[jd_level] - rank[resume_level])
    if distance == 0:
        return _issue(
            "seniority_alignment", "pass",
            "Seniority level matches the job description",
            f"Both the job description and resume read as '{jd_level}' level.",
            "",
            100,
        )
    if distance == 1:
        return _issue(
            "seniority_alignment", "warn",
            "Slight seniority mismatch",
            f"The job description reads as '{jd_level}' level, while your resume reads closer to "
            f"'{resume_level}' level.",
            "Adjust your summary/titles to better reflect the target seniority, if accurate.",
            60,
        )
    return _issue(
        "seniority_alignment", "fail",
        "Significant seniority mismatch",
        f"The job description reads as '{jd_level}' level, while your resume reads as '{resume_level}' "
        "level — a large gap that may cause automatic filtering.",
        "Double check this role is the right target, or reframe your experience to close the gap.",
        30,
    )


def run_keyword_match(resume_text: str, jd_text: str) -> tuple[list[Issue], KeywordDetails]:
    resume_lower = resume_text.lower()
    hard_skills, general_keywords = extract_keywords(jd_text)

    matched_hard, missing_hard = _match_terms(hard_skills, resume_lower)
    matched_general, missing_general = _match_terms(general_keywords, resume_lower)

    matched_all = matched_hard + matched_general
    missing_all = missing_hard + missing_general

    issues = [
        check_keyword_coverage(matched_all, missing_all),
        check_hard_skill_gap(matched_hard, missing_hard),
        check_seniority_alignment(jd_text, resume_text),
    ]
    details = KeywordDetails(
        matched=matched_all,
        missing=missing_all,
        hard_skills_matched=matched_hard,
        hard_skills_missing=missing_hard,
    )
    return issues, details
