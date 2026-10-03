import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

/* Docket tags: small, sharp, hairline-bordered. Not pills. */
const badgeVariants = cva(
  "inline-flex items-center rounded-sm border px-1.5 py-0.5 text-[0.68rem] font-medium uppercase tracking-wide transition-colors",
  {
    variants: {
      variant: {
        default: "border-brass/25 bg-brass/10 text-brass-text",
        secondary: "border-border bg-secondary text-secondary-foreground",
        destructive: "border-oxblood-bright/30 bg-oxblood-bright/12 text-oxblood-bright",
        outline: "border-border text-muted-foreground",
        success: "border-role-witness/30 bg-role-witness/12 text-role-witness",
        warning: "border-brass/30 bg-brass/12 text-brass-text",
        info: "border-role-defense/30 bg-role-defense/12 text-role-defense",
        live: "border-ember/40 bg-ember/12 text-ember",
        muted: "border-border bg-muted text-muted-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
