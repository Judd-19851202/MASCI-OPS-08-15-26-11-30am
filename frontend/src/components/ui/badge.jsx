import * as React from "react"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.1em] transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-[color:rgba(185,28,28,0.14)] bg-[color:var(--brand-primary-soft)] text-[color:var(--brand-primary)]",
        secondary:
          "border-[color:var(--border-hairline)] bg-[color:var(--paper-card-muted)] text-[color:var(--ink-soft)]",
        destructive:
          "border-[color:rgba(185,28,28,0.14)] bg-[color:var(--paper-tinted-error)] text-[color:var(--status-bad)]",
        outline: "border-[color:var(--border-bold)] bg-white text-[color:var(--ink-strong)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant,
  ...props
}) {
  return (<div className={cn(badgeVariants({ variant }), className)} {...props} />);
}

export { Badge, badgeVariants }
