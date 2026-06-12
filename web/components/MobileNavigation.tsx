"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { asset } from "@/lib/asset";
import type { Section } from "@/lib/sections";
import { cn } from "@/lib/utils";

type MobileNavigationProps = {
  sections: Section[];
  activeId: string;
  readIds: Set<string>;
  progress: number;
  onNavigate: (id: string) => void;
};

/**
 * Sticky dropdown navigation for mobile. Shows the automatically detected
 * active section and allows jumping to any other.
 */
export function MobileNavigation({
  sections,
  activeId,
  readIds,
  progress,
  onNavigate,
}: MobileNavigationProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const activeIndex = Math.max(
    0,
    sections.findIndex((s) => s.id === activeId),
  );
  const active = sections[activeIndex];

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div
      ref={ref}
      className="sticky top-0 z-50 border-b border-border bg-background/85 backdrop-blur-xl lg:hidden"
    >
      <div className="flex items-center gap-3 px-4 py-3">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={asset("/raido-fm-logo.webp")}
          alt="RAIDO FM"
          className="h-7 w-auto shrink-0"
          decoding="async"
        />

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-haspopup="listbox"
          className="flex flex-1 items-center justify-between rounded-lg border border-border bg-surface/60 px-3 py-2 text-sm"
        >
          <span className="flex items-center gap-2 truncate">
            <span className="font-mono text-xs text-muted">
              {String(activeIndex + 1).padStart(2, "0")}
            </span>
            <span className="truncate font-medium text-foreground">
              {active?.title}
            </span>
          </span>
          <ChevronDown
            className={cn(
              "size-4 text-muted transition-transform duration-200",
              open && "rotate-180",
            )}
          />
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-0.5 w-full bg-border/60">
        <motion.div
          className="h-full bg-gradient-to-r from-primary to-primary-glow"
          initial={false}
          animate={{ width: `${Math.round(progress * 100)}%` }}
          transition={{ duration: 0.25, ease: "easeOut" }}
        />
      </div>

      <AnimatePresence>
        {open && (
          <motion.ul
            role="listbox"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="absolute inset-x-0 top-full max-h-[70vh] overflow-y-auto border-b border-border bg-background/95 px-3 py-2 shadow-2xl backdrop-blur-xl"
          >
            {sections.map((section, i) => {
              const isActive = section.id === activeId;
              const isRead = readIds.has(section.id);
              return (
                <li key={section.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={isActive}
                    onClick={() => {
                      onNavigate(section.id);
                      setOpen(false);
                    }}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors",
                      isActive
                        ? "bg-primary/15 text-foreground"
                        : "text-muted hover:bg-surface hover:text-foreground",
                    )}
                  >
                    <span className="font-mono text-xs tabular-nums text-muted/60">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="flex-1 truncate">{section.title}</span>
                    {isActive ? (
                      <span className="size-2 rounded-full bg-primary shadow-[0_0_8px_rgba(139,92,246,0.8)]" />
                    ) : isRead ? (
                      <Check className="size-3.5 text-primary-glow/70" />
                    ) : null}
                  </button>
                </li>
              );
            })}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
