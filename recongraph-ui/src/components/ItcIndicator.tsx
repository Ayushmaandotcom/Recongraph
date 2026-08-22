"use client";

import React from "react";
import type { ItcAvailability } from "@/lib/types";
import { Badge } from "@/components/ui/badge";

const AVAILABILITY_VARIANT: Record<ItcAvailability, "success" | "danger" | "warning" | "neutral"> = {
  Available: "success",
  Unavailable: "danger",
  Ineligible: "warning",
  Unknown: "neutral",
};

interface ItcIndicatorProps {
  availability: ItcAvailability;
  claimPeriod?: string | null;
  reason?: string | null;
  className?: string;
}

/**
 * Reusable ITC (Input Tax Credit) availability indicator with claim period.
 */
export default function ItcIndicator({
  availability,
  claimPeriod,
  reason,
  className,
}: ItcIndicatorProps) {
  return (
    <div className={`flex flex-col gap-1 ${className ?? ""}`}>
      <Badge variant={AVAILABILITY_VARIANT[availability] ?? "neutral"}>
        ITC {availability}
      </Badge>
      {claimPeriod && (
        <span className="text-xs text-muted-foreground font-mono">
          Claim period: {claimPeriod}
        </span>
      )}
      {reason && (
        <span className="text-xs text-muted-foreground">{reason}</span>
      )}
    </div>
  );
}
