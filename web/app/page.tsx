import { LandingClient } from "@/components/LandingClient";
import { loadReadmeMarkdown } from "@/lib/readme";
import { parseSections } from "@/lib/sections";

const GITHUB_URL = "https://github.com/derpixler/raido-fm";
const SITE_URL = "https://raido.fm";
const OG_IMAGE = `${SITE_URL}/og.png`;
const DESCRIPTION =
  "An open-source manifest for autonomous AI radio. An LLM moderates, curates, and broadcasts 24/7 — multiple stations, each with its own personality, for ~€5/month.";

export default function Page() {
  const markdown = loadReadmeMarkdown();
  const sections = parseSections(markdown);

  const author = {
    "@type": "Person",
    "@id": `${SITE_URL}/#author`,
    name: "René Reimann",
    url: "https://github.com/derpixler",
    jobTitle: "Software Developer & Systems Architect",
    description:
      "Software developer and systems architect with 20+ years of building web applications, exploring autonomous AI infrastructure and the boundaries of synthetic media.",
    address: {
      "@type": "PostalAddress",
      addressLocality: "Halle (Saale)",
      addressCountry: "DE",
    },
    worksFor: [
      {
        "@type": "Organization",
        name: "Immoware24 GmbH",
        url: "https://www.immoware24.de",
      },
      {
        "@type": "Organization",
        name: "web dev media UG",
      },
    ],
    knowsAbout: [
      "Autonomous AI",
      "Synthetic media",
      "Web development",
      "Software architecture",
      "Open source",
    ],
    sameAs: [
      "https://github.com/derpixler",
      "https://www.linkedin.com/in/rene-reimann-18b50a127/",
    ],
  };

  // Strukturierte Metadaten (JSON-LD) als @graph — verknüpft Website, Konzept-
  // Artikel (readme) und die Landingpage (web/ ist nicht die Radio-Implementierung).
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "@id": `${SITE_URL}/#website`,
        url: SITE_URL,
        name: "RAIDO FM",
        description: DESCRIPTION,
        inLanguage: "en",
        publisher: { "@id": `${SITE_URL}/#author` },
      },
      author,
      {
        "@type": "TechArticle",
        "@id": `${SITE_URL}/#article`,
        headline: "RAIDO — A Manifest for Autonomous AI Radio",
        name: "RAIDO FM",
        description: DESCRIPTION,
        inLanguage: "en",
        image: OG_IMAGE,
        author: { "@id": `${SITE_URL}/#author` },
        publisher: { "@id": `${SITE_URL}/#author` },
        isPartOf: { "@id": `${SITE_URL}/#website` },
        mainEntityOfPage: SITE_URL,
        license: "https://creativecommons.org/licenses/by/4.0/",
        articleSection: sections.map((s) => s.title),
      },
      {
        "@type": "WebApplication",
        "@id": `${SITE_URL}/#landing`,
        name: "RAIDO FM Landing Page",
        applicationCategory: "WebApplication",
        applicationSubCategory: "Landing Page",
        description:
          "Static landing page presenting the RAIDO FM manifest document.",
        url: SITE_URL,
        image: OG_IMAGE,
        author: { "@id": `${SITE_URL}/#author` },
        license: "https://opensource.org/license/mit",
        isPartOf: { "@id": `${SITE_URL}/#website` },
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        // JSON-LD muss als Roh-String eingebettet werden.
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <LandingClient markdown={markdown} />
    </>
  );
}
