"use client";

import { useState } from "react";
import { ReconciliationResult } from "@/lib/types";

// Placeholder components to be implemented
import UploadScreen from "@/components/UploadScreen";
import DashboardScreen from "@/components/DashboardScreen";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [result, setResult] = useState<ReconciliationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleDemoLoad = async () => {
    setIsLoading(true);
    try {
      // 1. Try backend first (FastAPI)
      try {
        const res = await fetch(`${API_URL}/demo`);
        if (res.ok) {
          const data = await res.json();
          setResult(data);
          return;
        }
      } catch (e) {
        console.warn("Backend /demo failed, falling back to static JSON", e);
      }
      
      // 2. Fallback to static JSON for instant load (rider #1)
      const res = await fetch("/demo_results.json");
      if (!res.ok) throw new Error("Failed to load static demo data");
      const data = await res.json();
      setResult(data);
      
    } catch (error) {
      console.error("Error loading demo:", error);
      alert("Failed to load demo data.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (purchaseFile: File, gstFile: File) => {
    setIsLoading(true);
    setUploadError(null);
    try {
      // 1. POST both CSVs to /reconcile. The engine runs synchronously on the
      // backend, so by the time this resolves the result is already computed
      // and stored under run_id — no polling loop needed, just one more fetch.
      const form = new FormData();
      form.append("purchases", purchaseFile);
      form.append("gsts", gstFile);

      const reconcileRes = await fetch(`${API_URL}/reconcile`, {
        method: "POST",
        body: form,
      });

      if (!reconcileRes.ok) {
        const body = await reconcileRes.json().catch(() => null);
        throw new Error(body?.detail || `Reconcile failed (${reconcileRes.status})`);
      }

      const { run_id } = await reconcileRes.json();

      // 2. Fetch the finished result.
      const runRes = await fetch(`${API_URL}/runs/${run_id}`);
      if (!runRes.ok) {
        throw new Error(`Could not retrieve run ${run_id} (${runRes.status})`);
      }
      const data = await runRes.json();
      setResult(data);

    } catch (error) {
      console.error("Error running reconciliation:", error);
      const message = error instanceof Error ? error.message : "Upload failed.";
      setUploadError(
        message.includes("fetch")
          ? `Couldn't reach the backend at ${API_URL}. Is recongraph-api running?`
          : message
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-6 max-w-7xl mx-auto flex flex-col gap-8">
      <header className="flex items-center justify-between border-b border-[var(--color-border)] pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--color-primary)]">ReconGraph</h1>
          <p className="text-[var(--color-text-muted)] text-sm mt-1">Financial Intelligence Engine</p>
        </div>
        
        {result && (
          <button 
            onClick={() => setResult(null)}
            className="text-sm px-4 py-2 rounded bg-[var(--color-surface-hover)] hover:bg-[var(--color-surface-elevated)] border border-[var(--color-border)] transition-colors"
          >
            Start New Run
          </button>
        )}
      </header>

      {!result ? (
        <UploadScreen
          onDemoLoad={handleDemoLoad}
          onUpload={handleUpload}
          isLoading={isLoading}
          error={uploadError}
        />
      ) : (
        <DashboardScreen result={result} />
      )}
    </main>
  );
}
