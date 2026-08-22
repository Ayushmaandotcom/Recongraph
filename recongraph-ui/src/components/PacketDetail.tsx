"use client";

import React, { useState } from "react";
import { ReviewPacket, ExplanationNode } from "@/lib/types";
import ReactMarkdown from "react-markdown";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PacketDetailProps {
  packet: ReviewPacket;
  onBack: () => void;
}

export default function PacketDetail({ packet, onBack }: PacketDetailProps) {
  // Try to find the leading hypothesis to display its signals
  const hyp = packet.competitors?.[0];
  const signals: Record<string, number | null> = {
    entity: null,
    reference: null,
    amount: null,
    temporal: null,
    tax_identity: null
  };
  
  if (hyp?.supporting_evidence?.metadata) {
    const meta = hyp.supporting_evidence.metadata;
    // Extract signals if available in the metadata (or we mock them based on base_score for the demo)
    // In actual implementation, we'd pull from provider_projection_identities or trace
    // For the UI rider: we must use actual fields.
  }

  const [feedbackStatus, setFeedbackStatus] = useState<string | null>(null);

  const handleFeedback = async (action: "Approve" | "Reject") => {
    try {
      const res = await fetch(`${API_URL}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          packet_id: packet.packet_id,
          action: action,
          payload: {
            purchases: packet.purchases,
            gsts: packet.gsts,
            hypothesis: hyp
          }
        }),
      });
      if (res.ok) {
        setFeedbackStatus(`Successfully recorded: ${action}`);
        setTimeout(onBack, 1500); // go back to queue after feedback
      }
    } catch (e) {
      console.error("Feedback error", e);
      setFeedbackStatus("Failed to record feedback.");
    }
  };

  return (
    <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-right-8 duration-300">
      <div className="flex items-center gap-4 border-b border-[var(--color-border)] pb-4">
        <button 
          onClick={onBack}
          className="p-2 rounded-full hover:bg-[var(--color-surface-hover)] transition-colors text-[var(--color-text-muted)]"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold font-mono text-[var(--color-text)]">{packet.packet_id}</h2>
            <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-[var(--color-surface-elevated)] border border-[var(--color-border)]">
              {packet.action}
            </span>
          </div>
          <p className="text-lg text-[var(--color-text-muted)] mt-1">{packet.headline}</p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          {typeof packet.ml_confidence === "number" && (
            <div className="flex items-center gap-4 mr-4">
              <div className="flex flex-col items-end">
                <span className="text-xs uppercase tracking-wider text-[var(--color-text-muted)] font-semibold">Champion (LGBM)</span>
                <span className={`text-sm font-bold font-mono px-2 py-0.5 rounded mt-1 ${packet.ml_confidence >= 0.85 ? 'bg-green-100 text-green-800 border-green-300' : packet.ml_confidence >= 0.50 ? 'bg-yellow-100 text-yellow-800 border-yellow-300' : 'bg-red-100 text-red-800 border-red-300'} border`}>
                  {(packet.ml_confidence * 100).toFixed(1)}%
                </span>
              </div>
              
              {packet.ai_provenance && packet.ai_provenance.challenger_confidence !== undefined && (
                <div className="flex flex-col items-end border-l border-[var(--color-border)] pl-4">
                  <span className="text-xs uppercase tracking-wider text-[var(--color-text-muted)] font-semibold flex items-center gap-1">
                    <svg className="w-3 h-3 text-[var(--color-warning)]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    Challenger
                  </span>
                  <span className="text-sm font-bold font-mono px-2 py-0.5 rounded mt-1 bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-muted)]">
                    {(packet.ai_provenance.challenger_confidence * 100).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          )}
          {feedbackStatus ? (
            <span className="text-sm text-[var(--color-success)] font-medium">{feedbackStatus}</span>
          ) : (
            <>
              <button 
                onClick={() => handleFeedback("Reject")}
                className="px-4 py-2 rounded bg-transparent border border-[var(--color-danger)] text-[var(--color-danger)] hover:bg-[var(--color-danger)] hover:text-white transition-colors text-sm font-semibold"
              >
                Reject as Contradiction
              </button>
              <button 
                onClick={() => handleFeedback("Approve")}
                className="px-4 py-2 rounded bg-[var(--color-primary)] text-white hover:opacity-90 transition-opacity text-sm font-semibold shadow-md"
              >
                Approve as Match
              </button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col: The Records */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="glass-panel p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-[var(--color-primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Record Comparison
            </h3>
            
            {/* Purchase Records */}
            <div className="mb-6">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Internal Purchases</h4>
              {packet.purchases.length === 0 ? (
                <div className="p-4 bg-[var(--color-surface)] border border-[var(--color-border)] rounded text-sm text-[var(--color-text-muted)]">No purchase records in this packet.</div>
              ) : (
                <div className="space-y-3">
                  {packet.purchases.map(p => (
                    <div key={p.record_id} className="p-4 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md flex justify-between items-center group">
                      <div className="flex flex-col gap-1">
                        <span className="font-mono text-xs text-[var(--color-text-muted)]">{p.record_id}</span>
                        <span className="font-medium">{p.vendor_name || <span className="text-[var(--color-unknown)] italic">Unknown Vendor</span>}</span>
                        <div className="flex gap-3 text-sm mt-1">
                          <span className="text-[var(--color-text-muted)]">Ref: <span className="text-[var(--color-text)] font-mono">{p.reference || "N/A"}</span></span>
                          <span className="text-[var(--color-text-muted)]">GSTIN: <span className="text-[var(--color-text)] font-mono">{p.tax_identity || "N/A"}</span></span>
                          <span className="text-[var(--color-text-muted)]">Date: <span className="text-[var(--color-text)]">{p.record_date}</span></span>
                        </div>
                      </div>
                      <div className="text-xl font-semibold font-mono">
                        ₹{parseFloat(p.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* GST Records */}
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Counterparty GST</h4>
              {packet.gsts.length === 0 ? (
                <div className="p-4 bg-[var(--color-surface)] border border-[var(--color-border)] rounded text-sm text-[var(--color-text-muted)]">No GST records in this packet.</div>
              ) : (
                <div className="space-y-3">
                  {packet.gsts.map(g => (
                    <div key={g.record_id} className="p-4 bg-[var(--color-surface)] border border-l-4 border-l-[var(--color-primary)] border-[var(--color-border)] rounded-md flex justify-between items-center group">
                      <div className="flex flex-col gap-1">
                        <span className="font-mono text-xs text-[var(--color-text-muted)]">{g.record_id}</span>
                        <span className="font-medium">{g.vendor_name || <span className="text-[var(--color-unknown)] italic">Unknown Vendor</span>}</span>
                        <div className="flex gap-3 text-sm mt-1">
                          <span className="text-[var(--color-text-muted)]">Ref: <span className="text-[var(--color-text)] font-mono">{g.reference || "N/A"}</span></span>
                          <span className="text-[var(--color-text-muted)]">GSTIN: <span className="text-[var(--color-text)] font-mono">{g.tax_identity || "N/A"}</span></span>
                          <span className="text-[var(--color-text-muted)]">Date: <span className="text-[var(--color-text)]">{g.record_date}</span></span>
                        </div>
                      </div>
                      <div className="text-xl font-semibold font-mono">
                        ₹{parseFloat(g.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
          </div>
        </div>

        {/* Right Col: Signals & Explanation */}
        <div className="flex flex-col gap-6">
          <div className="glass-panel p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-[var(--color-primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Semantic Findings
            </h3>
            
            {/* The Thesis Bar Chart (Grey vs Red) */}
            <div className="space-y-4">
              {hyp?.semantic_findings?.length ? (
                <div className="flex flex-col gap-2">
                  {hyp.semantic_findings.map((finding: string, i: number) => (
                    <div key={i} className="px-3 py-2 bg-[var(--color-danger-muted)] text-[var(--color-danger)] border border-[var(--color-danger)]/30 rounded text-sm font-medium flex items-center gap-2">
                      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      {finding}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded text-sm text-[var(--color-text-muted)] text-center italic">
                  No blocking semantic findings detected.
                </div>
              )}
            </div>
            
            <div className="mt-6 pt-6 border-t border-[var(--color-border)]">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-3">AI Legal & Contextual Explanation</h4>
              <div className="text-sm bg-[var(--color-surface-hover)] p-4 rounded border border-[var(--color-border)] text-[var(--color-text)] leading-relaxed max-w-none">
                {packet.llm_explanation ? (
                  <ReactMarkdown>{packet.llm_explanation}</ReactMarkdown>
                ) : (
                  <span className="text-[var(--color-text-muted)] italic">No AI explanation provided for this packet.</span>
                )}
              </div>
              {packet.llm_citation && (
                <div className="mt-3 p-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded text-xs text-[var(--color-text-muted)]">
                  <span className="font-semibold text-[var(--color-text)] block mb-1">Citations & Retrieval Trace:</span>
                  <div className="font-mono whitespace-pre-wrap">{packet.llm_citation}</div>
                </div>
              )}
            </div>

            <div className="mt-6 pt-6 border-t border-[var(--color-border)]">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Deterministic Engine Trajectory</h4>
              <div className="text-sm bg-[var(--color-surface-hover)] p-4 rounded border border-[var(--color-border)] whitespace-pre-wrap font-mono text-[var(--color-text-muted)] leading-relaxed h-48 overflow-y-auto">
                {packet.explanation ? (
                  JSON.stringify(packet.explanation, null, 2)
                ) : (
                  "Engine rationale is logged in the Trace."
                )}
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
