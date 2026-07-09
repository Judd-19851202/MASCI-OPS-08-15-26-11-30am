import React from "react";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

/** Colored circle with initials. Stable color from the user id hash. */
export function UserAvatar({ name, userId, size = "md", className = "" }) {
  const sizes = {
    xs: "w-5 h-5 text-[9px]",
    sm: "w-7 h-7 text-[10px]",
    md: "w-9 h-9 text-sm",
    lg: "w-12 h-12 text-base",
  };
  const sz = sizes[size] || sizes.md;
  const initials = (name || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w.charAt(0).toUpperCase())
    .join("");
  // Deterministic color from userId
  const palette = [
    "bg-red-700", "bg-amber-600", "bg-emerald-600", "bg-blue-600",
    "bg-purple-600", "bg-pink-600", "bg-slate-700", "bg-orange-600",
  ];
  const hash = (userId || "")
    .split("")
    .reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const bg = palette[hash % palette.length];
  return (
    <div
      className={`${sz} ${bg} rounded-full flex items-center justify-center font-display font-black text-white shrink-0 ${className}`}
      title={name}
    >
      {initials}
    </div>
  );
}

/** "3m", "2h", "yesterday", "Apr 4". */
export function relativeTime(iso) {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  const now = Date.now();
  const s = Math.floor((now - then) / 1000);
  if (s < 45) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  if (s < 86400) return `${Math.floor(s / 3600)}h`;
  if (s < 86400 * 2) return "yesterday";
  if (s < 86400 * 7) return `${Math.floor(s / 86400)}d`;
  return formatPlatformDate(iso);
}

/** Robust FastAPI error → string. */
export function apiErr(detail, fallback = "Something went wrong.") {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((e) => e?.msg || JSON.stringify(e)).join(" ");
  return detail?.msg || String(detail);
}
