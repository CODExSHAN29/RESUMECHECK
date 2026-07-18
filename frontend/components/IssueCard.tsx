"use client";

import { useState } from "react";
import type { Issue } from "@/lib/types";
import StatusBadge from "./StatusBadge";

export default function IssueCard({ issue }: { issue: Issue }) {
  const [open, setOpen] = useState(issue.status !== "pass");

  return (
    <div className="rounded-lg border border-border">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <span className="text-sm font-medium">{issue.title}</span>
        <div className="flex shrink-0 items-center gap-3">
          <StatusBadge status={issue.status} />
          <span className="text-muted">{open ? "−" : "+"}</span>
        </div>
      </button>
      {open && (
        <div className="border-t border-border px-4 py-3 text-sm">
          <p className="text-muted">{issue.detail}</p>
          {issue.fix && (
            <p className="mt-2">
              <span className="font-medium">Fix: </span>
              {issue.fix}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
