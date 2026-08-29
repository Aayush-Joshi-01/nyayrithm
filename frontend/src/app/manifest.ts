import type { MetadataRoute } from "next"

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Nyayrithm",
    short_name: "Nyayrithm",
    description:
      "A graph of AI agents argues a case from your evidence, every claim seamed to its source.",
    start_url: "/",
    display: "standalone",
    background_color: "#0B0E14",
    theme_color: "#0B0E14",
    icons: [
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml" },
      { src: "/icon", sizes: "512x512", type: "image/png" },
    ],
  }
}
