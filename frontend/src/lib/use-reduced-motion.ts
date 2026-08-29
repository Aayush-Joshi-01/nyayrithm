"use client"

import { useEffect, useState } from "react"

/* Small local replacement for framer-motion's useReducedMotion so the landing
   bundle carries no animation library. SSR-safe: assumes no preference until
   mounted, matching the CSS default. */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    setReduced(mq.matches)
    const on = () => setReduced(mq.matches)
    mq.addEventListener("change", on)
    return () => mq.removeEventListener("change", on)
  }, [])

  return reduced
}
