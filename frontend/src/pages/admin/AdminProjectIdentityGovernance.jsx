// AdminProjectIdentityGovernance.jsx
//
// PROJECT-IDENTITY-005 (detection) + PROJECT-IDENTITY-006 (operator clarity).
// OMEGA · detection-only. No mutation. No auto-resolution.
// ID-006 added: governance status language, priority sorting by
// operational impact tier, impact badges, prominent affected-record
// count, top-10 cleanup list, zero-state explanation, "Why this matters"
// expandable panel.

import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  HelpCircle,
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

// ─── Conflict-type metadata ─────────────────────────────────────────
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

// ─── PROJECT-IDENTITY-006 · Operational impact tiers ────────────────
// Lower tier = higher priority. Derived from source_modules string match.
// Tier 1 (Payroll/Time) is reserved — the current scanner does not yet
// cover payroll collections; reserved here so the tier ladder stays
// stable when payroll/time-verification collections are added later.
const TIER = {
  PAYROLL: 1,
  DAILY_REPORTS: 2,
  JOB_PHOTOS: 3,
  SAFETY: 4,
  DISPATCH: 5,
  MATERIAL_EQUIPMENT: 6,
  ADMIN_LOW: 7,
  CERT_TEST: 8,
};

const TIER_LABEL = {
  1: "Payroll · Time",
  2: "Daily Reports",
  3: "Job Photos",
  4: "Safety · Incidents · Inspections",
  5: "Dispatch",
  6: "Material · Equipment",
  7: "Admin · Low-risk",
  8: "Preview · Cert · Test",
};

// Map source_modules.label → tier
function moduleTier(label) {
  const m = (label || "").toLowerCase();
  if (/payroll|time/.test(m)) return TIER.PAYROLL;
  if (/daily report/.test(m)) return TIER.DAILY_REPORTS;
  if (/job photo|photo/.test(m)) return TIER.JOB_PHOTOS;
  if (/incident|inspection|safety|jha|trench|fire ext|qa\/qc|qaqc|corrective/.test(m)) return TIER.SAFETY;
  if (/dispatch/.test(m)) return TIER.DISPATCH;
  if (/equipment|haul|po request|operations action|operational|asset|material/.test(m)) return TIER.MATERIAL_EQUIPMENT;
  if (/field leadership|submitter binding|meeting/.test(m)) return TIER.ADMIN_LOW;
  return TIER.ADMIN_LOW;
}

const CERT_RX = /(^|[-_\s])(TEST|SMOKE|VERIFY|CERT|DEMO|SEED|SAMPLE|PREVIEW|QA-)([-_\s]|$)|^ITER\d+|_PROD_CERT/i;

function isCertOrTest(item) {
  const blob = `${item.submitted_project_number || ""} ${item.submitted_project_name || ""}`;
  return CERT_RX.test(blob);
}

// Lowest tier across modules; cert/test family pushed to tier 8.
function itemTier(item) {
  if (isCertOrTest(item)) return TIER.CERT_TEST;
  const mods = item.source_modules || [];
  if (mods.length === 0) return TIER.ADMIN_LOW;
  return Math.min(...mods.map(moduleTier));
}

// ─── Impact badge helpers ───────────────────────────────────────────
function impactBadges(item) {
  const out = [];
  if (isCertOrTest(item)) out.push({ label: "Preview/Test", tone: "bg-slate-400 text-white" });
  const mods = item.source_modules || [];
  const seen = new Set();
  for (const m of mods) {
    const t = moduleTier(m);
    let label = m;
    let tone = "bg-slate-700 text-white";
    if (t === TIER.PAYROLL) { tone = "bg-red-800 text-white"; }
    else if (t === TIER.DAILY_REPORTS) { tone = "bg-red-700 text-white"; }
    else if (t === TIER.JOB_PHOTOS) { tone = "bg-red-600 text-white"; }
    else if (t === TIER.SAFETY) { tone = "bg-amber-600 text-white"; }
    else if (t === TIER.DISPATCH) { tone = "bg-orange-600 text-white"; }
    else if (t === TIER.MATERIAL_EQUIPMENT) { tone = "bg-slate-600 text-white"; }
    if (!seen.has(label)) {
      seen.add(label);
      out.push({ label, tone });
    }
  }
  return out;
}

// ─── Governance status derivation ───────────────────────────────────
function deriveGovernanceStatus(queue, metrics) {
  const open = (queue || []).filter((x) => x.status === "open");
  const criticalImpact = open.some((x) => itemTier(x) <= TIER.JOB_PHOTOS); // Payroll/DR/JP
  const safetyImpact = open.some((x) => itemTier(x) === TIER.SAFETY);
  const heavyUnmatched = (metrics?.unmatched_records || 0) > 1000;
  if (criticalImpact || (safetyImpact && heavyUnmatched)) {
    return {
      level: "critical",
      label: "Critical Review Needed",
      color: "bg-red-700",
      tone: "text-red-700",
      explainer:
        "Open conflicts affect high-impact operational modules (Daily Reports, Job Photos, or Payroll). Start with the Highest Impact list below.",
    };
  }
  if (open.length > 0) {
    return {
      level: "needs_review",
      label: "Needs Review",
      color: "bg-amber-500",
      tone: "text-amber-700",
      explainer:
        "Detection found conflicts that an admin should review. Records remain unchanged until you resolve them.",
    };
  }
  return {
    level: "healthy",
    label: "Healthy",
    color: "bg-emerald-700",
    tone: "text-emerald-700",
    explainer:
      "No open identity conflicts detected. Project numbers and names are aligned across the platform.",
  };
}

// ─── Metric card ────────────────────────────────────────────────────
function MetricCard({ icon: Icon, value, label, tone = "slate", caption }) {
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
      <div className="min-w-0">
        <div className="font-display text-2xl font-black leading-none truncate">
          {value ?? "—"}
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] mt-1 opacity-90">
          {label}
        </div>
        {caption && (
          <div className="text-[10px] mt-1 opacity-80 truncate">{caption}</div>
        )}
      </div>
    </div>
  );
}

// ─── Page ───────────────────────────────────────────────────────────
export default function AdminProjectIdentityGovernance() {
  const [metrics, setMetrics] = useState(null);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [filterStatus, setFilterStatus] = useState("open");
  const [filterType, setFilterType] = useState("");
  const [search, setSearch] = useState("");
  const [jobs, setJobs] = useState([]);
  const [showWhy, setShowWhy] = useState(false);

  const [loadCounter, setLoadCounter] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
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
        if (cancelled) return;
        setMetrics(m.data || {});
        setQueue(q.data || []);
        setJobs(jm.data || []);
      } catch {
        if (!cancelled) toast.error("Failed to load Project Identity Governance");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [filterStatus, filterType, loadCounter]);

  function rescan() {
    setScanning(true);
    api
      .post("/admin/project-identity/scan")
      .then((res) => {
        const total = res.data?.items_total ?? 0;
        toast.success(`Scan complete · ${total} items`);
        setLoadCounter((c) => c + 1);
      })
      .catch(() => toast.error("Scan failed"))
      .finally(() => setScanning(false));
  }

  function resolve(item, action, jobsMasterId, note) {
    api
      .post(
        `/admin/project-identity/queue/${encodeURIComponent(item.key)}/resolve`,
        { action, matched_jobs_master_id: jobsMasterId, note: note || "" }
      )
      .then(() => {
        toast.success(`Marked ${action.replace("_", " ")}`);
        setLoadCounter((c) => c + 1);
      })
      .catch((e) => toast.error(e?.response?.data?.detail || "Resolve failed"));
  }

  // ── Decorate + sort ─────────────────────────────────────────────
  const decorated = useMemo(() => {
    return (queue || [])
      .map((it) => ({ ...it, _tier: itemTier(it) }))
      .sort((a, b) => {
        if (a._tier !== b._tier) return a._tier - b._tier;
        const ar = a.record_count || 0;
        const br = b.record_count || 0;
        if (ar !== br) return br - ar;
        // newest activity first
        return (b.last_seen || "").localeCompare(a.last_seen || "");
      });
  }, [queue]);

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return decorated;
    return decorated.filter((it) => {
      const hay = `${it.submitted_project_number} ${it.submitted_project_name} ${it.suggested_canonical_number || ""} ${it.suggested_canonical_name || ""} ${(it.source_modules || []).join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [decorated, search]);

  // Top-10 highest-impact open items
  const topOpen = useMemo(() => {
    return decorated.filter((it) => it.status === "open").slice(0, 10);
  }, [decorated]);

  const status = useMemo(
    () => deriveGovernanceStatus(decorated, metrics),
    [decorated, metrics]
  );

  return (
    <AdminShell title="Project Identity Governance" section="project-identity">
      <div className="space-y-5" data-testid="project-identity-page">
        {/* Doctrine + status bar */}
        <div className="bg-white border-2 border-slate-200 rounded-md p-4">
          <div className="flex items-start gap-3">
            <ShieldCheck className={`w-6 h-6 shrink-0 mt-0.5 ${status.tone}`} />
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`inline-flex items-center px-2 py-0.5 ${status.color} text-white text-[11px] font-mono uppercase tracking-wider rounded font-bold`} data-testid="identity-governance-status">
                  {status.label}
                </span>
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  Project Identity Governance
                </span>
              </div>
              <p className="text-sm text-slate-700 mt-2 leading-relaxed">
                <strong>These are detected project identity issues. No records are changed until an admin resolves them.</strong>{" "}
                {status.explainer}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowWhy((s) => !s)}
              className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-wider text-slate-600 hover:text-slate-900"
              data-testid="identity-why-toggle"
            >
              <HelpCircle className="w-4 h-4" />
              Why this matters
              {showWhy ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
            </button>
          </div>
          {showWhy && (
            <div className="mt-3 bg-slate-50 border border-slate-200 rounded p-3 text-sm text-slate-700 space-y-1.5" data-testid="identity-why-panel">
              <div>• Duplicate project names split history across two folders, two dashboards, two exports.</div>
              <div>• Project numbers must stay consistent across every operational module (Daily Reports, Job Photos, Safety, Equipment, Dispatch).</div>
              <div>• Admins resolve identity conflicts. Detection never auto-mutates source records or jobs_master.</div>
              <div>• Historical records are never rewritten — submitted PN + submitted name are preserved verbatim.</div>
              <div>• Future grouping uses canonical identity, so resolving each conflict prevents future duplicate folders.</div>
            </div>
          )}
        </div>

        {/* Metrics */}
        {loading && !metrics ? (
          <div className="p-12 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
          </div>
        ) : metrics ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-4 gap-3">
            <MetricCard icon={CheckCircle2} value={metrics.canonical_projects} label="Canonical Projects" tone="green" />
            <MetricCard icon={AlertTriangle} value={metrics.governance_queue} label="Governance Queue" tone="red" caption="open items awaiting review" />
            <MetricCard icon={Activity} value={metrics.unmatched_records} label="Unmatched Records" tone="slate" caption="rows pointing at unknown PN" />
            <MetricCard icon={Activity} value={metrics.normalized_matches} label="Normalized Matches" tone="amber" caption="whitespace/dash variants" />
            <MetricCard icon={CheckCircle2} value={metrics.intentional_variants} label="Intentional Variants" tone="slate" />
            <MetricCard icon={AlertTriangle} value={metrics.projects_requiring_review} label="Projects Requiring Review" tone="red" />
            <MetricCard icon={Activity}
              value={metrics.last_governance_action?.resolved_at?.slice(0, 16) || "—"}
              label="Last Governance Action"
              tone="slate"
              caption={metrics.last_governance_action ? `→ ${metrics.last_governance_action.status}` : "no action yet"} />
            <MetricCard icon={ShieldCheck}
              value={`${metrics.identity_health_score}%`}
              label="Identity Health Score"
              tone={metrics.identity_health_score >= 90 ? "green" : metrics.identity_health_score >= 70 ? "amber" : "red"}
              caption={metrics.identity_health_score === 0 ? "starts at 0% until reviewed" : ""} />
          </div>
        ) : null}

        {/* Zero-state explainer when health is 0 */}
        {metrics && metrics.identity_health_score === 0 && (
          <div className="bg-amber-50 border border-amber-300 rounded p-3 text-sm text-amber-900" data-testid="identity-zero-state">
            <strong>Identity Health starts at 0% until detected conflicts are reviewed.</strong>{" "}
            The system is protecting records by requiring human confirmation. Work through the
            &ldquo;Highest Impact Issues To Fix First&rdquo; list below — each resolution increases the score.
          </div>
        )}

        {/* TOP 10 cleanup list */}
        {topOpen.length > 0 && (
          <div className="bg-white border-2 border-red-200 rounded-md overflow-hidden" data-testid="identity-top10">
            <div className="px-4 py-3 border-b-2 border-red-200 bg-red-50 flex items-center justify-between">
              <h2 className="font-display text-base font-bold text-red-900 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Highest Impact Issues To Fix First
              </h2>
              <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-red-700">
                top {topOpen.length} of {decorated.filter((x) => x.status === "open").length} open
              </span>
            </div>
            <ul className="divide-y divide-slate-100">
              {topOpen.map((it) => (
                <GovernanceItem key={`top-${it.key}`} item={it} jobs={jobs} onResolve={resolve} compact />
              ))}
            </ul>
          </div>
        )}

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

        {/* Full queue */}
        <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-4 py-3 border-b-2 border-slate-200 flex items-center justify-between">
            <h2 className="font-display text-base font-bold">Governance Queue</h2>
            <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-500">
              {visible.length} item{visible.length === 1 ? "" : "s"} · sorted by operational impact
            </span>
          </div>
          {visible.length === 0 ? (
            <div className="p-10 text-center text-slate-500 italic" data-testid="identity-empty">
              No governance items match the current filter. Run a re-scan to refresh detection.
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {visible.map((it) => (
                <GovernanceItem key={it.key} item={it} jobs={jobs} onResolve={resolve} />
              ))}
            </ul>
          )}
        </div>
      </div>
    </AdminShell>
  );
}

// ─── Single governance item ─────────────────────────────────────────
function GovernanceItem({ item, jobs, onResolve, compact = false }) {
  const [matchOpen, setMatchOpen] = useState(false);
  const [matchId, setMatchId] = useState(item.matched_jobs_master_id || "");
  const [note, setNote] = useState("");
  const typeMeta = CONFLICT_TYPES[item.conflict_type] || { label: item.conflict_type, color: "bg-slate-700" };
  const tier = item._tier || itemTier(item);
  const badges = impactBadges(item);

  return (
    <li className="p-4" data-testid={`identity-item-${item.conflict_type}-${item.submitted_project_number || "blank"}`}>
      {/* Top row · type, status, tier, affected record count */}
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span className={`inline-flex items-center px-2 py-0.5 ${typeMeta.color} text-white text-[10px] font-mono uppercase tracking-wider rounded font-bold`}>
          {item.conflict_type} · {typeMeta.label}
        </span>
        <span className="inline-flex items-center px-2 py-0.5 bg-slate-200 text-slate-700 text-[10px] font-mono uppercase tracking-wider rounded">
          {STATUS_LABEL[item.status] || item.status}
        </span>
        <span className="inline-flex items-center px-2 py-0.5 bg-slate-100 text-slate-700 text-[10px] font-mono uppercase tracking-wider rounded border border-slate-300" title={TIER_LABEL[tier]}>
          Tier {tier} · {TIER_LABEL[tier]}
        </span>
        <span className="font-display text-sm font-bold text-slate-900 ml-auto">
          Affected Records: {item.record_count}
        </span>
      </div>

      {/* Impact badges */}
      {badges.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 mb-2">
          <span className="font-mono text-[10px] uppercase tracking-wider text-slate-500">Modules affected:</span>
          {badges.map((b, i) => (
            <span key={i} className={`inline-flex items-center px-2 py-0.5 ${b.tone} text-[10px] font-mono uppercase tracking-wider rounded font-bold`}>
              {b.label}
            </span>
          ))}
        </div>
      )}

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

      <div className="font-mono text-[11px] text-slate-500 mt-1">
        Last seen {item.last_seen?.slice(0, 10) || "—"}
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
            <Button variant="outline" onClick={() => setMatchOpen(false)} className="h-9 text-xs">
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
