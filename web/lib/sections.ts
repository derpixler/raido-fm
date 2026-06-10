import { slugify } from "@/lib/utils";

export type Section = {
  /** URL-sichere ID, dient als Scroll-Anker und IntersectionObserver-Ziel. */
  id: string;
  /** Sichtbarer Titel (aus der `## `-Überschrift bzw. fest für den Hero). */
  title: string;
  /** Markdown-Body der Section (ohne die Überschrift). Leer für den Hero. */
  body: string;
};

/** Feste erste Section: der Hero wird als Komponente gerendert, nicht als Markdown. */
export const HERO_SECTION: Section = { id: "hero", title: "Hero", body: "" };

/**
 * Zerlegt ein Markdown-Dokument automatisch an jeder `## `-Überschrift in
 * einzelne Sections. So entsteht das Inhaltsverzeichnis dynamisch aus dem
 * Inhalt — neue Überschriften erscheinen ohne Code-Änderung in der Navigation.
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
      // Überschrift wandert in `title` und wird semantisch im <header> der
      // Section gerendert (nicht im Markdown-Body) — siehe LandingClient.
      current = { id: slugify(title), title, body: "" };
    } else if (current) {
      current.body += (current.body ? "\n" : "") + line;
    }
  }
  if (current) sections.push(current);

  return sections.map((s) => ({ ...s, body: s.body.trim() }));
}

/** Alle Sections inklusive Hero — Quelle der Wahrheit für Nav & Scroll-Spy. */
export function buildSections(markdown: string): Section[] {
  return [HERO_SECTION, ...parseSections(markdown)];
}
