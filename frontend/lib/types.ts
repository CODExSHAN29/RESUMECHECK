export type IssueStatus = "fail" | "warn" | "pass";

export type CategoryKey =
  | "parseability_format"
  | "layout_structure"
  | "content_completeness"
  | "keyword_match";

export interface Issue {
  id: string;
  category: CategoryKey;
  check: string;
  status: IssueStatus;
  title: string;
  detail: string;
  fix: string;
  weight: number;
  score: number;
}

export interface CategoryScore {
  key: CategoryKey;
  label: string;
  weight: number;
  score: number;
  issues: Issue[];
}

export interface RubricInfo {
  base_weights: Record<string, number>;
  applied_weights: Record<string, number>;
  jd_provided: boolean;
  note: string;
}

export interface KeywordDetails {
  matched: string[];
  missing: string[];
  hard_skills_matched: string[];
  hard_skills_missing: string[];
}

export interface CheckResult {
  id: string;
  created_at: string;
  filename: string;
  jd_provided: boolean;
  overall_score: number;
  categories: CategoryScore[];
  rubric: RubricInfo;
  jd_text: string | null;
  email: string | null;
  keyword_details: KeywordDetails | null;
}
