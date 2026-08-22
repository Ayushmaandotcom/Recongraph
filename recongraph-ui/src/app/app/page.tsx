"use client";

import { useState } from "react";
import Link from "next/link";
import { ReconciliationResult } from "@/lib/types";
import { Button } from "@/components/ui/button";

import UploadScreen from "@/components/UploadScreen";
import DashboardScreen from "@/components/DashboardScreen";

export default function AppPage() {
  const [result, setResult] = useState<ReconciliationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDemoLoad = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Try backend first (FastAPI)
      try {
        const res = await fetch("http://localhost:8000/demo");
        if (res.ok) {
          const data = await res.json();
          setResult(data);
          return;
        }
      } catch (e) {
        console.warn("Backend /demo failed, falling back to static JSON", e);
      }

      // 2. Fallback to static JSON for instant load
      const res = await fetch("/demo_results.json");
      if (!res.ok) throw new Error("Failed to load static demo data");
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error("Error loading demo:", err);
      setError("Failed to load the demo dataset. Check the console for details.");
    } finally {
      setIsLoading(false);
    }
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
          <Button variant="outline" size="sm" onClick={() => setResult(null)}>
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
        <DashboardScreen result={result} />
      )}
    </main>
  );
}
