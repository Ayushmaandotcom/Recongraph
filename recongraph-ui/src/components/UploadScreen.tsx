"use client";

import React from "react";

interface UploadScreenProps {
  onDemoLoad: () => void;
  isLoading: boolean;
}

export default function UploadScreen({ onDemoLoad, isLoading }: UploadScreenProps) {
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
          <div className="border-2 border-dashed border-[var(--color-border)] rounded-lg p-8 flex flex-col items-center justify-center text-center cursor-not-allowed opacity-50 bg-[var(--color-surface)]">
            <svg className="w-8 h-8 text-[var(--color-text-muted)] mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span className="font-medium text-sm">Purchase Register (CSV)</span>
            <span className="text-xs text-[var(--color-text-muted)] mt-1">Coming Soon</span>
          </div>
          
          <div className="border-2 border-dashed border-[var(--color-border)] rounded-lg p-8 flex flex-col items-center justify-center text-center cursor-not-allowed opacity-50 bg-[var(--color-surface)]">
            <svg className="w-8 h-8 text-[var(--color-text-muted)] mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span className="font-medium text-sm">GST Records (CSV)</span>
            <span className="text-xs text-[var(--color-text-muted)] mt-1">Coming Soon</span>
          </div>
        </div>

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
