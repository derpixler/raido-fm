/**
 * BasePath für statische Deployments in einem Unterverzeichnis (z. B. GitHub
 * Pages unter `/raido-fm`). Wird über die Umgebungsvariable gesteuert, sodass
 * lokale Entwicklung (`npm run dev`/`npm run build` ohne Variable) weiterhin
 * gegen den Site-Root läuft.
 */
export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

/**
 * Stellt einem absoluten Asset-Pfad (`/bild.webp`) den BasePath voran. Next.js
 * prefixt nur `_next`-, `next/image`- und `next/link`-Pfade automatisch — eigene
 * `<img src="/…">`, Audio-Quellen und Markdown-Bilder müssen wir selbst mappen.
 */
export function asset(path: string): string {
  if (!path.startsWith("/")) return path;
  return `${BASE_PATH}${path}`;
}
