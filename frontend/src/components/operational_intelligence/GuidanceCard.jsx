// Track 19.54 · Operational Guidance System (OGS).
//
// THE UNIVERSAL GUIDANCE CARD.
//
// One primitive. Every HIGH / CRITICAL / Attention item / Trend / Alert
// across the platform opens the SAME card. If a portal builds a
// different-looking card it violates the Track 19.54 doctrine.
//
// Sections (in order, per Track 19.54):
//   1. Title (attention · score · trend)
//   2. Operational Summary (≤ 2 sentences, from top_attention_label)
//   3. Why It Matters
//   4. Primary Drivers (ranked)
//   5. Recommended Actions (≤ 5, concrete)
//   6. Responsible Roles
//   7. Supporting Evidence (counts / dates / metrics)
//   8. Deep Links
//   9. Relevant Guidance
//  10. Decision Boundary
//
// Data comes from TWO existing endpoints — no new backend:
//   - The `product` object passed in (from `/api/operational-intelligence/summary`)
//   - Latest history row for the same product via
//     `GET /api/operational-intelligence/history?product_id=X&limit=1`
//     then `GET /api/operational-intelligence/history/{id}` for the full
//     `digest_object.sections`.
//
// Zero-drift guarantees:
//   • Never re-derives scoring.
//   • Never posts anywhere.
//   • Never queries domain collections.
//   • Never generates new recommendations — extracts from the composed
//     digest's `recommendations` section (already produced by the
//     certified OI engine).

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { X, AlertTriangle, ExternalLink, BookOpen, Users } from "lucide-react";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import AttentionChip from "./AttentionChip";
import TrendChip from "./TrendChip";
import { rolesFor, deepLinksFor } from "./guidanceMap";

const API = process.env.REACT_APP_BACKEND_URL;
const DECISION_BOUNDARY =
  "This information supports operational decision-making. The platform never makes operational decisions.";

async function _get(path) {
  const headers = buildScopedPortalAuthHeaders(["admin"], {
    "Content-Type": "application/json",
  });
  if (!headers["X-Admin-Token"]) return { ok: false, status: 401, body: null };
  try {
    const r = await fetch(`${API}${path}`, {
      headers,
    });
    const body = r.ok ? await r.json().catch(() => null) : null;
    return { ok: r.ok, status: r.status, body };
  } catch {
    return { ok: false, status: 0, body: null };
  }
}

function extractItems(section) {
  if (!section) return [];
  const raw = section.items || [];
  return raw
    .filter((x) => typeof x === "string")
    .filter((x) => x.trim() && !x.trim().startsWith("— Not applicable"));
}

function useLatestDigest(productId, enabled) {
  const [state, setState] = useState({
    loaded: false,
    ok: false,
    sections: [],
    subject: "",
    generatedAt: null,
  });

  useEffect(() => {
    if (!enabled || !productId) return;
    let cancelled = false;
    (async () => {
      const listResp = await _get(
        `/api/operational-intelligence/history?product_id=${encodeURIComponent(productId)}&limit=1`
      );
      if (cancelled) return;
      const list = (listResp.body && listResp.body.history) || [];
      if (!listResp.ok || list.length === 0) {
        setState({ loaded: true, ok: false, sections: [], subject: "", generatedAt: null });
        return;
      }
      const historyId = list[0].id;
      const detail = await _get(
        `/api/operational-intelligence/history/${encodeURIComponent(historyId)}`
      );
      if (cancelled) return;
      const dobj = (detail.body && detail.body.history && detail.body.history.digest_object) || {};
      setState({
        loaded: true,
        ok: detail.ok,
        sections: dobj.sections || [],
        subject: dobj.subject || "",
        generatedAt: list[0].generated_at || null,
      });
    })();
    return () => { cancelled = true; };
  }, [productId, enabled]);

  return state;
}

function sectionByKey(sections, key) {
  return (sections || []).find((s) => s && s.section_key === key) || null;
}

export default function GuidanceCard({ product, onClose }) {
  const digest = useLatestDigest(product && product.product_id, !!product);

  if (!product) return null;
  const productId = product.product_id;
  const displayName = product.display_name || productId;

  const attentionSection = sectionByKey(digest.sections, "needs_immediate_attention");
  const driversSection = sectionByKey(digest.sections, "key_drivers")
                     || sectionByKey(digest.sections, "primary_drivers");
  const recommendationsSection = sectionByKey(digest.sections, "recommendations")
                             || sectionByKey(digest.sections, "recommended_actions");
  const planSection = sectionByKey(digest.sections, "plan_this_week");
  const evidenceSection = sectionByKey(digest.sections, "supporting_evidence")
                      || sectionByKey(digest.sections, "operational_facts");

  const attentionItems = extractItems(attentionSection);
  const driverItems = extractItems(driversSection);
  const recommendationItems = extractItems(recommendationsSection).slice(0, 5);
  const planItems = extractItems(planSection);
  const evidenceItems = extractItems(evidenceSection);

  const operationalSummary = product.top_attention_label
    || (attentionItems[0] || null);

  const roles = rolesFor(productId);
  const links = deepLinksFor(productId);

  return (
    <div
      data-testid="guidance-card-overlay"
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-start sm:items-center justify-center p-2 sm:p-6 overflow-y-auto"
      onClick={onClose}
    >
      <div
        data-testid="guidance-card"
        className="bg-white w-full max-w-3xl rounded-lg shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Section 1 — Title */}
        <div
          data-testid="guidance-card-title"
          className="flex items-start justify-between gap-3 p-4 sm:p-5 border-b border-slate-200"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <AttentionChip
                level={product.attention_level}
                showHint
                testId="guidance-card-attention"
              />
              <TrendChip
                direction={product.trend_direction}
                percent={product.trend_percent}
                score={product.score}
                testId="guidance-card-trend"
              />
            </div>
            <h2 className="font-display text-lg font-bold text-slate-900 truncate">
              {displayName}
            </h2>
          </div>
          <button
            data-testid="guidance-card-close"
            className="p-2 rounded-md hover:bg-slate-100 text-slate-600"
            onClick={onClose}
            aria-label="Close guidance card"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 sm:p-5 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* Section 2 — Operational Summary */}
          <section data-testid="guidance-card-summary">
            <div className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1">
              Operational summary
            </div>
            <p className="text-sm text-slate-800 leading-snug">
              {operationalSummary
                ? operationalSummary
                : `${displayName} is currently ${(product.attention_level || "unknown").toLowerCase()} attention. No standout item requires immediate action.`}
            </p>
          </section>

          {/* Section 3 — Why It Matters */}
          <section data-testid="guidance-card-why">
            <div className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1">
              Why it matters
            </div>
            <p className="text-sm text-slate-800 leading-snug flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <span>
                {product.attention_level === "CRITICAL"
                  ? "Immediate action is required — a critical operational metric has degraded and is affecting the day."
                  : product.attention_level === "HIGH"
                  ? "This will affect today's operation if not addressed. Owners should act during today's window."
                  : product.attention_level === "MEDIUM"
                  ? "Plan a response this week. The signal is trending but not yet operationally blocking."
                  : "No operational consequence today. Signals are within healthy bands — no action required."}
              </span>
            </p>
          </section>

          {/* Section 4 — Primary Drivers */}
          <section data-testid="guidance-card-drivers">
            <div className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1">
              Primary drivers · ranked
            </div>
            {driverItems.length > 0 ? (
              <ol className="list-decimal ml-5 space-y-1 text-sm text-slate-800">
                {driverItems.map((it, i) => (
                  <li key={i} data-testid={`guidance-card-driver-${i}`}>{it}</li>
                ))}
              </ol>
            ) : (
              <p data-testid="guidance-card-drivers-empty" className="text-xs text-slate-500 italic">
                {digest.loaded ? "No drivers isolated from the latest digest." : "Loading drivers…"}
              </p>
            )}
          </section>

          {/* Section 5 — Recommended Actions */}
          <section data-testid="guidance-card-actions">
            <div className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1">
              Recommended actions · max 5
            </div>
            {recommendationItems.length > 0 ? (
              <ul className="space-y-1 text-sm text-slate-800">
                {recommendationItems.map((it, i) => (
                  <li
                    key={i}
                    data-testid={`guidance-card-action-${i}`}
                    className="flex items-start gap-2"
                  >
                    <span className="font-mono text-xs font-bold text-slate-500 shrink-0 mt-0.5">
                      {i + 1}.
                    </span>
                    <span>{it}</span>
                  </li>
                ))}
              </ul>
            ) : planItems.length > 0 ? (
              <ul className="space-y-1 text-sm text-slate-800">
                {planItems.slice(0, 5).map((it, i) => (
                  <li key={i} data-testid={`guidance-card-action-${i}`} className="flex items-start gap-2">
                    <span className="font-mono text-xs font-bold text-slate-500 shrink-0 mt-0.5">
                      {i + 1}.
                    </span>
                    <span>{it}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p data-testid="guidance-card-actions-empty" className="text-xs text-slate-500 italic">
                {digest.loaded
                  ? "The latest digest lists no operational actions. Consult the Cockpit drill-down."
                  : "Loading recommended actions…"}
              </p>
            )}
          </section>

          {/* Section 6 — Responsible Roles */}
          <section data-testid="guidance-card-roles">
            <div className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1 flex items-center gap-1">
              <Users className="w-3.5 h-3.5" /> Responsible roles
            </div>
            <div className="flex flex-wrap gap-1.5">
              {roles.map((r) => (
                <span
                  key={r}
                  data-testid={`guidance-card-role-${r.replace(/\s+/g, "-").toLowerCase()}`}
                  className="inline-flex items-center rounded border border-slate-300 bg-slate-50 px-1.5 py-0.5 text-[11px] font-mono font-bold text-slate-800"
                >
                  {r}
                </span>
              ))}
            </div>
          </section>

          {/* Section 7 — Supporting Evidence */}
          {evidenceItems.length > 0 && (
            <section data-testid="guidance-card-evidence">
              <div className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1">
                Supporting evidence
              </div>
              <ul className="text-sm text-slate-800 space-y-1">
                {evidenceItems.slice(0, 6).map((it, i) => (
                  <li key={i} data-testid={`guidance-card-evidence-${i}`} className="flex items-start gap-2">
                    <span className="text-slate-400 shrink-0">·</span>
                    <span>{it}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Section 8 — Deep Links */}
          <section data-testid="guidance-card-deep-links">
            <div className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1">
              Where to go
            </div>
            <div className="flex flex-wrap gap-2">
              {links.map((l) => (
                <Link
                  key={l.to}
                  to={l.to}
                  data-testid={`guidance-card-deep-link-${l.to.replace(/[^a-z0-9]/gi, "-")}`}
                  className="inline-flex items-center gap-1 text-xs font-mono font-bold text-slate-900 border-2 border-slate-300 hover:border-slate-900 rounded px-2 py-1 uppercase tracking-widest"
                  onClick={onClose}
                >
                  {l.label} <ExternalLink className="w-3 h-3" />
                </Link>
              ))}
            </div>
          </section>

          {/* Section 9 — Relevant Guidance */}
          <section data-testid="guidance-card-guidance">
            <div className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1 flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5" /> Relevant guidance
            </div>
            <Link
              to="/guidance"
              data-testid="guidance-card-guidance-link"
              className="inline-flex items-center gap-1 text-xs font-mono font-bold text-slate-900 border-b border-slate-300 hover:border-slate-900"
              onClick={onClose}
            >
              Open Operational Guidance Center <ExternalLink className="w-3 h-3" />
            </Link>
          </section>

          {/* Section 10 — Decision Boundary */}
          <section
            data-testid="guidance-card-decision-boundary"
            className="text-[11px] italic text-slate-500 border-t border-slate-200 pt-3"
          >
            {DECISION_BOUNDARY}
          </section>
        </div>
      </div>
    </div>
  );
}
