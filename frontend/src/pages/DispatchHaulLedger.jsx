// Track 13.21 · Phase C · Dispatch Companion Haul Ledger
//
// Route: /dispatch-portal/haul-ledger (dispatch + admin gated by RequireDispatch).
//
// Companion-only surface. The Dispatch MapLibre canvas at /dispatch-portal
// remains primary and hard-locked. This page is a date-range table view
// of company-wide material movement, loads, trucks, and scale-ticket proof.
//
// Consumes: GET /api/dispatch/haul-ledger (Phase C backend, read-only).
//
// Hard rules honored:
//   • No editing surface.
//   • No map mount.
//   • Project-scoped data is OPTIONAL via filter; default = company-wide.
//   • FleetWatcher line ALWAYS labeled "not connected" honestly.
//   • Empty + error states never invent data.

import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, Truck, FileCheck2, AlertTriangle, CheckCircle2,
  Search, RefreshCcw,
} from "lucide-react";
import { getDispatchToken } from "@/lib/dispatchAuth";
// TRACK 18.00 · Phase F · Transportation Operations unified branding.
import TransportationOpsTopBar from "@/components/transportation/TransportationOpsTopBar";

const API = `${process.env.REACT_APP_BACKEND_URL || ""}/api`;

function todayYyyyMmDd() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function daysAgoYyyyMmDd(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

const STATUS_LABEL = {
  no_activity: "No activity",
  verified: "Verified",
  partial: "Partial proof",
  missing_proof: "Missing proof",
  needs_review: "Needs review",
};

const STATUS_TONE = {
  verified: "bg-emerald-50 border-emerald-200 text-emerald-800",
  partial: "bg-amber-50 border-amber-200 text-amber-800",
  missing_proof: "bg-rose-50 border-rose-200 text-rose-800",
  needs_review: "bg-amber-50 border-amber-200 text-amber-800",
  no_activity: "bg-slate-50 border-slate-200 text-slate-600",
};

function StatusChip({ value, testId }) {
  const tone = STATUS_TONE[value] || STATUS_TONE.needs_review;
  const Icon = value === "verified" ? CheckCircle2 : (value === "missing_proof" ? AlertTriangle : FileCheck2);
  return (
    <span
      data-testid={testId}
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-mono uppercase tracking-wide ${tone}`}
    >
      <Icon className="w-3 h-3" aria-hidden="true" />
      {STATUS_LABEL[value] || value}
    </span>
  );
}

function Rollup({ label, value, tone = "slate", testId }) {
  const toneClass =
    tone === "rose"
      ? "bg-rose-50 border-rose-200 text-rose-900"
      : tone === "emerald"
      ? "bg-emerald-50 border-emerald-200 text-emerald-900"
      : "bg-white border-slate-200 text-slate-900";
  return (
    <div
      data-testid={testId}
      className={`rounded-md border px-3 py-2 ${toneClass}`}
    >
      <div className="text-[10px] font-mono uppercase tracking-wide text-slate-500">{label}</div>
      <div className="text-lg font-bold mt-0.5 font-mono">{value}</div>
    </div>
  );
}

export default function DispatchHaulLedger() {
  // Default = last 7 days (today inclusive) — common Dispatch lookback.
  const [dateFrom, setDateFrom] = React.useState(daysAgoYyyyMmDd(6));
  const [dateTo, setDateTo] = React.useState(todayYyyyMmDd());
  const [projectNumber, setProjectNumber] = React.useState("");
  const [materialCode, setMaterialCode] = React.useState("");
  const [truck, setTruck] = React.useState("");
  const [verification, setVerification] = React.useState("");
  const [state, setState] = React.useState({ status: "loading", body: null, err: null });
  const [reqId, setReqId] = React.useState(0);

  React.useEffect(() => {
    let cancelled = false;
    Promise.resolve().then(() => {
      if (!cancelled) setState({ status: "loading", body: null, err: null });
    });
    const params = new URLSearchParams();
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    if (projectNumber.trim()) params.set("project_number", projectNumber.trim());
    if (materialCode.trim()) params.set("material_code", materialCode.trim());
    if (truck.trim()) params.set("truck", truck.trim());
    if (verification) params.set("verification_status", verification);
    fetch(`${API}/dispatch/haul-ledger?${params.toString()}`, {
      headers: { "X-Dispatch-Token": getDispatchToken() },
    })
      .then(async (r) => {
        if (cancelled) return;
        if (!r.ok) {
          let detail = `HTTP ${r.status}`;
          try {
            const j = await r.json();
            if (j && j.detail) detail = `${detail} · ${j.detail}`;
          } catch { /* ignore */ }
          setState({ status: "error", body: null, err: detail });
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reqId]);

  const body = state.body || {};
  const rows = Array.isArray(body.rows) ? body.rows : [];
  const rollups = body.rollups || {};
  const byProject = Array.isArray(body.by_project) ? body.by_project : [];
  const byMaterial = Array.isArray(body.by_material) ? body.by_material : [];
  const sourceBreakdown = body.source_breakdown || {};

  return (
    <div className="min-h-screen bg-slate-50">
      <TransportationOpsTopBar />
      <header className="bg-white border-b border-slate-200 px-4 sm:px-6 py-3 flex items-center gap-3">
        <Link
          to="/dispatch-portal"
          data-testid="dispatch-haul-ledger-back"
          className="inline-flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          Back to Dispatch
        </Link>
        <Truck className="w-5 h-5 text-cyan-700 ml-2" aria-hidden="true" />
        <div>
          <h1 className="font-display text-base sm:text-lg font-bold text-slate-900" data-testid="dispatch-haul-ledger-title">
            Haul Ledger
          </h1>
          <p className="text-[11px] text-slate-500">
            Company-wide material movement, loads, trucks, and scale-ticket proof. Companion view — the live map remains primary at <Link to="/dispatch-portal" className="underline">/dispatch-portal</Link>.
          </p>
        </div>
        <button
          onClick={() => setReqId((x) => x + 1)}
          data-testid="dispatch-haul-ledger-refresh"
          className="ml-auto inline-flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900 border border-slate-200 rounded px-2 py-1"
        >
          <RefreshCcw className="w-3 h-3" aria-hidden="true" /> Refresh
        </button>
      </header>

      <main className="px-4 sm:px-6 py-4 max-w-7xl mx-auto">
        {/* Filters */}
        <section
          data-testid="dispatch-haul-ledger-filters"
          className="bg-white border border-slate-200 rounded-md p-3 sm:p-4 mb-4"
        >
          <div className="flex flex-wrap gap-3 items-end">
            <Field label="From" testId="dispatch-haul-ledger-from">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value || todayYyyyMmDd())}
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50"
                data-testid="dispatch-haul-ledger-from-input"
              />
            </Field>
            <Field label="To" testId="dispatch-haul-ledger-to">
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value || todayYyyyMmDd())}
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50"
                data-testid="dispatch-haul-ledger-to-input"
              />
            </Field>
            <Field label="Project #" testId="dispatch-haul-ledger-project">
              <input
                type="text"
                value={projectNumber}
                onChange={(e) => setProjectNumber(e.target.value)}
                placeholder="all"
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50 w-28"
                data-testid="dispatch-haul-ledger-project-input"
              />
            </Field>
            <Field label="Material code" testId="dispatch-haul-ledger-material">
              <input
                type="text"
                value={materialCode}
                onChange={(e) => setMaterialCode(e.target.value)}
                placeholder="all"
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50 w-28"
                data-testid="dispatch-haul-ledger-material-input"
              />
            </Field>
            <Field label="Truck" testId="dispatch-haul-ledger-truck">
              <input
                type="text"
                value={truck}
                onChange={(e) => setTruck(e.target.value)}
                placeholder="all"
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50 w-28"
                data-testid="dispatch-haul-ledger-truck-input"
              />
            </Field>
            <Field label="Verification" testId="dispatch-haul-ledger-verification">
              <select
                value={verification}
                onChange={(e) => setVerification(e.target.value)}
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50"
                data-testid="dispatch-haul-ledger-verification-select"
              >
                <option value="">all</option>
                <option value="verified">verified</option>
                <option value="missing_proof">missing_proof</option>
                <option value="partial">partial</option>
                <option value="needs_review">needs_review</option>
              </select>
            </Field>
            <button
              onClick={() => setReqId((x) => x + 1)}
              data-testid="dispatch-haul-ledger-apply"
              className="inline-flex items-center gap-1 text-xs bg-cyan-700 text-white rounded px-3 py-1.5 hover:bg-cyan-800"
            >
              <Search className="w-3 h-3" aria-hidden="true" /> Apply
            </button>
          </div>
          <p className="text-[10px] text-slate-500 font-mono mt-2">
            Source: <code>/api/dispatch/haul-ledger</code> · derived view across haul_cycles · dispatch_assignments · operational_attachments · daily_reports. Max 90-day window. No fabricated quantities.
          </p>
        </section>

        {/* Rollups */}
        {state.status === "data" && (
          <section
            data-testid="dispatch-haul-ledger-rollups"
            className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 mb-4"
          >
            <Rollup testId="dispatch-haul-ledger-rollup-loads" label="Loads" value={rollups.loads_count ?? 0} />
            <Rollup testId="dispatch-haul-ledger-rollup-cycles" label="Haul cycles" value={rollups.haul_cycles_count ?? 0} />
            <Rollup testId="dispatch-haul-ledger-rollup-tickets" label="Scale tickets" value={rollups.scale_ticket_count ?? 0} />
            <Rollup
              testId="dispatch-haul-ledger-rollup-missing"
              label="Missing proof"
              value={rollups.missing_proof_count ?? 0}
              tone={(rollups.missing_proof_count ?? 0) > 0 ? "rose" : "slate"}
            />
            <Rollup
              testId="dispatch-haul-ledger-rollup-net-tons"
              label="Net tons (tickets)"
              value={rollups.net_tons != null ? rollups.net_tons : "—"}
            />
            <Rollup testId="dispatch-haul-ledger-rollup-projects" label="Projects" value={rollups.projects_count ?? 0} />
            <Rollup testId="dispatch-haul-ledger-rollup-trucks" label="Trucks" value={rollups.trucks_count ?? 0} />
            <Rollup testId="dispatch-haul-ledger-rollup-materials" label="Materials" value={rollups.materials_count ?? 0} />
            <Rollup testId="dispatch-haul-ledger-rollup-dr-in" label="DR rows · in" value={rollups.dr_inbound_count ?? 0} />
            <Rollup testId="dispatch-haul-ledger-rollup-dr-out" label="DR rows · out" value={rollups.dr_outbound_count ?? 0} />
          </section>
        )}

        {/* Loading / Error / Empty */}
        {state.status === "loading" && (
          <p data-testid="dispatch-haul-ledger-loading" className="text-xs text-slate-500 mt-3">
            Loading haul ledger…
          </p>
        )}
        {state.status === "error" && (
          <div
            data-testid="dispatch-haul-ledger-error"
            className="mt-3 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2"
          >
            Haul ledger feed unavailable ({state.err || "unknown"}). No data invented. Retry by changing the date range or clicking Apply.
          </div>
        )}
        {state.status === "data" && rows.length === 0 && (
          <div
            data-testid="dispatch-haul-ledger-empty"
            className="mt-3 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded px-3 py-2"
          >
            No haul ledger activity for this range.
          </div>
        )}

        {/* Main rows table */}
        {state.status === "data" && rows.length > 0 && (
          <section className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid="dispatch-haul-ledger-table">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-2 py-2 text-left">Date</th>
                    <th className="px-2 py-2 text-left">Project</th>
                    <th className="px-2 py-2 text-left">Material</th>
                    <th className="px-2 py-2 text-left">Truck</th>
                    <th className="px-2 py-2 text-left">Driver</th>
                    <th className="px-2 py-2 text-left">Source → Destination</th>
                    <th className="px-2 py-2 text-right">Tickets</th>
                    <th className="px-2 py-2 text-right">Net tons</th>
                    <th className="px-2 py-2 text-left">Verification</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr
                      key={`hl-${r.haul_cycle_id || i}`}
                      data-testid={`dispatch-haul-ledger-row-${i}`}
                      className="border-t border-slate-100 hover:bg-slate-50/60"
                    >
                      <td className="px-2 py-1.5 font-mono">{r.date || "—"}</td>
                      <td className="px-2 py-1.5">
                        <span className="font-mono">{r.project_number || "—"}</span>
                        {r.project_name ? <span className="text-slate-500 ml-2 truncate inline-block max-w-[180px] align-middle">{r.project_name}</span> : null}
                      </td>
                      <td className="px-2 py-1.5">
                        {r.material_code ? <span className="font-mono mr-1">{r.material_code}</span> : null}
                        <span className="text-slate-700">{r.material_description || "—"}</span>
                      </td>
                      <td className="px-2 py-1.5 font-mono">{r.truck_id || "—"}</td>
                      <td className="px-2 py-1.5">{r.driver_name || "—"}</td>
                      <td className="px-2 py-1.5 text-slate-600">{[r.source_location, r.destination_location].filter(Boolean).join(" → ") || "—"}</td>
                      <td className="px-2 py-1.5 text-right font-mono">{r.scale_ticket_count ?? 0}</td>
                      <td className="px-2 py-1.5 text-right font-mono">{r.net_tons != null ? r.net_tons : "—"}</td>
                      <td className="px-2 py-1.5"><StatusChip value={r.verification_status} testId={`dispatch-haul-ledger-row-${i}-status`} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Per-project breakdown */}
        {state.status === "data" && byProject.length > 0 && (
          <section className="bg-white border border-slate-200 rounded-md p-3 sm:p-4 mt-4" data-testid="dispatch-haul-ledger-by-project">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-2">
              By Project
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-2 py-1 text-left">Project #</th>
                    <th className="px-2 py-1 text-right">Loads</th>
                    <th className="px-2 py-1 text-right">Tickets</th>
                    <th className="px-2 py-1 text-right">Missing proof</th>
                  </tr>
                </thead>
                <tbody>
                  {byProject.slice(0, 20).map((p, i) => (
                    <tr key={`bp-${p.project_number}`} className="border-t border-slate-100" data-testid={`dispatch-haul-ledger-by-project-row-${i}`}>
                      <td className="px-2 py-1 font-mono">{p.project_number}</td>
                      <td className="px-2 py-1 text-right font-mono">{p.loads}</td>
                      <td className="px-2 py-1 text-right font-mono">{p.ticket_count}</td>
                      <td className={`px-2 py-1 text-right font-mono ${p.missing_proof > 0 ? "text-rose-700" : ""}`}>{p.missing_proof}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Per-material breakdown */}
        {state.status === "data" && byMaterial.length > 0 && (
          <section className="bg-white border border-slate-200 rounded-md p-3 sm:p-4 mt-4" data-testid="dispatch-haul-ledger-by-material">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-2">
              By Material
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-2 py-1 text-left">Material</th>
                    <th className="px-2 py-1 text-right">Loads</th>
                    <th className="px-2 py-1 text-right">Tickets</th>
                  </tr>
                </thead>
                <tbody>
                  {byMaterial.slice(0, 20).map((m, i) => (
                    <tr key={`bm-${m.material}`} className="border-t border-slate-100" data-testid={`dispatch-haul-ledger-by-material-row-${i}`}>
                      <td className="px-2 py-1">{m.material}</td>
                      <td className="px-2 py-1 text-right font-mono">{m.loads}</td>
                      <td className="px-2 py-1 text-right font-mono">{m.ticket_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Trust footer */}
        <footer className="mt-6 text-[10px] text-slate-500 font-mono space-y-1" data-testid="dispatch-haul-ledger-footer">
          {state.status === "data" && (
            <p>
              Sources · haul_cycles {sourceBreakdown.haul_cycles ?? 0} · scale_tickets {sourceBreakdown.scale_tickets ?? 0} · daily_reports_in {sourceBreakdown.daily_reports_in ?? 0} · daily_reports_out {sourceBreakdown.daily_reports_out ?? 0} · fleetwatcher {sourceBreakdown.fleetwatcher ?? 0}
            </p>
          )}
          <p data-testid="dispatch-haul-ledger-fleetwatcher-trust">
            FleetWatcher not connected — ledger is currently based on MASCI daily reports, dispatch haul cycles, and scale-ticket attachments. No accounting, cost, or pay-quantity totals are computed by this surface.
          </p>
        </footer>
      </main>
    </div>
  );
}

function Field({ label, testId, children }) {
  return (
    <label className="inline-flex flex-col gap-1 text-[10px] uppercase tracking-wide text-slate-500 font-mono" data-testid={testId}>
      <span>{label}</span>
      {children}
    </label>
  );
}
