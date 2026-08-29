import { ImageResponse } from "next/og"

export const alt = "Nyayrithm: a graph of AI counsel argues your case from the evidence you give it"
export const size = { width: 1200, height: 630 }
export const contentType = "image/png"

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#0B0E14",
          padding: "72px",
          fontFamily: "Georgia, serif",
        }}
      >
        <div
          style={{
            fontSize: 22,
            letterSpacing: "0.24em",
            color: "#C88A4A",
            fontFamily: "monospace",
            textTransform: "uppercase",
          }}
        >
          Nyayrithm
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 84, color: "#ECE3D2", lineHeight: 1.05, fontWeight: 500 }}>
            The court,
          </div>
          <div style={{ fontSize: 84, color: "#ECE3D2", lineHeight: 1.05, fontStyle: "italic", fontWeight: 500 }}>
            after hours.
          </div>
          <div
            style={{
              marginTop: 28,
              fontSize: 30,
              color: "rgba(236,227,210,0.62)",
              fontFamily: "Helvetica, Arial, sans-serif",
              maxWidth: 900,
              lineHeight: 1.4,
            }}
          >
            A graph of AI counsel argues your case from the evidence you give it. Every claim seamed to its source.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            gap: 16,
            fontSize: 20,
            color: "rgba(236,227,210,0.4)",
            fontFamily: "monospace",
          }}
        >
          <span>Self-hostable</span>
          <span>·</span>
          <span>Provider-agnostic</span>
          <span>·</span>
          <span>Runs offline</span>
        </div>
      </div>
    ),
    { ...size },
  )
}
