// PortalHydratingLoader — iter88
//
// Shown briefly (typically < 500ms) when a portal guard is silently
// re-issuing a missing per-portal token via the directory session.
// Replaces the previous "bounce straight to /login" behavior so a
// multi-portal user who lost a token (stale bundle, cache hiccup, etc.)
// is held for a beat while the rescue happens instead of being kicked
// out and forced to re-enter credentials.
import React from "react";
import { Loader2 } from "lucide-react";

const ACCENT = {
  admin: "border-red-700 text-red-700",
  pm: "border-red-600 text-red-600",
  hr: "border-purple-700 text-purple-700",
  shop: "border-orange-600 text-orange-600",
};

const LABEL = {
  admin: "Admin Console",
  pm: "PM Portal",
  hr: "HR Portal",
  shop: "Shop Portal",
};

export default function PortalHydratingLoader({ portal = "admin" }) {
  const accent = ACCENT[portal] || ACCENT.admin;
  const label = LABEL[portal] || "portal";
  return (
    <div
      className="min-h-[60vh] flex flex-col items-center justify-center px-6"
      data-testid={`portal-hydrating-${portal}`}
    >
      <div className={`w-14 h-14 rounded-full border-4 ${accent} flex items-center justify-center mb-4`}>
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
      <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 font-bold">
        Restoring session
      </div>
      <div className="font-display text-xl font-black text-slate-900 mt-1">
        Reconnecting to {label}…
      </div>
      <div className="text-xs text-slate-500 mt-1">
        One moment — using your master sign-in.
      </div>
    </div>
  );
}
