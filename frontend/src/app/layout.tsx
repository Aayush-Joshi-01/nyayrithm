import type { Metadata } from "next"
import { Inter, Playfair_Display, Cinzel } from "next/font/google"
import "./globals.css"
import { QueryProvider } from "@/components/layout/QueryProvider"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
})

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  weight: ["400", "500", "600", "700", "800", "900"],
  style: ["normal", "italic"],
})

const cinzel = Cinzel({
  subsets: ["latin"],
  variable: "--font-cinzel",
  weight: ["400", "600", "700", "800", "900"],
})

export const metadata: Metadata = {
  title: "Nyayrithm — Legal Reasoning Platform",
  description: "AI-powered multi-modal legal reasoning and courtroom simulation",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${playfair.variable} ${cinzel.variable} ${inter.className}`}>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
