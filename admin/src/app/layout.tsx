import type { Metadata } from "next"
import { Spectral, Libre_Franklin, JetBrains_Mono } from "next/font/google"
import "./globals.css"
import { QueryProvider } from "@/components/layout/QueryProvider"
import { themeInitScript } from "@/components/theme/theme-init"

const spectral = Spectral({
  subsets: ["latin"], variable: "--font-spectral",
  weight: ["300", "400", "500", "600", "700"], style: ["normal", "italic"], display: "swap",
})
const franklin = Libre_Franklin({
  subsets: ["latin"], variable: "--font-franklin", weight: ["400", "500", "600", "700"], display: "swap",
})
const mono = JetBrains_Mono({
  subsets: ["latin"], variable: "--font-mono", weight: ["400", "500", "600"], display: "swap",
})

export const metadata: Metadata = {
  title: { default: "Nyayrithm Admin", template: "%s | Nyayrithm Admin" },
  description: "Platform operations: firms, plans, subscriptions, users and LLM consumption.",
  robots: { index: false, follow: false },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className={`${spectral.variable} ${franklin.variable} ${mono.variable} font-sans antialiased`}>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
