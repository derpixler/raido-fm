import { readFileSync } from "node:fs";
import { join } from "node:path";

import { BASE_PATH } from "@/lib/asset";

/**
 * Loads the real project readme.md (source of truth) and prepares it for the
 * landing page — content is adopted 1:1.
 *
 * - The H1 title + author intro before the first `## ` heading is removed,
 *   since the Hero handles that part visually.
 * - Image/asset paths (`assets/…`) are rewritten to `/…`, because the
 *   images were copied to `web/public/`.
 */
export function loadReadmeMarkdown(): string {
  const candidates = [
    join(process.cwd(), "..", "readme.md"),
    join(process.cwd(), "readme.md"),
  ];

  let raw = "";
  for (const path of candidates) {
    try {
      raw = readFileSync(path, "utf8");
      break;
    } catch {
      /* try next path */
    }
  }

  // From the first `## ` heading onwards (everything before is covered by the Hero).
  const firstHeading = raw.search(/^##\s+/m);
  let body = firstHeading >= 0 ? raw.slice(firstHeading) : raw;

  // Remove "Audio Summary" section — it now lives in the Hero player.
  body = body.replace(/^##\s+Audio Summary[\s\S]*?(?=^##\s+)/m, "");

  // Remove "Table of Contents" section — the page navigation replaces it.
  body = body.replace(/^##\s+Table of Contents[\s\S]*?(?=^##\s+)/m, "");

  // Remove "About the Author" section — the styled <AuthorCard /> replaces it
  // on the website (it stays in readme.md for GitHub readers).
  body = body.replace(/\n*##\s+About the Author[\s\S]*$/m, "");

  // Remove graffiti image from the Vision section — it's now the Hero background.
  body = body.replace(/^!\[[^\]]*\]\(assets\/we-are-not-your-bots-RAIDO-FM\.png\)\s*$/m, "");

  // Map relative asset paths to the public directory and switch to the
  // lightweight WebP variants of content images (the readme.md itself
  // still references the PNGs in /assets for GitHub).
  body = body
    .replace(/\]\(assets\//g, "](/")
    .replace(/\]\(\/architecture-overview\.png\)/g, "](/architecture-overview.webp)")
    .replace(/\]\(\/data-flow\.png\)/g, "](/data-flow.webp)")
    .replace(/\]\(index\.html\)/g, "](https://github.com/derpixler/raido-fm)");

  // Prepend BasePath so images also load in a subdirectory (e.g. GitHub Pages
  // /raido-fm). Internal anchors (`](#…`) and external links (`](http…`) are
  // left untouched since they don't start with `/`.
  if (BASE_PATH) {
    body = body.replace(/\]\(\//g, `](${BASE_PATH}/`);
  }

  return body;
}
