// Track 19.52 · P1 Command Center Remediation Execution.
//
// OiAttentionStrip — SINGLE shared consumer of the certified
// Operational Intelligence engine. Mounted at the top of every portal
// home identified in the Track 19.51 OI Integration Map.
//
// This is NOT a new intelligence framework. It is a pure read-only
// consumer of `GET /api/operational-intelligence/summary` — no new
// backend, no new score model, no new scheduler, no new email path.
//
// Contract:
//   props.productIds  — string[] · which OI products to surface
//                                    (e.g. ["safety_morning_digest"])
//   props.title       — optional strip title. Defaults to
//                       "Operational Intelligence · attention now".
//   props.testId      — required · stable data-testid root.
//
// Zero-drift guarantees:
//   • Never re-derives scores.
//   • Never queries domain collections.
//   • Never mutates OI data.
//   • Never sends emails.
//   • Never adds a new score model.
//   • Never adds a new scheduler.
//   • Never adds a new recipient system.
//
// Six-Pillar compliance:
//   Powerful   — one row per product with score, attention level,
//                trend arrow, and top_attention_label.
//   Simple     — first-time user reads the strip in <10 seconds.
//   Beautiful  — clean tiles, no vanity KPIs.
//   Trusted    — every value is echoed from the OI summary payload.
//   Proven     — every tile carries a stable data-testid.
//   Operational — every tile deep-links to
//                 `/admin/operational-intelligence` for drill-down.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, ArrowRight } from "lucide-react";
import { getAdminToken } from "@/lib/adminAuth";
import GuidanceCard from "./GuidanceCard";

const API = process.env.REACT_APP_BACKEND_URL;

const ATTENTION_TONE = {
  LOW:      { bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-900", chip: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  MEDIUM:   { bg: "bg-amber-50",   border: "border-amber-300",   text: "text-amber-900",   chip: "bg-amber-100 text-amber-800 border-amber-300" },
  HIGH:     { bg: "bg-orange-50",  border: "border-orange-300",  text: "text-orange-900",  chip: "bg-orange-100 text-orange-800 border-orange-300" },
  CRITICAL: { bg: "bg-red-50",     border: "border-red-300",     text: "text-red-900",     chip: "bg-red-100 text-red-800 border-red-300" },
  DEFAULT:  { bg: "bg-slate-50",   border: "border-slate-300",   text: "text-slate-900",   chip: "bg-slate-100 text-slate-800 border-slate-300" },
};

function toneFor(level) {
  return ATTENTION_TONE[level] || ATTENTION_TONE.DEFAULT;
}

function ArrowGlyph({ direction }) {
  const map = { up: "▲", down: "▼", flat: "→", "▲": "▲", "▼": "▼", "→": "→" };
  const cls = direction === "up" || direction === "▲"
    ? "text-emerald-700"
    : direction === "down" || direction === "▼"
    ? "text-red-700"
    : "text-slate-500";
  return <span className={`font-mono text-sm font-bold ${cls}`} aria-hidden="true">{map[direction] || "→"}</span>;
}

async function fetchOiSummary({ timeoutMs = 3000 } = {}) {
  const token = getAdminToken();
  if (!token) return { ok: false, status: 401, body: null, reason: "no_token" };
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const r = await fetch(`${API}/api/operational-intelligence/summary`, {
      headers: { "X-Admin-Token": token, "Content-Type": "application/json" },
      signal: controller.signal,
    });
    const body = r.ok ? await r.json().catch(() => null) : null;
    return { ok: r.ok, status: r.status, body, reason: r.ok ? "ok" : "http_error" };
  } catch (err) {
    const reason = err && err.name === "AbortError" ? "timeout" : "network";
    return { ok: false, status: 0, body: null, reason };
  } finally {
    clearTimeout(timer);
  }
}

// TRACK 22.4a · portal-specific fallback copy — operator-readable, calm,
// never blocks portal primary actions.
const PORTAL_FALLBACK_COPY = {
  admin: "Administrative intelligence is unavailable. Configuration, trust, and system controls remain available.",
  pm: "Project intelligence is unavailable. Project records, daily reports, photos, and reviews remain available.",
  safety: "Safety intelligence is unavailable. Incidents, meetings, JHPs, training, and trench safety remain available.",
  hr: "HR intelligence is unavailable. Employee lifecycle, requests, documents, and qualifications remain available.",
  shop: "Shop intelligence is unavailable. Equipment attention, repairs, holds, and recovery workflows remain available.",
  default: "Operational intelligence is temporarily unavailable. Core portal workflows remain available.",
};

export default function OiAttentionStrip({
  productIds,
  title = "Operational Intelligence · attention now",
  testId,
  portal = "default",
  timeoutMs = 3000,
}) {
  const [state, setState] = useState({ loaded: false, ok: false, status: 0, products: [], reason: "" });
  const productIdsKey = React.useMemo(() => productIds.join("|"), [productIds]);
  // Track 19.54 · OGS — clicking a tile opens the universal
  // Guidance Card modal in place. No navigation.
  const [openProduct, setOpenProduct] = useState(null);

  const load = React.useCallback(() => {
    setState((s) => ({ ...s, loaded: false }));
    fetchOiSummary({ timeoutMs }).then((r) => {
      const all = (r.body && Array.isArray(r.body.products)) ? r.body.products : [];
      const filtered = all.filter((p) => productIds.includes(p.product_id));
      setState({ loaded: true, ok: r.ok, status: r.status, products: filtered, reason: r.reason || "" });
    });
  }, [productIds, timeoutMs]);

  useEffect(() => {
    let cancelled = false;
    fetchOiSummary({ timeoutMs }).then((r) => {
      if (cancelled) return;
      const all = (r.body && Array.isArray(r.body.products)) ? r.body.products : [];
      const filtered = all.filter((p) => productIds.includes(p.product_id));
      setState({ loaded: true, ok: r.ok, status: r.status, products: filtered, reason: r.reason || "" });
    });
    return () => { cancelled = true; };
  }, [productIds, productIdsKey, timeoutMs]);

  const rootTestId = testId || "oi-attention-strip";

  // Honest empty / unauthorized / timeout state — no fake numbers, no filler,
  // never an infinite loading spinner. Track 22.4a fix.
  if (state.loaded && !state.ok) {
    const isAuth = state.status === 401 || state.status === 403;
    const isTimeout = state.reason === "timeout";
    const isNetwork = state.reason === "network";
    const fallbackCopy = PORTAL_FALLBACK_COPY[portal] || PORTAL_FALLBACK_COPY.default;
    const message = isAuth
      ? "Admin token required to view OI signals · request access from your administrator."
      : isTimeout
        ? fallbackCopy + " (timed out)"
        : isNetwork
          ? fallbackCopy + " (network error)"
          : fallbackCopy;
    return (
      <section
        data-testid={rootTestId}
        className="mb-4 rounded-md border-2 border-slate-200 bg-white px-4 py-3"
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-slate-700">
            <Activity className="w-4 h-4" />
            <span className="font-mono text-[11px] uppercase tracking-widest font-bold">{title}</span>
          </div>
          <div className="flex items-center gap-3">
            <span
              data-testid={`${rootTestId}-empty`}
              className="text-xs text-slate-500 italic"
            >
              {message}
            </span>
            {!isAuth && (
              <button
                type="button"
                onClick={load}
                data-testid={`${rootTestId}-retry`}
                className="text-[11px] font-mono uppercase tracking-widest font-bold text-slate-600 hover:text-slate-900"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section
      data-testid={rootTestId}
      className="mb-4 rounded-md border-2 border-slate-200 bg-white px-4 py-3"
    >
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 text-slate-700">
          <Activity className="w-4 h-4" />
          <span className="font-mono text-[11px] uppercase tracking-widest font-bold">
            {title}
          </span>
        </div>
        <Link
          to="/admin/operational-intelligence"
          data-testid={`${rootTestId}-open-cockpit`}
          className="inline-flex items-center gap-1 text-[11px] font-mono uppercase tracking-widest font-bold text-slate-600 hover:text-slate-900"
        >
          Open in Cockpit <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
      <div
        data-testid={`${rootTestId}-grid`}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
      >
        {state.products.map((p) => (
          <OiProductTile
            key={p.product_id}
            product={p}
            rootTestId={rootTestId}
            onOpen={() => setOpenProduct(p)}
          />
        ))}
        {state.loaded && state.products.length === 0 && (
          <div
            data-testid={`${rootTestId}-empty`}
            className="col-span-full text-xs text-slate-500 italic"
          >
            Configured intelligence products not implemented yet — showing portal-native queues below.
          </div>
        )}
        {!state.loaded && (
          <div
            data-testid={`${rootTestId}-loading`}
            className="col-span-full text-xs text-slate-500 font-mono uppercase tracking-widest"
          >
            Loading OI signals…
          </div>
        )}
      </div>
      {openProduct && (
        <GuidanceCard product={openProduct} onClose={() => setOpenProduct(null)} />
      )}
    </section>
  );
}

function OiProductTile({ product, rootTestId, onOpen }) {
  const tone = toneFor(product.attention_level);
  const hasScore = typeof product.score === "number";
  const label = product.top_attention_label;
  const tileTestId = `${rootTestId}-tile-${product.product_id}`;
  const hasError = !!product.error;

  return (
    <button
      type="button"
      onClick={onOpen}
      data-testid={tileTestId}
      className={`block w-full text-left rounded-md border-2 ${tone.border} ${tone.bg} px-3 py-2.5 hover:shadow-sm transition-shadow`}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className={`font-display text-sm font-bold ${tone.text} leading-snug truncate`}>
          {product.display_name || product.product_id}
        </div>
        {product.attention_level && (
          <span
            data-testid={`${tileTestId}-level`}
            className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-mono font-bold uppercase tracking-wider ${tone.chip}`}
          >
            {product.attention_level}
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span
          data-testid={`${tileTestId}-score`}
          className={`text-2xl font-black ${tone.text}`}
        >
          {hasScore ? product.score : "—"}
        </span>
        <ArrowGlyph direction={product.trend_direction} />
        {typeof product.trend_percent === "number" && (
          <span className="text-[11px] font-mono text-slate-600">
            {product.trend_percent > 0 ? "+" : ""}{product.trend_percent.toFixed(1)}%
          </span>
        )}
      </div>
      {label && !hasError && (
        <div
          data-testid={`${tileTestId}-top-attention`}
          className="mt-1 text-[12px] text-slate-700 leading-snug line-clamp-2"
        >
          {label}
        </div>
      )}
      {hasError && (
        <div
          data-testid={`${tileTestId}-error`}
          className="mt-1 text-[11px] text-slate-500 italic"
        >
          Insufficient data · consult Cockpit.
        </div>
      )}
      {!label && !hasError && hasScore && (
        <div className="mt-1 text-[12px] text-slate-500 italic">
          No attention items — portal is calm.
        </div>
      )}
    </button>
  );
}
