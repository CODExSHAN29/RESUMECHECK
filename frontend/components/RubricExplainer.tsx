"use client";

import { useState } from "react";
import type { RubricInfo } from "@/lib/types";

const LABELS: Record<string, string> = {
  parseability_format: "Parseability & Format",
  layout_structure: "Layout & Structure",
  content_completeness: "Content Completeness",
  keyword_match: "Keyword Match",
};

export default function RubricExplainer({ rubric }: { rubric: RubricInfo }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border border-border">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium"
      >
        How is this score calculated?
        <span className="text-muted">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="border-t border-border px-4 py-3 text-sm text-muted">
          <p>{rubric.note}</p>
          <ul className="mt-3 space-y-1">
            {Object.entries(rubric.applied_weights).map(([key, weight]) => (
              <li key={key} className="flex justify-between">
                <span>{LABELS[key] ?? key}</span>
                <span className="font-medium text-foreground">{Math.round(weight * 100)}%</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
