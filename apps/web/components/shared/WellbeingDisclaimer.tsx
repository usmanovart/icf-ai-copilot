"use client";

import { AlertTriangle, X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface WellbeingDisclaimerProps {
  /** Variant controls display prominence */
  variant?: "banner" | "inline" | "compact";
  /** Allow the user to dismiss the banner (banner variant only) */
  dismissible?: boolean;
  className?: string;
}

const DISCLAIMER_TEXT =
  "ICF AI Copilot is a personal development and decision-support tool. " +
  "It is not a medical, psychological, or clinical service. " +
  "None of the assessments, insights, or recommendations constitute medical advice. " +
  "If you are experiencing significant distress, please consult a qualified professional.";

/**
 * WellbeingDisclaimer
 *
 * Rendered on every AI response that touches wellbeing domains.
 * Required by the non-diagnostic guidelines (docs/safety/non-diagnostic-guidelines.md).
 */
export function WellbeingDisclaimer({
  variant = "inline",
  dismissible = false,
  className,
}: WellbeingDisclaimerProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  if (variant === "compact") {
    return (
      <p
        className={cn(
          "text-xs text-muted-foreground flex items-start gap-1.5",
          className
        )}
        role="note"
        aria-label="Non-diagnostic disclaimer"
      >
        <AlertTriangle className="h-3 w-3 mt-0.5 flex-shrink-0 text-amber-500" />
        <span>
          For personal development only — not medical or clinical advice.
          If you are in distress, please seek professional support.
        </span>
      </p>
    );
  }

  if (variant === "banner") {
    return (
      <div
        className={cn(
          "relative flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800",
          className
        )}
        role="note"
        aria-label="Non-diagnostic disclaimer"
      >
        <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-600" aria-hidden />
        <p>{DISCLAIMER_TEXT}</p>
        {dismissible && (
          <button
            onClick={() => setDismissed(true)}
            aria-label="Dismiss disclaimer"
            className="ml-auto flex-shrink-0 rounded p-0.5 text-amber-600 hover:bg-amber-100 focus:outline-none focus:ring-2 focus:ring-amber-400"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    );
  }

  // default: inline
  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800",
        className
      )}
      role="note"
      aria-label="Non-diagnostic disclaimer"
    >
      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-amber-500" aria-hidden />
      <p>{DISCLAIMER_TEXT}</p>
    </div>
  );
}
