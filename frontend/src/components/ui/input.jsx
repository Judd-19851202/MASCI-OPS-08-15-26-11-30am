import * as React from "react"

import { cn } from "@/lib/utils"

const Input = React.forwardRef(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        // TRACK 14.0-S2 · iPad Field Certification.
        // REMOVED `md:text-sm` so iOS Safari doesn't render the input
        // at 14px on iPad (which triggers a focus-zoom and shrinks
        // tap accuracy in the field). The `text-base` default is now
        // honored on tablet too; desktop reads the same. index.css
        // additionally forces 16px on coarse pointers for safety.
        "flex h-9 w-full min-w-0 rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      ref={ref}
      {...props} />
  );
})
Input.displayName = "Input"

export { Input }
