"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";

type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "neutral";

export type StatusKind = "action" | "ims";

const ACTION_META: Record<string, { label: string; variant: BadgeVariant }> = {
  auto_match: { label: "Auto Match", variant: "success" },
  review_weak: { label: "Weak Evidence", variant: "info" },
  review_ambiguous: { label: "Ambiguous", variant: "warning" },
  no_match: { label: "Leftover", variant: "danger" },
};

const IMS_META: Record<string, { label: string; variant: BadgeVariant }> = {
  "No Action": { label: "No Action", variant: "neutral" },
  Accept: { label: "Accept", variant: "success" },
  Reject: { label: "Reject", variant: "danger" },
  Pending: { label: "Pending", variant: "warning" },
  Ignore: { label: "Ignore", variant: "neutral" },
};

interface StatusBadgeProps {
  value: string;
  kind?: StatusKind;
  className?: string;
}

/**
 * Reusable status badge that maps an engine action or IMS action to a
 * color-coded badge. Falls back to a neutral badge for unknown values.
 */
export default function StatusBadge({ value, kind = "action", className }: StatusBadgeProps) {
  const meta = kind === "ims" ? IMS_META[value] : ACTION_META[value];
  const label = meta?.label ?? value;
  const variant = meta?.variant ?? "neutral";

  return (
    <Badge variant={variant} className={className}>
      {label}
    </Badge>
  );
}
