import type { KeywordDetails } from "@/lib/types";

export default function KeywordChecklist({ details }: { details: KeywordDetails }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <h3 className="text-sm font-semibold">Keyword checklist</h3>
      <p className="mt-1 text-xs text-muted">
        {details.matched.length} of {details.matched.length + details.missing.length} keywords from the
        job description were found in your resume.
      </p>

      {details.missing.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
            Missing — consider adding these
          </p>
          <ul className="space-y-1.5">
            {details.missing.map((kw) => (
              <li key={kw} className="flex items-center gap-2 text-sm">
                <span className="text-status-fail">✕</span>
                {kw}
              </li>
            ))}
          </ul>
        </div>
      )}

      {details.matched.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Matched</p>
          <ul className="space-y-1.5">
            {details.matched.map((kw) => (
              <li key={kw} className="flex items-center gap-2 text-sm">
                <span className="text-status-pass">✓</span>
                {kw}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
