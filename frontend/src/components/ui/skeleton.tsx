import { cn } from "@/lib/utils"

/* A light moving across the bench, not a generic pulse. */
function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("skeleton-shimmer rounded-sm bg-bone/[0.05]", className)}
      {...props}
    />
  )
}

export { Skeleton }
