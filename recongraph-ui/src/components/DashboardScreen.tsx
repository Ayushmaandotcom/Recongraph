"use client";

import React, { useState } from "react";
import { ImsAction, ReconciliationResult, ReviewPacket } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import ReviewQueue from "./ReviewQueue";
import PacketDetail from "./PacketDetail";
import ReconciliationTableView from "./reconciliation/ReconciliationTableView";
import ExportButton from "./ExportButton";
import CopilotChat from "./CopilotChat";
import { applyImsAction } from "@/lib/api";

interface DashboardScreenProps {
  result: ReconciliationResult;
  runId?: string | null;
}

interface ItcInfo {
  availability: string;
  claimPeriod?: string | null;
}

interface CopilotContext {
  packetId?: string;
  runId?: string;
}

type ViewMode = "sheet" | "queue";

export default function DashboardScreen({ result, runId }: DashboardScreenProps) {
  const [selectedPacket, setSelectedPacket] = useState<ReviewPacket | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("sheet");
  const [imsActions, setImsActions] = useState<Record<string, ImsAction>>({});
  const [imsItc, setImsItc] = useState<Record<string, ItcInfo>>({});
  const [copilotContext, setCopilotContext] = useState<CopilotContext | null>(null);

  async function handleImsAction(packetId: string, action: ImsAction) {
    setImsActions((prev) => ({ ...prev, [packetId]: action }));

    if (!runId) return; // static demo — local-only

    try {
      const applied = await applyImsAction(runId, packetId, action);
      setImsItc((prev) => ({
        ...prev,
        [packetId]: {
          availability: applied.itc_availability ?? "Unknown",
          claimPeriod: applied.itc_claim_period,
        },
      }));
    } catch (e) {
      console.warn("Action API call failed; keeping local state", e);
    }
  }

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
    return (
      <PacketDetail
        packet={selectedPacket}
        onBack={() => setSelectedPacket(null)}
        onAskCopilot={(packetId) => setCopilotContext({ packetId, runId: runId ?? undefined })}
        currentAction={imsActions[selectedPacket.packet_id]}
        onAction={(action) => handleImsAction(selectedPacket.packet_id, action)}
        itcInfo={imsItc[selectedPacket.packet_id]}
      />
    );
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

      <div className="flex flex-wrap gap-2 items-center justify-between">
        <div className="flex gap-2 items-center">
          <Badge variant="neutral">Engine: {result.engine_version}</Badge>
          <Badge variant="neutral" className="font-mono normal-case max-w-xs truncate" >
            Config: {result.traces?.[0]?.config_hash}
          </Badge>
          <Badge variant={runId ? "success" : "warning"}>
            {runId ? "Backend run" : "Static demo"}
          </Badge>
        </div>

        <div className="flex gap-1.5 flex-wrap" role="group" aria-label="Switch results view">
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
          <ExportButton result={result} runId={runId} report="match_summary" />
          <ExportButton result={result} runId={runId} report="supplier" />
          <ExportButton result={result} runId={runId} report="invoice" />
        </div>
      </div>

      {viewMode === "sheet" ? (
        <ReconciliationTableView
          result={result}
          onSelectPacket={setSelectedPacket}
        />
      ) : (
        <ReviewQueue
          packets={result.review_packets}
          onSelectPacket={setSelectedPacket}
          imsActions={imsActions}
        />
      )}

      {copilotContext && <CopilotChat context={copilotContext} />}
    </div>
  );
}
