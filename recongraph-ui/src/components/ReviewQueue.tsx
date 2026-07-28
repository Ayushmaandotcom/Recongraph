"use client";

import React, { useState } from "react";
import { ReviewPacket } from "@/lib/types";

interface ReviewQueueProps {
  packets: ReviewPacket[];
  onSelectPacket: (packet: ReviewPacket) => void;
}

export default function ReviewQueue({ packets, onSelectPacket }: ReviewQueueProps) {
  const [filter, setFilter] = useState<string>("ALL");
  
  const filteredPackets = filter === "ALL" 
    ? packets 
    : packets.filter(p => p.action === filter);

  return (
    <div className="glass-panel rounded-lg overflow-hidden flex flex-col">
      {/* Header & Filters */}
      <div className="p-5 border-b border-[var(--color-border)] flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Action Queue</h3>
          <p className="text-sm text-[var(--color-text-muted)]">Packets requiring human review or resolution</p>
        </div>
        
        <div className="flex gap-2">
          <button 
            onClick={() => setFilter("ALL")}
            className={`px-3 py-1.5 rounded text-sm transition-colors ${filter === "ALL" ? "bg-[var(--color-surface-elevated)] text-white font-medium" : "text-[var(--color-text-muted)] hover:text-white hover:bg-[var(--color-surface-hover)]"}`}
          >
            All
          </button>
          <button 
            onClick={() => setFilter("review_ambiguous")}
            className={`px-3 py-1.5 rounded text-sm transition-colors ${filter === "review_ambiguous" ? "bg-[var(--color-surface-elevated)] text-[var(--color-warning)] font-medium" : "text-[var(--color-text-muted)] hover:text-white hover:bg-[var(--color-surface-hover)]"}`}
          >
            Ambiguous
          </button>
          <button 
            onClick={() => setFilter("review_weak")}
            className={`px-3 py-1.5 rounded text-sm transition-colors ${filter === "review_weak" ? "bg-[var(--color-surface-elevated)] text-[var(--color-primary)] font-medium" : "text-[var(--color-text-muted)] hover:text-white hover:bg-[var(--color-surface-hover)]"}`}
          >
            Weak Evidence
          </button>
          <button 
            onClick={() => setFilter("no_match")}
            className={`px-3 py-1.5 rounded text-sm transition-colors ${filter === "no_match" ? "bg-[var(--color-surface-elevated)] text-[var(--color-danger)] font-medium" : "text-[var(--color-text-muted)] hover:text-white hover:bg-[var(--color-surface-hover)]"}`}
          >
            Leftovers
          </button>
        </div>
      </div>
      
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[var(--color-surface)] border-b border-[var(--color-border)] text-[var(--color-text-muted)] text-sm">
              <th className="p-4 font-medium">Packet ID</th>
              <th className="p-4 font-medium">Severity</th>
              <th className="p-4 font-medium w-1/2">Headline</th>
              <th className="p-4 font-medium">Shape (P:G)</th>
              <th className="p-4 font-medium text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredPackets.map((pkt) => {
              // Color coding by severity
              let badgeColor = "bg-[var(--color-unknown)] text-white";
              let actionLabel: string = pkt.action;
              
              if (pkt.action === "review_ambiguous") {
                badgeColor = "bg-[var(--color-warning-muted)] text-[var(--color-warning)] border border-[var(--color-warning)]/30";
                actionLabel = "Ambiguous";
              } else if (pkt.action === "review_weak") {
                badgeColor = "bg-[var(--color-primary-muted)] text-[var(--color-primary)] border border-[var(--color-primary)]/30";
                actionLabel = "Weak Evidence";
              } else if (pkt.action === "no_match") {
                badgeColor = "bg-[var(--color-danger-muted)] text-[var(--color-danger)] border border-[var(--color-danger)]/30";
                actionLabel = "Leftover";
              }
              
              return (
                <tr 
                  key={pkt.packet_id} 
                  className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] transition-colors group cursor-pointer"
                  onClick={() => onSelectPacket(pkt)}
                >
                  <td className="p-4 font-mono text-sm">{pkt.packet_id}</td>
                  <td className="p-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${badgeColor}`}>
                      {actionLabel}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm block truncate max-w-md" title={pkt.headline}>
                      {pkt.headline}
                    </span>
                  </td>
                  <td className="p-4 text-sm font-mono text-[var(--color-text-muted)]">
                    {pkt.purchases.length}:{pkt.gsts.length}
                  </td>
                  <td className="p-4 text-right">
                    <button className="text-[var(--color-primary)] hover:text-[var(--color-primary-hover)] text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                      Open Review →
                    </button>
                  </td>
                </tr>
              );
            })}
            
            {filteredPackets.length === 0 && (
              <tr>
                <td colSpan={5} className="p-10 text-center text-[var(--color-text-muted)]">
                  No packets match the selected filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
