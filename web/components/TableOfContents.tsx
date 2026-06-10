"use client";

import { GithubIcon, LinkedInIcon } from "@/components/icons";
import { ScrollProgress } from "@/components/ScrollProgress";
import { SignalNavigation } from "@/components/SignalNavigation";
import { asset } from "@/lib/asset";
import type { Section } from "@/lib/sections";

const GITHUB_URL = "https://github.com/derpixler";
const LINKEDIN_URL = "https://www.linkedin.com/in/rene-reimann-18b50a127/";

type TableOfContentsProps = {
  sections: Section[];
  activeId: string;
  readIds: Set<string>;
  progress: number;
  onNavigate: (id: string) => void;
};

/**
 * Sticky Desktop-Sidebar: Marke, Lesefortschritt und die Signal-Navigation.
 * Das Inhaltsverzeichnis entsteht dynamisch aus den Markdown-Überschriften.
 */
export function TableOfContents({
  sections,
  activeId,
  readIds,
  progress,
  onNavigate,
}: TableOfContentsProps) {
  return (
    <div className="flex flex-col gap-7">
      <a
        href="#hero"
        onClick={(e) => {
          e.preventDefault();
          onNavigate("hero");
        }}
        className="flex w-full items-center"
        aria-label="RAIDO FM — back to top"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={asset("/raido-fm-logo.webp")}
          alt="RAIDO FM"
          className="h-auto w-full"
          decoding="async"
        />
      </a>

      <ScrollProgress progress={progress} />

      <SignalNavigation
        sections={sections}
        activeId={activeId}
        readIds={readIds}
        onNavigate={onNavigate}
      />

      {/* Autoren-Block */}
      <div className="rounded-xl border border-border bg-surface/40 p-4">
        <div className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="https://github.com/derpixler.png"
            alt="René Reimann"
            className="size-11 shrink-0 rounded-full border border-border object-cover"
            loading="lazy"
            decoding="async"
          />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-foreground">
              René Reimann
            </p>
            <p className="truncate text-xs text-muted">
              Developer &amp; systems architect · Halle (Saale)
            </p>
          </div>
        </div>

        <p className="mt-3 text-xs leading-relaxed text-muted">
          Building autonomous AI infrastructure and exploring the boundaries of
          synthetic media.
        </p>

        <div className="mt-3 flex items-center gap-2">
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer noopener"
            aria-label="René Reimann on GitHub"
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium text-muted transition-colors hover:bg-surface hover:text-foreground"
          >
            <GithubIcon className="size-3.5" />
            GitHub
          </a>
          <a
            href={LINKEDIN_URL}
            target="_blank"
            rel="noreferrer noopener"
            aria-label="René Reimann on LinkedIn"
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium text-muted transition-colors hover:bg-surface hover:text-foreground"
          >
            <LinkedInIcon className="size-3.5" />
            LinkedIn
          </a>
        </div>
      </div>
    </div>
  );
}
