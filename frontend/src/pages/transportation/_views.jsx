/**
 * TRACK 16.06 · Transportation Compliance Center · Views.
 * Dashboard · Compliance · Documents · Inspections · Rate Schedules ·
 * Audit Timeline · Reports.
 *
 * Workspaces (Carrier/Driver/Truck) live in ./_workspaces.jsx.
 * Lists (CarriersList/DriversList/TrucksList) live in ./_lists.jsx.
 */
import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  Users, Building2, Truck as TruckIcon, AlertTriangle, CheckCircle2,
  ClipboardCheck, FileText, DollarSign, History, RefreshCw, Search, Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import {
  Chip, PageHeader, ComingSoon, EmptyState, txGet, STATE_LABEL,
} from "./_shared";
import { RateCreateDialog, InspectionWizard } from "./_widgets";

// ───────────────────────── Dashboard ─────────────────────────
export function TransportationDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet("/admin/transportation/dashboard");
      setData(r.data);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (loading && !data) {
    return <div data-testid="tx-dashboard-loading" className="text-slate-500">Loading…</div>;
  }
  if (!data) return null;
  const t = data.tiles || {};
  const score = data.compliance_score ?? 100;

  const tiles = [
    { key: "eligible_drivers", label: "Eligible Drivers", icon: Users, link: "drivers?state=eligible", value: t.eligible_drivers },
    { key: "eligible_trucks", label: "Eligible Trucks", icon: TruckIcon, link: "trucks?state=eligible", value: t.eligible_trucks },
    { key: "eligible_carriers", label: "Eligible Carriers", icon: Building2, link: "carriers?state=eligible", value: t.eligible_carriers },
    { key: "drivers_pending_review", label: "Drivers Pending Review", icon: AlertTriangle, link: "drivers?status=pending_review", value: t.drivers_pending_review },
    { key: "trucks_pending_inspection", label: "Trucks Pending Inspection", icon: ClipboardCheck, link: "inspections", value: t.trucks_pending_inspection },
    { key: "documents_awaiting_review", label: "Documents Awaiting Review", icon: FileText, link: "documents?status=pending_review", value: t.documents_awaiting_review },
    { key: "expiring_documents_30d", label: "Expiring Documents (30d)", icon: FileText, link: "documents?expiring=30", value: t.expiring_documents_30d },
    { key: "annual_inspections_due_30d", label: "Annual Inspections Due (30d)", icon: ClipboardCheck, link: "inspections?due=30", value: t.annual_inspections_due_30d },
    { key: "pending_corrections", label: "Pending Corrections", icon: AlertTriangle, link: "documents?status=needs_correction", value: t.pending_corrections },
  ];

  return (
    <div data-testid="tx-dashboard" className="space-y-6">
      <PageHeader
        testid="tx-dashboard-header"
        title="Transportation Compliance Center"
        subtitle="Single source of truth for Dispatch, Safety, HR, Operations, and Administration."
        right={<Button variant="outline" onClick={load} data-testid="tx-dashboard-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>}
      />

      {/* Top row: compliance score + active rate */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 border border-slate-200 rounded-md bg-white p-5" data-testid="tile-compliance-score">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-slate-600">Overall Transportation Compliance</div>
            <CheckCircle2 className={`h-5 w-5 ${score >= 80 ? "text-emerald-600" : score >= 50 ? "text-amber-600" : "text-rose-600"}`} />
          </div>
          <div className="flex items-baseline gap-3">
            <div className="text-4xl font-semibold text-slate-900" data-testid="tx-score-value">{score}</div>
            <div className="text-sm text-slate-500">/ 100</div>
          </div>
          <Progress value={score} className="mt-3 h-2" />
          <div className="text-xs text-slate-500 mt-2">
            Computed from eligibility states across all carriers, drivers, and trucks.
          </div>
        </div>
        <div className="border border-slate-200 rounded-md bg-white p-5" data-testid="tile-active-rate">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-slate-600">Active Rate Schedule</div>
            <DollarSign className="h-5 w-5 text-slate-400" />
          </div>
          {data.active_rate ? (
            <>
              <div className="text-3xl font-semibold text-slate-900" data-testid="tx-active-rate-value">
                ${Number(data.active_rate.hourly_rate).toFixed(2)}<span className="text-base text-slate-500">/hr</span>
              </div>
              <div className="text-xs text-slate-500 mt-1">
                v{data.active_rate.version} · effective {(data.active_rate.effective_date || "").slice(0, 10)}
              </div>
              <Link to="rate-schedules" className="inline-block mt-2 text-xs text-blue-600 hover:underline" data-testid="tx-active-rate-link">
                View history →
              </Link>
            </>
          ) : (
            <div className="text-sm text-slate-500" data-testid="tx-no-active-rate">No active rate schedule.</div>
          )}
        </div>
      </div>

      {/* KPI tile grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="tx-kpi-grid">
        {tiles.map((tile) => (
          <Link
            key={tile.key}
            to={tile.link}
            className="border border-slate-200 rounded-md bg-white p-4 hover:border-slate-300 hover:shadow-sm transition-all"
            data-testid={`kpi-${tile.key}`}
          >
            <div className="flex items-start justify-between">
              <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{tile.label}</div>
              <tile.icon className="h-4 w-4 text-slate-400" />
            </div>
            <div className="text-2xl font-semibold text-slate-900 mt-2">{tile.value ?? 0}</div>
          </Link>
        ))}
      </div>

      <div className="text-xs text-slate-400 border-t border-slate-100 pt-3" data-testid="tx-dashboard-disclaimer">
        {data.disclaimer}
      </div>

      {/* TRACK 16.11A · HR Health widget — read-only snapshot of the
         HR ↔ Transportation sync engine. */}
      <HrHealthWidget />

      {/* TRACK 16.15A · Top Cleanup Opportunity mirror. Pure UX bridge
         — reads the Track 16.15 cleanup-signals endpoint and surfaces
         the highest-priority signal directly inside Attention Required. */}
      <TopCleanupOpportunityCard />
    </div>
  );
}

// TRACK 16.15A · Top Cleanup Opportunity mirror.
//
// Pure UX bridge — reads the existing Track 16.15 cleanup-signals
// endpoint (no new API, no new scoring) and surfaces only the
// highest-priority signal directly inside the Transportation
// Dashboard's Attention Required area.
//
// Signals are already sorted server-side: action_required first, then
// by affected_count desc, so signals[0] IS the top opportunity.
function TopCleanupOpportunityCard() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    txGet("/admin/transportation/intelligence/cleanup-signals", { days: 30 })
      .then((r) => setData(r.data))
      .catch((e) => setErr(e.message));
  }, []);

  if (err) {
    return (
      <div
        data-testid="tx-dashboard-top-cleanup-error"
        className="text-xs text-slate-400"
      >
        Cleanup signals unavailable.
      </div>
    );
  }
  if (!data) {
    return (
      <div
        data-testid="tx-dashboard-top-cleanup-loading"
        className="text-xs text-slate-400"
      >
        Loading top cleanup signal…
      </div>
    );
  }

  const signals = data.signals || [];
  const top = signals[0];
  const cleanupHref = "/admin/transportation/intelligence/cleanup";

  if (!top) {
    return (
      <section
        data-testid="tx-dashboard-top-cleanup-empty"
        className="rounded-md border border-emerald-200 bg-emerald-50 p-4"
      >
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-5 w-5 text-emerald-700" />
          <div className="text-sm font-medium text-emerald-900">
            No cleanup signals detected. Transportation data is currently in a healthy state.
          </div>
        </div>
        <div className="text-[10px] uppercase tracking-wide text-emerald-700 mt-2">
          Source: Cleanup Companion · {data.note}
        </div>
      </section>
    );
  }

  const sev = top.severity || "watch";
  const sevPalette = sev === "action_required"
    ? "border-rose-300 bg-rose-50 text-rose-800"
    : "border-amber-300 bg-amber-50 text-amber-800";

  return (
    <section
      data-testid="tx-dashboard-top-cleanup"
      className="rounded-lg border border-amber-300 bg-amber-50 p-4"
    >
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-amber-800 font-semibold">
            Attention required · Top cleanup opportunity
          </div>
          <div
            className="text-lg font-semibold text-amber-900 mt-0.5"
            data-testid="tx-dashboard-top-cleanup-title"
          >
            {top.title}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            data-testid="tx-dashboard-top-cleanup-severity"
            className={`text-[11px] px-2 py-0.5 rounded-full border ${sevPalette}`}
          >
            {String(sev).replace("_", " ")}
          </span>
          <span
            data-testid="tx-dashboard-top-cleanup-count"
            className="text-[11px] px-2 py-0.5 rounded-full border border-amber-400 bg-amber-100 text-amber-900"
          >
            {top.affected_count} affected
          </span>
        </div>
      </div>
      <div
        className="text-xs text-amber-900"
        data-testid="tx-dashboard-top-cleanup-description"
      >
        {top.description}
      </div>
      <div
        className="text-xs text-amber-900 mt-1"
        data-testid="tx-dashboard-top-cleanup-recommended"
      >
        <span className="font-medium">Recommended action: </span>{top.recommended_action}
      </div>
      <div className="mt-3">
        <Link
          to={cleanupHref}
          data-testid="tx-dashboard-top-cleanup-link"
          className="inline-flex items-center rounded bg-amber-700 hover:bg-amber-800 text-white px-3 py-1.5 text-xs font-medium"
        >
          View in Cleanup Companion →
        </Link>
      </div>
      <div className="text-[10px] uppercase tracking-wide text-amber-700 mt-2">
        Source: Cleanup Companion · signal_key={top.signal_key}
      </div>
    </section>
  );
}

// TRACK 16.11A · HR ↔ Transportation Sync Health · dashboard widget.
function HrHealthWidget() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    txGet("/admin/transportation/hr-sync")
      .then((r) => setData(r.data))
      .catch((e) => setErr(e.message));
  }, []);
  if (err) return null;
  if (!data) return (
    <div data-testid="tx-dashboard-hr-health-loading" className="text-xs text-slate-400">
      Loading HR sync health…
    </div>
  );
  const counts = data.counts || {};
  const palette = {
    healthy: "bg-emerald-100 text-emerald-800 border-emerald-300",
    warning: "bg-amber-100 text-amber-800 border-amber-300",
    critical: "bg-rose-100 text-rose-800 border-rose-300",
    unknown: "bg-slate-100 text-slate-600 border-slate-300",
  };
  const cls = palette[data.health || "unknown"];
  return (
    <div className="border border-slate-200 rounded-md bg-white p-4" data-testid="tx-dashboard-hr-health">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-semibold text-slate-700">HR Synchronization Health</div>
        <span className={`text-[11px] px-2 py-0.5 rounded-full border ${cls}`} data-testid="tx-dashboard-hr-health-chip">
          {data.health || "unknown"}
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-slate-600">
        <div data-testid="tx-dashboard-hr-mismatches">
          <div className="uppercase tracking-wide text-[10px] text-slate-500">Mismatches</div>
          <div className="text-base font-semibold text-slate-900">{counts.sync_mismatches ?? 0}</div>
        </div>
        <div>
          <div className="uppercase tracking-wide text-[10px] text-slate-500">Dispatch risks</div>
          <div className="text-base font-semibold text-slate-900">{counts.dispatch_risks ?? 0}</div>
        </div>
        <div>
          <div className="uppercase tracking-wide text-[10px] text-slate-500">Avg sync age</div>
          <div className="text-base font-semibold text-slate-900">{data.average_sync_age_days ?? "—"}d</div>
        </div>
        <div>
          <div className="uppercase tracking-wide text-[10px] text-slate-500">Oldest sync age</div>
          <div className="text-base font-semibold text-slate-900">{data.oldest_sync_age_days ?? "—"}d</div>
        </div>
      </div>
      <div className="text-[10px] uppercase tracking-wide text-slate-400 mt-3">
        Last scan: {data.last_run_at ? data.last_run_at.slice(0, 19).replace("T", " ") : "—"}
      </div>
    </div>
  );
}

// ───────────────────────── Compliance dashboard ─────────────────────────
export function ComplianceDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet("/admin/transportation/dashboard");
      setData(r.data);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (loading && !data) return <div data-testid="compliance-loading">Loading…</div>;
  if (!data) return null;

  return (
    <div data-testid="tx-compliance-page" className="space-y-4">
      <PageHeader
        title="Compliance"
        subtitle="Eligibility breakdown by carrier, driver, and truck. Click any cell to filter."
        right={<Button variant="outline" onClick={load} data-testid="compliance-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>}
      />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ComplianceColumn title="Carriers" testid="cc-carriers" buckets={data.buckets?.carrier || {}} link="carriers" />
        <ComplianceColumn title="Drivers" testid="cc-drivers" buckets={data.buckets?.person || {}} link="drivers" />
        <ComplianceColumn title="Trucks" testid="cc-trucks" buckets={data.buckets?.truck || {}} link="trucks" />
      </div>
    </div>
  );
}

function ComplianceColumn({ title, testid, buckets, link }) {
  const total = Object.values(buckets || {}).reduce((a, b) => a + (b || 0), 0);
  const order = ["eligible", "pending_review", "needs_correction", "suspended", "expired", "not_dispatchable"];
  return (
    <div className="border border-slate-200 rounded-md bg-white p-4" data-testid={testid}>
      <div className="flex items-center justify-between mb-3">
        <div className="font-medium text-slate-900">{title}</div>
        <span className="text-xs text-slate-500">{total} total</span>
      </div>
      <div className="space-y-2">
        {order.map((state) => (
          <Link
            key={state}
            to={`${link}?state=${state}`}
            className="flex items-center justify-between hover:bg-slate-50 rounded px-2 py-1.5"
            data-testid={`${testid}-row-${state}`}
          >
            <Chip value={state} />
            <span className="text-sm font-medium text-slate-700">{buckets[state] || 0}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

// ───────────────────────── Document Center ─────────────────────────
export function DocumentCenter() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("");
  const [scope, setScope] = useState("all");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (status) params.status = status;
      if (scope && scope !== "all") params.scope = scope;
      const r = await txGet("/admin/transportation/documents/queue", params);
      setItems(r.data.items || []);
    } finally {
      setLoading(false);
    }
  }, [status, scope]);
  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid="tx-document-center" className="space-y-4">
      <PageHeader title="Document Center" subtitle="Review queue across all carrier and driver documents." />
      <div className="flex flex-wrap items-end gap-3" data-testid="doc-filters">
        <div>
          <Label className="text-xs">Status</Label>
          <Select value={status || "all"} onValueChange={(v) => setStatus(v === "all" ? "" : v)}>
            <SelectTrigger className="w-48" data-testid="doc-filter-status"><SelectValue placeholder="All" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="pending_review">Pending Review</SelectItem>
              <SelectItem value="accepted">Accepted</SelectItem>
              <SelectItem value="needs_correction">Needs Correction</SelectItem>
              <SelectItem value="expired">Expired</SelectItem>
              <SelectItem value="not_applicable">Not Applicable</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-xs">Scope</Label>
          <Select value={scope} onValueChange={setScope}>
            <SelectTrigger className="w-40" data-testid="doc-filter-scope"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="carrier">Carrier</SelectItem>
              <SelectItem value="driver">Driver</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button variant="outline" onClick={load} data-testid="doc-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
      </div>

      {loading ? <div data-testid="doc-loading">Loading…</div> : (
        items.length === 0 ? (
          <EmptyState title="No documents match this filter" hint="Try clearing filters." testid="doc-empty" />
        ) : (
          <div className="overflow-x-auto border border-slate-200 rounded">
            <table className="w-full text-sm" data-testid="doc-table">
              <thead className="bg-slate-50 text-left">
                <tr>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Scope</th>
                  <th className="px-3 py-2">Filename</th>
                  <th className="px-3 py-2">Uploaded</th>
                  <th className="px-3 py-2">Expires</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2 text-right">Review</th>
                </tr>
              </thead>
              <tbody>
                {items.map((d) => (
                  <DocRow key={d.id} doc={d} onChanged={load} />
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  );
}

function DocRow({ doc, onChanged }) {
  const [busy, setBusy] = useState(false);
  async function review(status) {
    setBusy(true);
    try {
      const path = doc.scope === "carrier"
        ? `/admin/transportation/documents/${doc.id}/review`
        : `/admin/transportation/driver-documents/${doc.id}/review`;
      const { api } = await import("@/lib/api");
      const { adminHeaders } = await import("./_shared");
      await api.patch(path, { status }, { headers: adminHeaders() });
      onChanged && onChanged();
    } finally { setBusy(false); }
  }
  return (
    <tr className="border-t border-slate-100" data-testid={`doc-row-${doc.id}`}>
      <td className="px-3 py-2 font-medium">{doc.document_type}</td>
      <td className="px-3 py-2 text-slate-600">{doc.scope}</td>
      <td className="px-3 py-2 truncate max-w-xs" title={doc.original_filename}>{doc.original_filename || "—"}</td>
      <td className="px-3 py-2 text-slate-600">{(doc.uploaded_at || "").slice(0, 10)}</td>
      <td className="px-3 py-2 text-slate-600">{doc.expires_at ? doc.expires_at.slice(0, 10) : "—"}</td>
      <td className="px-3 py-2"><Chip value={doc.status} /></td>
      <td className="px-3 py-2 text-right">
        {doc.status !== "accepted" && (
          <Button
            size="sm" variant="ghost"
            onClick={() => review("accepted")}
            disabled={busy}
            data-testid={`doc-accept-${doc.id}`}
            className="text-emerald-700 hover:bg-emerald-50"
          >Accept</Button>
        )}
        {doc.status !== "needs_correction" && (
          <Button
            size="sm" variant="ghost"
            onClick={() => review("needs_correction")}
            disabled={busy}
            data-testid={`doc-needs-correction-${doc.id}`}
            className="text-amber-700 hover:bg-amber-50"
          >Needs Correction</Button>
        )}
      </td>
    </tr>
  );
}

// ───────────────────────── Inspection Center ─────────────────────────
export function InspectionCenter() {
  const [items, setItems] = useState([]);
  const [disclaimer, setDisclaimer] = useState("");
  const [loading, setLoading] = useState(true);
  const [trigger, setTrigger] = useState("");
  const [result, setResult] = useState("");
  const [trucks, setTrucks] = useState([]);
  const [selectedTruck, setSelectedTruck] = useState("");
  const [wizardOpen, setWizardOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (trigger) params.trigger = trigger;
      if (result) params.result = result;
      const r = await txGet("/admin/transportation/inspections/queue", params);
      setItems(r.data.items || []);
      setDisclaimer(r.data.disclaimer || "");
      const t = await txGet("/admin/transportation/trucks");
      setTrucks(t.data.items || []);
    } finally {
      setLoading(false);
    }
  }, [trigger, result]);
  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid="tx-inspection-center" className="space-y-4">
      <PageHeader
        title="Inspection Center"
        subtitle="MASCI Hauler Truck Readiness Inspections · operational readiness only."
        right={
          <div className="flex items-center gap-2">
            <Select value={selectedTruck} onValueChange={setSelectedTruck}>
              <SelectTrigger className="w-56" data-testid="insp-launcher-truck-select">
                <SelectValue placeholder="Select truck…" />
              </SelectTrigger>
              <SelectContent>
                {trucks.map((t) => <SelectItem key={t.id} value={t.id}>{t.truck_number} · {t.ownership}</SelectItem>)}
              </SelectContent>
            </Select>
            <Button
              onClick={() => setWizardOpen(true)}
              disabled={!selectedTruck}
              data-testid="insp-launcher-start-btn"
            >
              <ClipboardCheck className="h-4 w-4 mr-1" />Start Inspection
            </Button>
          </div>
        }
      />
      <div className="flex flex-wrap items-end gap-3" data-testid="insp-filters">
        <div>
          <Label className="text-xs">Trigger</Label>
          <Select value={trigger || "all"} onValueChange={(v) => setTrigger(v === "all" ? "" : v)}>
            <SelectTrigger className="w-56" data-testid="insp-filter-trigger"><SelectValue placeholder="All triggers" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All triggers</SelectItem>
              {["initial_onboarding", "annual_recertification", "random", "safety_concern",
                "customer_complaint", "incident_or_accident", "vehicle_replacement",
                "major_modification", "management_requested", "dispatch_requested",
                "safety_requested"].map((t) => <SelectItem key={t} value={t}>{t.replace(/_/g, " ")}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-xs">Result</Label>
          <Select value={result || "all"} onValueChange={(v) => setResult(v === "all" ? "" : v)}>
            <SelectTrigger className="w-44" data-testid="insp-filter-result"><SelectValue placeholder="All results" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All results</SelectItem>
              {["ready", "pending_correction", "not_ready", "expired"].map((r) =>
                <SelectItem key={r} value={r}>{r.replace(/_/g, " ")}</SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>
        <Button variant="outline" onClick={load} data-testid="insp-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
      </div>

      {loading ? <div data-testid="insp-loading">Loading…</div> : (
        items.length === 0 ? (
          <EmptyState title="No inspections match this filter" testid="insp-empty" />
        ) : (
          <div className="overflow-x-auto border border-slate-200 rounded">
            <table className="w-full text-sm" data-testid="insp-table">
              <thead className="bg-slate-50 text-left">
                <tr>
                  <th className="px-3 py-2">Truck</th>
                  <th className="px-3 py-2">Trigger</th>
                  <th className="px-3 py-2">Inspector</th>
                  <th className="px-3 py-2">Inspected</th>
                  <th className="px-3 py-2">Expires</th>
                  <th className="px-3 py-2">Result</th>
                </tr>
              </thead>
              <tbody>
                {items.map((i) => (
                  <tr key={i.id} className="border-t border-slate-100" data-testid={`insp-row-${i.id}`}>
                    <td className="px-3 py-2 font-mono text-xs">{i.transport_truck_id?.slice(0, 8)}…</td>
                    <td className="px-3 py-2 text-slate-700">{(i.trigger || "").replace(/_/g, " ")}</td>
                    <td className="px-3 py-2">{i.inspector_name || "—"}</td>
                    <td className="px-3 py-2 text-slate-600">{(i.inspected_at || "").slice(0, 10)}</td>
                    <td className="px-3 py-2 text-slate-600">{i.expires_at ? i.expires_at.slice(0, 10) : "—"}</td>
                    <td className="px-3 py-2"><Chip value={i.result} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
      {disclaimer && (
        <div className="text-xs text-slate-500 border-t border-slate-100 pt-3" data-testid="insp-disclaimer">
          {disclaimer}
        </div>
      )}

      <InspectionWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        truckId={selectedTruck}
        onComplete={() => load()}
        testid="insp-center-wizard"
      />
    </div>
  );
}

// ───────────────────────── Rate Schedule Center ─────────────────────────
export function RateScheduleCenter() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet("/admin/transportation/rate-schedules");
      setItems(r.data.items || []);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const active = items.find((x) => x.status === "active");
  const history = items.filter((x) => x.id !== active?.id);

  return (
    <div data-testid="tx-rate-center" className="space-y-4">
      <PageHeader
        title="Rate Schedules"
        subtitle="Versioned hourly rate. Historic packets always retain their original locked rate."
        right={
          <>
            <Button variant="outline" onClick={load} data-testid="rate-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
            <Button onClick={() => setDialogOpen(true)} data-testid="rate-new-btn"><Plus className="h-4 w-4 mr-1" />New Version</Button>
          </>
        }
      />

      {active && (
        <div className="border border-emerald-200 bg-emerald-50/50 rounded-md p-4" data-testid="rate-active-card">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-xs uppercase tracking-wide text-emerald-700 font-medium">Active</div>
              <div className="text-3xl font-semibold text-slate-900 mt-1" data-testid="rate-active-value">
                ${Number(active.hourly_rate).toFixed(2)}<span className="text-base text-slate-500">/hr</span>
              </div>
              <div className="text-xs text-slate-600 mt-1">
                v{active.version} · effective {(active.effective_date || "").slice(0, 10)} · updated by {active.updated_by}
              </div>
            </div>
            <Chip value="active" />
          </div>
          <details className="mt-3 text-xs text-slate-600">
            <summary className="cursor-pointer text-slate-700 font-medium">Payment, ticket, and deduction rules</summary>
            <pre className="whitespace-pre-wrap mt-2 text-xs leading-relaxed">{active.payment_rules_text}</pre>
            <pre className="whitespace-pre-wrap mt-2 text-xs leading-relaxed">{active.ticket_rules_text}</pre>
            <pre className="whitespace-pre-wrap mt-2 text-xs leading-relaxed">{active.deduction_rules_text}</pre>
          </details>
        </div>
      )}

      <div className="overflow-x-auto border border-slate-200 rounded">
        <table className="w-full text-sm" data-testid="rate-history-table">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-3 py-2">Version</th>
              <th className="px-3 py-2">Hourly Rate</th>
              <th className="px-3 py-2">Effective</th>
              <th className="px-3 py-2">Updated By</th>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-3 py-4 text-center text-slate-500" data-testid="rate-loading">Loading…</td></tr>
            ) : history.length === 0 && !active ? (
              <tr><td colSpan={5} className="px-3 py-4 text-center text-slate-500" data-testid="rate-empty">No rate schedules yet.</td></tr>
            ) : (
              items.map((r) => (
                <tr key={r.id} className="border-t border-slate-100" data-testid={`rate-row-${r.id}`}>
                  <td className="px-3 py-2 font-medium">v{r.version}</td>
                  <td className="px-3 py-2">${Number(r.hourly_rate).toFixed(2)}</td>
                  <td className="px-3 py-2 text-slate-600">{(r.effective_date || "").slice(0, 10)}</td>
                  <td className="px-3 py-2 text-slate-600">{r.updated_by}</td>
                  <td className="px-3 py-2"><Chip value={r.status} /></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <RateCreateDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onCreated={() => load()}
      />
    </div>
  );
}

// ───────────────────────── Audit Timeline ─────────────────────────
export function AuditTimeline() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet("/admin/transportation/audit-timeline");
      setItems(r.data.items || []);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid="tx-audit-timeline" className="space-y-4">
      <PageHeader
        title="Audit Timeline"
        subtitle="Transportation-scoped view of the platform's unified audit ledger. Read-only."
        right={<Button variant="outline" onClick={load} data-testid="audit-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>}
      />
      {loading ? <div data-testid="audit-loading">Loading…</div> : (
        items.length === 0 ? (
          <EmptyState title="No audit events yet" hint="Audit events appear as carriers, drivers, trucks, packets, documents, and inspections are created or updated." testid="audit-empty" />
        ) : (
          <div className="space-y-2" data-testid="audit-list">
            {items.map((e) => (
              <div key={e.id} className="border border-slate-200 rounded p-3 bg-white" data-testid={`audit-row-${e.id}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-slate-900 truncate">{e.kind}</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {e.entity_type} · {(e.entity_id || "").slice(0, 12)}… · by {e.actor || "—"}
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 whitespace-nowrap">
                    {(e.ts || "").replace("T", " ").slice(0, 19)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
}

// ───────────────────────── Reports (placeholder) ─────────────────────────
export function ReportsView() {
  return (
    <div data-testid="tx-reports" className="space-y-4">
      <PageHeader
        title="Reports"
        subtitle="Operational and compliance exports for Transportation."
      />
      <ComingSoon feature="CSV / PDF exports across carriers, drivers, trucks, documents, and inspections" testid="reports-coming-soon" />
    </div>
  );
}
