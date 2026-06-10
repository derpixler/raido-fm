import { readFileSync } from "node:fs";
import { join } from "node:path";

import { BASE_PATH } from "@/lib/asset";

/**
 * Lädt die echte Projekt-readme.md (Quelle der Wahrheit) und bereitet sie für
 * die Landingpage auf — der Inhalt wird 1:1 übernommen.
 *
 * - Der H1-Titel + Autoren-Intro vor der ersten `## `-Überschrift wird entfernt,
 *   da der Hero diesen Part visuell übernimmt.
 * - Bild-/Asset-Pfade (`assets/…`) werden auf `/…` umgeschrieben, weil die
 *   Bilder nach `web/public/` kopiert wurden.
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
      /* nächsten Pfad versuchen */
    }
  }

  // Ab der ersten `## `-Überschrift (alles davor deckt der Hero ab).
  const firstHeading = raw.search(/^##\s+/m);
  let body = firstHeading >= 0 ? raw.slice(firstHeading) : raw;

  // "Audio Summary"-Sektion entfernen — sie steckt jetzt im Hero-Player.
  body = body.replace(/^##\s+Audio Summary[\s\S]*?(?=^##\s+)/m, "");

  // "Table of Contents"-Sektion entfernen — die Seiten-Navigation ersetzt sie.
  body = body.replace(/^##\s+Table of Contents[\s\S]*?(?=^##\s+)/m, "");

  // "About the Author"-Sektion entfernen — die gestaltete <AuthorCard /> ersetzt
  // sie auf der Website (in der readme.md bleibt sie für GitHub-Leser erhalten).
  body = body.replace(/\n*##\s+About the Author[\s\S]*$/m, "");

  // Graffiti-Bild aus der Vision entfernen — es ist jetzt der Hero-Hintergrund.
  body = body.replace(/^!\[[^\]]*\]\(assets\/we-are-not-your-bots-RAIDO-FM\.png\)\s*$/m, "");

  // Relative Asset-Pfade auf das öffentliche Verzeichnis mappen und auf die
  // leichtgewichtigen WebP-Varianten der Inhaltsbilder umstellen (die readme.md
  // selbst referenziert weiterhin die PNGs in /assets für GitHub).
  body = body
    .replace(/\]\(assets\//g, "](/")
    .replace(/\]\(\/architecture-overview\.png\)/g, "](/architecture-overview.webp)")
    .replace(/\]\(\/data-flow\.png\)/g, "](/data-flow.webp)")
    .replace(/\]\(index\.html\)/g, "](https://github.com/derpixler/raido-fm)");

  // BasePath voranstellen, damit die Bilder auch in einem Unterverzeichnis
  // (z. B. GitHub Pages /raido-fm) geladen werden. Interne Anker (`](#…`) und
  // externe Links (`](http…`) bleiben unberührt, da sie nicht mit `/` beginnen.
  if (BASE_PATH) {
    body = body.replace(/\]\(\//g, `](${BASE_PATH}/`);
  }

  return body;
}
