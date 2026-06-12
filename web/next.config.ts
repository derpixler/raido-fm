import type { NextConfig } from "next";

// For deployments in a subdirectory (e.g. GitHub Pages under
// `/raido-fm`). Empty locally → the site runs against the site root.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Static export: `next build` produces ready-to-serve static HTML in `out/`.
  output: "export",
  // Required for static export (no server image optimization); the site only uses
  // simple <img> tags anyway.
  images: { unoptimized: true },
  // Automatically prefixes `_next` assets as well as next/link and next/image paths.
  ...(basePath ? { basePath, assetPrefix: basePath } : {}),
};

export default nextConfig;
