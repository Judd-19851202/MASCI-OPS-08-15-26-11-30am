import * as React from "react"

import { cn } from "@/lib/utils"

const Textarea = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "wp16-focus-ring flex min-h-[132px] w-full rounded-[1rem] border border-[color:var(--border-bold)] bg-white px-3.5 py-3 text-[0.95rem] text-[color:var(--ink-strong)] shadow-[0_10px_24px_rgba(15,23,42,0.05)] transition-[background-color,border-color,color,box-shadow] duration-[140ms] placeholder:text-[color:var(--ink-faint)] hover:border-[color:var(--border-strong)] focus:border-[color:var(--brand-primary)] disabled:cursor-not-allowed disabled:border-[color:var(--border-hairline)] disabled:bg-[color:var(--surface-disabled)] disabled:text-[color:var(--ink-disabled)]",
        className
      )}
      ref={ref}
      {...props} />
  );
})
Textarea.displayName = "Textarea"

export { Textarea }
