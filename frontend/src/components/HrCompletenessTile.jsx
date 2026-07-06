// TRACK 23.6 · HR Employee Record Completeness tile.
//
// Read-only check-engine light for whether Employee Lifecycle records
// carry the identity fields Daily Report autofill / HR Time
// Verification / Payroll Variance / PM Intelligence rely on.
//
// * Does NOT edit employee records.
// * Does NOT replace the Employee Lifecycle table.
// * Does NOT fire alerts.
// * Uses the shared normalized identity contract from Track 23.5
//   via `GET /api/hr/employee-completeness`.
//
// Auth: HR or Admin token. Sensitive HR fields never leak through
// this endpoint (server projection guarantees).
import React from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Download, FileText, X, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getHrToken } from "@/lib/hrAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BAND_STYLES = {
  green: {
    ring: "border-emerald-300 bg-emerald-50",
    dot: "bg-emerald-600",
    label: "text-emerald-900",
    icon: CheckCircle2,
  },
  amber: {
    ring: "border-amber-300 bg-amber-50",
    dot: "bg-amber-500",
    label: "text-amber-900",
    icon: AlertTriangle,
  },
  red: {
    ring: "border-rose-300 bg-rose-50",
    dot: "bg-rose-600",
    label: "text-rose-900",
    icon: AlertTriangle,
  },
};

function _authHeaders() {
  const h = {};
  const hr = getHrToken();
  if (hr) h["X-HR-Token"] = hr;
  if (typeof window !== "undefined" && window.localStorage) {
    const admin = window.localStorage.getItem("masci.admin.token");
    if (admin) h["X-Admin-Token"] = admin;
  }
  return h;
}

export default function HrCompletenessTile({ className = "" }) {
  const [snap, setSnap] = React.useState(null);
  const [err, setErr] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [filter, setFilter] = React.useState(""); // "" | trade_role | crew | supervisor
  const [includeInactive, setIncludeInactive] = React.useState(false);

  const load = React.useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const qs = new URLSearchParams();
      if (includeInactive) qs.set("include_inactive", "true");
      const r = await fetch(
        `${API}/hr/employee-completeness${qs.toString() ? "?" + qs.toString() : ""}`,
        { headers: _authHeaders() },
      );
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setSnap(await r.json());
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }, [includeInactive]);

  React.useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <section
        className={`rounded-lg border border-slate-200 bg-white p-5 ${className}`}
        data-testid="hr-completeness-tile-loading"
      >
        <div className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">
          Employee Record Completeness
        </div>
        <div className="mt-2 text-sm text-slate-400">Loading…</div>
      </section>
    );
  }

  if (err || !snap) {
    return (
      <section
        className={`rounded-lg border border-slate-200 bg-white p-5 ${className}`}
        data-testid="hr-completeness-tile-error"
      >
        <div className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">
          Employee Record Completeness
        </div>
        <div className="mt-2 text-sm text-rose-700">
          Unable to load ({err || "no data"})
        </div>
      </section>
    );
  }

  const band = BAND_STYLES[snap.status_band] || BAND_STYLES.amber;
  const BandIcon = band.icon;
  const displayedMissing = snap.missing_records.filter((r) => {
    if (!filter) return true;
    return r.missing_fields.includes(filter);
  });

  return (
    <section
      className={`rounded-lg border-2 ${band.ring} p-5 ${className}`}
      data-testid="hr-completeness-tile"
    >
      <div className="flex items-start gap-4">
        <div className={`shrink-0 w-10 h-10 rounded-full ${band.dot} text-white flex items-center justify-center`} aria-hidden>
          <BandIcon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-baseline gap-3">
            <h3
              className={`font-display text-lg font-black ${band.label}`}
              data-testid="hr-completeness-title"
            >
              Employee Record Completeness
            </h3>
            <span
              className={`font-mono text-xs uppercase tracking-[0.2em] ${band.label}`}
              data-testid="hr-completeness-band"
            >
              · {snap.status_band}
            </span>
            <span
              className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500"
              data-testid="hr-completeness-generated-at"
            >
              · Snapshot {snap.generated_at.slice(0, 19).replace("T", " ")} UTC
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Identity fields used by Daily Reports, HR, Payroll, and PM Intelligence.
          </p>

          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Metric label="Trade / Role"
              value={snap.trade_role_complete_count} total={snap.total_active}
              testid="hr-completeness-metric-trade" />
            <Metric label="Crew"
              value={snap.crew_complete_count} total={snap.total_active}
              testid="hr-completeness-metric-crew" />
            <Metric label="Supervisor"
              value={snap.supervisor_complete_count} total={snap.total_active}
              testid="hr-completeness-metric-supervisor" />
            <Metric label="Fully complete"
              value={snap.complete_count} total={snap.total_active}
              highlight
              percent={snap.completion_percent}
              testid="hr-completeness-metric-fully" />
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setDrawerOpen(true)}
              data-testid="hr-completeness-view-missing"
              className="text-xs"
            >
              <FileText className="w-3.5 h-3.5 mr-1" />
              View missing records ({snap.missing_records.length})
            </Button>
            <a
              href={`${API}/hr/employee-completeness.csv${includeInactive ? "?include_inactive=true" : ""}`}
              onClick={(e) => {
                // fetch with auth header, blob → download (browsers can't
                // send headers on <a href>). Fall back to plain nav if
                // fetch fails (older browsers).
                e.preventDefault();
                fetch(e.currentTarget.href, { headers: _authHeaders() })
                  .then((r) => r.blob())
                  .then((b) => {
                    const url = URL.createObjectURL(b);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "MASCI_Employee_Completeness.csv";
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                  })
                  .catch(() => { window.open(e.currentTarget.href, "_blank"); });
              }}
              className="inline-flex items-center gap-1 text-xs h-8 px-3 rounded-md border border-slate-300 bg-white hover:bg-slate-50 text-slate-700"
              data-testid="hr-completeness-export-csv"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </a>
            <label
              className="inline-flex items-center gap-1.5 text-xs text-slate-600 ml-2 select-none"
              data-testid="hr-completeness-include-inactive-label"
            >
              <input
                type="checkbox"
                checked={includeInactive}
                onChange={(e) => setIncludeInactive(e.target.checked)}
                className="rounded border-slate-300"
                data-testid="hr-completeness-include-inactive"
              />
              Include inactive
            </label>
            <Link
              to="/hr/employees"
              className="ml-auto text-xs text-blue-700 hover:underline inline-flex items-center gap-1"
              data-testid="hr-completeness-lifecycle-link"
            >
              Open Employee Lifecycle
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>

      {drawerOpen && (
        <MissingDrawer
          rows={displayedMissing}
          totalMissing={snap.missing_records.length}
          filter={filter}
          setFilter={setFilter}
          onClose={() => setDrawerOpen(false)}
        />
      )}
    </section>
  );
}

function Metric({ label, value, total, highlight = false, percent, testid }) {
  const pct = total ? Math.round((value / total) * 100) : 0;
  return (
    <div
      className={`rounded-md border ${highlight ? "border-slate-400 bg-white" : "border-slate-200 bg-white/70"} px-3 py-2`}
      data-testid={testid}
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className="mt-1 flex items-baseline gap-1.5">
        <span className="font-display text-2xl font-black text-slate-900">{value}</span>
        <span className="text-xs text-slate-500">/ {total}</span>
      </div>
      <div className="text-[11px] text-slate-500 mt-0.5">
        {percent !== undefined ? `${percent}%` : `${pct}%`}
      </div>
    </div>
  );
}

function MissingDrawer({ rows, totalMissing, filter, setFilter, onClose }) {
  return (
    <div
      className="fixed inset-0 z-40 bg-black/40 flex items-stretch justify-end"
      onClick={onClose}
      data-testid="hr-completeness-drawer-backdrop"
    >
      <div
        role="dialog"
        aria-label="Employee records missing HR identity fields"
        className="w-full max-w-3xl bg-white h-full overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        data-testid="hr-completeness-drawer"
      >
        <div className="sticky top-0 bg-white border-b border-slate-200 px-5 py-4 flex items-center gap-3">
          <div className="min-w-0 flex-1">
            <h4 className="font-display text-lg font-black">Employees Missing HR Identity Fields</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              {rows.length} of {totalMissing} shown · Read-only · Edit in Employee Lifecycle.
            </p>
          </div>
          <button
            type="button"
            className="rounded-md p-1.5 hover:bg-slate-100"
            onClick={onClose}
            aria-label="Close"
            data-testid="hr-completeness-drawer-close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-3 flex flex-wrap gap-2 border-b border-slate-100 bg-slate-50">
          <FilterChip active={filter === ""} onClick={() => setFilter("")} testid="hr-completeness-filter-all">All</FilterChip>
          <FilterChip active={filter === "trade_role"} onClick={() => setFilter("trade_role")} testid="hr-completeness-filter-trade">Missing Trade/Role</FilterChip>
          <FilterChip active={filter === "crew"} onClick={() => setFilter("crew")} testid="hr-completeness-filter-crew">Missing Crew</FilterChip>
          <FilterChip active={filter === "supervisor"} onClick={() => setFilter("supervisor")} testid="hr-completeness-filter-supervisor">Missing Supervisor</FilterChip>
        </div>

        {rows.length === 0 ? (
          <div className="p-8 text-sm text-slate-500 text-center" data-testid="hr-completeness-drawer-empty">
            No employees match this filter — nothing to clean up here.
          </div>
        ) : (
          <table className="w-full text-sm" data-testid="hr-completeness-drawer-table">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="text-left px-4 py-2 font-mono text-[10px] uppercase tracking-[0.14em]">Employee</th>
                <th className="text-left px-4 py-2 font-mono text-[10px] uppercase tracking-[0.14em]">Employee ID</th>
                <th className="text-left px-4 py-2 font-mono text-[10px] uppercase tracking-[0.14em]">Missing</th>
                <th className="text-left px-4 py-2 font-mono text-[10px] uppercase tracking-[0.14em]">Status</th>
                <th className="text-right px-4 py-2 font-mono text-[10px] uppercase tracking-[0.14em]">Open</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id || r.employee_id || r.name} data-testid={`hr-completeness-row-${r.id || r.employee_id || r.name}`} className="border-t border-slate-100">
                  <td className="px-4 py-2">
                    <div className="font-medium text-slate-900">{r.display_identity}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      {[
                        r.trade_role_display && `Trade: ${r.trade_role_display}`,
                        r.crew_display && `Crew: ${r.crew_display}`,
                        r.supervisor_display && `Sup: ${r.supervisor_display}`,
                      ].filter(Boolean).join(" · ") || "No HR identity fields set"}
                    </div>
                  </td>
                  <td className="px-4 py-2 font-mono text-xs text-slate-700">{r.employee_id || "—"}</td>
                  <td className="px-4 py-2">
                    <div className="flex flex-wrap gap-1">
                      {r.missing_fields.map((f) => (
                        <span
                          key={f}
                          className="inline-flex items-center rounded-full bg-rose-100 text-rose-800 text-[10px] font-bold uppercase tracking-wide px-2 py-0.5"
                        >
                          {f.replace("_", " ")}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-2 text-xs text-slate-600">{r.lifecycle_status}</td>
                  <td className="px-4 py-2 text-right">
                    <Link
                      to={`/hr/employees?focus=${encodeURIComponent(r.id || r.employee_id || r.name)}`}
                      className="inline-flex items-center gap-1 text-xs text-blue-700 hover:underline"
                    >
                      Edit <ExternalLink className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function FilterChip({ active, onClick, children, testid }) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testid}
      className={`text-xs px-3 py-1 rounded-full border ${
        active
          ? "bg-slate-900 text-white border-slate-900"
          : "bg-white text-slate-700 border-slate-300 hover:border-slate-400"
      }`}
    >
      {children}
    </button>
  );
}
