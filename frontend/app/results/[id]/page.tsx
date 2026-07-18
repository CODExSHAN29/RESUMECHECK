"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import CategoryBreakdown from "@/components/CategoryBreakdown";
import EmailCaptureForm from "@/components/EmailCaptureForm";
import KeywordChecklist from "@/components/KeywordChecklist";
import RubricExplainer from "@/components/RubricExplainer";
import ScoreGauge from "@/components/ScoreGauge";
import { ApiError, getReport } from "@/lib/api";
import type { CheckResult } from "@/lib/types";

export default function ResultsPage() {
  const params = useParams<{ id: string }>();
  const [result, setResult] = useState<CheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getReport(params.id)
      .then((data) => {
        if (!cancelled) setResult(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError && err.status === 404
              ? "This report couldn't be found. It may have expired or the link is incorrect."
              : "Couldn't load this report. Please try again."
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [params.id]);

  if (error) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-16 text-center">
        <p className="text-status-fail">{error}</p>
        <Link href="/" className="mt-4 inline-block text-sm font-medium text-accent">
          Check another resume
        </Link>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-16 text-center text-muted">
        Loading your report...
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-16">
      <div className="flex flex-col items-center text-center">
        <ScoreGauge score={result.overall_score} />
        <p className="mt-2 text-sm text-muted">{result.filename}</p>
      </div>

      <div className="mt-10">
        <RubricExplainer rubric={result.rubric} />
      </div>

      {result.jd_provided && result.keyword_details && (
        <div className="mt-6">
          <KeywordChecklist details={result.keyword_details} />
        </div>
      )}

      <div className="mt-10">
        <h2 className="mb-4 text-lg font-semibold">Category breakdown</h2>
        <CategoryBreakdown categories={result.categories} />
      </div>

      <div className="mt-10">
        <EmailCaptureForm reportId={result.id} />
      </div>

      <div className="mt-8 text-center">
        <Link href="/" className="text-sm font-medium text-accent">
          Check another resume
        </Link>
      </div>
    </div>
  );
}
