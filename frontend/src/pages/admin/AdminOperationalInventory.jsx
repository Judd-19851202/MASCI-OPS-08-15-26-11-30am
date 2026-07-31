// AdminOperationalInventory.jsx — Pass 2 of the Operational Inventory
// initiative. Programmatic mirror of /app/docs/OPERATIONAL_INVENTORY.md.
//
// Read-only admin dashboard. Backend is the canonical source of truth
// (see /api/admin/operational-inventory). Drift detection surfaces
// portals/articles/routes/workflows that lack required coverage fields.
//
// Scope discipline: admin-strict, no mutations, no PII.
import React, { useEffect, useMemo, useState } from "react";
import {
  Map, RefreshCcw, Loader2, AlertCircle, CheckCircle2, AlertTriangle,
  ShieldAlert, Languages, Compass, Users, Workflow, ExternalLink,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

// 10 audit fields (column order on the portal matrix)
const FIELDS = [
  { key: "who_uses_it",          label: "Who uses it" },
  { key: "login_required",       label: "Login" },
  { key: "guidance_exists",      label: "Guidance" },
  { key: "onboarding_exists",    label: "Onboarding" },
  { key: "contextual_help",      label: "Ctxt help" },
  { key: "why_explanation",      label: "WHY" },
  { key: "troubleshooting",      label: "Troubleshoot" },
  { key: "discoverability",      label: "Discoverability" },
  { key: "mobile_ux",            label: "Mobile" },
  { key: "translation_readiness", label: "Translation" },
];

const STATUS_BADGE = {
  complete: "bg-emerald-100 text-emerald-800 border-emerald-300",
  partial:  "bg-amber-100  text-amber-800  border-amber-300",
  missing:  "bg-red-100    text-red-800    border-red-300",
  "n/a":    "bg-slate-100  text-slate-600  border-slate-300",
  deferred: "bg-sky-100    text-sky-800    border-sky-300",
};

const STATUS_DOT = {
  complete: "bg-emerald-500",
  partial:  "bg-amber-500",
  missing:  "bg-red-600",
  "n/a":    "bg-slate-400",
  deferred: "bg-sky-500",
};

const SEVERITY_PILL = {
  p0: "bg-red-700 text-white",
  p1: "bg-amber-600 text-white",
  p2: "bg-slate-600 text-white",
};

function StatusCell({ field }) {
  if (!field) return <span className="text-slate-300">—</span>;
  const cls = STATUS_BADGE[field.status] || STATUS_BADGE.missing;
  return (
    <div className="inline-flex items-center gap-1.5" title={field.detail || ""}>
      <span className={`inline-block w-2 h-2 rounded-full ${STATUS_DOT[field.status] || STATUS_DOT.missing}`} />
      <span className={`px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider ${cls}`}>
        {field.status}
      </span>
    </div>
  );
}

const TABS = [
  { key: "overview",     label: "Overview",     icon: Map },
  { key: "portals",      label: "Portals",      icon: Compass },
  { key: "user-types",   label: "User Types",   icon: Users },
  { key: "routes",       label: "Public Routes", icon: ExternalLink },
  { key: "workflows",    label: "Workflows",    icon: Workflow },
  { key: "translation",  label: "Translation",  icon: Languages },
  { key: "drift",        label: "Drift",        icon: ShieldAlert },
];

export default function AdminOperationalInventory() {
  const [snap, setSnap] = useState(null);
  const [sampleAsset, setSampleAsset] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("overview");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [inventoryResponse, assetResponse] = await Promise.all([
        api.get("/admin/operational-inventory"),
        api.get("/asset-spine/assets"),
      ]);
      setSnap(inventoryResponse.data);
      setSampleAsset(assetResponse?.data?.items?.[0] || null);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Failed to load inventory";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const driftBySeverity = snap?.drift?.by_severity || { p0: 0, p1: 0, p2: 0 };
  const driftItems = snap?.drift?.items || [];

  return (
    <AdminShell title="Operational Inventory" section="operational-inventory" experienceLevel="wp17c" experienceTone="admin">
      <div className="space-y-6" data-testid="admin-operational-inventory-panel">
        {/* Header */}
        <div className="wp17-table-shell flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="text-xs font-mono uppercase tracking-widest text-slate-500">
              Governance · Pass 2 · Read-Only
            </div>
            <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
              <Map className="h-7 w-7 text-amber-600" />
              Operational Inventory
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Live programmatic mirror of{" "}
              <code className="px-1 py-0.5 bg-slate-100 rounded text-[12px]">/app/docs/OPERATIONAL_INVENTORY.md</code>.
              10-field coverage matrix across every portal, user type, public route, and cross-cutting
              workflow. Surfaces drift as the platform grows. No mutations from this surface.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {sampleAsset ? (
              <Button asChild variant="outline" size="sm" data-testid="admin-operational-inventory-sample-detail-link">
                <a href={`/admin/assets/${sampleAsset.asset_id}`}>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Representative detail
                </a>
              </Button>
            ) : null}
            <Button
              variant="outline" size="sm" onClick={load} disabled={loading}
              data-testid="admin-operational-inventory-refresh"
            >
              {loading
                ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                : <RefreshCcw className="h-4 w-4 mr-2" />}
              Refresh
            </Button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm flex gap-2 items-start">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Stat strip */}
        {snap && (
          <div className="wp17-metric-grid" data-testid="inventory-stat-strip">
            <Stat label="Portals" value={snap.totals.portals} />
            <Stat label="User types" value={snap.totals.user_types} />
            <Stat label="Public routes" value={snap.totals.public_routes} />
            <Stat label="Guidance articles" value={snap.totals.guidance_articles} />
            <Stat label="Drift · P0" value={driftBySeverity.p0} tone={driftBySeverity.p0 ? "red" : "slate"} />
            <Stat label="Drift · P1" value={driftBySeverity.p1} tone={driftBySeverity.p1 ? "amber" : "slate"} />
            <Stat label="Drift · P2" value={driftBySeverity.p2} tone={driftBySeverity.p2 ? "slate" : "slate"} />
            <Stat label="Translation %" value={`${snap.translation.pct_body}%`} tone={snap.translation.pct_body >= 80 ? "emerald" : "red"} />
          </div>
        )}

        {/* Tabs */}
        <div className="wp17-panel border-b border-slate-200 flex flex-wrap gap-1" data-testid="inventory-tabs">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = tab === t.key;
            return (
              <button
                key={t.key}
                type="button"
                onClick={() => setTab(t.key)}
                className={`inline-flex items-center gap-1.5 px-3 py-2 text-[12px] font-mono uppercase tracking-wider border-b-2 transition-colors ${
                  active
                    ? "border-amber-600 text-amber-700"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
                data-testid={`inventory-tab-${t.key}`}
              >
                <Icon className="w-3.5 h-3.5" />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        {loading && !snap && (
          <div className="text-center py-10">
            <Loader2 className="h-6 w-6 animate-spin mx-auto text-slate-400" />
          </div>
        )}

        {snap && tab === "overview" && <OverviewTab snap={snap} />}
        {snap && tab === "portals" && <PortalsTab rows={snap.portals} />}
        {snap && tab === "user-types" && <UserTypesTab rows={snap.user_types} />}
        {snap && tab === "routes" && <RoutesTab rows={snap.public_routes} />}
        {snap && tab === "workflows" && <WorkflowsTab rows={snap.workflows} />}
        {snap && tab === "translation" && <TranslationTab data={snap.translation} />}
        {snap && tab === "drift" && <DriftTab items={driftItems} bySev={driftBySeverity} />}
      </div>
    </AdminShell>
  );
}

function Stat({ label, value, tone = "slate" }) {
  const tones = {
    slate:   "text-slate-900",
    red:     "text-red-700",
    amber:   "text-amber-700",
    emerald: "text-emerald-700",
  };
  return (
    <div className="wp17-metric-card">
      <div className="wp17-metric-card__label">{label}</div>
      <div className={`wp17-metric-card__value mt-1 ${tones[tone] || tones.slate}`}>{value}</div>
    </div>
  );
}

function OverviewTab({ snap }) {
  const portalGaps = snap.portals.filter((p) =>
    Object.values(p.fields).some((f) => f.status === "missing")
  ).length;
  const routeGaps = snap.public_routes.filter((r) => !r.has_guidance).length;
  const workflowGaps = snap.workflows.filter((w) => !w.has_guidance).length;
  return (
    <div className="space-y-4" data-testid="inventory-overview">
      <div className="bg-slate-900 text-white rounded-md p-5">
        <div className="font-mono text-[10px] uppercase tracking-widest text-amber-400 mb-1">
          Pass 2 · Live governance signal
        </div>
        <h2 className="text-xl font-bold leading-tight">
          {snap.drift.total === 0
            ? "No operational drift detected."
            : `${snap.drift.total} operational drift items across ${Object.keys(snap.drift.by_severity).length} severities.`}
        </h2>
        <p className="mt-2 text-sm text-slate-300 max-w-3xl">
          This dashboard catches blind spots automatically. The static doc remains the authoritative
          human-readable artifact; this surface is the always-current code-derived view that prevents
          regression. Severity P0 blocks operations; P1 blocks confident rollout; P2 is backlog hygiene.
        </p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4">
        <SummaryCard label="Portals with gaps" value={portalGaps} total={snap.portals.length} />
        <SummaryCard label="Public routes missing guidance" value={routeGaps} total={snap.public_routes.length} />
        <SummaryCard label="Workflows missing guidance" value={workflowGaps} total={snap.workflows.length} />
      </div>
      <div className="bg-amber-50 border border-amber-200 rounded p-4 text-sm">
        <div className="font-mono text-[10px] uppercase tracking-wider text-amber-700 font-bold mb-1">
          Governance roadmap
        </div>
        <ul className="space-y-1 text-slate-800">
          <li>• <strong>Pass 1</strong> — Markdown audit (delivered)</li>
          <li>• <strong>Pass 2</strong> — This dashboard (LIVE)</li>
          <li>• <strong>Pass 3</strong> — Translation schema (body_es + Block renderer)</li>
          <li>• <strong>Pass 4</strong> — Field Leadership portal door (/leadership/login + /sign-in tile)</li>
          <li>• <strong>Pass 5</strong> — Per-persona onboarding articles</li>
          <li>• <strong>Pass 6</strong> — Cross-cutting workflow coverage</li>
          <li>• <strong>Pass 7</strong> — QR poster rollout</li>
        </ul>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, total }) {
  const tone = value === 0 ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200";
  return (
    <div className={`rounded-md border p-4 ${tone}`}>
      <div className="text-[10px] font-mono uppercase tracking-wider text-slate-600">{label}</div>
      <div className="text-3xl font-bold mt-1 text-slate-900">
        {value}
        <span className="text-sm font-normal text-slate-500 ml-1">/ {total}</span>
      </div>
    </div>
  );
}

function PortalsTab({ rows }) {
  return (
    <div className="overflow-x-auto" data-testid="inventory-portals-tab">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-100 border-y border-slate-200">
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600 sticky left-0 bg-slate-100">
              Portal
            </th>
            {FIELDS.map((f) => (
              <th key={f.key} className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600 whitespace-nowrap">
                {f.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((p) => (
            <tr key={p.portal} className="border-b border-slate-100 hover:bg-slate-50" data-testid={`inventory-portal-row-${p.portal}`}>
              <td className="p-2 sticky left-0 bg-white">
                <div className="font-bold text-slate-900">{p.label}</div>
                <div className="text-[11px] text-slate-500">{p.purpose}</div>
                {p.anomaly && (
                  <div className="mt-1 inline-flex items-center gap-1 text-[10px] font-mono uppercase text-red-700 bg-red-50 border border-red-200 rounded px-1.5 py-0.5">
                    <AlertTriangle className="w-3 h-3" /> {p.anomaly}
                  </div>
                )}
              </td>
              {FIELDS.map((f) => (
                <td key={f.key} className="p-2 align-top">
                  <StatusCell field={p.fields[f.key]} />
                  <div className="text-[10px] text-slate-500 mt-1 max-w-[160px]">
                    {p.fields[f.key]?.detail}
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function UserTypesTab({ rows }) {
  return (
    <div className="overflow-x-auto" data-testid="inventory-usertypes-tab">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-100 border-y border-slate-200">
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">User type</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Primary portal</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Cross-portal reads</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Native articles</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Discoverability</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Guidance</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Translation</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((u) => (
            <tr key={u.key} className="border-b border-slate-100 hover:bg-slate-50" data-testid={`inventory-usertype-row-${u.key}`}>
              <td className="p-2 font-bold text-slate-900">{u.label}</td>
              <td className="p-2 text-slate-700">{u.primary_portal}</td>
              <td className="p-2 text-[12px] text-slate-500">{u.cross_portal_reads.join(", ") || "—"}</td>
              <td className="p-2 text-slate-700">{u.native_articles}</td>
              <td className="p-2"><StatusCell field={u.fields.discoverability} /></td>
              <td className="p-2"><StatusCell field={u.fields.guidance_exists} /></td>
              <td className="p-2"><StatusCell field={u.fields.translation_readiness} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RoutesTab({ rows }) {
  return (
    <div className="overflow-x-auto" data-testid="inventory-routes-tab">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-100 border-y border-slate-200">
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Public route</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Purpose</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Guidance article</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.route} className="border-b border-slate-100 hover:bg-slate-50" data-testid={`inventory-route-row-${r.route.replace(/\//g, "_")}`}>
              <td className="p-2 font-mono text-[12px] text-slate-900">{r.route}</td>
              <td className="p-2 text-slate-700">{r.purpose}</td>
              <td className="p-2 text-[12px] text-slate-500">
                {r.guidance_id ? <code>{r.guidance_id}</code> : <span className="italic">none</span>}
              </td>
              <td className="p-2">
                {r.has_guidance
                  ? <span className="inline-flex items-center gap-1 text-emerald-700"><CheckCircle2 className="w-4 h-4" />covered</span>
                  : <span className="inline-flex items-center gap-1 text-red-700"><AlertTriangle className="w-4 h-4" />gap</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function WorkflowsTab({ rows }) {
  return (
    <div className="overflow-x-auto" data-testid="inventory-workflows-tab">
      <p className="text-sm text-slate-600 mb-3">
        Cross-cutting workflows registered by the audit. Per-portal workflow coverage is shown
        separately on the Guidance Coverage page.
      </p>
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-100 border-y border-slate-200">
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Workflow</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Portal</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Guidance article</th>
            <th className="text-left p-2 font-mono text-[10px] uppercase tracking-wider text-slate-600">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((w) => (
            <tr key={w.id} className="border-b border-slate-100 hover:bg-slate-50" data-testid={`inventory-workflow-row-${w.id}`}>
              <td className="p-2 font-bold text-slate-900">{w.label}</td>
              <td className="p-2 text-slate-700">{w.portal}</td>
              <td className="p-2 text-[12px] text-slate-500">
                {w.guidance_id ? <code>{w.guidance_id}</code> : <span className="italic">none</span>}
              </td>
              <td className="p-2">
                {w.has_guidance
                  ? <span className="inline-flex items-center gap-1 text-emerald-700"><CheckCircle2 className="w-4 h-4" />covered</span>
                  : <span className="inline-flex items-center gap-1 text-red-700"><AlertTriangle className="w-4 h-4" />gap</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TranslationTab({ data }) {
  return (
    <div className="space-y-4" data-testid="inventory-translation-tab">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
        <Stat label="Total articles" value={data.total_articles} />
        <Stat label="title_es present" value={data.title_es_present} tone={data.pct_title >= 80 ? "emerald" : "red"} />
        <Stat label="body_es present"  value={data.body_es_present}  tone={data.pct_body  >= 80 ? "emerald" : "red"} />
        <Stat label="Schema landed" value={data.schema_landed ? "yes" : "no"} tone={data.schema_landed ? "emerald" : "amber"} />
      </div>
      <div className="bg-slate-50 border border-slate-200 rounded p-4 text-sm">
        <div className="font-mono text-[10px] uppercase tracking-wider text-slate-600 font-bold mb-2">
          Pass 3 expectation
        </div>
        <p className="text-slate-800">
          Wire <code>useT()</code> into the guidance Block renderer + add <code>title_es</code> /{" "}
          <code>body_es</code> fields to the article schema. Missing translation → graceful fallback to English.
          English remains canonical. This panel goes green as Pass 3 lands.
        </p>
      </div>
      <h3 className="font-bold text-slate-900 mt-4">By section</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-100 border-y border-slate-200">
              <th className="text-left p-2 font-mono text-[10px] uppercase text-slate-600">Section</th>
              <th className="text-left p-2 font-mono text-[10px] uppercase text-slate-600">Total</th>
              <th className="text-left p-2 font-mono text-[10px] uppercase text-slate-600">title_es</th>
              <th className="text-left p-2 font-mono text-[10px] uppercase text-slate-600">body_es</th>
              <th className="text-left p-2 font-mono text-[10px] uppercase text-slate-600">% body</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.by_section).map(([sid, row]) => (
              <tr key={sid} className="border-b border-slate-100">
                <td className="p-2 font-bold text-slate-900">{row.label}</td>
                <td className="p-2">{row.total}</td>
                <td className="p-2">{row.title_es}</td>
                <td className="p-2">{row.body_es}</td>
                <td className="p-2">
                  <span className={`px-1.5 py-0.5 rounded text-[11px] font-mono ${row.pct_body >= 80 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                    {row.pct_body}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3 className="font-bold text-slate-900 mt-4">By scope</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-100 border-y border-slate-200">
              <th className="text-left p-2 font-mono text-[10px] uppercase text-slate-600">Scope</th>
              <th className="text-left p-2 font-mono text-[10px] uppercase text-slate-600">Total</th>
              <th className="text-left p-2 font-mono text-[10px] uppercase text-slate-600">title_es</th>
              <th className="text-left p-2 font-mono text-[10px] uppercase text-slate-600">body_es</th>
              <th className="text-left p-2 font-mono text-[10px] uppercase text-slate-600">% body</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.by_scope).map(([sc, row]) => (
              <tr key={sc} className="border-b border-slate-100">
                <td className="p-2 font-bold text-slate-900">{sc}</td>
                <td className="p-2">{row.total}</td>
                <td className="p-2">{row.title_es}</td>
                <td className="p-2">{row.body_es}</td>
                <td className="p-2">
                  <span className={`px-1.5 py-0.5 rounded text-[11px] font-mono ${row.pct_body >= 80 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                    {row.pct_body}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DriftTab({ items, bySev }) {
  const sorted = useMemo(() => {
    const order = { p0: 0, p1: 1, p2: 2 };
    return [...items].sort((a, b) => (order[a.severity] ?? 9) - (order[b.severity] ?? 9));
  }, [items]);

  if (!items.length) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded p-6 text-center" data-testid="inventory-drift-empty">
        <CheckCircle2 className="h-10 w-10 mx-auto text-emerald-600" />
        <h3 className="mt-2 font-bold text-slate-900">No operational drift detected.</h3>
        <p className="text-sm text-slate-600 mt-1">
          Every portal has a login door, every public route has guidance, every workflow is documented.
        </p>
      </div>
    );
  }
  return (
    <div className="space-y-3" data-testid="inventory-drift-tab">
      <div className="flex gap-2 text-xs">
        <span className={`px-2 py-0.5 rounded font-mono uppercase ${SEVERITY_PILL.p0}`}>P0 · {bySev.p0}</span>
        <span className={`px-2 py-0.5 rounded font-mono uppercase ${SEVERITY_PILL.p1}`}>P1 · {bySev.p1}</span>
        <span className={`px-2 py-0.5 rounded font-mono uppercase ${SEVERITY_PILL.p2}`}>P2 · {bySev.p2}</span>
      </div>
      <ul className="space-y-2">
        {sorted.map((it, i) => (
          <li
            key={`${it.category}-${it.subject}-${i}`}
            className="border border-slate-200 rounded p-3 bg-white flex gap-3"
            data-testid={`inventory-drift-item-${it.category}-${it.subject}`}
          >
            <span className={`shrink-0 inline-flex items-center justify-center px-2 py-0.5 rounded text-[10px] font-mono uppercase ${SEVERITY_PILL[it.severity] || SEVERITY_PILL.p2}`}>
              {it.severity}
            </span>
            <div className="flex-1 min-w-0">
              <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
                {it.category} · {it.subject}
              </div>
              <div className="text-sm text-slate-900">{it.message}</div>
              {it.fix_pass && (
                <div className="mt-1 text-[11px] text-amber-700">
                  Scheduled fix: {it.fix_pass}
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
