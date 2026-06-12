"use client";

import { motion } from "framer-motion";
import { Heart } from "lucide-react";
import { useMemo } from "react";

import { AuthorCard } from "@/components/AuthorCard";
import { Hero } from "@/components/Hero";
import { GithubIcon } from "@/components/icons";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { MobileNavigation } from "@/components/MobileNavigation";
import { TableOfContents } from "@/components/TableOfContents";
import { useScrollProgress } from "@/hooks/use-scroll-progress";
import { useScrollSpy } from "@/hooks/use-scroll-spy";
import { buildSections } from "@/lib/sections";
import { scrollToSection } from "@/lib/scroll";

const GITHUB_URL = "https://github.com/derpixler/raido-fm";

/**
 * Interactive, semantically structured layout of the landing page.
 * The 1:1 Markdown content (from readme.md) is passed as a prop and structured
 * into <main> › <article> › <section> › <header>.
 */
export function LandingClient({ markdown }: { markdown: string }) {
  const sections = useMemo(() => buildSections(markdown), [markdown]);
  const ids = useMemo(() => sections.map((s) => s.id), [sections]);
  const contentSections = useMemo(
    () => sections.filter((s) => s.id !== "hero"),
    [sections],
  );

  const { activeId, readIds } = useScrollSpy(ids);
  const progress = useScrollProgress();

  return (
    <>
      <MobileNavigation
        sections={sections}
        activeId={activeId}
        readIds={readIds}
        progress={progress}
        onNavigate={scrollToSection}
      />

      {/* Full-bleed Hero across the full header width */}
      <section id="hero" aria-label="Introduction" className="scroll-mt-0">
        <Hero />
      </section>

      <div className="mx-auto grid w-full max-w-7xl grid-cols-1 gap-10 px-5 lg:grid-cols-[16rem_minmax(0,1fr)] lg:gap-16 lg:px-8">
        {/* Sticky desktop navigation */}
        <aside
          className="hidden lg:block"
          aria-label="Page navigation and reading progress"
        >
          <div className="sticky top-0 max-h-screen overflow-y-auto py-12 pr-2">
            <TableOfContents
              sections={sections}
              activeId={activeId}
              readIds={readIds}
              progress={progress}
              onNavigate={scrollToSection}
            />
          </div>
        </aside>

        <main className="min-w-0 pb-24 pt-4 lg:pt-12">
          <article
            className="mt-8"
            itemScope
            itemType="https://schema.org/TechArticle"
            aria-label="RAIDO — A Manifest for Autonomous AI Radio"
          >
            <meta
              itemProp="headline"
              content="RAIDO — A Manifest for Autonomous AI Radio"
            />
            <meta itemProp="author" content="René Reimann" />
            <meta itemProp="inLanguage" content="en" />

            <div className="space-y-20">
              {contentSections.map((section, index) => {
                const position = index + 1;
                const titleId = `${section.id}-title`;
                return (
                  <motion.section
                    key={section.id}
                    id={section.id}
                    aria-labelledby={titleId}
                    data-section={section.id}
                    data-index={position}
                    itemProp="hasPart"
                    itemScope
                    itemType="https://schema.org/CreativeWork"
                    className="scroll-mt-24 lg:scroll-mt-12"
                    initial={{ opacity: 0, y: 28 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: "0px 0px -15% 0px" }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                  >
                    {/* Non-visible section metadata (Microdata) */}
                    <meta itemProp="position" content={String(position)} />
                    <meta itemProp="name" content={section.title} />

                    <header className="mb-4">
                      <span
                        aria-hidden="true"
                        className="font-mono text-xs font-medium tracking-widest text-primary-glow"
                      >
                        {String(position).padStart(2, "0")}
                      </span>
                      <h2
                        id={titleId}
                        className="mt-1 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl"
                      >
                        {section.title}
                      </h2>
                    </header>

                    <div itemProp="text">
                      <MarkdownRenderer content={section.body} />
                    </div>
                  </motion.section>
                );
              })}
            </div>
          </article>

          <AuthorCard />

          <footer className="mt-24 border-t border-border pt-8">
            <div className="flex flex-col items-start justify-between gap-4 text-sm text-muted sm:flex-row sm:items-center">
              <p className="flex items-center gap-1.5">
                Built with <Heart className="size-4 text-primary-glow" /> for
                open communities.
              </p>
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noreferrer noopener"
                className="inline-flex items-center gap-2 text-muted transition-colors hover:text-foreground"
              >
                <GithubIcon className="size-4" />
                derpixler/raido-fm
              </a>
            </div>
          </footer>
        </main>
      </div>
    </>
  );
}
