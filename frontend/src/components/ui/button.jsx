import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "wp17-cta wp16-focus-ring inline-flex items-center justify-center gap-2 whitespace-nowrap border text-sm font-semibold tracking-[0.01em] disabled:pointer-events-none disabled:opacity-[var(--disabled-opacity)] [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "wp17-cta--primary",
        destructive:
          "wp17-cta--danger",
        outline:
          "wp17-cta--outline",
        secondary:
          "wp17-cta--secondary",
        ghost: "wp17-cta--ghost",
        link: "wp17-cta--link",
      },
      size: {
        default: "wp17-cta--md",
        sm: "wp17-cta--sm",
        lg: "wp17-cta--lg",
        icon: "wp17-cta--icon",
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
