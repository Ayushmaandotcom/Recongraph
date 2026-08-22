"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import type { MatchStatus } from "@/lib/types";

const STATUS_META: Record<string, { variant: "success" | "warning" | "danger" | "info" | "neutral" }> = {
  "Exact Match": { variant: "success" },
  "Suggested Match": { variant: "info" },
  "Mismatch": { variant: "danger" },
  "Manual Match": { variant: "warning" },
  "Only in 2A/2B": { variant: "neutral" },
  "Only in Books": { variant: "neutral" },
};

interface MatchStatusPillProps {
  status: MatchStatus;
  className?: string;
}

/**
 * Reusable pill for the field-rule match status taxonomy
 * (Exact / Suggested / Mismatch / Only-in-2B / Only-in-Books).
 */
export default function MatchStatusPill({ status, className }: MatchStatusPillProps) {
  const meta = STATUS_META[status] ?? { variant: "neutral" as const };
  return (
    <Badge variant={meta.variant} className={className}>
      {status}
    </Badge>
  );
}
