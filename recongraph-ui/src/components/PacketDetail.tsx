"use client";

import React from "react";
import { ReviewPacket } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface PacketDetailProps {
  packet: ReviewPacket;
  onBack: () => void;
}

function RecordRow({
  record,
  highlighted,
}: {
  record: ReviewPacket["purchases"][number];
  highlighted?: boolean;
}) {
  return (
    <div
      className={`p-4 bg-secondary border rounded-md flex flex-wrap justify-between items-center gap-3 ${
        highlighted ? "border-l-4 border-l-primary border-border" : "border-border"
      }`}
    >
      <div className="flex flex-col gap-1 min-w-0">
        <span className="font-mono text-xs text-muted-foreground break-all">{record.record_id}</span>
        <span className="font-medium">
          {record.vendor_name || <span className="text-muted-foreground italic">Unknown Vendor</span>}
        </span>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm mt-1">
          <span className="text-muted-foreground">
            Ref: <span className="text-foreground font-mono">{record.reference || "N/A"}</span>
          </span>
          <span className="text-muted-foreground">
            GSTIN: <span className="text-foreground font-mono">{record.tax_identity || "N/A"}</span>
          </span>
          <span className="text-muted-foreground">
            Date: <span className="text-foreground">{record.record_date}</span>
          </span>
        </div>
      </div>
      <div className="text-lg font-semibold font-mono whitespace-nowrap tabular-nums">
        ₹{parseFloat(record.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
      </div>
    </div>
  );
}

export default function PacketDetail({ packet, onBack }: PacketDetailProps) {
  // Leading hypothesis carries the semantic findings
  const hyp = packet.competitors?.[0];

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-300">
      <div className="flex items-start gap-4 border-b border-border pb-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={onBack}
          aria-label="Back to review queue"
          className="mt-1"
        >
          <svg aria-hidden="true" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </Button>
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-xl font-bold font-mono text-foreground">{packet.packet_id}</h2>
            <Badge variant="neutral">{packet.action}</Badge>
          </div>
          <p className="text-base text-muted-foreground mt-1">{packet.headline}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: The Records */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <Card aria-labelledby="record-comparison-heading">
            <CardContent className="pt-1">
              <h3 id="record-comparison-heading" className="text-base font-semibold mb-4 flex items-center gap-2">
                <svg aria-hidden="true" className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Record Comparison
              </h3>

              {/* Purchase Records */}
              <div className="mb-6">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Internal Purchases
                </h4>
                {packet.purchases.length === 0 ? (
                  <div className="p-4 bg-muted border border-border rounded text-sm text-muted-foreground">
                    No purchase records in this packet.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {packet.purchases.map((p) => (
                      <RecordRow key={p.record_id} record={p} />
                    ))}
                  </div>
                )}
              </div>

              {/* GST Records */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Counterparty GST
                </h4>
                {packet.gsts.length === 0 ? (
                  <div className="p-4 bg-muted border border-border rounded text-sm text-muted-foreground">
                    No GST records in this packet.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {packet.gsts.map((g) => (
                      <RecordRow key={g.record_id} record={g} highlighted />
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Col: Signals & Explanation */}
        <div className="flex flex-col gap-6">
          <Card aria-labelledby="semantic-findings-heading">
            <CardContent className="pt-1">
              <h3 id="semantic-findings-heading" className="text-base font-semibold mb-4 flex items-center gap-2">
                <svg aria-hidden="true" className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Semantic Findings
              </h3>

              <div className="space-y-4">
                {hyp?.semantic_findings?.length ? (
                  <ul className="flex flex-col gap-2" aria-label="Blocking semantic findings">
                    {hyp.semantic_findings.map((finding: string, i: number) => (
                      <li
                        key={i}
                        className="px-3 py-2 bg-destructive/15 text-destructive border border-destructive/40 rounded text-sm font-medium flex items-start gap-2"
                      >
                        <svg aria-hidden="true" className="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {finding}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="p-3 bg-muted border border-border rounded text-sm text-muted-foreground text-center italic">
                    No blocking semantic findings detected.
                  </div>
                )}
              </div>

              <div className="mt-6 pt-6 border-t border-border">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Explanation Trajectory
                </h4>
                <div className="text-xs bg-muted p-4 rounded border border-border whitespace-pre-wrap font-mono text-muted-foreground leading-relaxed overflow-x-auto max-h-96">
                  {packet.explanation
                    ? JSON.stringify(packet.explanation, null, 2)
                    : "Engine rationale is logged in the Trace."}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
