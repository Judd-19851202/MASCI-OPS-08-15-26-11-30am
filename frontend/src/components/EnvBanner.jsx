// iter436 (2026-05-26) — Environment / DB banner
//
// After the 2026-05-26 preview→production data crossover, operators need
// an unmissable visual cue when they're looking at the preview site so
// no one accidentally enters real operational data there. This banner
// renders ONLY when /api/version reports app_env != "production".
// On production it is invisible.
import React, { useEffect, useState } from "react";
import { fetchVersionCached } from "@/lib/versionCache";

// TRACK 14.0-RC1-FERRARI · Use cached /api/version helper so portal
// navigation doesn't re-fetch on every mount.
export default function EnvBanner() {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    let alive = true;
    fetchVersionCached()
      .then((v) => alive && setInfo(v))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  if (!info) return null;
  const env = (info.app_env || "production").toLowerCase();
  if (env === "production") return null;

  const palette =
    env === "preview"
      ? "bg-amber-500 text-slate-900 border-amber-700"
      : "bg-rose-600 text-white border-rose-800";

  return (
    <div
      data-testid="env-banner"
      className={`sticky top-0 z-[90] px-3 py-1.5 text-center text-[11px] sm:text-xs font-mono uppercase tracking-widest border-b ${palette}`}
      role="status"
      aria-live="polite"
    >
      {env === "preview" ? "⚠ NON-PRODUCTION ENVIRONMENT" : `⚠ ${env.toUpperCase()} ENVIRONMENT`}
      <span className="ml-2 opacity-70">· db: {info.db_name || "?"}</span>
      <span className="ml-2 opacity-70 hidden sm:inline">
        · do not enter real operational data
      </span>
    </div>
  );
}
