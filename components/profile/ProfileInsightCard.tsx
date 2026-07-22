"use client";

import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface InsightItem {
  label: string;
  description?: string;
  framework_ref?: string;
}

interface ProfileInsightCardProps {
  title: string;
  icon: LucideIcon;
  iconColorClass: string;
  items: InsightItem[];
  emptyMessage?: string;
  className?: string;
}

/**
 * ProfileInsightCard — reusable card for Strengths, Risks, Opportunities panels.
 */
export function ProfileInsightCard({
  title,
  icon: Icon,
  iconColorClass,
  items,
  emptyMessage = "None identified yet.",
  className,
}: ProfileInsightCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card p-5 flex flex-col gap-3",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <div
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-md",
            iconColorClass
          )}
        >
          <Icon className="h-4 w-4" />
        </div>
        <h3 className="font-semibold text-foreground">{title}</h3>
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      ) : (
        <ul className="space-y-3">
          {items.map((item, i) => (
            <li key={i} className="text-sm">
              <p className="font-medium text-foreground">{item.label}</p>
              {item.description && (
                <p className="mt-0.5 text-muted-foreground">{item.description}</p>
              )}
              {item.framework_ref && (
                <span className="mt-1 inline-block rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
                  {item.framework_ref}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
