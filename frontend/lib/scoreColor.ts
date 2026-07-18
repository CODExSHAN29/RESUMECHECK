export function scoreColorVar(score: number): string {
  if (score >= 80) return "var(--status-pass)";
  if (score >= 50) return "var(--status-warn)";
  return "var(--status-fail)";
}

export function scoreLabel(score: number): string {
  if (score >= 80) return "Strong";
  if (score >= 50) return "Needs work";
  return "At risk";
}
