import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-[background-color,color,border-color,transform] duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-45 active:translate-y-px",
  {
    variants: {
      variant: {
        default:
          "bg-brass text-primary-foreground font-semibold hover:bg-brass-lit",
        /* alias kept for existing call sites */
        amber:
          "bg-brass text-primary-foreground font-semibold hover:bg-brass-lit",
        destructive:
          "bg-transparent text-oxblood-bright border border-oxblood-bright/35 hover:bg-oxblood-bright/12",
        outline:
          "border border-border bg-transparent text-foreground/80 hover:border-brass/40 hover:text-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-accent",
        ghost: "text-foreground/60 hover:text-foreground hover:bg-accent/60",
        link: "text-brass-text underline-offset-4 hover:underline p-0 h-auto",
        record:
          "font-mono text-xs tracking-wide text-foreground/55 border border-border bg-transparent hover:text-foreground hover:border-brass/40",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-sm px-3 text-xs",
        lg: "h-11 px-7 text-[0.9rem]",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
