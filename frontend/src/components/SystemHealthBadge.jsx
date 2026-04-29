import React, { useEffect, useRef, useState } from "react";
import { CheckCircle2, AlertTriangle, AlertCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";

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
  { path: "/jhas",              label: "JHAs",             critical: false },
  { path: "/incidents",         label: "Incidents",        critical: false },
  { path: "/daily-reports",     label: "Daily Reports",    critical: false },
];

const POLL_INTERVAL_MS = 60_000;
const SLOW_THRESHOLD_MS = 2000;

async function pingOne(ep) {
  const t0 = performance.now();
  try {
    const r = await api.get(ep.path, { timeout: 8000 });
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
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [lastChecked, setLastChecked] = useState(null);
  const [alertSent, setAlertSent] = useState(null); // {ts, key} of last successful alert
  const timerRef = useRef(null);
  const prevWorstRef = useRef("ok");

  const runAll = async () => {
    setLoading(true);
    const out = await Promise.all(ENDPOINTS.map(pingOne));
    setResults(out);
    setLastChecked(new Date());
    setLoading(false);
  };

  useEffect(() => {
    runAll();
    timerRef.current = setInterval(runAll, POLL_INTERVAL_MS);
    return () => clearInterval(timerRef.current);
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
        title={`Last check: ${lastChecked ? lastChecked.toLocaleTimeString() : "—"}\nClick for details`}
        data-testid="system-health-toggle"
      >
        <badge.Icon className={`w-3.5 h-3.5 ${worst === "loading" ? "animate-spin" : ""}`} />
        <span>{badge.label}</span>
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-80 bg-white border-2 border-slate-300 rounded-md shadow-xl z-50 p-3"
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
              ? `Last: ${lastChecked.toLocaleTimeString()} · auto-refresh 60s`
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
                  📧 Email alert sent to <strong>{alertSent.to}</strong> at {alertSent.ts.toLocaleTimeString()}
                </div>
              )}
            </div>
          )}
          {worst !== "error" && alertSent && (
            <div className="mt-2 text-[10px] bg-emerald-50 border border-emerald-200 text-emerald-900 rounded px-2 py-1.5 font-mono">
              ✓ Last outage email sent at {alertSent.ts.toLocaleTimeString()} (now recovered)
            </div>
          )}
        </div>
      )}
    </div>
  );
}
