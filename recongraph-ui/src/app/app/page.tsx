"use client";

import { useState } from "react";
import Link from "next/link";
import { ReconciliationResult } from "@/lib/types";
import { Button } from "@/components/ui/button";

import UploadScreen from "@/components/UploadScreen";
import DashboardScreen from "@/components/DashboardScreen";
import { loadDemo } from "@/lib/api";

export default function AppPage() {
  const [result, setResult] = useState<ReconciliationResult | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDemoLoad = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Try backend first (FastAPI) — returns { run_id, result }
      try {
        const data = await loadDemo();
        if (data?.result) {
          setRunId(data.run_id ?? null);
          setResult(data.result);
          return;
        }
      } catch (e) {
        console.warn("Backend /demo failed, falling back to static JSON", e);
      }

      // 2. Fallback to static JSON for instant load (no run_id)
      const res = await fetch("/demo_results.json");
      if (!res.ok) throw new Error("Failed to load static demo data");
      const data = await res.json();
      setRunId(null);
      setResult(data);
    } catch (err) {
      console.error("Error loading demo:", err);
      setError("Failed to load the demo dataset. Check the console for details.");
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setResult(null);
    setRunId(null);
  };

  return (
    <main className="min-h-screen px-4 py-6 md:px-6 max-w-7xl mx-auto flex flex-col gap-6">
      <header className="flex items-center justify-between border-b border-border pb-4">
        <Link href="/" className="group">
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            Recon<span className="text-primary">Graph</span>
          </h1>
          <p className="text-muted-foreground text-xs mt-0.5 group-hover:text-foreground/80 transition-colors">
            Deterministic GST Reconciliation
          </p>
        </Link>

        {result && (
          <Button variant="outline" size="sm" onClick={reset}>
            Start New Run
          </Button>
        )}
      </header>

      {error && (
        <div
          role="alert"
          className="px-4 py-3 rounded-md bg-destructive/15 border border-destructive/40 text-destructive text-sm"
        >
          {error}
        </div>
      )}

      {!result ? (
        <UploadScreen onDemoLoad={handleDemoLoad} isLoading={isLoading} />
      ) : (
        <DashboardScreen result={result} runId={runId} />
      )}
    </main>
  );
}
