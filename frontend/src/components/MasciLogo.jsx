import React from "react";
import { cn } from "@/lib/utils";

export const MasciLogo = ({ className = "", size = "md" }) => {
  const sizes = {
    sm: "text-lg",
    md: "text-2xl",
    lg: "text-4xl",
    xl: "text-5xl",
  };
  return (
    <div
      className={cn("flex items-center gap-2 select-none", className)}
      data-testid="masci-logo"
    >
      <span
        className={cn(
          "font-display font-black tracking-tighter text-slate-900",
          sizes[size]
        )}
      >
        MASCI
      </span>
      <span
        className="bg-yellow-400 inline-block"
        style={{
          width: size === "xl" ? 14 : size === "lg" ? 12 : 10,
          height: size === "xl" ? 14 : size === "lg" ? 12 : 10,
        }}
      />
      <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 hidden sm:inline">
        Safety
      </span>
    </div>
  );
};
