import type { MetadataRoute } from "next"

import { MARKETING_URL as SITE_URL } from "@/lib/site"

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: "*", allow: "/", disallow: ["/dashboard/", "/api/", "/login", "/signup"] },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  }
}
