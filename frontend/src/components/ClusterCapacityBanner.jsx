// iter437 (2026-05-26) — Cluster capacity banner.
//
// Surfaces Atlas storage utilization directly on every page so an
// over-quota condition cannot silently block writes again. Renders
// ONLY when severity >= "warning" — invisible during normal operation.
//
// Background: today's restore drill exposed the production cluster at
// 99-105% of the 512 MB free-tier quota. While in that state, ANY write
// (daily report, incident, photo upload) returns
//   OperationFailure: "Writes are blocked on your cluster."
// Field crews would see a save failure with no indication of why.
import { useEffect, useState } from "react";

const API = process.env.REACT_APP_BACKEND_URL;
const POLL_MS = 60_000; // backend caches for 60s; align refresh.

export default function ClusterCapacityBanner() {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    let alive = true;
    let timer = null;

    const tick = () => {
      fetch(`${API}/api/cluster/capacity`, { cache: "no-store" })
        .then((r) => (r.ok ? r.json() : null))
        .then((v) => alive && setInfo(v))
        .catch(() => {});
    };

    tick();
    timer = setInterval(tick, POLL_MS);
    return () => {
      alive = false;
      if (timer) clearInterval(timer);
    };
  }, []);

  if (!info || !info.ok) return null;
  const sev = (info.severity || "ok").toLowerCase();
  if (sev !== "warning" && sev !== "critical") return null;

  const palette =
    sev === "critical"
      ? "bg-rose-600 text-white border-rose-800"
      : "bg-amber-500 text-slate-900 border-amber-700";

  const headline =
    sev === "critical"
      ? "⛔ DATABASE WRITES MAY FAIL — cluster at capacity"
      : "⚠ Database approaching capacity — plan upgrade";

  return (
    <div
      data-testid="cluster-capacity-banner"
      className={`sticky top-0 z-[95] px-3 py-1.5 text-center text-[11px] sm:text-xs font-mono uppercase tracking-widest border-b ${palette}`}
      role="status"
      aria-live="polite"
    >
      <span>{headline}</span>
      <span className="ml-2 opacity-80">
        · {info.storage_used_mb} MB / {info.tier_quota_mb} MB
        {" "}
        ({info.storage_used_pct}%)
      </span>
      {sev === "critical" && (
        <span className="ml-2 opacity-80 hidden md:inline">
          · contact admin · upgrade Atlas tier
        </span>
      )}
    </div>
  );
}
