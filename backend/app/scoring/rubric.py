from app.models.schemas import CategoryScore, CheckResult, Issue, KeywordDetails, RubricInfo

CATEGORY_LABELS: dict[str, str] = {
    "parseability_format": "Parseability & Format",
    "layout_structure": "Layout & Structure",
    "content_completeness": "Content Completeness",
    "keyword_match": "Keyword Match",
}

BASE_WEIGHTS_WITH_JD: dict[str, float] = {
    "parseability_format": 0.25,
    "layout_structure": 0.25,
    "content_completeness": 0.25,
    "keyword_match": 0.25,
}

BASE_WEIGHTS_NO_JD: dict[str, float] = {
    "parseability_format": 1 / 3,
    "layout_structure": 1 / 3,
    "content_completeness": 1 / 3,
}

# Sub-check weights within each category. Each check module must emit exactly
# one Issue per key here, and the weights for a category must sum to 1.0 —
# this dict is the single source of truth the frontend's rubric panel reads.
SUB_WEIGHTS: dict[str, dict[str, float]] = {
    "parseability_format": {
        "file_format": 0.30,
        "text_extraction": 0.40,
        "fonts": 0.30,
    },
    "layout_structure": {
        "multi_column": 0.25,
        "tables_as_layout": 0.20,
        "text_boxes_images": 0.15,
        "header_footer_contact": 0.20,
        "section_headings": 0.20,
    },
    "content_completeness": {
        "contact_info": 0.25,
        "length": 0.15,
        "date_formatting": 0.20,
        "bullet_formatting": 0.20,
        "file_name": 0.20,
    },
    "keyword_match": {
        "keyword_coverage": 0.60,
        "hard_skill_gap": 0.25,
        "seniority_alignment": 0.15,
    },
}


def sub_weight(category: str, check: str) -> float:
    return SUB_WEIGHTS[category][check]


def build_category_score(category_key: str, weight: float, issues: list[Issue]) -> CategoryScore:
    score = sum(issue.score * SUB_WEIGHTS[category_key][issue.check] for issue in issues)
    return CategoryScore(
        key=category_key,
        label=CATEGORY_LABELS[category_key],
        weight=weight,
        score=round(score, 1),
        issues=issues,
    )


def assemble_result(
    filename: str,
    jd_provided: bool,
    jd_text: str | None,
    parseability_format_issues: list[Issue],
    layout_structure_issues: list[Issue],
    content_completeness_issues: list[Issue],
    keyword_match_issues: list[Issue] | None,
    keyword_details: KeywordDetails | None = None,
) -> CheckResult:
    base_weights = BASE_WEIGHTS_WITH_JD if jd_provided else BASE_WEIGHTS_NO_JD

    categories = [
        build_category_score("parseability_format", base_weights["parseability_format"], parseability_format_issues),
        build_category_score("layout_structure", base_weights["layout_structure"], layout_structure_issues),
        build_category_score(
            "content_completeness", base_weights["content_completeness"], content_completeness_issues
        ),
    ]
    if jd_provided and keyword_match_issues is not None:
        categories.append(
            build_category_score("keyword_match", base_weights["keyword_match"], keyword_match_issues)
        )

    overall_score = round(sum(c.score * c.weight for c in categories))

    # A resume an ATS can't read at all shouldn't land in a middling score
    # just because other categories have nothing to flag as "wrong" — cap it.
    unreadable = any(
        issue.check == "text_extraction" and issue.status == "fail"
        for issue in parseability_format_issues
    )
    if unreadable:
        overall_score = min(overall_score, 25)

    note = (
        "Score is based on 4 categories, each weighted 25%."
        if jd_provided
        else "Score is based on 3 categories (Parseability & Format, Layout & Structure, "
        "Content Completeness), each weighted ~33%. Paste a job description to add "
        "Keyword Match as a 4th category."
    )

    rubric = RubricInfo(
        base_weights=BASE_WEIGHTS_WITH_JD,
        applied_weights={c.key: c.weight for c in categories},
        jd_provided=jd_provided,
        note=note,
    )

    return CheckResult(
        filename=filename,
        jd_provided=jd_provided,
        overall_score=overall_score,
        categories=categories,
        rubric=rubric,
        jd_text=jd_text,
        keyword_details=keyword_details if jd_provided else None,
    )
