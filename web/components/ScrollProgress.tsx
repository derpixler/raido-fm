"use client";

import { motion } from "framer-motion";

/** Animated progress bar incl. percentage ("X% read"). */
export function ScrollProgress({ progress }: { progress: number }) {
  const percent = Math.round(progress * 100);

  return (
    <div>
      <div className="flex items-center justify-between text-xs text-muted">
        <span className="font-mono tabular-nums text-foreground">
          {percent}%
        </span>
        <span>read</span>
      </div>
      <div
        className="mt-2 h-1 w-full overflow-hidden rounded-full bg-border"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Reading progress"
      >
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-primary to-primary-glow"
          initial={false}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.25, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
