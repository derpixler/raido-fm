import type { NextConfig } from "next";

// Für Deployments in einem Unterverzeichnis (z. B. GitHub Pages unter
// `/raido-fm`). Lokal leer → die Seite läuft gegen den Site-Root.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Statischer Export: `next build` erzeugt fertiges, statisches HTML in `out/`.
  output: "export",
  // Für den Static Export nötig (keine Server-Bildoptimierung); die Seite nutzt
  // ohnehin nur einfache <img>-Tags.
  images: { unoptimized: true },
  // Prefixt automatisch `_next`-Assets sowie next/link- und next/image-Pfade.
  ...(basePath ? { basePath, assetPrefix: basePath } : {}),
};

export default nextConfig;
