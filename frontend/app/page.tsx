"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import UploadBox from "@/components/UploadBox";
import { ApiError, checkResume } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!file) {
      setError("Please upload a resume first.");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      const result = await checkResume(file, jobDescription);
      router.push(`/results/${result.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-16">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Will your resume make it past the ATS?
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-muted">
          Most employers filter resumes through an Applicant Tracking System before a human ever
          sees them. Upload yours and get a free, transparent breakdown in seconds — no account
          required.
        </p>
      </div>

      <div className="mt-10 space-y-5">
        <UploadBox file={file} onFileSelected={setFile} disabled={isSubmitting} />

        <div>
          <label htmlFor="jd" className="mb-1.5 block text-sm font-medium">
            Job description <span className="font-normal text-muted">(optional)</span>
          </label>
          <textarea
            id="jd"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            disabled={isSubmitting}
            rows={6}
            placeholder="Paste a job description here to also check how well your resume matches its keywords..."
            className="w-full rounded-lg border border-border bg-surface p-3 text-sm outline-none focus:border-accent disabled:opacity-60"
          />
        </div>

        {error && <p className="text-sm text-status-fail">{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={isSubmitting || !file}
          className="w-full rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-accent-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? "Checking your resume..." : "Check My Resume"}
        </button>
        <p className="text-center text-xs text-muted">
          Your resume is used only to generate this report and isn&apos;t shared with anyone.
        </p>
      </div>
    </div>
  );
}
