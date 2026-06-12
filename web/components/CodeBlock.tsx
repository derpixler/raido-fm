"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

type CodeBlockProps = {
  children: React.ReactNode;
  rawCode: string;
  language?: string;
};

/** Code block with dark theme, language label and copy button. */
export function CodeBlock({ children, rawCode, language }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(rawCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* Clipboard not available — silently ignore. */
    }
  };

  return (
    <div className="group relative my-6 overflow-hidden rounded-xl border border-border bg-[#0A0A0A]">
      <div className="flex items-center justify-between border-b border-border/70 px-4 py-2">
        <span className="font-mono text-xs uppercase tracking-wider text-muted">
          {language || "code"}
        </span>
        <button
          type="button"
          onClick={copy}
          aria-label="Copy code"
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium text-muted transition-colors hover:bg-surface hover:text-foreground",
          )}
        >
          {copied ? (
            <>
              <Check className="size-3.5 text-primary-glow" />
              Copied
            </>
          ) : (
            <>
              <Copy className="size-3.5" />
              Copy
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto whitespace-pre p-4 text-sm leading-relaxed [&>code]:bg-transparent [&>code]:p-0 [&>code]:font-mono">
        {children}
      </pre>
    </div>
  );
}
