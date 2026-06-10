"use client";

import { motion } from "framer-motion";

import type { Section } from "@/lib/sections";
import { cn } from "@/lib/utils";

type SignalNavigationProps = {
  sections: Section[];
  activeId: string;
  readIds: Set<string>;
  onNavigate: (id: string) => void;
};

type Status = "active" | "read" | "pending";

function statusOf(id: string, activeId: string, readIds: Set<string>): Status {
  if (id === activeId) return "active";
  if (readIds.has(id)) return "read";
  return "pending";
}

/**
 * Navigation im Stil einer Radio-Signalstrecke:
 * ○ nicht erreicht · ● gelesen · ▶ aktiv — verbunden durch eine Signalleitung.
 */
export function SignalNavigation({
  sections,
  activeId,
  readIds,
  onNavigate,
}: SignalNavigationProps) {
  return (
    <nav aria-label="Table of contents">
      <ol className="relative">
        {sections.map((section, i) => {
          const status = statusOf(section.id, activeId, readIds);
          const next = sections[i + 1];
          const lineFilled =
            status === "read" ||
            (status === "active" && readIds.has(section.id)) ||
            (next && (next.id === activeId || readIds.has(next.id)));

          return (
            <li key={section.id} className="relative">
              <button
                type="button"
                onClick={() => onNavigate(section.id)}
                aria-current={status === "active" ? "true" : undefined}
                className={cn(
                  "group flex w-full items-center gap-3 rounded-lg py-1.5 pl-1 pr-2 text-left transition-colors",
                  status === "active"
                    ? "text-foreground"
                    : "text-muted hover:text-foreground",
                )}
              >
                <SignalMarker status={status} />
                <span className="flex items-baseline gap-2 truncate text-sm">
                  <span className="font-mono text-[0.7rem] tabular-nums text-muted/60">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span
                    className={cn(
                      "truncate transition-colors",
                      status === "active" && "font-medium",
                    )}
                  >
                    {section.title}
                  </span>
                </span>
              </button>

              {i < sections.length - 1 && (
                <span
                  aria-hidden="true"
                  className="absolute left-[0.6875rem] top-[1.85rem] h-[calc(100%-1.4rem)] w-px overflow-hidden bg-border"
                >
                  <motion.span
                    className="block w-full bg-gradient-to-b from-primary-glow to-primary"
                    initial={false}
                    animate={{ height: lineFilled ? "100%" : "0%" }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                  />
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function SignalMarker({ status }: { status: Status }) {
  return (
    <span className="relative flex size-[1.375rem] shrink-0 items-center justify-center">
      {status === "active" && (
        <motion.span
          className="absolute inset-0 rounded-full bg-primary/30"
          animate={{ scale: [1, 1.6, 1], opacity: [0.6, 0, 0.6] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: "easeOut" }}
        />
      )}
      {status === "active" ? (
        // ▶ aktiv
        <span className="relative flex size-[1.05rem] items-center justify-center rounded-full bg-primary text-white shadow-[0_0_12px_rgba(139,92,246,0.8)]">
          <svg viewBox="0 0 8 8" className="size-2 fill-current">
            <path d="M1 0.5 L7 4 L1 7.5 Z" />
          </svg>
        </span>
      ) : status === "read" ? (
        // ● gelesen
        <span className="size-2.5 rounded-full bg-primary-glow shadow-[0_0_8px_rgba(167,139,250,0.6)]" />
      ) : (
        // ○ nicht erreicht
        <span className="size-2.5 rounded-full border border-border bg-transparent" />
      )}
    </span>
  );
}
