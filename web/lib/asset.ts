/**
 * BasePath for static deployments in a subdirectory (e.g. GitHub Pages under
 * `/raido-fm`). Controlled via environment variable so local development
 * (`npm run dev`/`npm run build` without the variable) still runs against
 * the site root.
 */
export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

/**
 * Prepends BasePath to an absolute asset path (`/image.webp`). Next.js only
 * automatically prefixes `_next`, `next/image` and `next/link` paths — custom
 * `<img src="/…">`, audio sources and Markdown images must be mapped manually.
 */
export function asset(path: string): string {
  if (!path.startsWith("/")) return path;
  return `${BASE_PATH}${path}`;
}
