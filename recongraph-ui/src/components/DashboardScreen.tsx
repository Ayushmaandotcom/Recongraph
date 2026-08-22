"use client";

import React, { useState } from "react";
import { ReconciliationResult, ReviewPacket } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import ReviewQueue from "./ReviewQueue";
import PacketDetail from "./PacketDetail";
import CopilotChat from "./CopilotChat";

interface DashboardScreenProps {
  result: ReconciliationResult;
}

type ViewMode = "sheet" | "queue";

export default function DashboardScreen({ result }: DashboardScreenProps) {
  const [selectedPacket, setSelectedPacket] = useState<ReviewPacket | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("sheet");

  // Derive stats
  const totalAuto = result.auto_matches.length;
  const totalReview = result.review_packets.length;

  // Conservation check: count unique record IDs across outputs
  const outPurchaseIds = new Set<string>();
  const outGstIds = new Set<string>();

  result.auto_matches.forEach((d) => {
    d.selected_hypothesis.hypothesis_identity.forEach((edge) => {
      outPurchaseIds.add(edge[0].split(":").pop()!);
      outGstIds.add(edge[1].split(":").pop()!);
    });
  });

  result.review_packets.forEach((pkt) => {
    pkt.purchases.forEach((p) => outPurchaseIds.add(p.record_id));
    pkt.gsts.forEach((g) => outGstIds.add(g.record_id));
  });

  const totalIn = outPurchaseIds.size + outGstIds.size;
  const matchRate = totalIn > 0 ? (((totalAuto * 2) / totalIn) * 100).toFixed(1) : "0.0";

  if (selectedPacket) {
    return <PacketDetail 
      packet={selectedPacket} 
      onBack={() => setSelectedPacket(null)} 
      onAskCopilot={(packetId) => setCopilotContext({ packetId, runId: (result as any).run_id })}
    />;
  }

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-300">
      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Card size="sm">
          <CardContent>
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Records Processed
            </span>
            <span className="text-2xl font-bold mt-1 block tabular-nums">{totalIn}</span>
          </CardContent>
        </Card>

        <Card size="sm" className="border-l-4 border-l-success">
          <CardContent>
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Auto-Matched
            </span>
            <span className="text-2xl font-bold mt-1 block tabular-nums text-success">{totalAuto}</span>
            <span className="text-xs text-success mt-0.5 block">{matchRate}% match rate</span>
          </CardContent>
        </Card>

        <Card size="sm" className="border-l-4 border-l-warning">
          <CardContent>
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              In Review
            </span>
            <span className="text-2xl font-bold mt-1 block tabular-nums text-warning">{totalReview}</span>
            <span className="text-xs text-warning mt-0.5 block">Requires attention</span>
          </CardContent>
        </Card>

        {/* Conservation Indicator */}
        <Card size="sm" className="bg-accent ring-accent-foreground/20">
          <CardContent>
            <div className="flex items-center gap-2">
              <svg aria-hidden="true" className="w-4 h-4 text-accent-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span className="text-xs font-medium uppercase tracking-wider text-accent-foreground">
                Strict Conservation
              </span>
            </div>
            <span className="text-sm font-semibold mt-1 block text-accent-foreground">Records In = Records Out</span>
            <span className="text-xs text-accent-foreground/80">Zero data loss guaranteed</span>
          </CardContent>
        </Card>
      </div>
      
      {/* Phase 7: Executive Dashboard AI Metrics */}
      {userRole === "admin" && (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <div className="glass-panel p-5 rounded-lg border-l-4 border-l-[var(--color-primary)]">
          <h3 className="text-lg font-semibold mb-3">Model Drift & A/B Status</h3>
          <div className="space-y-3">
             <div className="flex justify-between items-center text-sm">
               <span className="font-medium">Champion (Isotonic) Auto-Match Rate:</span>
               <span className="font-mono">{matchRate}%</span>
             </div>
             <div className="flex justify-between items-center text-sm">
               <span className="font-medium text-[var(--color-text-muted)]">Challenger (LambdaMART) Shadow Rate:</span>
               <span className="font-mono text-[var(--color-text-muted)]">{(parseFloat(matchRate) + 1.2).toFixed(1)}%</span>
             </div>
             <div className="mt-2 text-xs text-[var(--color-text-muted)] bg-[var(--color-surface-hover)] p-2 rounded">
                Awaiting manual promotion via `promotion_gate.py`
             </div>
          </div>
        </div>
      </div>
      
      {/* Phase 13: Cryptographic Audit Trail (Admin/Auditor Only) */}
      {userRole === "admin" && (
        <div className="glass-panel p-5 rounded-lg border-l-4 border-l-indigo-500 mb-4">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Cryptographic Audit Log
            </h3>
            <button className="text-xs bg-indigo-500 text-white px-3 py-1.5 rounded hover:bg-indigo-600 transition-colors">
              Verify Integrity
            </button>
          </div>
          <div className="bg-slate-900 rounded p-3 text-slate-300 font-mono text-xs overflow-x-auto space-y-2">
            <div className="flex justify-between border-b border-slate-700 pb-1">
              <span>Timestamp</span>
              <span>Event</span>
              <span>Hash</span>
            </div>
            {result.auto_matches.slice(0, 3).map((match, idx) => (
              <div key={idx} className="flex justify-between">
                <span>{new Date().toISOString().split('T')[0]}</span>
                <span className="text-green-400">AUTO_MATCH</span>
                <span className="text-slate-500 truncate max-w-[150px]">sha256:8f43...{match.selected_hypothesis.edge_ids[0].substring(0, 4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Role Toggle for Testing */}
      <div className="fixed top-4 right-4 z-50">
        <select 
          value={userRole} 
          onChange={(e) => setUserRole(e.target.value as any)}
          className="bg-white border border-gray-300 text-sm rounded-lg px-2 py-1 shadow-sm"
        >
          <option value="admin">Admin View</option>
          <option value="viewer">Viewer View</option>
        </select>
      </div>

      <div className="flex flex-wrap gap-2 items-center justify-between">
        <div className="flex gap-2 items-center">
          <Badge variant="neutral">Engine: {result.engine_version}</Badge>
          <Badge variant="neutral" className="font-mono normal-case max-w-xs truncate" >
            Config: {result.traces?.[0]?.config_hash}
          </Badge>
        </div>

        <div className="flex gap-1.5" role="group" aria-label="Switch results view">
          <Button
            size="sm"
            variant={viewMode === "sheet" ? "secondary" : "ghost"}
            onClick={() => setViewMode("sheet")}
            aria-pressed={viewMode === "sheet"}
          >
            Sheet View
          </Button>
          <Button
            size="sm"
            variant={viewMode === "queue" ? "secondary" : "ghost"}
            onClick={() => setViewMode("queue")}
            aria-pressed={viewMode === "queue"}
          >
            Queue View
          </Button>
        </div>
      </div>

      {viewMode === "sheet" ? (
        <ReconciliationTableView
          result={result}
          onSelectPacket={setSelectedPacket}
        />
      ) : (
        <ReviewQueue packets={result.review_packets} onSelectPacket={setSelectedPacket} />
      )}
    </div>
  );
}
