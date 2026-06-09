// AdminProjectIdentityGovernance.jsx
//
// PROJECT-IDENTITY-005 · OMEGA DIRECTIVE
//
// Detection-only dashboard. Surfaces six conflict types (A–F) detected by
// the backend scanner. Operator chooses one of four resolutions per item:
//   • Match Existing Project
//   • Leave Unmatched
//   • Mark Intentional
//   • Dismiss
// No deletes. No merges. No rewrites. No automatic mutation.

import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Eye,
  Loader2,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { toast } from "sonner";

const CONFLICT_TYPES = {
  A: { label: "Same PN · Different Name", color: "bg-red-700" },
  B: { label: "Same Name · Different PN", color: "bg-red-700" },
  C: { label: "PN Variation (normalizable)", color: "bg-amber-600" },
  D: { label: "Unknown Project", color: "bg-red-800" },
  E: { label: "Blank PN · Has Name", color: "bg-slate-600" },
  F: { label: "Has PN · Blank Name", color: "bg-slate-600" },
};

const STATUS_LABEL = {
  open: "Open",
  matched: "Matched",
  left_unmatched: "Left Unmatched",
  intentional: "Intentional",
  dismissed: "Dismissed",
};

function MetricCard({ icon: Icon, value, label, tone = "slate" }) {
  const tones = {
    slate: "bg-slate-900 text-white",
    red: "bg-red-700 text-white",
    amber: "bg-amber-500 text-slate-900",
    green: "bg-emerald-700 text-white",
  };
  return (
    <div
      className={`${tones[tone]} px-4 py-3 rounded-md flex items-center gap-3`}
      data-testid={`identity-metric-${label.toLowerCase().replace(/\s+/g, "-")}`}
    >
      <Icon className="w-6 h-6 shrink-0" />
      <div>
        <div className="font-display text-2xl font-black leading-none">
          {value ?? "—"}
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] mt-1 opacity-90">
          {label}
        </div>
      </div>
    </div>
  );
}

export default function AdminProjectIdentityGovernance() {
  const [metrics, setMetrics] = useState(null);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [filterStatus, setFilterStatus] = useState("open");
  const [filterType, setFilterType] = useState("");
  const [search, setSearch] = useState("");
  const [jobs, setJobs] = useState([]);

  async function load() {
    setLoading(true);
    try {
      const [m, q, jm] = await Promise.all([
        api.get("/admin/project-identity/metrics"),
        api.get("/admin/project-identity/queue", {
          params: {
            ...(filterStatus ? { status: filterStatus } : {}),
            ...(filterType ? { conflict_type: filterType } : {}),
          },
        }),
        api.get("/jobs-master").catch(() => ({ data: [] })),
      ]);
      setMetrics(m.data || {});
      setQueue(q.data || []);
      setJobs(jm.data || []);
    } catch (e) {
      toast.error("Failed to load Project Identity Governance");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterStatus, filterType]);

  async function rescan() {
    setScanning(true);
    try {
      const res = await api.post("/admin/project-identity/scan");
      const total = res.data?.items_total ?? 0;
      toast.success(`Scan complete · ${total} items`);
      await load();
    } catch {
      toast.error("Scan failed");
    } finally {
      setScanning(false);
    }
  }

  async function resolve(item, action, jobsMasterId, note) {
    try {
      await api.post(
        `/admin/project-identity/queue/${encodeURIComponent(item.key)}/resolve`,
        { action, matched_jobs_master_id: jobsMasterId, note: note || "" }
      );
      toast.success(`Marked ${action.replace("_", " ")}`);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Resolve failed");
    }
  }

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return queue;
    return queue.filter((it) => {
      const hay = `${it.submitted_project_number} ${it.submitted_project_name} ${it.suggested_canonical_number || ""} ${it.suggested_canonical_name || ""} ${(it.source_modules || []).join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [queue, search]);

  return (
    <AdminShell title="Project Identity Governance" section="project-identity">
      <div className="space-y-5" data-testid="project-identity-page">
        {/* Doctrine bar */}
        <div className="bg-amber-50 border-2 border-amber-300 rounded-md p-4 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
          <div className="text-sm text-amber-900">
            <strong>Detection only.</strong> This screen never auto-mutates
            records or jobs_master. Every resolution is a human decision.
            <span className="ml-2 text-amber-700 font-mono text-xs uppercase tracking-wider">
              ONE PN · ONE PROJECT · ONE NAME · ONE HISTORY
            </span>
          </div>
        </div>

        {/* Metrics */}
        {loading && !metrics ? (
          <div className="p-12 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
          </div>
        ) : metrics ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-4 gap-3">
            <MetricCard icon={CheckCircle2} value={metrics.canonical_projects} label="Canonical Projects" tone="green" />
            <MetricCard icon={AlertTriangle} value={metrics.governance_queue} label="Governance Queue" tone="red" />
            <MetricCard icon={Activity} value={metrics.unmatched_records} label="Unmatched Records" tone="slate" />
            <MetricCard icon={Activity} value={metrics.normalized_matches} label="Normalized Matches" tone="amber" />
            <MetricCard icon={CheckCircle2} value={metrics.intentional_variants} label="Intentional Variants" tone="slate" />
            <MetricCard icon={Eye} value={metrics.projects_requiring_review} label="Projects Requiring Review" tone="red" />
            <MetricCard icon={Activity}
              value={metrics.last_governance_action?.resolved_at?.slice(0, 16) || "—"}
              label="Last Governance Action" tone="slate" />
            <MetricCard icon={ShieldCheck} value={`${metrics.identity_health_score}%`} label="Identity Health Score" tone={metrics.identity_health_score >= 90 ? "green" : metrics.identity_health_score >= 70 ? "amber" : "red"} />
          </div>
        ) : null}

        {/* Toolbar */}
        <div className="bg-white border border-slate-200 rounded-md p-3 flex flex-wrap gap-2 items-center">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search PN / name / module…"
            className="flex-1 min-w-[200px] h-10 border-2"
            data-testid="identity-search"
          />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="h-10 px-3 border border-slate-200 rounded-md font-mono text-sm bg-white"
            data-testid="identity-status-filter"
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="matched">Matched</option>
            <option value="left_unmatched">Left Unmatched</option>
            <option value="intentional">Intentional</option>
            <option value="dismissed">Dismissed</option>
          </select>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="h-10 px-3 border border-slate-200 rounded-md font-mono text-sm bg-white"
            data-testid="identity-type-filter"
          >
            <option value="">All conflict types</option>
            {Object.entries(CONFLICT_TYPES).map(([k, v]) => (
              <option key={k} value={k}>{`${k} · ${v.label}`}</option>
            ))}
          </select>
          <Button
            onClick={rescan}
            disabled={scanning}
            className="bg-slate-900 hover:bg-slate-800 text-white h-10"
            data-testid="identity-rescan-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${scanning ? "animate-spin" : ""}`} />
            {scanning ? "Scanning…" : "Re-scan platform"}
          </Button>
        </div>

        {/* Queue */}
        <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-4 py-3 border-b-2 border-slate-200 flex items-center justify-between">
            <h2 className="font-display text-base font-bold">Governance Queue</h2>
            <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-500">
              {visible.length} item{visible.length === 1 ? "" : "s"}
            </span>
          </div>
          {visible.length === 0 ? (
            <div className="p-10 text-center text-slate-500 italic" data-testid="identity-empty">
              No governance items match the current filter. Run a re-scan to
              refresh detection.
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {visible.map((it) => (
                <GovernanceItem
                  key={it.key}
                  item={it}
                  jobs={jobs}
                  onResolve={resolve}
                />
              ))}
            </ul>
          )}
        </div>
      </div>
    </AdminShell>
  );
}

function GovernanceItem({ item, jobs, onResolve }) {
  const [matchOpen, setMatchOpen] = useState(false);
  const [matchId, setMatchId] = useState(item.matched_jobs_master_id || "");
  const [note, setNote] = useState("");
  const typeMeta = CONFLICT_TYPES[item.conflict_type] || { label: item.conflict_type, color: "bg-slate-700" };

  return (
    <li className="p-4" data-testid={`identity-item-${item.conflict_type}-${item.submitted_project_number || "blank"}`}>
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span className={`inline-flex items-center px-2 py-0.5 ${typeMeta.color} text-white text-[10px] font-mono uppercase tracking-wider rounded font-bold`}>
          {item.conflict_type} · {typeMeta.label}
        </span>
        <span className="inline-flex items-center px-2 py-0.5 bg-slate-200 text-slate-700 text-[10px] font-mono uppercase tracking-wider rounded">
          {STATUS_LABEL[item.status] || item.status}
        </span>
        <span className="font-mono text-[11px] text-slate-500">
          {item.record_count} record{item.record_count === 1 ? "" : "s"} · last seen {item.last_seen?.slice(0, 10) || "—"}
        </span>
        <span className="font-mono text-[11px] text-slate-500 ml-auto">
          {(item.source_modules || []).join(" · ")}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Submitted</div>
          <div className="font-display font-bold text-slate-900">
            {item.submitted_project_number ? `#${item.submitted_project_number}` : <span className="text-slate-400">(blank PN)</span>}{" "}
            <span className="font-normal text-slate-700">{item.submitted_project_name || <span className="text-slate-400">(blank name)</span>}</span>
          </div>
        </div>
        {(item.suggested_canonical_number || item.suggested_canonical_name) && (
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-emerald-700">Suggested canonical</div>
            <div className="font-display font-bold text-slate-900">
              #{item.suggested_canonical_number}{" "}
              <span className="font-normal text-slate-700">{item.suggested_canonical_name}</span>
            </div>
          </div>
        )}
      </div>

      {item.status === "open" && (
        <div className="mt-3 flex flex-wrap gap-2 items-center">
          <Button
            onClick={() => setMatchOpen((o) => !o)}
            className="h-9 bg-emerald-700 hover:bg-emerald-800 text-white text-xs"
            data-testid={`identity-match-${item.key}`}
          >
            Match Existing Project
          </Button>
          <Button
            variant="outline"
            onClick={() => onResolve(item, "leave_unmatched", null, "")}
            className="h-9 text-xs border-2"
            data-testid={`identity-leave-${item.key}`}
          >
            Leave Unmatched
          </Button>
          <Button
            variant="outline"
            onClick={() => onResolve(item, "intentional", null, "")}
            className="h-9 text-xs border-2"
            data-testid={`identity-intentional-${item.key}`}
          >
            Mark Intentional
          </Button>
          <Button
            variant="outline"
            onClick={() => onResolve(item, "dismiss", null, "")}
            className="h-9 text-xs border-2"
            data-testid={`identity-dismiss-${item.key}`}
          >
            <XCircle className="w-3.5 h-3.5 mr-1" /> Dismiss
          </Button>
        </div>
      )}

      {matchOpen && item.status === "open" && (
        <div className="mt-3 bg-slate-50 border border-slate-200 rounded-md p-3 space-y-2">
          <select
            value={matchId}
            onChange={(e) => setMatchId(e.target.value)}
            className="h-10 w-full border-2 border-slate-300 rounded px-3 text-sm bg-white"
            data-testid={`identity-match-select-${item.key}`}
          >
            <option value="">— Pick canonical project —</option>
            {jobs.map((j) => (
              <option key={j.id || j.project_number} value={j.id}>
                #{j.project_number} · {j.project_name}
              </option>
            ))}
          </select>
          <Input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Optional note (max 500 chars)"
            maxLength={500}
            className="h-10 border-2"
            data-testid={`identity-match-note-${item.key}`}
          />
          <div className="flex gap-2 justify-end">
            <Button
              variant="outline"
              onClick={() => setMatchOpen(false)}
              className="h-9 text-xs"
            >
              Cancel
            </Button>
            <Button
              disabled={!matchId}
              onClick={() => {
                onResolve(item, "match", matchId, note);
                setMatchOpen(false);
              }}
              className="h-9 bg-emerald-700 hover:bg-emerald-800 text-white text-xs"
              data-testid={`identity-match-confirm-${item.key}`}
            >
              Confirm Match
            </Button>
          </div>
        </div>
      )}
    </li>
  );
}
