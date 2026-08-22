"use client";

import React, { useState } from "react";
import type { ReconciliationResult } from "@/lib/types";
import { buildReportCsv, type ReportKind } from "@/lib/csv";
import { exportReport } from "@/lib/api";
import { Button } from "@/components/ui/button";

interface ExportButtonProps {
  result: ReconciliationResult;
  report?: ReportKind;
  runId?: string | null;
  filename?: string;
  className?: string;
}

/**
 * Reusable export button. When a backend `runId` is present it downloads from
 * the API (`/runs/{id}/export`); otherwise it falls back to client-side CSV
 * generation so the static demo still works.
 */
export default function ExportButton({
  result,
  report = "match_summary",
  runId,
  filename,
  className,
}: ExportButtonProps) {
  const [busy, setBusy] = useState(false);

  async function handleExport() {
    setBusy(true);
    try {
      if (runId) {
        await exportReport(runId, report, "csv", filename);
        return;
      }
      const csv = buildReportCsv(result, report);
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename ?? `recongraph-${report}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export failed", e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Button size="sm" variant="outline" onClick={handleExport} disabled={busy} className={className}>
      <svg aria-hidden="true" className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3M3 16v2a2 2 0 002 2h14a2 2 0 002-2v-2" />
      </svg>
      {busy ? "Exporting…" : `Export ${report.replace("_", " ")}`}
    </Button>
  );
}
