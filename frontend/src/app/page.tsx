import type { Metadata } from "next"
import { LandingPage } from "@/components/landing/LandingPage"
import { FAQ_ITEMS } from "@/components/landing/faq-data"

export const metadata: Metadata = {
  title: "AI trial simulation for case preparation",
  description:
    "Nyayrithm runs a graph of AI agents that argue a case from the evidence you give it. Each agent plays a legal role with scoped knowledge, and every claim is seamed to the passage it came from. Self-hostable, provider-agnostic, and runnable fully offline.",
  alternates: { canonical: "/" },
}

const SITE_URL = "https://nyayrithm.aayushjoshi.dev"

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#org`,
      name: "Nyayrithm",
      url: SITE_URL,
      description:
        "Nyayrithm builds a multi-agent, evidence-grounded courtroom simulation platform for legal case preparation and research.",
      founder: { "@type": "Person", name: "Aayush Joshi" },
    },
    {
      "@type": "SoftwareApplication",
      "@id": `${SITE_URL}/#app`,
      name: "Nyayrithm",
      applicationCategory: "BusinessApplication",
      applicationSubCategory: "Legal case-preparation software",
      operatingSystem: "Web, self-hosted (Docker), Linux",
      offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
      featureList: [
        "Multi-agent courtroom, deposition, and strategy-session simulation",
        "Role-scoped retrieval over ingested evidence (PDF, audio, video, image)",
        "Inline evidence citations resolvable to the exact source passage",
        "Dynamic spawning of specialist expert-witness agents mid-proceeding",
        "Per-agent choice of LLM provider and model",
        "Self-hostable and provider-agnostic; runs fully offline",
      ],
      publisher: { "@id": `${SITE_URL}/#org` },
    },
    {
      "@type": "FAQPage",
      "@id": `${SITE_URL}/#faq`,
      mainEntity: FAQ_ITEMS.map((f) => ({
        "@type": "Question",
        name: f.q,
        acceptedAnswer: { "@type": "Answer", text: f.a },
      })),
    },
  ],
}

export default function Page() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <LandingPage />
    </>
  )
}
