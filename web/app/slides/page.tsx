import type { Metadata } from "next";

import { SlideDeck } from "@/components/SlideDeck";

export const metadata: Metadata = {
  title: "Slides",
  description:
    "RAIDO FM — A Manifest for Autonomous AI Radio, as a slide deck.",
  // Die Folien sind ein Begleitformat — die Landingpage bleibt die kanonische Seite.
  robots: { index: false, follow: true },
};

export default function SlidesPage() {
  return <SlideDeck />;
}
