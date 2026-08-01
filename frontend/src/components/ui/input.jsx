import * as React from "react"

import { cn } from "@/lib/utils"

const Input = React.forwardRef(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "wp17-focus-ring wp17-control flex h-[3rem] w-full min-w-0 rounded-[1rem] border border-[color:var(--border-bold)] bg-white px-3.5 py-2 text-[0.95rem] text-[color:var(--ink-strong)] placeholder:text-[color:var(--ink-faint)] file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-[color:var(--ink-strong)] disabled:cursor-not-allowed disabled:border-[color:var(--border-hairline)] disabled:bg-[color:var(--surface-disabled)] disabled:text-[color:var(--ink-disabled)]",
        className
      )}
      ref={ref}
      {...props} />
  );
})
Input.displayName = "Input"

export { Input }
