import React, { useEffect, useRef, useState } from "react";
import { CheckCircle2, AlertTriangle, AlertCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
// TRACK 27.03 · Final Completion · canonical local-time formatter.
import { formatPlatformTimeOnly } from "@/lib/platformTime";

/**
 * SystemHealthBadge — tiny live-status badge for /admin.
 *
 * Pings every critical endpoint every 60 seconds. Aggregates status:
 *   🟢 ALL OK         — every endpoint < 1 second + 200/2xx
 *   🟡 SLOW or 4xx    — anything 4xx (other than expected 401), or > 2 second p95
 *   🔴 ERROR          — any 5xx OR network failure (this is the Cloudflare-520 alarm)
 *
 * Click to expand a per-endpoint dropdown showing each result + last latency.
 *
 * Lives in the top-right of AdminHub. Polls in the background; never blocks
 * any user action; never raises (errors are caught + counted as "down").
 */

const ENDPOINTS = [
  { path: "/health",            label: "Health",           critical: true  },
  { path: "/employees",         label: "Employees",        critical: true  },
  { path: "/suppliers",         label: "Suppliers",        critical: true  },
  { path: "/equipment-master",  label: "Equipment",        critical: true  },
  { path: "/equipment-types",   label: "Equipment Types",  critical: true  },
  { path: "/inspections",       label: "Inspections",      critical: true  },
  { path: "/meetings",          label: "Meetings",         critical: false },
  { path: "/jhas",              label: "JHPs",             critical: false },
  { path: "/incidents",         label: "Incidents",        critical: false },
  { path: "/daily-reports",     label: "Daily Reports",    critical: false },
];

const POLL_INTERVAL_MS = 60_000;
const SLOW_THRESHOLD_MS = 2000;
// TRACK 14.0-PLATFORM-STABILITY · Health board TRANSIENT fix.
// Number of consecutive failures required before flipping a service
// to the red "DOWN" state. Single transient blips (ingress jitter,
// brief worker saturation, an in-flight load racing with the poll)
// no longer poison the badge. 3 consecutive 60s polls = 2.5–3 min of
// confirmed failure before alarming.
const FAIL_STREAK_THRESHOLD = 3;

// TRACK 14.0-RC1-FERRARI (2026-02-15) · Cross-mount cache.
//
// The badge lives inside AdminShell + PmShell. When a super-admin
// hops portals (Admin → PM → HR → Safety → ...) the shell re-mounts
// on every navigation, and the previous implementation re-fired all
// 10 probes immediately on each remount. Across a fast 7-portal
// click-through that's ~70 redundant pings in <30s — exactly the
// "probe storm" iter508 flagged.
//
// We now keep the most recent probe results in a module-level
// cache. On remount, if the cache is fresh (< POLL_INTERVAL_MS), we
// reuse it and skip the synchronous probe. The 60s interval timer
// still fires on the new mount so the badge stays current — we
// just skip the redundant first-load probe within the cache TTL.
const _resultsCache = {
  results: null,
  lastChecked: null,
  failStreak: {},
};
function _cacheFresh() {
  if (!_resultsCache.lastChecked) return false;
  return Date.now() - _resultsCache.lastChecked.getTime() < POLL_INTERVAL_MS;
}

async function pingOne(ep) {
  const t0 = performance.now();
  try {
    // Longer timeout on the universal /health probe — under heavy gallery
    // load the FastAPI worker can be busy rendering thumbs for 5-10s.
    // Other endpoints get a tighter budget so genuine outages still
    // surface within the poll window.
    const timeout = ep.path === "/health" ? 15000 : 10000;
    // TRACK 14.0-PLATFORM-STABILITY · skipSessionStatus suppresses the
    // global "Session Expired" / "Connection Problem" modals on these
    // background polls. The badge is the modal — we don't want a
    // probe failure to ALSO raise a platform-wide overlay.
    const r = await api.get(ep.path, { timeout, skipSessionStatus: true });
    const ms = Math.round(performance.now() - t0);
    return {
      ...ep,
      ok: true,
      status: r.status || 200,
      ms,
      level: ms > SLOW_THRESHOLD_MS ? "warn" : "ok",
      msg: `${r.status || 200} · ${ms}ms`,
    };
  } catch (err) {
    const ms = Math.round(performance.now() - t0);
    const status = err?.response?.status;
    // 401/403 on a health probe means "you don't have permission" —
    // not "service is down". Show as a neutral auth gate, not a red
    // outage. Examples: a PM viewing /admin would see admin-only
    // probes 401 even though the platform itself is fine.
    if (status === 401 || status === 403) {
      return {
        ...ep,
        ok: false,
        status,
        ms,
        level: "ok",
        msg: `${status} · auth`,
        _authGated: true,
      };
    }
    const level =
      status && status >= 500
        ? "error"
        : status === 0 || !status
        ? "error" // network failure / Cloudflare 520
        : "warn"; // 4xx unexpected
    return {
      ...ep,
      ok: false,
      status: status || 0,
      ms,
      level,
      msg: status ? `${status} · ${ms}ms` : `network · ${ms}ms`,
    };
  }
}

export default function SystemHealthBadge() {
  // TRACK 14.0-RC1-FERRARI · Hydrate from the cross-mount cache when
  // a fresh probe set exists. Eliminates the probe storm on portal
  // navigation (iter508 P3 follow-up).
  const [results, setResults] = useState(() => _resultsCache.results || []);
  const [loading, setLoading] = useState(() => !_cacheFresh());
  const [open, setOpen] = useState(false);
  const [lastChecked, setLastChecked] = useState(() => _resultsCache.lastChecked);
  const [alertSent, setAlertSent] = useState(null); // {ts, key} of last successful alert
  const timerRef = useRef(null);
  const prevWorstRef = useRef("ok");
  // Per-endpoint consecutive-fail streak. Shared across mounts via
  // the cache so streak isn't reset on portal navigation.
  const failStreakRef = useRef(_resultsCache.failStreak);

  const runAll = async () => {
    setLoading(true);
    const out = await Promise.all(ENDPOINTS.map(pingOne));
    // Apply streak debouncing: require FAIL_STREAK_THRESHOLD (3)
    // consecutive failures before painting the endpoint red. Earlier
    // failures show as a calm amber "transient" but never flip the
    // overall badge to "DOWN". A single successful poll resets the
    // streak immediately. This eliminates the false "TRANSIENT" /
    // "DOWN" flashes that production users were reporting from
    // single-poll ingress hiccups.
    for (const r of out) {
      if (r.level === "error") {
        failStreakRef.current[r.path] = (failStreakRef.current[r.path] || 0) + 1;
        if (failStreakRef.current[r.path] < FAIL_STREAK_THRESHOLD) {
          r.level = "warn";
          r.msg = `${r.msg} · transient (${failStreakRef.current[r.path]}/${FAIL_STREAK_THRESHOLD})`;
        }
      } else {
        failStreakRef.current[r.path] = 0;
      }
    }
    setResults(out);
    const now = new Date();
    setLastChecked(now);
    setLoading(false);
    // TRACK 14.0-RC1-FERRARI · publish to the cross-mount cache so
    // the next remount (portal switch) reuses these results within
    // the POLL_INTERVAL_MS window.
    _resultsCache.results = out;
    _resultsCache.lastChecked = now;
    _resultsCache.failStreak = failStreakRef.current;
  };

  useEffect(() => {
    // TRACK 14.0-RC1-FERRARI · On mount, ONLY run a fresh probe if
    // the cache is stale. A fresh cache (set < POLL_INTERVAL_MS ago)
    // means another mount of this same component just probed; we
    // reuse those results and skip a redundant 10-endpoint burst.
    if (!_cacheFresh()) {
      runAll();
    }
    // TRACK 14.0-RC1-PERF: Pause health polling when the tab is hidden.
    // The visibilitychange handler re-runs immediately on focus so
    // the badge is current the moment the user comes back.
    const tick = () => {
      if (document.visibilityState === "visible") runAll();
    };
    timerRef.current = setInterval(tick, POLL_INTERVAL_MS);
    const onVis = () => {
      if (document.visibilityState === "visible") runAll();
    };
    document.addEventListener("visibilitychange", onVis);
    return () => {
      clearInterval(timerRef.current);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, []);

  // Aggregate worst level across critical endpoints.
  const worst = results.length
    ? results.reduce((acc, r) => {
        if (r.level === "error" && r.critical) return "error";
        if (acc === "error") return acc;
        if (r.level === "warn") return "warn";
        return acc;
      }, "ok")
    : "loading";

  // Fire an outage email the moment we transition into "error" (or stay in
  // error long enough that the server cooldown has elapsed). The server
  // enforces OUTAGE_ALERT_COOLDOWN_MINUTES so we can call this aggressively
  // without spamming the inbox.
  useEffect(() => {
    if (worst !== "error" || results.length === 0) {
      prevWorstRef.current = worst;
      return;
    }
    // Only fire on transition into error, or every poll while in error
    // (server-side cooldown will gate duplicates).
    const failed = results.filter((r) => r.level === "error");
    if (failed.length === 0) return;
    const issueKey = failed.map((r) => r.path).sort().join(",");
    const summary = `${failed.length} endpoint(s) returning 5xx or unreachable: ${failed.map((r) => `${r.label} (${r.msg})`).join(" · ")}`;
    api
      .post("/admin/alert-outage", {
        issue_key: issueKey,
        summary,
        failed_endpoints: failed.map((r) => ({
          label: r.label,
          path: r.path,
          status: r.status,
          ms: r.ms,
        })),
      })
      .then((res) => {
        if (res?.data?.sent) {
          setAlertSent({ ts: new Date(), to: res.data.to, key: issueKey });
          // light toast only on the first send so we don't nag
          if (prevWorstRef.current !== "error") {
            toast.error(`Outage email sent to ${res.data.to}`);
          }
        }
      })
      .catch(() => {
        // The /alert-outage call itself may fail if the backend is fully
        // down — this is the documented limitation. Nothing more we can do
        // from inside the page; the user already sees the red badge.
      });
    prevWorstRef.current = worst;
  }, [worst, results]);

  const badge = {
    ok:      { bg: "bg-emerald-600",  text: "text-emerald-50", label: "ALL OK",   ring: "ring-emerald-300", Icon: CheckCircle2 },
    warn:    { bg: "bg-amber-500",    text: "text-amber-50",   label: "SLOW",     ring: "ring-amber-300",   Icon: AlertTriangle },
    error:   { bg: "bg-red-600",      text: "text-red-50",     label: "DOWN",     ring: "ring-red-300",     Icon: AlertCircle },
    loading: { bg: "bg-slate-400",    text: "text-slate-50",   label: "CHECKING", ring: "ring-slate-300",   Icon: Loader2 },
  }[worst];

  return (
    <div className="relative inline-block" data-testid="system-health-badge">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md ${badge.bg} ${badge.text} font-mono text-[10px] uppercase tracking-[0.2em] font-bold shadow-sm ring-1 ${badge.ring} hover:opacity-90 transition-opacity`}
        title={`Last check: ${lastChecked ? formatPlatformTimeOnly(lastChecked) : "—"}\nClick for details`}
        data-testid="system-health-toggle"
      >
        <badge.Icon className={`w-3.5 h-3.5 ${worst === "loading" ? "animate-spin" : ""}`} />
        <span>{badge.label}</span>
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-md shadow-xl z-50 p-3"
          data-testid="system-health-dropdown"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-700 font-bold">
              System Health
            </div>
            <button
              type="button"
              onClick={() => {
                runAll();
              }}
              disabled={loading}
              className="text-[10px] font-mono uppercase tracking-wide text-slate-500 hover:text-slate-900 disabled:opacity-50"
              data-testid="system-health-recheck"
            >
              {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : "↻ Re-check"}
            </button>
          </div>
          <div className="text-[10px] text-slate-500 font-mono mb-2">
            {lastChecked
              ? `Last: ${formatPlatformTimeOnly(lastChecked)} · auto-refresh 60s`
              : "Loading…"}
          </div>
          <ul className="space-y-1">
            {results.map((r) => (
              <li
                key={r.path}
                className={`flex items-center justify-between text-xs px-2 py-1.5 rounded border ${
                  r.level === "ok"
                    ? "border-emerald-200 bg-emerald-50"
                    : r.level === "warn"
                    ? "border-amber-200 bg-amber-50"
                    : "border-red-200 bg-red-50"
                }`}
              >
                <span className="font-mono">
                  <span
                    className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${
                      r.level === "ok"
                        ? "bg-emerald-600"
                        : r.level === "warn"
                        ? "bg-amber-500"
                        : "bg-red-600"
                    }`}
                  />
                  {r.label}
                </span>
                <span className="font-mono text-[10px] text-slate-600">{r.msg}</span>
              </li>
            ))}
          </ul>
          {worst === "error" && (
            <div className="mt-2 text-[10px] bg-red-100 border border-red-300 text-red-900 rounded px-2 py-1.5 font-mono">
              ⚠ Backend is returning 5xx or unreachable. Re-deploy or check server logs.
              {alertSent && (
                <div className="mt-1 text-[10px] font-mono text-red-800">
                  📧 Email alert sent to <strong>{alertSent.to}</strong> at {formatPlatformTimeOnly(alertSent.ts)}
                </div>
              )}
            </div>
          )}
          {worst !== "error" && alertSent && (
            <div className="mt-2 text-[10px] bg-emerald-50 border border-emerald-200 text-emerald-900 rounded px-2 py-1.5 font-mono">
              ✓ Last outage email sent at {formatPlatformTimeOnly(alertSent.ts)} (now recovered)
            </div>
          )}
        </div>
      )}
    </div>
  );
}
