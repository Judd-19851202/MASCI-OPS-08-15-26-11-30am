// PmProjectDetail.jsx — Phase V-Prelude · Wave 1.1.
//
// Calm per-project detail surface that hosts the Operational Timeline
// sidecar. This page is intentionally MINIMAL — its sole job is to
// give the chronology sidecar a high-context home inside the PM portal,
// so real operators can validate timeline usability during the Wave 1
// observation window.
//
// DO NOT add tiles, KPIs, charts, or dashboard widgets here (Wave 1.1
// hard rule: "no dashboard additions"). This is a single-project
// chronology surface.
//
// Track 13.13 (2026-06-12) · Build Queue #4 — Operational Events
// Project-Day Panel. Calm, read-only, text-only. Source: existing
// public endpoint GET /api/operational-events/project-day/{project_number}/{date}.
// NO charts, NO KPIs, NO invented categories, NO fabricated counts.
// Endpoint returns per-asset arrival/departure rows; the panel renders
// exactly that shape (asset · first_seen · last_seen · still_on_site).
// Empty + offline + error states are honest. No new backend, no new
// route, no new permission.

import React from "react";
import { useParams, Link } from "react-router-dom";
import { Briefcase, Activity, Truck, CheckCircle2, AlertTriangle, FileCheck2, Users, ArrowRight } from "lucide-react";
import PmShell from "@/components/PmShell";
import OperationalTimelineSidecar from "@/components/operational/OperationalTimelineSidecar";
import TrenchSafetyOnProjectPanel from "@/components/trench/TrenchSafetyOnProjectPanel";
import JobTeamRosterPanel from "@/components/team/JobTeamRosterPanel";
import PmCostCodeAssignmentCard from "@/components/pm/PmCostCodeAssignmentCard";
import PmOperationalKPIs from "@/components/PmOperationalKPIs";
import {
  TransportationReadinessCard,
  TransportationRiskBanner,
  TransportationCloseoutAwareness,
} from "@/components/operations_transportation_integration";
import { sanitizeOperatorProjectNumber, sanitizeOperatorReference } from "@/lib/operatorLanguage";

const API = `${process.env.REACT_APP_BACKEND_URL || ""}/api`;

// Render YYYY-MM-DD for the local user's calendar day. Endpoint expects
// a literal YYYY-MM-DD path segment with no timezone qualifier.
function todayYyyyMmDd() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// Read-only project-day panel. Public endpoint · no auth headers needed.
// State machine:
//   loading  → fetching
//   error    → endpoint failed or returned ok=false
//   empty    → ok=true but assets.length===0 and total_events===0
//   data     → ok=true with assets to render
function ProjectDayEventsPanel({ projectNumber }) {
  const [date, setDate] = React.useState(todayYyyyMmDd());
  const [state, setState] = React.useState({ status: "loading", body: null, err: null });

  React.useEffect(() => {
    if (!projectNumber || !date) return undefined;
    let cancelled = false;
    // Reset to loading via a microtask so we don't call setState
    // synchronously inside the effect body.
    Promise.resolve().then(() => {
      if (!cancelled) setState({ status: "loading", body: null, err: null });
    });
    fetch(`${API}/operational-events/project-day/${encodeURIComponent(projectNumber)}/${encodeURIComponent(date)}`)
      .then(async (r) => {
        if (cancelled) return;
        if (!r.ok) {
          setState({ status: "error", body: null, err: `HTTP ${r.status}` });
          return;
        }
        const body = await r.json().catch(() => null);
        if (!body || body.ok !== true) {
          setState({ status: "error", body, err: "Bad response shape" });
          return;
        }
        setState({ status: "data", body, err: null });
      })
      .catch((e) => {
        if (cancelled) return;
        setState({ status: "error", body: null, err: e.message || "Fetch failed" });
      });
    return () => { cancelled = true; };
  }, [projectNumber, date]);

  const assets = state.body?.assets || [];
  const total = state.body?.total_events ?? 0;

  return (
    <section
      data-testid="pm-project-day-events-panel"
      className="bg-white border border-slate-200 rounded-md p-4 sm:p-6 mt-4"
    >
      <header className="flex items-baseline gap-2 flex-wrap">
        <Activity className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
        <h2 className="font-display text-base font-bold text-slate-900">
          Project-Day Events
        </h2>
        <span className="text-[11px] text-slate-500 italic">
          Daily operational activity for this project.
        </span>
        <label className="ml-auto inline-flex items-center gap-2 text-[11px] text-slate-600">
          <span className="font-mono uppercase tracking-wide">Day</span>
          <input
            data-testid="pm-project-day-events-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value || todayYyyyMmDd())}
            className="font-mono text-[11px] px-2 py-1 border border-slate-200 rounded bg-slate-50 text-slate-800"
          />
        </label>
      </header>

      <p className="text-[11px] text-slate-500 mt-2">
        Per-asset arrival and departure summary for the chosen day.
      </p>

      {state.status === "loading" && (
        <p data-testid="pm-project-day-events-loading" className="text-xs text-slate-500 mt-3">
          Loading project-day events…
        </p>
      )}

      {state.status === "error" && (
        <div
          data-testid="pm-project-day-events-error"
          className="mt-3 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2"
        >
          Project-day feed unavailable ({state.err || "unknown"}). No fabricated data is shown. Retry by reselecting the date.
        </div>
      )}

      {state.status === "data" && assets.length === 0 && (
        <div
          data-testid="pm-project-day-events-empty"
          className="mt-3 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded px-3 py-2"
        >
          No project-day events recorded on {date}. <span className="text-slate-400">total_events = {total}</span>
        </div>
      )}

      {state.status === "data" && assets.length > 0 && (
        <div className="mt-3 overflow-x-auto">
          <div className="text-[11px] text-slate-500 mb-2">
            <span data-testid="pm-project-day-events-count">
              {assets.length} asset(s) · {total} total event(s)
            </span>
          </div>
          <table
            data-testid="pm-project-day-events-table"
            className="w-full text-xs border-collapse"
          >
            <thead>
              <tr className="text-left text-[10px] uppercase tracking-wide text-slate-500 border-b border-slate-200">
                <th className="py-1.5 pr-3 font-mono">Asset</th>
                <th className="py-1.5 pr-3 font-mono">Kind</th>
                <th className="py-1.5 pr-3 font-mono">First seen</th>
                <th className="py-1.5 pr-3 font-mono">Last seen</th>
                <th className="py-1.5 pr-3 font-mono">Status</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((a) => (
                <tr
                  key={a.asset_key}
                  data-testid={`pm-project-day-events-row-${a.asset_key}`}
                  className="border-b border-slate-100 last:border-b-0"
                >
                  <td className="py-1.5 pr-3 font-mono text-slate-800">
                    {sanitizeOperatorReference(a.asset_label || a.asset_key, "Asset record")}
                  </td>
                  <td className="py-1.5 pr-3 text-slate-600">
                    {a.asset_kind || "—"}
                  </td>
                  <td className="py-1.5 pr-3 font-mono text-slate-700">
                    {a.first_seen || "—"}
                  </td>
                  <td className="py-1.5 pr-3 font-mono text-slate-700">
                    {a.last_seen || (a.still_on_site ? "—" : "—")}
                  </td>
                  <td className="py-1.5 pr-3">
                    {a.still_on_site ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold uppercase tracking-wide">
                        On site
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-slate-50 text-slate-600 border border-slate-200 text-[10px] font-bold uppercase tracking-wide">
                        Departed
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────
// Track 13.20 · Material Movement Ledger · Phase B · PM Project Panel
//
// Read-only, project-scoped material movement panel. Consumes the
// existing enriched endpoint added in Track 13.19:
//   GET /api/material-movement/daily/{project_number}/{date}
//
// Surfaces:
//   • verification_status (closed set: no_activity/verified/partial/missing_proof/needs_review)
//   • proof_summary counters
//   • rollups counters
//   • materials in/out (legacy incoming[]/outgoing[])
//   • haul_cycles[] (Phase A)
//   • scale_ticket_proofs[] (Phase A — Track 13.14 weights + net_tons)
//
// Hard rules:
//   • Project-scoped only. No company-wide view.
//   • No editing. No mutations. No new endpoint.
//   • Honest empty/error states. No fabricated counts.
//   • FleetWatcher field is rendered ONLY if source_breakdown emits it
//     and ONLY to confirm "not connected" — never inflated.
// ─────────────────────────────────────────────────────────────────

const STATUS_LABEL = {
  no_activity: "No activity",
  verified: "Verified",
  partial: "Partial proof",
  missing_proof: "Missing proof",
  needs_review: "Needs review",
  mismatch: "Mismatch",
};

const STATUS_TONE = {
  no_activity: "bg-slate-50 border-slate-200 text-slate-600",
  verified: "bg-emerald-50 border-emerald-200 text-emerald-800",
  partial: "bg-amber-50 border-amber-200 text-amber-800",
  missing_proof: "bg-rose-50 border-rose-200 text-rose-800",
  needs_review: "bg-amber-50 border-amber-200 text-amber-800",
  mismatch: "bg-rose-50 border-rose-200 text-rose-800",
};

function ProjectMaterialMovementPanel({ projectNumber }) {
  const [date, setDate] = React.useState(todayYyyyMmDd());
  const [state, setState] = React.useState({ status: "loading", body: null, err: null });

  React.useEffect(() => {
    if (!projectNumber || !date) return undefined;
    let cancelled = false;
    Promise.resolve().then(() => {
      if (!cancelled) setState({ status: "loading", body: null, err: null });
    });
    fetch(`${API}/material-movement/daily/${encodeURIComponent(projectNumber)}/${encodeURIComponent(date)}`)
      .then(async (r) => {
        if (cancelled) return;
        if (!r.ok) {
          setState({ status: "error", body: null, err: `HTTP ${r.status}` });
          return;
        }
        const body = await r.json().catch(() => null);
        if (!body || typeof body !== "object") {
          setState({ status: "error", body, err: "Bad response shape" });
          return;
        }
        setState({ status: "data", body, err: null });
      })
      .catch((e) => {
        if (cancelled) return;
        setState({ status: "error", body: null, err: e.message || "Fetch failed" });
      });
    return () => { cancelled = true; };
  }, [projectNumber, date]);

  const body = state.body || {};
  const verification = body.verification_status || "no_activity";
  const proofSummary = body.proof_summary || {};
  const rollups = body.rollups || {};
  const sourceBreakdown = body.source_breakdown || {};
  const incoming = Array.isArray(body.incoming) ? body.incoming : [];
  const outgoing = Array.isArray(body.outgoing) ? body.outgoing : [];
  const haulCycles = Array.isArray(body.haul_cycles) ? body.haul_cycles : [];
  const proofs = Array.isArray(body.scale_ticket_proofs) ? body.scale_ticket_proofs : [];

  const isEmpty =
    state.status === "data"
    && verification === "no_activity"
    && incoming.length === 0
    && outgoing.length === 0
    && haulCycles.length === 0
    && proofs.length === 0;

  return (
    <section
      data-testid="pm-project-material-movement-panel"
      className="bg-white border border-slate-200 rounded-md p-4 sm:p-6 mt-4"
    >
      <header className="flex items-baseline gap-2 flex-wrap">
        <Truck className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
        <h2 className="font-display text-base font-bold text-slate-900">
          Material Movement
        </h2>
        <span className="text-[11px] text-slate-500 italic">
          Project-scoped material in/out, haul cycles, and scale-ticket proof for the selected day.
        </span>
        <label className="ml-auto inline-flex items-center gap-2 text-[11px] text-slate-600">
          <span className="font-mono uppercase tracking-wide">Day</span>
          <input
            data-testid="pm-project-mm-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value || todayYyyyMmDd())}
            className="font-mono text-[11px] px-2 py-1 border border-slate-200 rounded bg-slate-50 text-slate-800"
          />
        </label>
      </header>

      <p className="text-[11px] text-slate-500 mt-2">
        Material movement for the chosen day — derived from daily reports, dispatch, haul cycles, and scale-ticket proof. No invented quantities.
      </p>

      {state.status === "loading" && (
        <p data-testid="pm-project-mm-loading" className="text-xs text-slate-500 mt-3">
          Loading material movement…
        </p>
      )}

      {state.status === "error" && (
        <div
          data-testid="pm-project-mm-error"
          className="mt-3 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2"
        >
          Material movement feed unavailable ({state.err || "unknown"}). No data invented. Retry by reselecting the date.
        </div>
      )}

      {state.status === "data" && isEmpty && (
        <div
          data-testid="pm-project-mm-empty"
          className="mt-3 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded px-3 py-2"
        >
          No material movement recorded for this project on this date.
        </div>
      )}

      {state.status === "data" && !isEmpty && (
        <>
          {/* Status row */}
          <div className="mt-3 flex flex-wrap items-center gap-2" data-testid="pm-project-mm-status-row">
            <span
              data-testid="pm-project-mm-verification-chip"
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-mono uppercase tracking-wide ${STATUS_TONE[verification] || STATUS_TONE.needs_review}`}
            >
              {verification === "verified" ? (
                <CheckCircle2 className="w-3 h-3" aria-hidden="true" />
              ) : verification === "missing_proof" || verification === "mismatch" ? (
                <AlertTriangle className="w-3 h-3" aria-hidden="true" />
              ) : (
                <FileCheck2 className="w-3 h-3" aria-hidden="true" />
              )}
              {STATUS_LABEL[verification] || verification}
            </span>
            <Counter testId="pm-project-mm-counter-tickets" label="Tickets" value={proofSummary.scale_ticket_count ?? 0} />
            <Counter testId="pm-project-mm-counter-missing" label="Missing proof" value={proofSummary.missing_proof_count ?? 0} tone={(proofSummary.missing_proof_count ?? 0) > 0 ? "rose" : "slate"} />
            <Counter testId="pm-project-mm-counter-cycles" label="Haul cycles" value={rollups.haul_cycles_count ?? haulCycles.length} />
            <Counter
              testId="pm-project-mm-counter-net-tons"
              label="Net tons (tickets)"
              value={rollups.net_tons_from_tickets != null ? rollups.net_tons_from_tickets : "—"}
            />
            <Counter testId="pm-project-mm-counter-trucks" label="Trucks" value={rollups.trucks_count ?? 0} />
          </div>

          {/* Materials In */}
          {incoming.length > 0 && (
            <div className="mt-4" data-testid="pm-project-mm-incoming">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-1">
                Materials In
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border border-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-2 py-1 text-left">Material</th>
                      <th className="px-2 py-1 text-left">Qty</th>
                      <th className="px-2 py-1 text-left">Unit</th>
                      <th className="px-2 py-1 text-left">Supplier</th>
                      <th className="px-2 py-1 text-left">Ticket #</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incoming.map((r, i) => (
                      <tr key={`in-${i}`} className="border-t border-slate-100" data-testid={`pm-project-mm-incoming-row-${i}`}>
                        <td className="px-2 py-1">{r.material || "—"}</td>
                        <td className="px-2 py-1">{r.quantity ?? ""}</td>
                        <td className="px-2 py-1">{r.unit || ""}</td>
                        <td className="px-2 py-1">{r.source || ""}</td>
                        <td className="px-2 py-1 text-slate-500 font-mono">{r.ticket_number || ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Materials Out */}
          {outgoing.length > 0 && (
            <div className="mt-4" data-testid="pm-project-mm-outgoing">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-1">
                Materials Out (Hauled Off)
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border border-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-2 py-1 text-left">Material</th>
                      <th className="px-2 py-1 text-left">Qty</th>
                      <th className="px-2 py-1 text-left">Unit</th>
                      <th className="px-2 py-1 text-left">Hauler</th>
                      <th className="px-2 py-1 text-left">Destination</th>
                      <th className="px-2 py-1 text-left">Ticket / Manifest</th>
                    </tr>
                  </thead>
                  <tbody>
                    {outgoing.map((r, i) => (
                      <tr key={`out-${i}`} className="border-t border-slate-100" data-testid={`pm-project-mm-outgoing-row-${i}`}>
                        <td className="px-2 py-1">{r.material || "—"}</td>
                        <td className="px-2 py-1">{r.quantity ?? ""}</td>
                        <td className="px-2 py-1">{r.unit || ""}</td>
                        <td className="px-2 py-1">{r.hauler || ""}</td>
                        <td className="px-2 py-1">{r.destination || ""}</td>
                        <td className="px-2 py-1 text-slate-500 font-mono">{r.ticket_or_manifest || ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Haul cycles */}
          {haulCycles.length > 0 && (
            <div className="mt-4" data-testid="pm-project-mm-haul-cycles">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-1">
                Haul Cycles · derived from dispatch completion
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border border-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-2 py-1 text-left">Truck</th>
                      <th className="px-2 py-1 text-left">Driver</th>
                      <th className="px-2 py-1 text-left">Material</th>
                      <th className="px-2 py-1 text-left">Haul type</th>
                      <th className="px-2 py-1 text-left">Source → Destination</th>
                      <th className="px-2 py-1 text-left">Completed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {haulCycles.map((c, i) => (
                      <tr key={`hc-${c.id || i}`} className="border-t border-slate-100" data-testid={`pm-project-mm-cycle-row-${i}`}>
                        <td className="px-2 py-1 font-mono">{c.truck_id || "—"}</td>
                        <td className="px-2 py-1">{sanitizeOperatorReference(c.driver_name, "")}</td>
                        <td className="px-2 py-1">{c.material || ""}</td>
                        <td className="px-2 py-1">{c.haul_type || "Material"}</td>
                        <td className="px-2 py-1 text-slate-600">{[c.source_location, c.destination].filter(Boolean).join(" → ") || ""}</td>
                        <td className="px-2 py-1 text-slate-500 font-mono">{c.completed_at ? c.completed_at.slice(11, 16) : ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Scale ticket proofs */}
          {proofs.length > 0 && (
            <div className="mt-4" data-testid="pm-project-mm-proofs">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-1">
                Scale-Ticket Proof
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border border-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-2 py-1 text-left">Type</th>
                      <th className="px-2 py-1 text-left">Truck</th>
                      <th className="px-2 py-1 text-left">Material code</th>
                      <th className="px-2 py-1 text-right">Gross lbs</th>
                      <th className="px-2 py-1 text-right">Tare lbs</th>
                      <th className="px-2 py-1 text-right">Net lbs</th>
                      <th className="px-2 py-1 text-right">Net tons</th>
                      <th className="px-2 py-1 text-left">Uploaded by</th>
                    </tr>
                  </thead>
                  <tbody>
                    {proofs.map((p, i) => (
                      <tr key={`pf-${p.id || i}`} className="border-t border-slate-100" data-testid={`pm-project-mm-proof-row-${i}`}>
                        <td className="px-2 py-1 font-mono text-[11px]">{p.type || "—"}</td>
                        <td className="px-2 py-1 font-mono">{p.truck_id || "—"}</td>
                        <td className="px-2 py-1 font-mono">{p.material_code || ""}</td>
                        <td className="px-2 py-1 text-right font-mono">{p.weight_gross_lbs ?? ""}</td>
                        <td className="px-2 py-1 text-right font-mono">{p.weight_tare_lbs ?? ""}</td>
                        <td className="px-2 py-1 text-right font-mono">{p.weight_net_lbs ?? ""}</td>
                        <td className="px-2 py-1 text-right font-mono">{p.net_tons ?? ""}</td>
                        <td className="px-2 py-1 text-slate-600">{p.uploaded_by || ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Source breakdown · trust line */}
          <p className="mt-4 text-[10px] text-slate-500 font-mono" data-testid="pm-project-mm-source-breakdown">
            Sources · daily_reports {sourceBreakdown.daily_reports ?? 0} · dispatch {sourceBreakdown.dispatch_assignments ?? 0} · haul_cycles {sourceBreakdown.haul_cycles ?? 0} · scale_tickets {sourceBreakdown.scale_tickets ?? 0} · fleetwatcher {sourceBreakdown.fleetwatcher ?? 0} (not connected)
          </p>
        </>
      )}
    </section>
  );
}

function Counter({ testId, label, value, tone }) {
  const toneClass =
    tone === "rose"
      ? "bg-rose-50 border-rose-200 text-rose-800"
      : "bg-slate-50 border-slate-200 text-slate-700";
  return (
    <span
      data-testid={testId}
      className={`inline-flex items-baseline gap-1 px-2 py-0.5 rounded border text-[11px] font-mono ${toneClass}`}
    >
      <span className="uppercase tracking-wide text-[10px] text-slate-500">{label}</span>
      <span className="font-bold">{value}</span>
    </span>
  );
}

export default function PmProjectDetail() {
  const { projectNumber } = useParams();
  const pn = (projectNumber || "").trim();
  const safePn = sanitizeOperatorProjectNumber(pn, "Operations support");

  return (
    <PmShell
      title="Project detail"
      section="jobs"
      intro={
        <p className="text-xs text-slate-500">
          Single-project chronology with job setup for cost-code assignments.
        </p>
      }
    >
      <div
        data-testid="pm-project-detail-page"
        className="bg-white border border-slate-200 rounded-md p-4 sm:p-6"
      >
        <header className="flex items-baseline gap-2 flex-wrap">
          <Briefcase className="w-4 h-4 text-slate-400 shrink-0" aria-hidden="true" />
          <span
            data-testid="pm-project-detail-number"
            className="font-mono font-bold text-slate-900 text-lg break-all"
          >
            {safePn || "—"}
          </span>
          {pn && (
            <Link
              to={`/pm/project/${encodeURIComponent(pn)}/thread`}
              data-testid="pm-project-detail-open-thread-link"
              className="ml-2 inline-flex items-center px-2.5 py-1 text-[11px] font-mono font-bold uppercase tracking-widest border-2 border-slate-300 hover:border-slate-900 text-slate-900 rounded"
            >
              Universal Thread
            </Link>
          )}
          <Link
            to="/pm/jobs"
            data-testid="pm-project-detail-back"
            className="ml-auto text-xs text-slate-500 hover:text-slate-800 underline-offset-2 hover:underline"
          >
            ← All jobs
          </Link>
        </header>
        <p className="text-xs text-slate-500 mt-1">
          Operational chronology for this project, plus the job-setup view for cost-code assignments.
        </p>
      </div>

      <OperationalTimelineSidecar projectNumber={pn} />

      {/* TRACK 23.7 · PM Operational KPIs — production intelligence,
          NO cost data. Consumes the shared aggregator spine used by
          Safety Portal and future Scheduling. */}
      {pn && <PmOperationalKPIs projectNumber={pn} />}

      {pn && (
        <div className="mt-4">
          <PmCostCodeAssignmentCard projectNumber={pn} />
        </div>
      )}

      {/* TRACK 16.16 · Operations × Transportation Integration Layer.
          Calm read-only awareness on the per-project workspace —
          the project workspace consumes Transportation, never the
          other way around. All four widgets share ONE fetch via
          useTransportationReadiness. */}
      {pn && (
        <div data-testid="pm-project-tx-integration" className="mt-4 space-y-3">
          <TransportationRiskBanner />
          <TransportationReadinessCard />
        </div>
      )}

      {/* Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE.
          Inline Project Team panel — always visible on PM Project Detail
          so PMs can manage staffing without leaving the project. */}
      {pn && (
        <div data-testid="pm-project-team-section" className="mt-4">
          <JobTeamRosterPanel projectNumber={pn} scope="pm" />
          <p className="mt-2 text-xs text-slate-500">
            <Link
              to={`/pm/job/${encodeURIComponent(pn)}/team`}
              className="text-amber-700 hover:text-amber-900 underline inline-flex items-center gap-1"
              data-testid="pm-project-team-full-page-link"
            >
              <Users className="w-3 h-3" /> Open dedicated Team page
              <ArrowRight className="w-3 h-3" />
            </Link>
          </p>
        </div>
      )}

      {/* Track 13.13 · Build Queue #4 — Operational Events Project-Day
          panel. Read-only · honest empty/error states · no charts ·
          no invented categories. Uses the live project-day activity feed. */}
      {pn && <ProjectDayEventsPanel projectNumber={pn} />}

      {/* Track 13.20 · Phase B · Material Movement Ledger PM panel.
          Read-only · project-scoped · honest empty/error states.
          Uses the live material-movement feed for the chosen project day. */}
      {pn && <ProjectMaterialMovementPanel projectNumber={pn} />}

      {/* Phase 4A — Trench Safety Operations Integration */}
      <TrenchSafetyOnProjectPanel projectNumber={pn} />

      {/* TRACK 16.16 · Project Closeout Awareness. Shows unresolved
          Transportation items or the calm "Transportation Complete"
          badge at the bottom of the project workspace. */}
      {pn && (
        <div data-testid="pm-project-tx-closeout" className="mt-4">
          <TransportationCloseoutAwareness />
        </div>
      )}
    </PmShell>
  );
}
