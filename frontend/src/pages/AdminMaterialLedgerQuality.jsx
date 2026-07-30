// Track 13.22 · Phase D · Admin Material Ledger Data-Quality + CSV Export
//
// Route: /admin/material-ledger-quality (admin-gated via RequireAdmin).
//
// Admin-facing surface focused on operational data-quality of the Material
// Movement Ledger:
//   • missing proof
//   • partial proof
//   • needs-review rows
//   • per-project / per-material / per-truck breakdowns
//   • CSV export
//
// Reuses the dispatch+admin gated endpoint introduced in Track 13.21:
//   GET /api/dispatch/haul-ledger
// Track 13.22 extended that endpoint with `format=csv` for the export
// pathway. NO new collection. NO cost / accounting / pay / contract fields.

import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, Truck, FileCheck2, AlertTriangle, CheckCircle2,
  Search, RefreshCcw, Download,
} from "lucide-react";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";

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

function Field({ label, testId, children }) {
  return (
    <label className="inline-flex flex-col gap-1 text-[10px] uppercase tracking-wide text-slate-500 font-mono" data-testid={testId}>
      <span>{label}</span>
      {children}
    </label>
  );
}

export default function AdminMaterialLedgerQuality() {
  // Admin default focus: last 30 days, verification_status = missing_proof.
  const [dateFrom, setDateFrom] = React.useState(daysAgoYyyyMmDd(29));
  const [dateTo, setDateTo] = React.useState(todayYyyyMmDd());
  const [projectNumber, setProjectNumber] = React.useState("");
  const [materialCode, setMaterialCode] = React.useState("");
  const [truck, setTruck] = React.useState("");
  const [verification, setVerification] = React.useState("missing_proof");
  const [state, setState] = React.useState({ status: "loading", body: null, err: null });
  const [reqId, setReqId] = React.useState(0);

  // Build the query string ONCE per render so the CSV link and the JSON
  // fetch always agree on filters.
  const buildParams = React.useCallback(() => {
    const p = new URLSearchParams();
    if (dateFrom) p.set("date_from", dateFrom);
    if (dateTo) p.set("date_to", dateTo);
    if (projectNumber.trim()) p.set("project_number", projectNumber.trim());
    if (materialCode.trim()) p.set("material_code", materialCode.trim());
    if (truck.trim()) p.set("truck", truck.trim());
    if (verification) p.set("verification_status", verification);
    return p;
  }, [dateFrom, dateTo, projectNumber, materialCode, truck, verification]);

  React.useEffect(() => {
    let cancelled = false;
    Promise.resolve().then(() => {
      if (!cancelled) setState({ status: "loading", body: null, err: null });
    });
    const params = buildParams();
    fetch(`${API}/dispatch/haul-ledger?${params.toString()}`, {
      headers: buildScopedPortalAuthHeaders(["admin"]),
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
   
  }, [buildParams, reqId]);

  const downloadCsv = React.useCallback(async () => {
    try {
      const params = buildParams();
      params.set("format", "csv");
      const res = await fetch(`${API}/dispatch/haul-ledger?${params.toString()}`, {
        headers: buildScopedPortalAuthHeaders(["admin"]),
      });
      if (!res.ok) {
        alert(`Export failed · HTTP ${res.status}`);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const fname = `masci_haul_ledger_${dateFrom}_to_${dateTo}.csv`;
      a.download = fname;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Export failed · ${e.message || e}`);
    }
  }, [buildParams, dateFrom, dateTo]);

  const body = state.body || {};
  const rows = Array.isArray(body.rows) ? body.rows : [];
  const rollups = body.rollups || {};
  const byProject = Array.isArray(body.by_project) ? body.by_project : [];
  const byMaterial = Array.isArray(body.by_material) ? body.by_material : [];
  const sourceBreakdown = body.source_breakdown || {};

  const content = (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-4 sm:px-6 py-3 flex items-center gap-3">
        <Link
          to="/admin"
          data-testid="admin-mlq-back"
          className="inline-flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          Back to Admin
        </Link>
        <Truck className="w-5 h-5 text-slate-700 ml-2" aria-hidden="true" />
        <div>
          <h1 className="font-display text-base sm:text-lg font-bold text-slate-900" data-testid="admin-mlq-title">
            Material Ledger Quality
          </h1>
          <p className="text-[11px] text-slate-500">
            Company-wide data-quality view over the Material Movement Ledger. Read-only · operational rows only · no cost / accounting / pay-app / contract fields.
          </p>
        </div>
        <button
          onClick={() => setReqId((x) => x + 1)}
          data-testid="admin-mlq-refresh"
          className="ml-auto inline-flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900 border border-slate-200 rounded px-2 py-1"
        >
          <RefreshCcw className="w-3 h-3" aria-hidden="true" /> Refresh
        </button>
        <button
          onClick={downloadCsv}
          data-testid="admin-mlq-export-csv"
          className="inline-flex items-center gap-1 text-xs bg-slate-900 text-white rounded px-3 py-1.5 hover:bg-slate-800"
        >
          <Download className="w-3 h-3" aria-hidden="true" /> Export CSV
        </button>
      </header>

      <main className="px-4 sm:px-6 py-4 max-w-7xl mx-auto">
        {/* Filters */}
        <section
          data-testid="admin-mlq-filters"
          className="bg-white border border-slate-200 rounded-md p-3 sm:p-4 mb-4"
        >
          <div className="flex flex-wrap gap-3 items-end">
            <Field label="From" testId="admin-mlq-from">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value || todayYyyyMmDd())}
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50"
                data-testid="admin-mlq-from-input"
              />
            </Field>
            <Field label="To" testId="admin-mlq-to">
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value || todayYyyyMmDd())}
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50"
                data-testid="admin-mlq-to-input"
              />
            </Field>
            <Field label="Project #" testId="admin-mlq-project">
              <input
                type="text"
                value={projectNumber}
                onChange={(e) => setProjectNumber(e.target.value)}
                placeholder="all"
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50 w-28"
                data-testid="admin-mlq-project-input"
              />
            </Field>
            <Field label="Material code" testId="admin-mlq-material">
              <input
                type="text"
                value={materialCode}
                onChange={(e) => setMaterialCode(e.target.value)}
                placeholder="all"
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50 w-28"
                data-testid="admin-mlq-material-input"
              />
            </Field>
            <Field label="Truck" testId="admin-mlq-truck">
              <input
                type="text"
                value={truck}
                onChange={(e) => setTruck(e.target.value)}
                placeholder="all"
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50 w-28"
                data-testid="admin-mlq-truck-input"
              />
            </Field>
            <Field label="Verification" testId="admin-mlq-verification">
              <select
                value={verification}
                onChange={(e) => setVerification(e.target.value)}
                className="font-mono text-xs px-2 py-1 border border-slate-200 rounded bg-slate-50"
                data-testid="admin-mlq-verification-select"
              >
                <option value="missing_proof">missing_proof (default)</option>
                <option value="partial">partial</option>
                <option value="needs_review">needs_review</option>
                <option value="verified">verified</option>
                <option value="">all</option>
              </select>
            </Field>
            <button
              onClick={() => setReqId((x) => x + 1)}
              data-testid="admin-mlq-apply"
              className="inline-flex items-center gap-1 text-xs bg-slate-900 text-white rounded px-3 py-1.5 hover:bg-slate-800"
            >
              <Search className="w-3 h-3" aria-hidden="true" /> Apply
            </button>
          </div>
          <p className="text-[10px] text-slate-500 font-mono mt-2">
            Source: <code>/api/dispatch/haul-ledger</code> (dispatch+admin gated) · CSV export at the same path with <code>format=csv</code>. Max 90-day window. No fabricated quantities.
          </p>
        </section>

        {/* Rollups */}
        {state.status === "data" && (
          <section
            data-testid="admin-mlq-rollups"
            className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 mb-4"
          >
            <Rollup testId="admin-mlq-rollup-cycles" label="Haul cycles" value={rollups.haul_cycles_count ?? 0} />
            <Rollup testId="admin-mlq-rollup-loads" label="Loads (filtered)" value={rollups.loads_count ?? 0} />
            <Rollup
              testId="admin-mlq-rollup-missing"
              label="Missing proof"
              value={rollups.missing_proof_count ?? 0}
              tone={(rollups.missing_proof_count ?? 0) > 0 ? "rose" : "slate"}
            />
            <Rollup testId="admin-mlq-rollup-tickets" label="Scale tickets" value={rollups.scale_ticket_count ?? 0} />
            <Rollup
              testId="admin-mlq-rollup-net-tons"
              label="Net tons (tickets)"
              value={rollups.net_tons != null ? rollups.net_tons : "—"}
            />
            <Rollup testId="admin-mlq-rollup-projects" label="Projects" value={rollups.projects_count ?? 0} />
            <Rollup testId="admin-mlq-rollup-trucks" label="Trucks" value={rollups.trucks_count ?? 0} />
            <Rollup testId="admin-mlq-rollup-materials" label="Materials" value={rollups.materials_count ?? 0} />
            <Rollup testId="admin-mlq-rollup-dr-in" label="DR rows · in" value={rollups.dr_inbound_count ?? 0} />
            <Rollup testId="admin-mlq-rollup-dr-out" label="DR rows · out" value={rollups.dr_outbound_count ?? 0} />
          </section>
        )}

        {state.status === "loading" && (
          <p data-testid="admin-mlq-loading" className="text-xs text-slate-500 mt-3">
            Loading material ledger data-quality view…
          </p>
        )}
        {state.status === "error" && (
          <div
            data-testid="admin-mlq-error"
            className="mt-3 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2"
          >
            Material ledger data-quality feed unavailable ({state.err || "unknown"}). No data invented. Retry by changing the date range or clicking Apply.
          </div>
        )}
        {state.status === "data" && rows.length === 0 && (
          <div
            data-testid="admin-mlq-empty"
            className="mt-3 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded px-3 py-2"
          >
            No material ledger issues for this range.
          </div>
        )}

        {/* Main rows table — admin focuses on filtered rows (default missing_proof) */}
        {state.status === "data" && rows.length > 0 && (
          <section className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid="admin-mlq-table">
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
                      key={`mlq-${r.haul_cycle_id || i}`}
                      data-testid={`admin-mlq-row-${i}`}
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
                      <td className="px-2 py-1.5"><StatusChip value={r.verification_status} testId={`admin-mlq-row-${i}-status`} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* By Project */}
        {state.status === "data" && byProject.length > 0 && (
          <section className="bg-white border border-slate-200 rounded-md p-3 sm:p-4 mt-4" data-testid="admin-mlq-by-project">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-2">
              By Project · sorted by load count
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
                  {byProject.slice(0, 25).map((p, i) => (
                    <tr key={`mlq-bp-${p.project_number}`} className="border-t border-slate-100" data-testid={`admin-mlq-by-project-row-${i}`}>
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

        {/* By Material */}
        {state.status === "data" && byMaterial.length > 0 && (
          <section className="bg-white border border-slate-200 rounded-md p-3 sm:p-4 mt-4" data-testid="admin-mlq-by-material">
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
                  {byMaterial.slice(0, 25).map((m, i) => (
                    <tr key={`mlq-bm-${m.material}`} className="border-t border-slate-100" data-testid={`admin-mlq-by-material-row-${i}`}>
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
        <footer className="mt-6 text-[10px] text-slate-500 font-mono space-y-1" data-testid="admin-mlq-footer">
          {state.status === "data" && (
            <p>
              Sources · haul_cycles {sourceBreakdown.haul_cycles ?? 0} · scale_tickets {sourceBreakdown.scale_tickets ?? 0} · daily_reports_in {sourceBreakdown.daily_reports_in ?? 0} · daily_reports_out {sourceBreakdown.daily_reports_out ?? 0} · fleetwatcher {sourceBreakdown.fleetwatcher ?? 0}
            </p>
          )}
          <p data-testid="admin-mlq-fleetwatcher-trust">
            FleetWatcher not connected — admin view is currently based on MASCI daily reports, dispatch haul cycles, and scale-ticket attachments. No accounting, cost, pay-quantity, or contract totals are computed by this surface.
          </p>
        </footer>
      </main>
    </div>
  );

  return (
    <AdminRouteShell
      pageTitle="Material Ledger Quality"
      subtitle="Admin data-quality view over dispatch haul proof, gaps, and review-ready rows."
      portalRole="Admin · Material Ledger"
      crumbs={[
        { label: "Operations Control" },
        { label: "Material Ledger Quality" },
      ]}
      contentClassName="px-0 py-0"
      testId="admin-material-ledger-quality-shell"
    >
      {content}
    </AdminRouteShell>
  );
}
