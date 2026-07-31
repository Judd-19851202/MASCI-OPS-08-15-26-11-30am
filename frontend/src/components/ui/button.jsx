import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "wp16-focus-ring inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full border text-sm font-semibold tracking-[0.01em] transition-[background-color,border-color,color,box-shadow,transform,opacity] duration-[140ms] ease-[cubic-bezier(0.22,0.7,0.2,1)] disabled:pointer-events-none disabled:opacity-[var(--disabled-opacity)] [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "border-[color:var(--brand-primary)] bg-[color:var(--brand-primary)] text-white shadow-[0_16px_36px_rgba(15,23,42,0.12)] hover:border-[color:var(--brand-primary-hover)] hover:bg-[color:var(--brand-primary-hover)]",
        destructive:
          "border-[color:var(--status-bad)] bg-[color:var(--status-bad)] text-white shadow-[0_16px_36px_rgba(15,23,42,0.12)] hover:opacity-95",
        outline:
          "border-[color:var(--border-bold)] bg-white text-[color:var(--ink-strong)] shadow-[0_10px_24px_rgba(15,23,42,0.06)] hover:bg-[color:var(--paper-card-muted)]",
        secondary:
          "border-[color:var(--border-hairline)] bg-[color:var(--paper-card-muted)] text-[color:var(--ink-strong)] shadow-[0_10px_24px_rgba(15,23,42,0.06)] hover:border-[color:var(--border-bold)] hover:bg-white",
        ghost: "border-transparent bg-transparent text-[color:var(--ink-strong)] hover:border-[color:var(--border-hairline)] hover:bg-white",
        link: "border-transparent bg-transparent px-0 text-[color:var(--brand-primary)] hover:text-[color:var(--brand-primary-hover)] hover:underline",
      },
      size: {
        default: "h-[3rem] px-4 py-2",
        sm: "h-[2.6rem] px-3 text-xs",
        lg: "h-[3.25rem] px-5 text-base",
        icon: "h-[var(--control-height-md)] w-[var(--control-height-md)]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props} />
  );
})
Button.displayName = "Button"

export { Button, buttonVariants }
