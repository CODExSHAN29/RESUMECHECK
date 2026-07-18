"use client";

import { useState } from "react";
import { ApiError, emailReport } from "@/lib/api";

export default function EmailCaptureForm({ reportId }: { reportId: string }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("sending");
    setMessage(null);
    try {
      const res = await emailReport(reportId, email);
      setStatus("done");
      setMessage(res.sent ? "Report sent! Check your inbox." : res.message || "Saved.");
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof ApiError ? err.message : "Couldn't save your email. Try again.");
    }
  }

  if (status === "done") {
    return (
      <div className="rounded-lg border border-border p-4 text-sm">
        <p className="font-medium text-status-pass">{message}</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-border p-4">
      <h3 className="text-sm font-semibold">Email me this report</h3>
      <p className="mt-1 text-xs text-muted">
        We&apos;ll also let you know when ResumeCheck templates launch.
      </p>
      <div className="mt-3 flex gap-2">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="flex-1 rounded-lg border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <button
          type="submit"
          disabled={status === "sending"}
          className="shrink-0 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-accent-foreground hover:opacity-90 disabled:opacity-50"
        >
          {status === "sending" ? "Sending..." : "Send"}
        </button>
      </div>
      {status === "error" && <p className="mt-2 text-xs text-status-fail">{message}</p>}
    </form>
  );
}
