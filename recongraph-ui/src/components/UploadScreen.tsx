"use client";

import React, { useState, useRef } from "react";

interface UploadScreenProps {
  onDemoLoad: () => void;
  onUpload: (purchaseFile: File, gstFile: File) => void;
  isLoading: boolean;
  error?: string | null;
}

function FileDropSlot({
  label,
  file,
  onSelect,
  disabled,
}: {
  label: string;
  file: File | null;
  onSelect: (f: File) => void;
  disabled: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => inputRef.current?.click()}
      className={`border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center text-center transition-colors bg-[var(--color-surface)] ${
        file
          ? "border-[var(--color-primary)]"
          : "border-[var(--color-border)] hover:border-[var(--color-primary)]"
      } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        disabled={disabled}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onSelect(f);
        }}
      />
      <svg className="w-8 h-8 text-[var(--color-text-muted)] mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <span className="font-medium text-sm">{label}</span>
      <span className="text-xs text-[var(--color-text-muted)] mt-1 truncate max-w-[180px]">
        {file ? file.name : "Click to choose CSV"}
      </span>
    </button>
  );
}

export default function UploadScreen({ onDemoLoad, onUpload, isLoading, error }: UploadScreenProps) {
  const [purchaseFile, setPurchaseFile] = useState<File | null>(null);
  const [gstFile, setGstFile] = useState<File | null>(null);
  const canRun = purchaseFile && gstFile && !isLoading;

  return (
    <div className="flex flex-col items-center justify-center mt-20 gap-8">
      <div className="text-center space-y-3 max-w-xl">
        <h2 className="text-4xl font-bold tracking-tight text-[var(--color-text)]">
          Reconcile with Confidence.
        </h2>
        <p className="text-lg text-[var(--color-text-muted)]">
          The deterministic graph engine that proves every match and explains every conflict without data loss.
        </p>
      </div>

      <div className="glass-panel w-full max-w-2xl rounded-xl p-10 flex flex-col items-center gap-6 shadow-2xl">
        <div className="grid grid-cols-2 gap-6 w-full">
          <FileDropSlot
            label="Purchase Register (CSV)"
            file={purchaseFile}
            onSelect={setPurchaseFile}
            disabled={isLoading}
          />
          <FileDropSlot
            label="GST Records (CSV)"
            file={gstFile}
            onSelect={setGstFile}
            disabled={isLoading}
          />
        </div>

        {error && (
          <div className="w-full text-sm text-red-500 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-2">
            {error}
          </div>
        )}

        <button
          onClick={() => canRun && onUpload(purchaseFile!, gstFile!)}
          disabled={!canRun}
          className="w-full py-4 rounded-lg bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white font-semibold tracking-wide transition-all shadow-lg disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isLoading ? "Executing Engine..." : "Run Reconciliation"}
        </button>

        <div className="w-full flex items-center gap-4">
          <div className="h-px bg-[var(--color-border)] flex-1"></div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Or try it out</span>
          <div className="h-px bg-[var(--color-border)] flex-1"></div>
        </div>

        <button
          onClick={onDemoLoad}
          disabled={isLoading}
          className="w-full py-4 rounded-lg bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white font-semibold tracking-wide transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-wait"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Executing Engine...
            </>
          ) : (
            "Load Demo Dataset (Challenge Referee)"
          )}
        </button>
      </div>
    </div>
  );
}
