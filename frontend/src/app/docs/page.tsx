import type { Metadata } from "next"
import { DocsPage } from "@/components/docs/DocsPage"

export const metadata: Metadata = {
  title: "Documentation",
  description:
    "How to run, understand, and extend Nyayrithm: quick start, architecture, the multi-agent system, the role-scoped RAG pipeline, LLM providers, WebSocket events, authentication, and configuration.",
  alternates: { canonical: "/docs" },
  openGraph: {
    title: "Nyayrithm Documentation",
    description:
      "Run the full stack locally in five minutes. Architecture, the agent system, role-scoped retrieval, providers, and configuration.",
    url: "https://nyayrithm.aayushjoshi.dev/docs",
  },
}

const SITE_URL = "https://nyayrithm.aayushjoshi.dev"

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "@id": `${SITE_URL}/docs#article`,
  headline: "Nyayrithm Documentation",
  description:
    "Developer documentation for Nyayrithm: a self-hostable, provider-agnostic multi-agent courtroom simulation platform.",
  about: [
    "multi-agent legal reasoning",
    "role-scoped retrieval-augmented generation",
    "AI courtroom simulation",
    "self-hosted legal AI",
  ],
  author: { "@type": "Person", name: "Aayush Joshi" },
  publisher: { "@type": "Organization", name: "Nyayrithm", url: SITE_URL },
  isPartOf: { "@type": "WebSite", name: "Nyayrithm", url: SITE_URL },
}

export default function Page() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <DocsPage />
    </>
  )
}
