// DraftHealthTile.jsx — iter442 · Field-trust observability surface.
//
// Tiny, calm, admin-only read-only consumer of /api/draft-telemetry/recent.
// Surfaces the health of the Daily Report (and sibling form) draft
// system on the operator's device — the very surface that the P0
// field incident was about. NEVER renders form content. NEVER renders
// photo blobs. ONLY sizes, error names, timestamps, transitions.
//
// What it shows
// -------------
//   - Health verdict pill: healthy / watch / degraded
//   - Failed saves in last 24h
//   - Restore-then-discard decisions in last 24h (operator gave up)
//   - Distinct affected devices in last 24h
//   - Last telemetry event timestamp ("12s ago")
//
// What it doesn't show
// --------------------
//   - No payload content. No PII. No photo references. No form text.
//   - No charts. No graphs. No drill-down panel.
//
// Refresh: silent 60-second poll. Manual refresh button is available
// but the tile is calm by default — no spinner, no animation, no
// loud color unless health is genuinely degraded.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, RefreshCw, AlertTriangle, CheckCircle2, EyeOff } from "lucide-react";
import { api } from "@/lib/api";

const POLL_MS = 60_000;
const DAY_MS = 24 * 60 * 60 * 1000;
// TRUST-1 · TF-012 · "Quiet" verdict floor. Below this many events in
// the last 60s the tile can't distinguish "no failures" from "no
// telemetry reaching the server" (CDN blocked, route dropped, etc.).
// We surface a calm "Quiet" pill so the admin knows the signal is
// suspicious rather than confidently green.
const QUIET_FLOOR_60S = 1;

function _fmtRelative(iso) {
  if (!iso) return "—";
  try {
    const t = new Date(iso).getTime();
    if (!t) return "—";
    const dt = Math.max(0, Date.now() - t);
    const s = Math.floor(dt / 1000);
    if (s < 60) return `${s}s ago`;
    const m = Math.floor(s / 60);
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    const d = Math.floor(h / 24);
    return `${d}d ago`;
  } catch {
    return "—";
  }
}

function _verdict({ failedSaves24h, discardsAfterFail24h, health }) {
  // TRUST-1 · TF-012 — if the live /health probe says the route is
  // alive but no events landed in the last 60s, we cannot trust a
  // "healthy" verdict. Distinct from genuine green so the admin can
  // tell that the signal itself may be off-air.
  if (
    health
    && health.ok === true
    && typeof health.recent_events_60s === "number"
    && health.recent_events_60s < QUIET_FLOOR_60S
  ) {
    return "quiet";
  }
  if (failedSaves24h === 0 && discardsAfterFail24h === 0) return "healthy";
  if (failedSaves24h <= 5 && discardsAfterFail24h <= 1) return "watch";
  return "degraded";
}

const VERDICT_META = {
  healthy: {
    Icon: CheckCircle2,
    label: "Healthy",
    tint: "border-emerald-300 bg-emerald-50 text-emerald-900",
    pill: "bg-emerald-600 text-white",
  },
  quiet: {
    Icon: EyeOff,
    label: "Quiet",
    tint: "border-slate-300 bg-slate-50 text-slate-800",
    pill: "bg-slate-600 text-white",
  },
  watch: {
    Icon: Activity,
    label: "Watch",
    tint: "border-amber-300 bg-amber-50 text-amber-900",
    pill: "bg-amber-600 text-white",
  },
  degraded: {
    Icon: AlertTriangle,
    label: "Degraded",
    tint: "border-rose-300 bg-rose-50 text-rose-900",
    pill: "bg-rose-600 text-white",
  },
};

export default function DraftHealthTile({ testId = "draft-health-tile" }) {
  const [events, setEvents] = useState(null);
  const [health, setHealth] = useState(null);
  const [loadedAt, setLoadedAt] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [err, setErr] = useState(null);

  const fetchEvents = useCallback(async () => {
    setRefreshing(true);
    setErr(null);
    try {
      // Cap at 200 (server max) — gives us a 24h window for normal
      // platform usage. We compute everything client-side; we do NOT
      // ask the server to aggregate (server is dumb store).
      // TF-012 — also probe /health so we can detect a telemetry-
      // pipeline failure that would otherwise look like a calm day.
      const [r, hres] = await Promise.all([
        api.get("/draft-telemetry/recent?limit=200"),
        api.get("/draft-telemetry/health").catch(() => null),
      ]);
      const items = (r && r.data && r.data.items) || [];
      setEvents(items);
      setHealth(hres && hres.data ? hres.data : null);
      setLoadedAt(Date.now());
    } catch (e) {
      setErr(e?.message || "failed to load");
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents();
    const id = setInterval(fetchEvents, POLL_MS);
    return () => clearInterval(id);
  }, [fetchEvents]);

  const stats = useMemo(() => {
    const out = {
      failedSaves24h: 0,
      discardsAfterFail24h: 0,
      affectedDevices24h: 0,
      affectedDevicesList: [],
      lastEventReceivedAt: null,
      anonShare: 0,
      total24h: 0,
    };
    if (!events || !events.length) return out;
    const cutoff = Date.now() - DAY_MS;
    const failDevices = new Set();
    // TRUST-1 · TF-005/019/020 — per-device deterministic triage map.
    // Keyed by deviceId; remembers most recent failure event + token
    // kind so the admin can read off a Support ID and event type in
    // one tap. Lightweight (max 5 entries), text-only, no charts.
    const deviceMap = new Map();
    let anonCount = 0;
    let total24h = 0;
    let mostRecent = null;
    // Walk by receivedAt; events come sorted desc already.
    for (const e of events) {
      const rt = e && e.receivedAt ? new Date(e.receivedAt).getTime() : 0;
      if (!rt) continue;
      if (!mostRecent || rt > mostRecent) mostRecent = rt;
      if (rt < cutoff) continue;
      total24h += 1;
      if ((e.tokenKind || "") === "anon") anonCount += 1;
      if (e.event === "draft.write.fail") {
        out.failedSaves24h += 1;
        if (e.deviceId) failDevices.add(e.deviceId);
      }
      if (e.event === "draft.restore.action" && e.meta && e.meta.choice === "discard") {
        // A discard immediately after observed failures hints the
        // operator gave up. Cheap heuristic: count any discard in
        // the 24h window.
        out.discardsAfterFail24h += 1;
      }
      // Per-device triage map — fail / discard / recovery.absent are
      // the events that indicate operator-trust concern. Take only the
      // FIRST (most recent, since events are desc) match per device.
      const concernEvents = new Set([
        "draft.write.fail",
        "draft.restore.action",
        "draft.recovery.absent",
        "quota.warning",
      ]);
      if (e.deviceId && concernEvents.has(e.event) && !deviceMap.has(e.deviceId)) {
        deviceMap.set(e.deviceId, {
          deviceId: e.deviceId,
          tokenKind: e.tokenKind || "anon",
          event: e.event,
          choice: (e.meta && e.meta.choice) || null,
          trigger: (e.meta && e.meta.trigger) || null,
          errorName: (e.meta && e.meta.errorName) || null,
          receivedAt: e.receivedAt,
        });
      }
    }
    out.affectedDevices24h = failDevices.size;
    out.affectedDevicesList = Array.from(deviceMap.values()).slice(0, 5);
    out.lastEventReceivedAt = mostRecent ? new Date(mostRecent).toISOString() : null;
    out.anonShare = total24h > 0 ? Math.round((anonCount / total24h) * 100) : 0;
    out.total24h = total24h;
    return out;
  }, [events]);

  const [expanded, setExpanded] = useState(false);

  const verdict = _verdict({ ...stats, health });
  const meta = VERDICT_META[verdict];
  const Icon = meta.Icon;

  return (
    <section
      data-testid={testId}
      data-verdict={verdict}
      className={`rounded-lg border-2 ${meta.tint} px-4 py-3`}
    >
      <header className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4" aria-hidden="true" />
          <h3 className="font-mono text-[11px] uppercase tracking-[0.2em] font-bold">
            Daily Report · Draft Health
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wider ${meta.pill}`}
            data-testid={`${testId}-verdict`}
          >
            {meta.label}
          </span>
          <button
            type="button"
            onClick={fetchEvents}
            disabled={refreshing}
            data-testid={`${testId}-refresh`}
            className="text-current opacity-70 hover:opacity-100 disabled:opacity-40"
            title="Refresh draft health"
            aria-label="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-x-6 gap-y-3 text-[11px]" data-testid={`${testId}-stats`}>
        <div>
          <div className="font-mono uppercase tracking-wider opacity-70">Failed saves · 24h</div>
          <div className="font-display text-2xl font-black leading-none mt-0.5"
               data-testid={`${testId}-failed-saves`}>
            {stats.failedSaves24h}
          </div>
        </div>
        <div>
          <div className="font-mono uppercase tracking-wider opacity-70">Discards · 24h</div>
          <div className="font-display text-2xl font-black leading-none mt-0.5"
               data-testid={`${testId}-discards`}>
            {stats.discardsAfterFail24h}
          </div>
        </div>
        <div>
          <div className="font-mono uppercase tracking-wider opacity-70">Devices affected</div>
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            disabled={stats.affectedDevicesList.length === 0}
            data-testid={`${testId}-devices`}
            aria-expanded={expanded}
            aria-label="Toggle affected device triage"
            className={`font-display text-2xl font-black leading-none mt-0.5 inline-flex items-baseline gap-1
              ${stats.affectedDevicesList.length === 0
                ? "cursor-default opacity-90"
                : "cursor-pointer hover:opacity-80"}`}
          >
            <span>{stats.affectedDevices24h}</span>
            {stats.affectedDevicesList.length > 0 ? (
              <span className="font-mono text-[10px] uppercase tracking-wider opacity-60">
                {expanded ? "hide" : "view"}
              </span>
            ) : null}
          </button>
        </div>
        <div>
          <div className="font-mono uppercase tracking-wider opacity-70">Last event</div>
          <div className="font-display text-base font-bold leading-tight mt-0.5"
               data-testid={`${testId}-last-event`}>
            {_fmtRelative(stats.lastEventReceivedAt)}
          </div>
        </div>
      </div>

      <footer className="flex items-center justify-between mt-3 pt-2 border-t border-current/10 text-[10px] font-mono uppercase tracking-wider opacity-70">
        <span data-testid={`${testId}-total`}>
          {stats.total24h} events · 24h · {stats.anonShare}% anon
          {health && typeof health.recent_events_60s === "number"
            ? ` · ${health.recent_events_60s}/60s`
            : ""}
        </span>
        <span data-testid={`${testId}-loaded-at`}>
          {loadedAt ? `loaded ${_fmtRelative(new Date(loadedAt).toISOString())}` : "loading…"}
        </span>
      </footer>

      {/* TRUST-1 · TF-005 / TF-019 / TF-020 — affected-device expander.
          Text-only operational triage: most recent Support IDs that
          hit a concern event in the last 24h with their event type,
          trigger, and timestamp. Lightweight by design — no charts,
          no per-device drill page. Closes the "what's actually
          wrong?" question in under a minute. */}
      {expanded && stats.affectedDevicesList.length > 0 ? (
        <div
          data-testid={`${testId}-affected-list`}
          className="mt-3 pt-2 border-t border-current/10"
        >
          <div className="font-mono text-[10px] uppercase tracking-wider opacity-70 mb-1.5">
            Recent affected · Support IDs · top 5
          </div>
          <ul className="space-y-1">
            {stats.affectedDevicesList.map((d) => {
              const short = (d.deviceId || "—").slice(0, 12) + (d.deviceId && d.deviceId.length > 12 ? "…" : "");
              const evShort = (d.event || "").replace(/^draft\./, "").replace(/^quota\./, "q.");
              const detail = d.errorName
                ? d.errorName
                : d.choice
                  ? d.choice
                  : d.trigger || "—";
              return (
                <li
                  key={d.deviceId}
                  data-testid={`${testId}-affected-row`}
                  data-device-id={d.deviceId}
                  className="grid grid-cols-12 gap-2 items-center text-[11px] leading-tight"
                >
                  <span className="col-span-4 font-mono text-current/80 truncate" title={d.deviceId}>
                    {short}
                  </span>
                  <span className="col-span-3 font-mono uppercase tracking-wider text-current/70">
                    {evShort}
                  </span>
                  <span className="col-span-3 font-mono text-current/60 truncate" title={detail}>
                    {detail}
                  </span>
                  <span className="col-span-2 font-mono text-[10px] text-current/60 text-right">
                    {_fmtRelative(d.receivedAt)}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      {verdict === "quiet" ? (
        <p
          className="text-[11px] mt-2 leading-snug"
          data-testid={`${testId}-quiet-note`}
        >
          Signal quiet · the route answered, but no events arrived in
          the last 60s. Verify a recent operator session before trusting
          a green count.
        </p>
      ) : null}

      {err ? (
        <p className="text-[11px] mt-2 text-rose-700" data-testid={`${testId}-error`}>
          could not load · {err}
        </p>
      ) : null}
    </section>
  );
}
