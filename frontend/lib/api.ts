import type { CheckResult } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseErrorMessage(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.detail || `Request failed with status ${res.status}`;
  } catch {
    return `Request failed with status ${res.status}`;
  }
}

export async function checkResume(file: File, jobDescription: string): Promise<CheckResult> {
  const formData = new FormData();
  formData.append("resume", file);
  if (jobDescription.trim()) {
    formData.append("job_description", jobDescription.trim());
  }

  const res = await fetch(`${API_URL}/api/check`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorMessage(res));
  }
  return res.json();
}

export async function getReport(id: string): Promise<CheckResult> {
  const res = await fetch(`${API_URL}/api/report/${id}`);
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorMessage(res));
  }
  return res.json();
}

export async function emailReport(
  id: string,
  email: string
): Promise<{ saved: boolean; sent: boolean; message?: string }> {
  const res = await fetch(`${API_URL}/api/report/${id}/email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorMessage(res));
  }
  return res.json();
}
