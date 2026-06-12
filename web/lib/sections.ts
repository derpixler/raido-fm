import { slugify } from "@/lib/utils";

export type Section = {
  /** URL-safe ID, serves as scroll anchor and IntersectionObserver target. */
  id: string;
  /** Visible title (from the `## ` heading or hardcoded for the Hero). */
  title: string;
  /** Markdown body of the section (without the heading). Empty for the Hero. */
  body: string;
};

/** Fixed first section: the Hero is rendered as a component, not as Markdown. */
export const HERO_SECTION: Section = { id: "hero", title: "Hero", body: "" };

/**
 * Splits a Markdown document at every `## ` heading into individual sections.
 * This way the table of contents is generated dynamically from the content —
 * new headings appear in the navigation without code changes.
 */
export function parseSections(markdown: string): Section[] {
  const lines = markdown.split("\n");
  const sections: Section[] = [];
  let current: Section | null = null;

  for (const line of lines) {
    const match = /^##\s+(.+?)\s*$/.exec(line);
    if (match) {
      if (current) sections.push(current);
      const title = match[1].trim();
      // Heading goes into `title` and is semantically rendered in the <header>
      // of the section (not in the Markdown body) — see LandingClient.
      current = { id: slugify(title), title, body: "" };
    } else if (current) {
      current.body += (current.body ? "\n" : "") + line;
    }
  }
  if (current) sections.push(current);

  return sections.map((s) => ({ ...s, body: s.body.trim() }));
}

/** All sections including Hero — source of truth for nav & scroll spy. */
export function buildSections(markdown: string): Section[] {
  return [HERO_SECTION, ...parseSections(markdown)];
}
