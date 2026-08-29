/* The scroll container for ordinary dashboard content pages. The full-bleed
   proceeding view opts out and manages its own height. */
export function PageScroll({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-full overflow-y-auto px-6 py-8">{children}</div>
  )
}
