import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono-jb",
  display: "swap",
});

const SITE_URL = "https://raido.fm";
const TITLE = "RAIDO FM — A Concept for Autonomous AI Radio";
const DESCRIPTION =
  "An open-source concept for autonomous AI radio. An LLM moderates, curates, and broadcasts 24/7 — multiple stations, each with its own personality, for ~€5/month.";
const OG_IMAGE = {
  url: "/og.png",
  width: 1200,
  height: 630,
  alt: "WE ARE NOT YOUR BOTS — RAIDO FM, spray-painted on a studio wall",
};

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: TITLE,
    template: "%s · RAIDO FM",
  },
  description: DESCRIPTION,
  applicationName: "Raido FM",
  category: "technology",
  alternates: {
    canonical: "/",
  },
  keywords: [
    "RAIDO FM",
    "AI Radio",
    "Autonomous Radio",
    "AI DJ",
    "LLM radio",
    "AI radio station",
    "Open Source",
    "Icecast",
    "Piper TTS",
    "Groq",
    "synthetic media",
  ],
  authors: [{ name: "René Reimann", url: "https://github.com/derpixler" }],
  creator: "René Reimann",
  publisher: "René Reimann",
  formatDetection: { email: false, address: false, telephone: false },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: SITE_URL,
    siteName: "RAIDO FM",
    title: TITLE,
    description: DESCRIPTION,
    images: [OG_IMAGE],
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    images: [OG_IMAGE.url],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
};

export const viewport: Viewport = {
  themeColor: "#050505",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-atmosphere bg-grid min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
