import type { IssueStatus } from "@/lib/types";

const LABELS: Record<IssueStatus, string> = {
  pass: "Pass",
  warn: "Needs attention",
  fail: "Fail",
};

const COLOR_VARS: Record<IssueStatus, string> = {
  pass: "var(--status-pass)",
  warn: "var(--status-warn)",
  fail: "var(--status-fail)",
};

export default function StatusBadge({ status }: { status: IssueStatus }) {
  const color = COLOR_VARS[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
      style={{ backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`, color }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
      {LABELS[status]}
    </span>
  );
}
