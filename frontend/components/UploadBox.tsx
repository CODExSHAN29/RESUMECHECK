"use client";

import { useRef, useState } from "react";

const ACCEPTED_EXTENSIONS = [".pdf", ".docx"];

function isAcceptedFile(file: File): boolean {
  const lower = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

export default function UploadBox({
  file,
  onFileSelected,
  disabled,
}: {
  file: File | null;
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFile(f: File | undefined) {
    if (!f) return;
    if (!isAcceptedFile(f)) {
      setError("Please upload a PDF or DOCX file.");
      return;
    }
    setError(null);
    onFileSelected(f);
  }

  return (
    <div>
      <div
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          if (!disabled) handleFile(e.dataTransfer.files?.[0]);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-14 text-center transition-colors ${
          isDragging ? "border-accent bg-accent/5" : "border-border"
        } ${disabled ? "cursor-not-allowed opacity-60" : "hover:border-accent"}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          disabled={disabled}
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        {file ? (
          <>
            <p className="text-sm font-medium">{file.name}</p>
            <p className="mt-1 text-xs text-muted">Click or drop a different file to replace it</p>
          </>
        ) : (
          <>
            <p className="text-sm font-medium">Drag and drop your resume here</p>
            <p className="mt-1 text-xs text-muted">or click to browse — PDF or DOCX, up to 10MB</p>
          </>
        )}
      </div>
      {error && <p className="mt-2 text-xs text-status-fail">{error}</p>}
    </div>
  );
}
