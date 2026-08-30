import type { Metadata } from "next"
import { Spectral, Libre_Franklin, JetBrains_Mono } from "next/font/google"
import "./globals.css"
import { QueryProvider } from "@/components/layout/QueryProvider"
import { themeInitScript } from "@/components/theme/theme-init"
import { MARKETING_URL } from "@/lib/site"

const spectral = Spectral({
  subsets: ["latin"],
  variable: "--font-spectral",
  weight: ["300", "400", "500", "600", "700"],
  style: ["normal", "italic"],
  display: "swap",
})

const franklin = Libre_Franklin({
  subsets: ["latin"],
  variable: "--font-franklin",
  weight: ["400", "500", "600", "700"],
  display: "swap",
})

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "600"],
  display: "swap",
})

const SITE_URL = MARKETING_URL

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Nyayrithm: AI trial simulation for case preparation",
    template: "%s | Nyayrithm",
  },
  description:
    "Nyayrithm runs a graph of AI agents that argue a case from the evidence you give it. Each agent plays a legal role with scoped knowledge, and every claim is seamed to the passage it came from. Self-hostable and provider-agnostic.",
  applicationName: "Nyayrithm",
  keywords: [
    "AI trial simulation",
    "courtroom simulation software",
    "multi-agent legal reasoning",
    "case preparation tool",
    "cross-examination practice",
    "moot court AI",
    "legal-tech",
    "self-hosted legal AI",
    "role-scoped RAG",
    "evidence citation",
  ],
  authors: [{ name: "Aayush Joshi" }],
  creator: "Aayush Joshi",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: "Nyayrithm",
    title: "Nyayrithm: AI trial simulation for case preparation",
    description:
      "A graph of AI counsel argues your case from the evidence you give it. Every claim seamed to its source. Self-hostable, provider-agnostic.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Nyayrithm: AI trial simulation for case preparation",
    description:
      "A graph of AI counsel argues your case from the evidence you give it. Every claim seamed to its source.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 },
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body
        className={`${spectral.variable} ${franklin.variable} ${mono.variable} font-sans antialiased`}
      >
        {/*
          DIRECTION CONTRACT: "The Night Court" / "The Court in Session"  (seed 6c3fad03)
          THESIS: A courtroom rendered as its own interface. Two times of day, one
            world. Refuses the marble-columns legal pastiche and the sterile
            SaaS-screenshot hero. The proceeding is the only thing that matters,
            so the proceeding is the hero.
          OWN-WORLD: Dark ("after hours") is near-black ink (#0B0E14) lit by one
            warm brass pool; light ("in session") is cool institutional paper
            (#F2F3F5), no cream. Brass #C88A4A and ember #FF7A3D are identical in
            both themes; ember is reserved for what is LIVE and nothing else.
            Spectral serif is the record's voice; Libre Franklin is the room;
            JetBrains Mono is line numbers, timestamps, citations. 1px hairlines,
            tonal depth, shadows only on floating surfaces, glass only at the nav.
          STORY: The visitor reads a real proceeding argued from real evidence,
            every claim seamed to its source; understands the simulation is
            credible, not a chatbot; convenes a proceeding.
          FIRST VIEWPORT: Title in Spectral with a theme-reactive sub-line, one
            line of literal value-prop copy, one ember action plus a quiet "Read
            the docs". Beside it, a live transcript panel: newest line struck
            forward with a solid ember edge, a custody line in the margin marking
            cited / inferred / disputed.
          FORM: The court reporter's realtime record fused with the night
            courtroom; user-pinned direction; seed key 6c3fad03.
          FINISH: unreviewed and undocumented is unfinished.
        */}
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
