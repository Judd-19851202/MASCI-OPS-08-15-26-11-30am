import React from "react";
import { CircleHelp } from "lucide-react";
import { cn } from "@/lib/utils";
import { SEMANTIC_ICON_REGISTRY } from "@/components/icons/semanticRegistry";

const SIZE_MAP = {
  xs: "h-3.5 w-3.5",
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
  xl: "h-7 w-7",
};

const TONE_MAP = {
  default: "text-current",
  muted: "text-slate-500",
  inverse: "text-white",
  success: "text-emerald-700",
  warning: "text-amber-700",
  danger: "text-red-700",
  info: "text-cyan-700",
};

export function AppIcon({
  icon: Icon,
  name,
  size = "sm",
  tone = "default",
  className,
  decorative = true,
  strokeWidth = 1.9,
  ...props
}) {
  const ResolvedIcon = Icon || (name ? SEMANTIC_ICON_REGISTRY[name] : null) || CircleHelp;

  return (
    <ResolvedIcon
      aria-hidden={decorative ? "true" : undefined}
      focusable="false"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("wp17-icon shrink-0", SIZE_MAP[size] || SIZE_MAP.sm, TONE_MAP[tone] || TONE_MAP.default, className)}
      {...props}
    />
  );
}

export function SemanticIcon(props) {
  return <AppIcon {...props} />;
}

export default AppIcon;