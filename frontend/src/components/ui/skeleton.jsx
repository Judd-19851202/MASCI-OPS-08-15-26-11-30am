import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}) {
  return (
    <div
      className={cn("animate-pulse rounded-[var(--radius-control)] bg-[color:rgba(120,113,108,0.12)]", className)}
      {...props} />
  );
}

export { Skeleton }
