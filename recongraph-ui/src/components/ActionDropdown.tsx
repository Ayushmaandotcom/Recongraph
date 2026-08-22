"use client";

import React, { useState } from "react";
import type { ImsAction } from "@/lib/types";
import { Button } from "@/components/ui/button";

const ACTIONS: { value: ImsAction; variant: "ghost" | "secondary" | "destructive" | "default" }[] = [
  { value: "Accept", variant: "default" },
  { value: "Reject", variant: "destructive" },
  { value: "Pending", variant: "secondary" },
  { value: "Ignore", variant: "ghost" },
];

interface ActionDropdownProps {
  current?: ImsAction;
  onAction?: (action: ImsAction) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Reusable IMS action control (Accept / Reject / Pending / Ignore).
 * Mutually-exclusive segmented control; the selected action is highlighted.
 */
export default function ActionDropdown({
  current = "No Action",
  onAction,
  disabled,
  className,
}: ActionDropdownProps) {
  const [selected, setSelected] = useState<ImsAction>(current);

  function choose(action: ImsAction) {
    setSelected(action);
    onAction?.(action);
  }

  return (
    <div className={`flex flex-wrap gap-1.5 ${className ?? ""}`} role="group" aria-label="IMS action">
      {ACTIONS.map(({ value, variant }) => (
        <Button
          key={value}
          size="xs"
          variant={selected === value ? "default" : variant}
          onClick={() => choose(value)}
          disabled={disabled}
          aria-pressed={selected === value}
          className={selected === value ? "bg-primary" : ""}
        >
          {value}
        </Button>
      ))}
    </div>
  );
}
