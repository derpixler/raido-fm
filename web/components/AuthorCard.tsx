"use client";

import { motion } from "framer-motion";
import { MapPin } from "lucide-react";

import { GithubIcon, LinkedInIcon } from "@/components/icons";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const GITHUB_URL = "https://github.com/derpixler";
const LINKEDIN_URL = "https://www.linkedin.com/in/rene-reimann-18b50a127/";
const REPO_URL = "https://github.com/derpixler/raido-fm";

/** Highlight-Stationen aus dem Werdegang — kompakt als „Pills". */
const HIGHLIGHTS = [
  "20+ years building for the web",
  "Software Engineer · Immoware24",
  "Ex-CHECK24 · Ex-Inpsyde",
  "Co-author · WordPress book (Rheinwerk)",
  "Co-host · WP Sofa podcast",
];

/**
 * Eigenständige, gestaltete Autoren-Sektion (statt eines schlichten Markdown-
 * Blockquotes). Die Inhalte spiegeln das öffentliche Profil von René Reimann.
 */
export function AuthorCard() {
  return (
    // Semantischer Wrapper trägt die Microdata (inkl. itemID) — framer-motion
    // reicht itemID nicht durch, daher animieren wir das innere <div>.
    <section
      aria-labelledby="author-title"
      className="mt-24"
      itemScope
      itemType="https://schema.org/Person"
      // Gleiche ID wie die JSON-LD-Person (page.tsx) → eine Entität für Suchmaschinen.
      itemID="https://raido.fm/#author"
    >
      <motion.div
        initial={{ opacity: 0, y: 28 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "0px 0px -15% 0px" }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="relative overflow-hidden rounded-3xl border border-border bg-surface/60 p-8 backdrop-blur sm:p-10"
      >
        {/* Violetter Glow oben rechts als dezenter Akzent */}
        <div className="pointer-events-none absolute -right-16 -top-16 size-56 rounded-full bg-primary/20 blur-[100px]" />

        <span className="font-mono text-xs font-medium tracking-widest text-primary-glow">
          ABOUT THE AUTHOR
        </span>

      <div className="mt-6 flex flex-col gap-8 sm:flex-row sm:items-start">
        {/* Monogramm-Avatar (kein Foto hinterlegt) */}
        <div
          aria-hidden="true"
          className="relative flex size-24 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-primary-glow text-3xl font-semibold tracking-tight text-white shadow-[0_16px_40px_-12px_rgba(139,92,246,0.7)]"
        >
          RR
          <span className="absolute inset-0 rounded-2xl ring-1 ring-inset ring-white/15" />
        </div>

        <div className="min-w-0 flex-1">
          <h2
            id="author-title"
            className="text-2xl font-semibold tracking-tight text-foreground"
            itemProp="name"
          >
            René Reimann
          </h2>
          <p
            className="mt-1 text-sm text-muted"
            itemProp="jobTitle"
          >
            Software Developer &amp; Systems Architect
          </p>
          <p
            className="mt-1 flex items-center gap-1.5 text-sm text-muted"
            itemProp="address"
            itemScope
            itemType="https://schema.org/PostalAddress"
          >
            <MapPin className="size-3.5 text-primary-glow" />
            <span itemProp="addressLocality">Halle (Saale)</span>
            <span itemProp="addressCountry" content="DE">
              , Germany
            </span>
          </p>

          <p className="mt-5 border-l-2 border-primary/60 pl-4 text-base italic text-muted/90">
            &ldquo;Syntax is a commodity. Context is the currency.&rdquo;
          </p>

          <p className="mt-5 text-base leading-relaxed text-muted" itemProp="description">
            Software developer and systems architect with 20+ years of building
            web applications. Today he explores autonomous AI infrastructure and
            the boundaries of synthetic media — RAIDO FM is one of those
            experiments.
          </p>

          <ul className="mt-5 flex flex-wrap gap-2" aria-label="Career highlights">
            {HIGHLIGHTS.map((item) => (
              <li
                key={item}
                className="rounded-full border border-border bg-background/60 px-3 py-1 text-xs text-muted"
              >
                {item}
              </li>
            ))}
          </ul>

          <div className="mt-7 flex flex-wrap gap-3">
            <a
              href={LINKEDIN_URL}
              target="_blank"
              rel="noreferrer noopener"
              className={cn(buttonVariants({ variant: "default", size: "sm" }))}
              itemProp="sameAs"
            >
              <LinkedInIcon className="size-4" />
              LinkedIn
            </a>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer noopener"
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
              itemProp="sameAs"
            >
              <GithubIcon className="size-4" />
              GitHub
            </a>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer noopener"
              className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
            >
              derpixler/raido-fm
            </a>
          </div>
        </div>
      </div>
      </motion.div>
    </section>
  );
}
