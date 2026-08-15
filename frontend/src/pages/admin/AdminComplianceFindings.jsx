// Phase 2 P0 · Compliance Findings list
// Route: /admin/compliance-findings · admin-strict gate
//
// Surfaces every cross-portal contradiction the detection engine has flagged.
// Supports filters by severity / status / rule_id / category / text search.
// Admin can acknowledge or resolve a finding inline (with optional note).

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, Link, useNavigate } from "react-router-dom";
import {
  ShieldCheck, AlertOctagon, AlertTriangle, Activity, CheckCircle2,
  Search, RefreshCw, X, ArrowLeft,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import AdminShell from "@/components/AdminShell";
import { LifecycleGuide } from "@/components/LifecycleGuide";
import { api } from "@/lib/api";
import { operationalError } from "@/lib/errors";
import { usePageTitle } from "@/lib/usePageTitle";
import { toast } from "sonner";

const SEVERITY_META = {
  critical: { icon: AlertOctagon,  text: "text-rose-900",  bg: "bg-rose-100",  border: "border-rose-300" },
  high:     { icon: AlertTriangle, text: "text-amber-900", bg: "bg-amber-100", border: "border-amber-300" },
  medium:   { icon: Activity,      text: "text-yellow-900", bg: "bg-yellow-100", border: "border-yellow-300" },
  low:      { icon: ShieldCheck,   text: "text-sky-900",   bg: "bg-sky-100",   border: "border-sky-300" },
  info:     { icon: CheckCircle2,  text: "text-slate-700", bg: "bg-slate-100", border: "border-slate-300" },
};

function SeverityBadge({ severity }) {
  const meta = SEVERITY_META[severity] || SEVERITY_META.info;
  const Icon = meta.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 border rounded text-[10px] font-mono uppercase tracking-wider ${meta.bg} ${meta.text} ${meta.border}`}>
      <Icon className="w-3 h-3" />{severity}
    </span>
  );
}

function StatusBadge({ status }) {
  const tints = {
    open: "bg-rose-100 text-rose-900 border-rose-300",
    acknowledged: "bg-amber-100 text-amber-900 border-amber-300",
    resolved: "bg-emerald-100 text-emerald-900 border-emerald-300",
  };
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 border rounded text-[10px] font-mono uppercase tracking-wider ${tints[status] || "bg-slate-50 border-slate-300"}`}>
      {status}
    </span>
  );
}

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

export default function AdminComplianceFindings() {
  usePageTitle("Compliance Findings · Admin");
  const qs = useQuery();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [sevTotals, setSevTotals] = useState({});
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const [filters, setFilters] = useState({
    severity: qs.get("severity") || "",
    status: qs.get("status") || "",
    rule_id: qs.get("rule_id") || "",
    category: qs.get("category") || "",
    q: qs.get("q") || "",
  });

  const [actionTarget, setActionTarget] = useState(null); // {finding, mode}
  const [actionNote, setActionNote] = useState("");
  const [actionSubmitting, setActionSubmitting] = useState(false);

  const buildQuery = useCallback(() => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v) params.set(k, v);
    });
    return params.toString();
  }, [filters]);

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try {
      const qStr = buildQuery();
      const sep = qStr ? "?" + qStr + "&" : "?";
      const { data } = await api.get(`/admin/compliance/findings${sep}limit=1000`);
      setItems(data?.items || []);
      setTotal(typeof data?.total === "number" ? data.total : (data?.items || []).length);
      setSevTotals(data?.severity_totals || {});
    } catch (e) {
      setErr(operationalError(e, "Could not load findings."));
    } finally {
      setLoading(false);
    }
  }, [buildQuery]);

  useEffect(() => { load(); }, [load]);

  // Sync the active filters into the URL bar so deep-links work.
  useEffect(() => {
    const qStr = buildQuery();
    navigate(`/admin/compliance-findings${qStr ? "?" + qStr : ""}`, { replace: true });
  }, [filters, buildQuery, navigate]);

  const updateFilter = (k, v) => setFilters((f) => ({ ...f, [k]: v }));
  const clearFilters = () => setFilters({ severity: "", status: "", rule_id: "", category: "", q: "" });
  const anyFilterActive = Object.values(filters).some(Boolean);

  const grouped = useMemo(() => {
    const by = { critical: [], high: [], medium: [], low: [], info: [] };
    items.forEach((it) => {
      const s = it.severity || "info";
      (by[s] || by.info).push(it);
    });
    return by;
  }, [items]);

  const openAction = (finding, mode) => {
    setActionTarget({ finding, mode });
    setActionNote("");
  };

  const submitAction = async () => {
    if (!actionTarget) return;
    setActionSubmitting(true);
    try {
      const { finding, mode } = actionTarget;
      await api.post(`/admin/compliance/findings/${finding.id}/${mode}`, { note: actionNote.trim() || null });
      toast.success(`Finding ${mode === "acknowledge" ? "acknowledged" : "resolved"}.`);
      setActionTarget(null);
      setActionNote("");
      await load();
    } catch (e) {
      toast.error(operationalError(e, "Action failed."));
    } finally {
      setActionSubmitting(false);
    }
  };

  return (
    <AdminShell
      title="Compliance Findings"
      section="governance"
      intro={
        <div className="flex items-start gap-3">
          <Link to="/admin/governance/legacy-health" className="text-xs text-slate-600 hover:text-slate-900 inline-flex items-center gap-1 mt-1" data-testid="findings-back-to-dashboard">
            <ArrowLeft className="w-3 h-3" /> Governance Health
          </Link>
        </div>
      }
    >
      <div className="space-y-4 mt-5" data-testid="admin-compliance-findings">
        {/* iter367 · operational coaching uniformity — short, field-direct.
            Admin page convention is English-only (no t() wrapper), matching
            the rest of /admin/*. */}
        <LifecycleGuide
          id="admin-compliance-findings"
          icon={AlertOctagon}
          accent="rose"
          title="How findings work"
          summary="Live contradictions detected across portals. Acknowledge to silence; resolve to mark fixed in source."
          sections={[
            { label: "Why this matters", body: "Each finding maps to a specific detector rule (CAPA overdue, identity drift, expired CDL, etc). A clean board here means cross-portal accountability is healthy." },
            { label: "Lifecycle", body: "Open → Acknowledged (silenced, still visible) → Resolved (marked fixed). Findings auto-disappear when the underlying condition is corrected at the source." },
          ]}
        />

        {/* Filter bar */}
        <div className="bg-white border border-slate-200 rounded-md p-3 space-y-3" data-testid="findings-filter-bar">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">Severity</label>
              <select
                value={filters.severity}
                onChange={(e) => updateFilter("severity", e.target.value)}
                className="w-full h-9 text-sm border border-slate-300 rounded px-2"
                data-testid="findings-filter-severity"
              >
                <option value="">All</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
                <option value="info">Info</option>
              </select>
            </div>
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">Status</label>
              <select
                value={filters.status}
                onChange={(e) => updateFilter("status", e.target.value)}
                className="w-full h-9 text-sm border border-slate-300 rounded px-2"
                data-testid="findings-filter-status"
              >
                <option value="">Open + Acknowledged</option>
                <option value="open">Open</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">Rule</label>
              <Input
                value={filters.rule_id}
                onChange={(e) => updateFilter("rule_id", e.target.value)}
                placeholder="e.g. DRV_MED_EXPIRED"
                className="h-9 text-sm"
                data-testid="findings-filter-rule"
              />
            </div>
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">Category</label>
              <Input
                value={filters.category}
                onChange={(e) => updateFilter("category", e.target.value)}
                placeholder="driver · training · ppe · capa"
                className="h-9 text-sm"
                data-testid="findings-filter-category"
              />
            </div>
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold flex items-center gap-1 mb-1">
                <Search className="w-3 h-3" /> Search
              </label>
              <Input
                value={filters.q}
                onChange={(e) => updateFilter("q", e.target.value)}
                placeholder="Name · description"
                className="h-9 text-sm"
                data-testid="findings-filter-search"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={load} disabled={loading} size="sm" data-testid="findings-refresh">
              <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? "animate-spin" : ""}`} /> Refresh
            </Button>
            {anyFilterActive && (
              <Button variant="outline" onClick={clearFilters} size="sm" data-testid="findings-clear-filters">
                <X className="w-3.5 h-3.5 mr-1" /> Clear filters
              </Button>
            )}
            <div className="ml-auto text-xs text-slate-600 font-mono">
              {loading ? "Loading…" : `${total} finding${total === 1 ? "" : "s"}`}
            </div>
          </div>
        </div>

        {err ? (
          <div className="bg-rose-50 border border-rose-300 rounded-md p-3 text-sm text-rose-900" data-testid="findings-error">{err}</div>
        ) : null}

        {/* Findings list */}
        {items.length === 0 && !loading ? (
          <div className="bg-white border-2 border-dashed border-slate-200 rounded-md p-10 text-center" data-testid="findings-empty">
            <ShieldCheck className="w-10 h-10 mx-auto text-emerald-600 mb-3" />
            <div className="font-display text-lg font-black text-slate-900">No findings match.</div>
            <div className="text-sm text-slate-600 mt-1">
              Either the filters narrow to zero, or the detector found no contradictions.
            </div>
          </div>
        ) : null}

        {["critical", "high", "medium", "low", "info"].map((sev) => {
          const group = grouped[sev] || [];
          if (group.length === 0) return null;
          return (
            <section key={sev} className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid={`findings-group-${sev}`}>
              <header className="px-3 py-2 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={sev} />
                  <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">{sevTotals[sev] ?? group.length} findings{(sevTotals[sev] ?? group.length) > group.length ? ` · showing ${group.length}` : ""}</span>
                </div>
              </header>
              <ul className="divide-y divide-slate-100">
                {group.map((f) => (
                  <li key={f.id} className="p-3 sm:p-4 flex flex-col sm:flex-row sm:items-start gap-3" data-testid={`finding-row-${f.id}`}>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-slate-900 text-sm">{f.entity_name || "(unnamed)"}</span>
                        <StatusBadge status={f.status} />
                        <span className="font-mono text-[10px] text-slate-500">{f.rule_id}</span>
                      </div>
                      <p className="text-sm text-slate-700 mt-1.5 leading-snug">{f.description}</p>
                      <div className="text-[11px] font-mono text-slate-500 mt-1.5 flex flex-wrap gap-x-3 gap-y-1">
                        <span>Last detected: {(f.last_detected_at || "").slice(0, 19).replace("T", " ")}</span>
                        {f.first_detected_at && f.first_detected_at !== f.last_detected_at ? (
                          <span>First: {f.first_detected_at.slice(0, 10)}</span>
                        ) : null}
                        {f.acknowledged_by ? (
                          <span>Ack by {f.acknowledged_by} {f.acknowledged_at ? `@ ${f.acknowledged_at.slice(0, 10)}` : ""}</span>
                        ) : null}
                        {f.resolved_by ? (
                          <span>Resolved by {f.resolved_by} {f.resolved_at ? `@ ${f.resolved_at.slice(0, 10)}` : ""}</span>
                        ) : null}
                      </div>
                      {f.acknowledged_note ? (
                        <div className="text-xs italic text-amber-800 mt-1.5">Ack note: {f.acknowledged_note}</div>
                      ) : null}
                      {f.resolved_note ? (
                        <div className="text-xs italic text-emerald-800 mt-1">Resolution note: {f.resolved_note}</div>
                      ) : null}
                    </div>
                    {f.status !== "resolved" ? (
                      <div className="flex sm:flex-col gap-2 shrink-0">
                        {f.status === "open" ? (
                          <Button variant="outline" size="sm" onClick={() => openAction(f, "acknowledge")} data-testid={`finding-ack-${f.id}`}>
                            Acknowledge
                          </Button>
                        ) : null}
                        <Button size="sm" onClick={() => openAction(f, "resolve")} data-testid={`finding-resolve-${f.id}`}>
                          Resolve
                        </Button>
                      </div>
                    ) : null}
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>

      {/* Acknowledge / Resolve dialog */}
      <Dialog open={!!actionTarget} onOpenChange={(open) => !open && setActionTarget(null)}>
        <DialogContent data-testid="finding-action-dialog">
          <DialogHeader>
            <DialogTitle>
              {actionTarget?.mode === "acknowledge" ? "Acknowledge finding" : "Resolve finding"}
            </DialogTitle>
          </DialogHeader>
          {actionTarget ? (
            <div className="space-y-3">
              <div className="bg-slate-50 border border-slate-200 rounded p-3 text-sm text-slate-800">
                <div className="font-semibold">{actionTarget.finding.entity_name}</div>
                <div className="text-xs text-slate-600 mt-1">{actionTarget.finding.description}</div>
              </div>
              <div>
                <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">
                  Note (optional)
                </label>
                <Textarea
                  value={actionNote}
                  onChange={(e) => setActionNote(e.target.value)}
                  placeholder={actionTarget.mode === "acknowledge"
                    ? "Why is this being acknowledged but not yet resolved?"
                    : "Resolution detail (what was done, link, etc.)"}
                  className="text-sm"
                  rows={3}
                  data-testid="finding-action-note"
                />
              </div>
            </div>
          ) : null}
          <DialogFooter>
            <Button variant="outline" onClick={() => setActionTarget(null)} disabled={actionSubmitting} data-testid="finding-action-cancel">
              Cancel
            </Button>
            <Button onClick={submitAction} disabled={actionSubmitting} data-testid="finding-action-submit">
              {actionSubmitting ? "Saving…" : actionTarget?.mode === "acknowledge" ? "Acknowledge" : "Resolve"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AdminShell>
  );
}
