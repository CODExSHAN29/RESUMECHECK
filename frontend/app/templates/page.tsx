import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Templates — ResumeCheck",
};

export default function TemplatesPage() {
  return (
    <div className="mx-auto max-w-2xl px-6 py-24 text-center">
      <h1 className="text-2xl font-semibold tracking-tight">Templates — coming soon</h1>
      <p className="mx-auto mt-3 max-w-md text-muted">
        We&apos;re building a library of ATS-friendly resume templates you&apos;ll be able to buy and
        export directly. Check your resume today, and we&apos;ll let you know when templates launch.
      </p>
    </div>
  );
}
