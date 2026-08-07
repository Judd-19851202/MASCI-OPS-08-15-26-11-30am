// AdminCommandCenter.jsx — Pillar 2 · Phase A · iter500
//
// Executive Operations Command Center: single-glass view answering
// "What is hurting MASCI right now? · How severe? · Who owns it? ·
//  What is being done? · When will it be resolved?"
//
// 5 cards + Pulse Strip + drilldown modal. All data from
// /api/admin/command-center/snapshot (server-side cached 15s).
// No actions, no writes, no notifications fired from this surface.
//
// See: FINAL_PHASE_A_RECOMMENDATION.md, EXECUTIVE_SCORING_CERTIFICATION.md
//
import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import AdminShell from "@/components/AdminShell";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { Button } from "@/components/ui/button";
// TRACK 27.03 · Phase 3 · Canonical local-time formatter.
import { formatPlatformTime } from "@/lib/platformTime";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const POLL_MS = 30000;

const PILL_STYLES = {
  GREEN: "bg-emerald-100 text-emerald-800 border-emerald-300",
  AMBER: "bg-amber-100 text-amber-800 border-amber-300",
  RED: "bg-rose-100 text-rose-800 border-rose-300",
};

function fmtTs(ts) {
  // TRACK 27.03 · Phase 3 · Local wall-clock via canonical formatter.
  return formatPlatformTime(ts);
}

function Pill({ status, size = "md", testid }) {
  const cls = PILL_STYLES[status] || PILL_STYLES.GREEN;
  const sizeCls = size === "lg" ? "px-4 py-1.5 text-base" : "px-2.5 py-0.5 text-xs font-semibold";
  return (
    <span
      className={`inline-flex items-center rounded-full border ${cls} ${sizeCls}`}
      data-testid={testid}
    >
      {status}
    </span>
  );
}

function CardShell({ card, onItemClick }) {
  const pill = card.pill || "GREEN";
  const headline = card.warnings && card.warnings[0]
    ? card.warnings[0].message
    : `All clear · ${card.title.toLowerCase()}`;

  return (
    <div
      className="rounded-lg bg-white border border-slate-200 shadow-sm p-4 flex flex-col"
      data-testid={`cc-card-${card.card_id}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {card.title}
        </div>
        <Pill status={pill} testid={`cc-card-${card.card_id}-pill`} />
      </div>
      <div className="text-sm text-slate-700 mb-3" data-testid={`cc-card-${card.card_id}-headline`}>
        {headline}
      </div>
      {card.warnings && card.warnings.length > 1 && (
        <ul className="text-xs text-slate-500 list-disc pl-5 mb-2 space-y-1">
          {card.warnings.slice(1, 4).map((w, i) => (
            <li key={i}>
              <span className={`font-semibold ${w.severity === "red" ? "text-rose-700" : "text-amber-700"}`}>
                {w.severity.toUpperCase()}
              </span>
              {" · "}{w.message}
            </li>
          ))}
        </ul>
      )}
      {card.items && card.items.length > 0 && pill !== "GREEN" && (
        <div className="mt-auto pt-2 border-t border-slate-100">
          <div className="text-[10px] uppercase font-semibold text-slate-400 mb-1.5">
            Top items requiring attention
          </div>
          <ul className="space-y-1.5">
            {card.items.slice(0, 3).map((it, i) => (
              <li
                key={i}
                className="text-xs cursor-pointer hover:bg-slate-50 -mx-1 px-1 py-1 rounded"
                onClick={() => onItemClick(card.card_id, it)}
                data-testid={`cc-card-${card.card_id}-item-${i}`}
              >
                <div className="flex items-start gap-2">
                  <span className={`mt-0.5 inline-block h-2 w-2 rounded-full ${
                    it.severity === "red" ? "bg-rose-500" : "bg-amber-500"
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-slate-800 truncate">{it.what_wrong}</div>
                    <div className="text-slate-500 truncate">
                      Owner: <span className="font-semibold">{it.owner}</span> · ETA: {it.eta}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function DrilldownModal({ open, item, cardId, onClose }) {
  if (!open || !item) return null;
  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
      onClick={onClose}
      data-testid="cc-drilldown-modal"
    >
      <div
        className="bg-white rounded-lg max-w-xl w-full p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="text-lg font-bold text-slate-900">Operational Drilldown</div>
          <Pill status={item.severity === "red" ? "RED" : "AMBER"} testid="cc-drilldown-pill" />
        </div>
        <dl className="space-y-3 text-sm">
          <div>
            <dt className="text-xs uppercase font-semibold text-slate-500">What is wrong?</dt>
            <dd className="text-slate-900 mt-0.5" data-testid="cc-drill-what">{item.what_wrong}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase font-semibold text-slate-500">Why is it RED/AMBER?</dt>
            <dd className="text-slate-900 mt-0.5" data-testid="cc-drill-why">{item.why_red}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase font-semibold text-slate-500">Who owns it?</dt>
            <dd className="text-slate-900 mt-0.5 font-semibold" data-testid="cc-drill-owner">{item.owner}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase font-semibold text-slate-500">What is being done?</dt>
            <dd className="text-slate-900 mt-0.5" data-testid="cc-drill-status">{item.current_status}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase font-semibold text-slate-500">When will it resolve?</dt>
            <dd className="text-slate-900 mt-0.5" data-testid="cc-drill-eta">{item.eta}</dd>
          </div>
        </dl>
        <div className="mt-5 flex items-center justify-between border-t pt-3">
          <span className="text-xs text-slate-400">Rule: {item.rule_id} · Card: {cardId}</span>
          <div className="flex gap-2">
            {item.drill_to && (
              <Link
                to={item.drill_to}
                className="px-3 py-1.5 bg-slate-900 text-white text-sm rounded hover:bg-slate-800"
                data-testid="cc-drill-open-link"
              >
                Open source record →
              </Link>
            )}
            <Button variant="outline" size="sm" onClick={onClose} data-testid="cc-drill-close">
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminCommandCenter() {
  const [snap, setSnap] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const [drilldown, setDrilldown] = useState({ open: false, item: null, cardId: null });

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/admin/command-center/snapshot`, {
        headers: buildScopedPortalAuthHeaders(["admin"]),
      });
      if (!r.ok) {
        setErr(`HTTP ${r.status}`);
        return;
      }
      const d = await r.json();
      setSnap(d);
      setErr(null);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [load]);

  const handleItemClick = (cardId, item) => {
    setDrilldown({ open: true, item, cardId });
  };

  return (
    <AdminShell
      title="Operations Command Center"
      section="command-center"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Single-glass operational health. Read-only · refreshes every 30s · every RED item
          answers <span className="font-semibold">what · why · who · being-done · ETA</span>.
        </p>
      }
    >
      {loading && (
        <div className="text-sm text-slate-500" data-testid="cc-loading">
          Loading the latest command center view…
        </div>
      )}
      {err && (
        <div
          className="rounded-md bg-rose-50 border border-rose-200 text-rose-700 p-3 text-sm"
          data-testid="cc-error"
        >
          We could not load the command center right now. {err}
        </div>
      )}
      {snap && (
        <div className="space-y-4" data-testid="cc-snapshot">
          <div className="rounded-lg border border-teal-200 bg-teal-50 p-4 text-sm text-teal-900" data-testid="cc-portfolio-link-callout">
            Cross-project cost, schedule, commitments, and direct project drill-back now live in{` `}
            <Link to="/admin/executive-overview" className="font-semibold underline" data-testid="cc-portfolio-link">
              Portfolio Intelligence
            </Link>
            . Keep this Command Center for live operational triage and owner accountability.
          </div>
          {/* PULSE STRIP — 5-sec view */}
          <div
            className="rounded-lg bg-slate-900 text-white p-4 flex items-center justify-between"
            data-testid="cc-pulse-strip"
          >
            <div className="flex items-center gap-4">
              <div>
                <div className="text-[10px] uppercase tracking-widest text-slate-400 mb-1">
                  Pulse · Company Health
                </div>
                <div className="flex items-center gap-3">
                  <Pill status={snap.pulse?.pill || snap.pill} size="lg" testid="cc-pulse-pill" />
                  <span className="text-lg font-bold" data-testid="cc-pulse-headline">
                    {snap.pulse?.headline || "—"}
                  </span>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase tracking-widest text-slate-400">Updated</div>
              <div className="text-xs font-mono text-slate-200" data-testid="cc-computed-at">
                {fmtTs(snap.computed_at)}
              </div>
              <div className="mt-1 flex justify-end">
                <Button
                  size="sm"
                  variant="outline"
                  className="bg-slate-800 border-slate-700 text-white hover:bg-slate-700 h-7 px-3 text-xs"
                  onClick={load}
                  data-testid="cc-refresh-btn"
                >
                  Refresh
                </Button>
              </div>
            </div>
          </div>

          {/* 5-CARD GRID — 30-sec view */}
          <div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3"
            data-testid="cc-cards-grid"
          >
            {(snap.cards || []).map((c) => (
              <CardShell key={c.card_id} card={c} onItemClick={handleItemClick} />
            ))}
          </div>

          {/* TUNING LINK */}
          <div className="text-xs text-slate-500 pt-2 border-t border-slate-100" data-testid="cc-admin-settings-note">
            Timing and thresholds can be updated from the admin settings record. Every change is audit-logged.
          </div>
        </div>
      )}

      <DrilldownModal
        open={drilldown.open}
        item={drilldown.item}
        cardId={drilldown.cardId}
        onClose={() => setDrilldown({ open: false, item: null, cardId: null })}
      />
    </AdminShell>
  );
}
