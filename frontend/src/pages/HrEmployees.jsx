// HrEmployees.jsx — Iter152 (Phase C). HR Portal employee lifecycle
// management. Route: /hr/employees.
//
// Capabilities:
//   * List employees with default = "actively employed" only.
//   * "Show inactive" toggle to surface Terminated / Retired / etc.
//   * Add Employee dialog.
//   * Click row → side drawer with Edit / Status / Offboarding Summary tabs.
//   * Auto-offboarding playbook fires server-side when status →
//     Terminated/Resigned/Retired.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Users, Plus, Search, ArrowLeft, Home, RefreshCw,
  UserCheck, UserMinus, Briefcase, AlertOctagon, CheckCircle2,
  ChevronRight, FileText, ClipboardList, Wrench,
  Printer, Download, X, Bookmark,
} from "lucide-react";
import axios from "axios";
import { getHrToken } from "@/lib/hrAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle,
} from "@/components/ui/sheet";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { PortalShell } from "@/design-system";
import HrSideNavV2 from "@/components/hr/sidebar/HrSideNavV2";
import NotificationBell from "@/components/NotificationBell";
import {
  listHrEmployees, createHrEmployee, patchHrEmployee,
  changeHrEmployeeStatus, offboardingSummary, reactivateHrEmployee,
  LIFECYCLE_STATUSES, EMPLOYMENT_BUCKETS, statusesForBucket,
  fetchHrFacets,
} from "@/lib/employeesApi";
import { useRememberedFilter } from "@/lib/useRememberedFilter";
import { friendlyError } from "@/lib/friendlyErrors";
import { isHr } from "@/lib/hrAuth";
import { isAdmin, getAdminToken } from "@/lib/adminAuth";
import AccessDenied from "@/pages/AccessDenied";
import { toast } from "sonner";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import GlobalSearch from "@/components/GlobalSearch";
import { LIFECYCLE_STATUS_TINTS } from "@/lib/statusBadges";
import { HelpTip, HelpTipBlock } from "@/components/HelpTip";
import { useT } from "@/lib/i18n";
import { formatEmployeeIdentity } from "@/lib/identity";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const SEPARATION_TYPES = ["voluntary", "involuntary", "layoff"];
const DRIVER_STATUSES = ["active", "suspended", "restricted", "inactive"];

// iter287 · CDL endorsements + restrictions — structured codes only.
// Order is operator-facing display order (N first because MASCI uses
// Tanker most often for asphalt-oil tanker assignments).
const CDL_ENDORSEMENTS = [
  { code: "N", label: "Tanker (N)" },
  { code: "H", label: "Hazmat (H)" },
  { code: "X", label: "Tanker + Hazmat (X)" },
  { code: "T", label: "Doubles/Triples (T)" },
  { code: "P", label: "Passenger (P)" },
  { code: "S", label: "School Bus (S)" },
];
const CDL_RESTRICTIONS = [
  { code: "air_brake", label: "Air Brake Restriction" },
  { code: "manual_transmission", label: "Manual Transmission Restriction" },
];

const STATUS_COLORS = LIFECYCLE_STATUS_TINTS;

export default function HrEmployees() {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const initialQ = searchParams.get("q") || "";
  const allowed = isHr() || isAdmin();
  // TRACK 27.00 · Bucket is now the primary employment filter. The
  // legacy `show_inactive` toggle is removed — bucket=any is its
  // replacement. Detailed status becomes a secondary filter.
  const [bucket, setBucket] = useRememberedFilter("hr.employees.bucket_v2", "active");
  const [statusFilter, setStatusFilter] = useRememberedFilter("hr.employees.status", "all");
  const [rehireFilter, setRehireFilter] = useRememberedFilter("hr.employees.rehire_eligibility", "all");
  const [crewFilter, setCrewFilter] = useRememberedFilter("hr.employees.crew", "all");
  const [supervisorFilter, setSupervisorFilter] = useRememberedFilter("hr.employees.supervisor", "all");
  const [tradeFilter, setTradeFilter] = useRememberedFilter("hr.employees.trade", "all");
  const [q, setQ] = useState(initialQ);
  const [items, setItems] = useState([]);
  const [totalMatching, setTotalMatching] = useState(0);
  const [truncated, setTruncated] = useState(false);
  const [warning, setWarning] = useState(null);
  const [facets, setFacets] = useState({ crews: [], supervisors: [], trades: [], buckets: [] });
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [editId, setEditId] = useState(null);
  const [editTab, setEditTab] = useState("details");

  // Available detailed statuses depend on the picked bucket.
  const bucketStatuses = statusesForBucket(bucket);   // null = any
  const availableStatuses = bucketStatuses || LIFECYCLE_STATUSES;

  // If bucket narrows and current status is outside it, snap status to "all".
  useEffect(() => {
    if (statusFilter !== "all" && bucketStatuses && !bucketStatuses.includes(statusFilter)) {
      setStatusFilter("all");
    }
  }, [bucket]);

  const fetchAll = useCallback(async () => {
    if (!allowed) { setLoading(false); return; }
    setLoading(true);
    try {
      const params = {
        bucket,
        ...(statusFilter !== "all" ? { lifecycle_status: statusFilter } : {}),
        ...(rehireFilter !== "all" ? { rehire_eligibility: rehireFilter } : {}),
        ...(crewFilter !== "all" ? { crew: crewFilter } : {}),
        ...(supervisorFilter !== "all" ? { supervisor: supervisorFilter } : {}),
        ...(tradeFilter !== "all" ? { trade: tradeFilter } : {}),
        ...(q ? { q } : {}),
      };
      const r = await listHrEmployees(params);
      setItems(r.items || []);
      setTotalMatching(r.total_matching ?? (r.items?.length || 0));
      setTruncated(!!r.truncated);
      setWarning(r.warning || null);
    } catch (e) {
      toast.error(friendlyError(e, "Could not load employees"));
    } finally { setLoading(false); }
  }, [allowed, bucket, statusFilter, rehireFilter, crewFilter, supervisorFilter, tradeFilter, q]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Load facets once on mount; refetch after any employee write so
  // new crew/supervisor/trade values appear immediately.
  useEffect(() => {
    fetchHrFacets().then(setFacets).catch(() => {});
  }, []);

  // Track 15.21A · Build the exact query string the export endpoint
  // needs from the live filter state so the .xlsx mirrors the on-screen
  // roster row-for-row (same dataset, same count, zero drift).
  const buildExportParams = useCallback(() => {
    const p = new URLSearchParams();
    if (bucket && bucket !== "any") p.set("bucket", bucket);
    if (bucket === "any") p.set("bucket", "any");
    if (statusFilter !== "all") p.set("lifecycle_status", statusFilter);
    if (rehireFilter !== "all") p.set("rehire_eligibility", rehireFilter);
    if (crewFilter !== "all") p.set("crew", crewFilter);
    if (supervisorFilter !== "all") p.set("supervisor", supervisorFilter);
    if (tradeFilter !== "all") p.set("trade", tradeFilter);
    if (q) p.set("q", q);
    return p;
  }, [bucket, statusFilter, rehireFilter, crewFilter, supervisorFilter, tradeFilter, q]);

  const onPrint = useCallback(() => {
    // Use the browser's native print pipeline. The scoped @media print
    // stylesheet (below) hides chrome and renders only the roster.
    if (typeof window !== "undefined") window.print();
  }, []);

  const [exporting, setExporting] = useState(false);
  const onExportXlsx = useCallback(async () => {
    if (exporting) return;
    setExporting(true);
    try {
      const params = buildExportParams();
      const url = `${process.env.REACT_APP_BACKEND_URL}/api/hr/employees/export.xlsx`;
      const headers = {};
      const hr = getHrToken(); if (hr) headers["X-HR-Token"] = hr;
      const ad = getAdminToken(); if (ad) headers["X-Admin-Token"] = ad;
      const resp = await axios.get(url, {
        headers, params, responseType: "blob",
      });
      const today = new Date().toISOString().slice(0, 10);
      const blobUrl = URL.createObjectURL(resp.data);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `MASCI_HR_Employee_Roster_${today}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 250);
      toast.success(`Exported ${items.length} employee${items.length === 1 ? "" : "s"}`);
    } catch (e) {
      toast.error(friendlyError(e, "Could not export roster"));
    } finally { setExporting(false); }
  }, [exporting, buildExportParams, items.length]);

  // TRACK 27.00 · KPI cards read from the current items array so the
  // table row count and each KPI number are always in lockstep. If a
  // user narrows the filter to Retired, they'll see:
  //   Retired: 12 · Total in View: 12 · rows in table: 12
  // — one truth source, five reflections of it.
  const counts = useMemo(() => {
    const buckets = { active: 0, pending: 0, off_roll: 0, terminated: 0, retired: 0 };
    items.forEach((e) => {
      const s = e.lifecycle_status || (e.is_active === false ? "Inactive" : "Active");
      if (["Active", "Seasonal", "Leave of Absence"].includes(s)) buckets.active++;
      else if (s === "Pending Hire") buckets.pending++;
      else if (["Inactive", "Suspended"].includes(s)) buckets.off_roll++;
      else if (["Terminated", "Resigned"].includes(s)) buckets.terminated++;
      else if (s === "Retired") buckets.retired++;
      else buckets.off_roll++;   // fail-closed
    });
    return buckets;
  }, [items]);

  // Filter chip descriptors — one per active narrowing. Chips are
  // individually removable so HR can undo one filter at a time
  // instead of resetting everything.
  const activeChips = useMemo(() => {
    const chips = [];
    if (bucket !== "any") chips.push({ key: "bucket", label: EMPLOYMENT_BUCKETS.find((b) => b.value === bucket)?.label || bucket, onClear: () => setBucket("any") });
    if (statusFilter !== "all") chips.push({ key: "status", label: `Status: ${statusFilter}`, onClear: () => setStatusFilter("all") });
    if (crewFilter !== "all") chips.push({ key: "crew", label: `Crew: ${crewFilter}`, onClear: () => setCrewFilter("all") });
    if (supervisorFilter !== "all") chips.push({ key: "supervisor", label: `Supervisor: ${supervisorFilter}`, onClear: () => setSupervisorFilter("all") });
    if (tradeFilter !== "all") chips.push({ key: "trade", label: `Trade: ${tradeFilter}`, onClear: () => setTradeFilter("all") });
    if (rehireFilter !== "all") chips.push({ key: "rehire", label: `Rehire: ${rehireFilter.replace(/_/g, " ")}`, onClear: () => setRehireFilter("all") });
    if (q) chips.push({ key: "q", label: `Search: "${q}"`, onClear: () => setQ("") });
    return chips;
  }, [bucket, statusFilter, crewFilter, supervisorFilter, tradeFilter, rehireFilter, q, setBucket, setCrewFilter, setRehireFilter, setStatusFilter, setSupervisorFilter, setTradeFilter]);

  const resetFilters = useCallback(() => {
    setBucket("active");
    setStatusFilter("all");
    setCrewFilter("all");
    setSupervisorFilter("all");
    setTradeFilter("all");
    setRehireFilter("all");
    setQ("");
  }, [setBucket, setStatusFilter, setCrewFilter, setSupervisorFilter, setTradeFilter, setRehireFilter]);

  // TRACK 27.00 · 12 approved saved views (Section 5 of the audit).
  // These are pre-filled filter states — no new endpoint, no new
  // data model. `applyView({...})` merges partial filter overrides
  // into the current state so each view leaves other filters at
  // their defaults.
  const applyView = useCallback((v) => {
    resetFilters();
    if (v.bucket) setBucket(v.bucket);
    if (v.crew) setCrewFilter(v.crew);
    if (v.supervisor) setSupervisorFilter(v.supervisor);
    if (v.rehire) setRehireFilter(v.rehire);
    if (v.status) setStatusFilter(v.status);
  }, [resetFilters, setBucket, setCrewFilter, setSupervisorFilter, setRehireFilter, setStatusFilter]);

  const savedViews = useMemo(() => ([
    { id: "all-active",       label: "All Actively Employed", apply: { bucket: "active" } },
    { id: "paving-crew",      label: "Paving Crew",           apply: { bucket: "active", crew: "Paving" } },
    { id: "concrete-crew",    label: "Concrete Crew",         apply: { bucket: "active", crew: "Concrete" } },
    { id: "shop-crew",        label: "Shop",                  apply: { bucket: "active", crew: "Shop" } },
    { id: "safety-crew",      label: "Safety",                apply: { bucket: "active", crew: "Safety" } },
    { id: "utility-crew",     label: "Utility",               apply: { bucket: "active", crew: "Utility" } },
    { id: "milling-crew",     label: "Milling",               apply: { bucket: "active", crew: "Milling" } },
    { id: "mot-crew",         label: "MOT",                   apply: { bucket: "active", crew: "MOT" } },
    { id: "terminated",       label: "Terminated / Separated", apply: { bucket: "terminated" } },
    { id: "retired",          label: "Retired Employees",     apply: { bucket: "retired" } },
    { id: "rehire-eligible",  label: "Rehire Eligible",       apply: { rehire: "eligible" } },
    { id: "missing-super",    label: "Missing Supervisor",    apply: { bucket: "active", supervisor: "(unassigned)" } },
    { id: "no-crew",          label: "No Crew Assigned",      apply: { bucket: "active", crew: "(unassigned)" } },
  ]), []);


  if (!allowed) return <AccessDenied attemptedPortal="hr" />;

  return (
    <PortalShell
      portalName="MASCI" portalRole="HR Portal · Employee Lifecycle"
      pageTitle="Employees"
      subtitle="Directory · lifecycle · identity"
      sideNav={<HrSideNavV2 />}
    >
    <div className="min-h-screen" data-testid="hr-employees-page">
      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-6 sm:py-8">
        <HelpTipBlock formKey="employee-lifecycle" showCounter />

        {/* TRACK 27.00 · KPI cards. All numbers derive from `items`,
            which is the same array the table below iterates, so KPI
            counts and table row count can never drift. */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-4" data-testid="hremp-kpi-row">
          <SummaryTile label="Actively Employed" value={counts.active} icon={UserCheck} accent="emerald" />
          <SummaryTile label="Pending / Onboarding" value={counts.pending} icon={Briefcase} accent="blue" />
          <SummaryTile label="Off-roll / Inactive" value={counts.off_roll} icon={UserMinus} accent="slate" />
          <SummaryTile label="Terminated" value={counts.terminated} icon={AlertOctagon} accent="rose" />
          <SummaryTile label="Retired" value={counts.retired} icon={CheckCircle2} accent="purple" />
          <SummaryTile label="Total in View" value={items.length} icon={Users} accent="amber" />
        </div>

        {/* TRACK 27.00 · Saved views strip. Twelve pre-filled filter
            states approved by HR. Click = reset then apply. */}
        <div className="flex flex-wrap gap-1.5 mb-3" data-testid="hremp-saved-views">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 self-center mr-1">
            <Bookmark className="w-3 h-3 inline mr-1" /> Quick views:
          </span>
          {savedViews.map((v) => (
            <button
              key={v.id}
              type="button"
              onClick={() => applyView(v.apply)}
              className="px-2.5 py-1 rounded border border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-400 text-[11px] font-medium text-slate-700 transition"
              data-testid={`hremp-view-${v.id}`}
            >
              {v.label}
            </button>
          ))}
        </div>

        {/* TRACK 27.00 · Filter bar. Every filter has an honest
            fallback ("(unassigned)" for blank crew/supervisor/trade).
            No hardcoded crews or supervisors — the dropdowns pull
            from /api/hr/employees/facets. */}
        <div className="bg-white border border-slate-200 rounded-md p-3 sm:p-4 mb-3 flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">Group</span>
            <Select value={bucket} onValueChange={setBucket}>
              <SelectTrigger className="w-[190px] h-9 text-xs" data-testid="hremp-bucket-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EMPLOYMENT_BUCKETS.map((b) => (
                  <SelectItem key={b.value} value={b.value} data-testid={`hremp-bucket-opt-${b.value}`}>
                    {b.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">Status</span>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[160px] h-9 text-xs" data-testid="hremp-status-filter">
                <SelectValue placeholder="Any" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any status</SelectItem>
                {availableStatuses.map((s) => (
                  <SelectItem key={s} value={s} data-testid={`hremp-status-opt-${s.replace(/\s+/g,'-')}`}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Select value={crewFilter} onValueChange={setCrewFilter}>
            <SelectTrigger className="w-[150px] h-9 text-xs" data-testid="hremp-crew-filter">
              <SelectValue placeholder="Crew" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Any crew</SelectItem>
              {(facets.crews || []).map((c) => (
                <SelectItem key={c.value} value={c.value} data-testid={`hremp-crew-opt-${c.value.replace(/\W+/g,'-')}`}>
                  {c.label} <span className="text-slate-400">· {c.count}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={supervisorFilter} onValueChange={setSupervisorFilter}>
            <SelectTrigger className="w-[170px] h-9 text-xs" data-testid="hremp-supervisor-filter">
              <SelectValue placeholder="Supervisor" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Any supervisor</SelectItem>
              {(facets.supervisors || []).map((s) => (
                <SelectItem key={s.value} value={s.value} data-testid={`hremp-supervisor-opt-${s.value.replace(/\W+/g,'-')}`}>
                  {s.label} <span className="text-slate-400">· {s.count}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={tradeFilter} onValueChange={setTradeFilter}>
            <SelectTrigger className="w-[160px] h-9 text-xs" data-testid="hremp-trade-filter">
              <SelectValue placeholder="Trade / Role" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Any trade</SelectItem>
              {(facets.trades || []).map((t) => (
                <SelectItem key={t.value} value={t.value} data-testid={`hremp-trade-opt-${t.value.replace(/\W+/g,'-')}`}>
                  {t.label} <span className="text-slate-400">· {t.count}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={rehireFilter} onValueChange={setRehireFilter}>
            <SelectTrigger className="w-[170px] h-9 text-xs" data-testid="hremp-rehire-filter">
              <SelectValue placeholder="Rehire eligibility" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Any rehire status</SelectItem>
              <SelectItem value="eligible">Rehire Eligible</SelectItem>
              <SelectItem value="not_eligible">Not Rehire Eligible</SelectItem>
              <SelectItem value="review_required">Review Required</SelectItem>
            </SelectContent>
          </Select>

          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <Input
              value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Search name, ID, trade, crew, supervisor…"
              className="pl-8 h-9 text-xs"
              data-testid="hremp-search-input"
            />
          </div>

          <Button variant="outline" size="sm" onClick={resetFilters} className="text-xs" data-testid="hremp-reset-filters" data-print-hide>
            <X className="w-3.5 h-3.5 mr-1" /> Reset
          </Button>
          <Button variant="outline" size="sm" onClick={fetchAll} className="text-xs" data-testid="hremp-refresh" data-print-hide>
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
          <Button
            variant="outline" size="sm" onClick={onPrint}
            className="text-xs" data-testid="hremp-print" data-print-hide
            disabled={loading || items.length === 0}
            title="Print the roster shown below"
          >
            <Printer className="w-3.5 h-3.5 mr-1" /> Print
          </Button>
          <Button
            variant="outline" size="sm" onClick={onExportXlsx}
            className="text-xs" data-testid="hremp-export-xlsx" data-print-hide
            disabled={loading || items.length === 0 || exporting}
            title="Download the roster shown below as an Excel file"
          >
            <Download className="w-3.5 h-3.5 mr-1" /> {exporting ? "Exporting…" : "Export Excel"}
          </Button>
          <AddDialog
            open={addOpen}
            setOpen={setAddOpen}
            onSaved={(e) => {
              setAddOpen(false);
              if (e && e.openDrawerId) {
                setEditId(e.openDrawerId);
              }
              fetchAll();
              fetchHrFacets().then(setFacets).catch(() => {});
            }}
          />
        </div>

        {/* TRACK 27.00 · Honest result summary line. This count MUST
            equal the KPI Total-in-View tile AND the number of rows in
            the table AND the export .xlsx row count AND the print
            output row count. If it ever doesn't, something upstream
            is lying. */}
        <div className="flex flex-wrap items-center gap-2 mb-3 text-xs" data-testid="hremp-result-summary">
          <span className="font-medium text-slate-700" data-testid="hremp-result-count">
            Showing <strong>{items.length}</strong>{" "}
            {items.length === 1 ? "employee" : "employees"}
            {truncated && (
              <span className="ml-1 text-amber-700" data-testid="hremp-truncated">
                (first {items.length} of <strong>{totalMatching}</strong> — narrow filters to see all)
              </span>
            )}
            {!truncated && totalMatching > 0 && bucket !== "any" && (
              <span className="ml-1 text-slate-500">· matches filter</span>
            )}
          </span>
          {activeChips.map((c) => (
            <button
              key={c.key}
              type="button"
              onClick={c.onClear}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 border border-slate-300 text-[11px] text-slate-700 hover:bg-slate-200"
              data-testid={`hremp-chip-${c.key}`}
              title="Remove this filter"
            >
              {c.label} <X className="w-3 h-3" />
            </button>
          ))}
        </div>

        {/* TRACK 27.00 · Impossible-intersection warning banner. */}
        {warning && warning.code === "impossible_intersection" && (
          <div
            className="mb-3 p-3 rounded-md border border-amber-300 bg-amber-50 text-amber-900 text-xs"
            role="alert"
            data-testid="hremp-warning-impossible"
          >
            <div className="font-semibold mb-0.5">Filter combination has no matches</div>
            <div>{warning.message}</div>
          </div>
        )}

        {/* TRACK 27.02 · Empty-state banner. When any filter is active
            AND the result is 0 (but not an impossible intersection),
            explain which filters are narrowing the view so HR can
            fix the search instead of thinking the page is broken. */}
        {!loading && !warning && items.length === 0 && activeChips.length > 0 && (
          <div
            className="mb-3 p-3 rounded-md border border-slate-300 bg-slate-50 text-slate-700 text-xs"
            data-testid="hremp-empty-state"
          >
            <div className="font-semibold mb-0.5">No employees match your filters</div>
            <div>
              Active filters:{" "}
              <span className="font-mono">
                {activeChips.map((c) => c.label).join(" · ")}
              </span>
            </div>
            <button
              type="button"
              onClick={resetFilters}
              className="mt-1.5 text-slate-600 hover:text-slate-900 underline text-[11px]"
              data-testid="hremp-empty-reset"
            >
              Reset filters
            </button>
          </div>
        )}

        {loading ? (
          <div className="bg-white border border-slate-200 rounded-md py-10 text-center text-slate-500 text-sm">Loading…</div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No employees match the current filter"
            hint="Try clearing the search box, adjusting the status filter, or toggling Show Inactive."
            testId="hremp-empty"
          />
        ) : (
          <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr className="text-left text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">Legal Name</th>
                  <th className="px-4 py-2.5">Preferred Name</th>
                  <th className="px-4 py-2.5">Trade / Role</th>
                  <th className="px-4 py-2.5">Crew</th>
                  <th className="px-4 py-2.5">Supervisor</th>
                  <th className="px-4 py-2.5">Accountability</th>
                  <th className="px-4 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((e) => {
                  const status = e.lifecycle_status || (e.is_active === false ? "Inactive" : "Active");
                  // Track 14.0 · HR Identity Directory column rule:
                  //   Legal Name    = first + last when stored, else
                  //                   the denormalised `name` so the
                  //                   row never reads as blank for
                  //                   legacy records.
                  //   Preferred     = preferred_name only, with a
                  //                   clean em-dash placeholder when
                  //                   no preferred is on file.
                  const legalParts = [e.legal_first_name, e.legal_last_name].filter(Boolean).join(" ");
                  const legalName = legalParts || e.name || "—";
                  const preferred = (e.preferred_name || "").trim();
                  return (
                    <tr
                      key={e.id}
                      onClick={() => { setEditTab("details"); setEditId(e.id); }}
                      className="hover:bg-slate-50 cursor-pointer"
                      data-testid={`hremp-row-${e.id}`}
                    >
                      <td className="px-4 py-2.5">
                        <button
                          type="button"
                          onClick={(ev) => { ev.stopPropagation(); setEditTab("status"); setEditId(e.id); }}
                          className="cursor-pointer"
                          data-testid={`hremp-status-badge-${e.id}`}
                          aria-label="Edit status"
                        >
                          <StatusBadge kind="lifecycle" value={status} size="sm" />
                        </button>
                      </td>
                      <td className="px-4 py-2.5 font-bold text-slate-900" data-testid={`hremp-row-legal-name-${e.id}`}>
                        {legalName}
                      </td>
                      <td
                        className={`px-4 py-2.5 text-sm ${preferred ? "text-slate-900 font-semibold italic" : "text-slate-300"}`}
                        data-testid={`hremp-row-preferred-name-${e.id}`}
                      >
                        {preferred || "—"}
                      </td>
                      <td className="px-4 py-2.5 text-slate-600 text-xs">{e.trade || "—"} {e.role && <span className="text-slate-400">· {e.role}</span>}</td>
                      <td className="px-4 py-2.5 text-slate-600 text-xs">{e.crew || "—"}</td>
                      <td className="px-4 py-2.5 text-slate-600 text-xs">{e.supervisor || "—"}</td>
                      <td className="px-4 py-2.5">
                        <Link
                          to={`/hr/employees/${e.id}/accountability`}
                          onClick={(ev) => ev.stopPropagation()}
                          className="inline-flex items-center gap-1 text-[11px] font-mono uppercase tracking-wider text-purple-800 hover:text-purple-900 hover:underline"
                          data-testid={`hremp-acct-link-${e.id}`}
                        >
                          <ClipboardList className="w-3 h-3" /> Accountability
                        </Link>
                      </td>
                      <td className="px-4 py-2.5"><ChevronRight className="w-4 h-4 text-slate-300" /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {/* Track 15.21A · PRINT-ONLY ROSTER
          Hidden on screen; appears only when the browser is in print
          preview / paper output. Mirrors the export .xlsx column-for-
          column so the same 9 fields land on paper and in Excel. */}
      <div className="hr-print-only" data-print-only data-testid="hremp-print-region">
        <div className="hr-print-header">
          <div className="hr-print-title">MASCI Employee Roster</div>
          <div className="hr-print-meta">
            {formatPlatformDate()}
            {" · "}
            {EMPLOYMENT_BUCKETS.find((b) => b.value === bucket)?.label || bucket}
            {statusFilter !== "all" ? ` · status: ${statusFilter}` : ""}
            {crewFilter !== "all" ? ` · crew: ${crewFilter}` : ""}
            {supervisorFilter !== "all" ? ` · supervisor: ${supervisorFilter}` : ""}
            {tradeFilter !== "all" ? ` · trade: ${tradeFilter}` : ""}
            {rehireFilter !== "all" ? ` · rehire: ${rehireFilter}` : ""}
            {q ? ` · search: “${q}”` : ""}
            {" · "}
            <span data-testid="hremp-print-count">{items.length}</span>
            {" "}{items.length === 1 ? "employee" : "employees"}
          </div>
        </div>
        <table className="hr-print-table">
          <thead>
            <tr>
              <th>Employee Name</th>
              <th>Preferred Name</th>
              <th>Status</th>
              <th>Position</th>
              <th>Department</th>
              <th>Phone</th>
              <th>Email</th>
              <th>Hire Date</th>
              <th>Supervisor</th>
            </tr>
          </thead>
          <tbody>
            {items.map((e) => {
              const legalParts = [e.legal_first_name, e.legal_last_name].filter(Boolean).join(" ");
              const legalName = legalParts || e.name || "";
              const status = e.lifecycle_status || (e.is_active === false ? "Inactive" : "Active");
              return (
                <tr key={`print-${e.id}`} data-testid={`hremp-print-row-${e.id}`}>
                  <td>{legalName}</td>
                  <td>{e.preferred_name || ""}</td>
                  <td>{status}</td>
                  <td>{e.role || ""}</td>
                  <td>{e.department || ""}</td>
                  <td>{e.phone || ""}</td>
                  <td>{e.email || ""}</td>
                  <td>{e.original_hire_date || e.hire_date || ""}</td>
                  <td>{e.supervisor || ""}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Scoped print stylesheet — hides screen chrome, reveals the
          print-only region, paginates the table cleanly. */}
      <style>{`
        .hr-print-only { display: none; }
        @media print {
          @page { size: landscape; margin: 0.4in; }
          html, body { background: #fff !important; }
          /* Hide every interactive surface on the screen. */
          aside, nav, header, [data-print-hide],
          [data-testid="hr-employees-page"] > main > :not(.hr-print-only) {
            display: none !important;
          }
          /* Reveal & isolate the print-only region. */
          [data-testid="hr-employees-page"] { display: block !important; }
          [data-testid="hr-employees-page"] > main {
            max-width: none !important; padding: 0 !important; margin: 0 !important;
          }
          .hr-print-only {
            display: block !important;
            color: #000;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
          }
          .hr-print-header {
            margin: 0 0 12pt 0;
            padding: 0 0 8pt 0;
            border-bottom: 1.5pt solid #000;
          }
          .hr-print-title { font-size: 16pt; font-weight: 700; letter-spacing: 0.5pt; }
          .hr-print-meta { font-size: 9pt; color: #333; margin-top: 3pt; }
          .hr-print-table { width: 100%; border-collapse: collapse; font-size: 8.5pt; }
          .hr-print-table thead { display: table-header-group; } /* repeat header on each page */
          .hr-print-table th {
            text-align: left; font-weight: 700; font-size: 7.5pt;
            text-transform: uppercase; letter-spacing: 0.4pt;
            border-bottom: 1pt solid #000; padding: 4pt 6pt 4pt 0; vertical-align: bottom;
          }
          .hr-print-table td {
            padding: 3.5pt 6pt 3.5pt 0; border-bottom: 0.4pt solid #999;
            vertical-align: top; line-height: 1.25;
          }
          .hr-print-table tr { page-break-inside: avoid; }
        }
      `}</style>

      <EmployeeDrawer
        id={editId}
        initialTab={editTab}
        onClose={() => { setEditId(null); setEditTab("details"); fetchAll(); }}
      />
    </div>
    </PortalShell>
  );
}

function SummaryTile({ label, value, icon: Icon, accent }) {
  const palette = {
    emerald: "border-emerald-300 text-emerald-900",
    slate: "border-slate-300 text-slate-700",
    blue: "border-blue-300 text-blue-900",
    rose: "border-rose-300 text-rose-900",
    purple: "border-purple-300 text-purple-900",
    amber: "border-amber-300 text-amber-900",
  }[accent] || "border-slate-300 text-slate-900";
  return (
    <div className={`bg-white border-2 ${palette} rounded-md p-3`} data-testid={`hremp-summary-${label.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')}`}>
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 opacity-70" />
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-80 font-bold">{label}</span>
      </div>
      <div className="font-display text-2xl font-black mt-1 leading-none">{value}</div>
    </div>
  );
}

function AddDialog({ open, setOpen, onSaved }) {
  const [form, setForm] = useState({
    name: "", trade: "", role: "", crew: "", employee_id: "", email: "",
    phone: "", supervisor: "", department: "", default_project_number: "",
    lifecycle_status: "Active", hire_date: "",
  });
  // iter316 · informational duplicate warning state. When the backend
  // returns a `possible_existing_inactive` payload we show the
  // candidate row and let HR either Reactivate or force-create.
  const [dupCandidate, setDupCandidate] = useState(null);

  const submitInternal = async (force) => {
    if (!form.name.trim()) { toast.error("Name is required"); return; }
    try {
      const r = await createHrEmployee(form, { force });
      toast.success(`Added ${r.name}`);
      onSaved(r);
      setForm({ ...form, name: "", employee_id: "", email: "", phone: "" });
      setDupCandidate(null);
    } catch (e2) {
      // iter316 · detect structured inactive-match payload.
      const detail = e2?.response?.data?.detail;
      if (detail && typeof detail === "object" && detail.error === "possible_existing_inactive") {
        setDupCandidate(detail.candidate || null);
        return;
      }
      toast.error(friendlyError(e2, "Could not save employee"));
    }
  };
  const submit = (e) => { e.preventDefault(); submitInternal(false); };
  const submitForce = () => submitInternal(true);
  const goReactivate = () => {
    if (dupCandidate?.id) {
      setOpen(false);
      onSaved({ openDrawerId: dupCandidate.id });
    }
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" className="text-xs" data-testid="hremp-add-trigger">
          <Plus className="w-3.5 h-3.5 mr-1" /> Add Employee
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg" data-testid="hremp-add-dialog">
        <DialogHeader><DialogTitle>Add Employee</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
            <div className="sm:col-span-2">
              <Label>Name *</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="hremp-add-name" />
            </div>
            <div>
              <Label>Employee ID</Label>
              <Input value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })} data-testid="hremp-add-empid" />
            </div>
            <div>
              <Label>Status</Label>
              <Select value={form.lifecycle_status} onValueChange={(v) => setForm({ ...form, lifecycle_status: v })}>
                <SelectTrigger data-testid="hremp-add-status"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {LIFECYCLE_STATUSES.map((s) => (<SelectItem key={s} value={s}>{s}</SelectItem>))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Trade</Label>
              <Input value={form.trade} onChange={(e) => setForm({ ...form, trade: e.target.value })} data-testid="hremp-add-trade" />
            </div>
            <div>
              <Label>Role / Title</Label>
              <Input value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} />
            </div>
            <div>
              <Label>Crew</Label>
              <Input value={form.crew} onChange={(e) => setForm({ ...form, crew: e.target.value })} />
            </div>
            <div>
              <Label>Supervisor</Label>
              <Input value={form.supervisor} onChange={(e) => setForm({ ...form, supervisor: e.target.value })} />
            </div>
            <div>
              <Label>Department</Label>
              <Input value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
            </div>
            <div>
              <Label>Hire Date</Label>
              <Input type="date" value={form.hire_date} onChange={(e) => setForm({ ...form, hire_date: e.target.value })} />
            </div>
            <div>
              <Label>Email</Label>
              <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div>
              <Label>Phone</Label>
              <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
          </div>
          {dupCandidate && (
            <div
              className="rounded-md border-2 border-amber-300 bg-amber-50 p-3 text-xs text-amber-900"
              data-testid="hremp-add-dup-warning"
            >
              <div className="font-bold uppercase tracking-wider text-[10px] text-amber-700 mb-1">
                Possible existing inactive/terminated employee
              </div>
              <div>
                <span className="font-bold">{dupCandidate.name}</span>
                {dupCandidate.employee_id && (
                  <span className="text-amber-700"> · ID {dupCandidate.employee_id}</span>
                )}
                {dupCandidate.email && (
                  <span className="text-amber-700"> · {dupCandidate.email}</span>
                )}
                <div className="mt-0.5">
                  Status:{" "}
                  <span className="font-bold">{dupCandidate.lifecycle_status}</span>
                  {dupCandidate.termination_date && (
                    <span className="text-amber-700">
                      {" "}· terminated {dupCandidate.termination_date}
                    </span>
                  )}
                  {dupCandidate.rehire_eligibility && (
                    <span className="text-amber-700">
                      {" "}· rehire eligibility:{" "}
                      <span className="font-bold">{dupCandidate.rehire_eligibility}</span>
                    </span>
                  )}
                </div>
                <div className="mt-2 text-amber-900/90">
                  Reactivate this existing employee instead of creating a duplicate?
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                <Button
                  type="button"
                  size="sm"
                  className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs"
                  data-testid="hremp-add-dup-reactivate"
                  onClick={goReactivate}
                >
                  Open & reactivate existing record
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="text-xs border-amber-500 text-amber-900"
                  data-testid="hremp-add-dup-force"
                  onClick={submitForce}
                >
                  Create new record anyway
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="text-xs"
                  onClick={() => setDupCandidate(null)}
                  data-testid="hremp-add-dup-dismiss"
                >
                  Edit details
                </Button>
              </div>
            </div>
          )}
          <DialogFooter className="gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)} data-testid="hremp-add-cancel">Cancel</Button>
            <Button type="submit" data-testid="hremp-add-submit">Save</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function EmployeeDrawer({ id, onClose, initialTab = "details" }) {
  const { t } = useT();
  const [employee, setEmployee] = useState(null);
  const [summary, setSummary] = useState(null);
  // iter453.5 REC-2 · honour caller's requested initial tab; re-seed when id changes
  // so successive drawer opens (Edit row vs Status badge click) land on the right tab.
  const [tab, setTab] = useState(initialTab || "details");
  useEffect(() => { setTab(initialTab || "details"); }, [id, initialTab]);
  const [statusForm, setStatusForm] = useState({
    lifecycle_status: "Active",
    reason: "",
    separation_type: "",
    termination_date: "",
    last_day_worked: "",
    leave_start_date: "",
    expected_return_date: "",
    // iter316 · rehire eligibility on offboarding transitions.
    rehire_eligibility: "",
    rehire_eligibility_reason: "",
  });
  const [saving, setSaving] = useState(false);
  // iter316 · reactivate-dialog state.
  const [reactivateOpen, setReactivateOpen] = useState(false);
  const [reactivateForm, setReactivateForm] = useState({
    lifecycle_status: "Active",
    rehire_date: "",
    reason: "",
  });
  // Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE — employee's
  // active project assignments. Read-only · live · honest empty state.
  const [projectAssignments, setProjectAssignments] = useState({ loaded: false, items: [] });

  useEffect(() => {
    if (!id) { setEmployee(null); setSummary(null); setProjectAssignments({ loaded: false, items: [] }); return; }
    offboardingSummary(id).then((s) => {
      setSummary(s);
      setEmployee(s.employee);
      setStatusForm({
        lifecycle_status: s.lifecycle_status || "Active",
        reason: "",
        separation_type: "",
        termination_date: "",
        last_day_worked: "",
        leave_start_date: "",
        expected_return_date: "",
        rehire_eligibility: "",
        rehire_eligibility_reason: "",
      });
      // Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE — fetch
      // active project_team_assignments for this employee. Use email
      // (preferred resolution key); falls back to employee id.
      const key = s?.employee?.email || s?.employee?.id || id;
      const API = process.env.REACT_APP_BACKEND_URL;
      const hrTok = (typeof window !== "undefined" && window.localStorage)
        ? (window.localStorage.getItem("masci.hr.token") || window.localStorage.getItem("masci.admin.token"))
        : null;
      const headers = hrTok
        ? { "X-HR-Token": window.localStorage.getItem("masci.hr.token") || "", "X-Admin-Token": window.localStorage.getItem("masci.admin.token") || "" }
        : {};
      fetch(`${API}/api/employees/${encodeURIComponent(key)}/project-assignments`, { headers })
        .then((r) => r.ok ? r.json() : { items: [] })
        .then((body) => setProjectAssignments({ loaded: true, items: body.items || [] }))
        .catch(() => setProjectAssignments({ loaded: true, items: [] }));
    }).catch(() => setEmployee(null));
  }, [id]);

  const submitStatusChange = async () => {
    if (!employee) return;
    const prevStatus = summary?.lifecycle_status || employee.lifecycle_status || "Active";
    const isOffboarding = ["Terminated", "Resigned", "Retired"].includes(statusForm.lifecycle_status);
    const wasOffboarded = ["Terminated", "Resigned", "Retired"].includes(summary?.lifecycle_status);
    const offboardingTransition = isOffboarding && !wasOffboarded;
    // iter453.9 · validation toasts use a 6 s duration so HR has time
    // to perceive them before they auto-dismiss. Prefixed with the
    // word "Required" so the user can never mistake them for a noop
    // or a success.
    const VALIDATION_OPTS = { duration: 6000 };
    if (offboardingTransition && !statusForm.separation_type && !employee.separation_type) {
      toast.error(t("Required: pick a separation type — voluntary, involuntary, or layoff"), VALIDATION_OPTS);
      return;
    }
    if (offboardingTransition && !statusForm.rehire_eligibility && !employee.rehire_eligibility) {
      toast.error(t("Required: pick a rehire eligibility — Eligible, Not Eligible, or Review Required"), VALIDATION_OPTS);
      return;
    }
    if (
      offboardingTransition
      && ["not_eligible", "review_required"].includes(statusForm.rehire_eligibility)
      && !statusForm.rehire_eligibility_reason.trim()
      && !employee.rehire_eligibility_reason
    ) {
      toast.error(t("Required: add a short reason for this rehire eligibility decision"), VALIDATION_OPTS);
      return;
    }
    setSaving(true);
    try {
      const payload = {
        lifecycle_status: statusForm.lifecycle_status,
        reason: statusForm.reason,
      };
      if (statusForm.separation_type) payload.separation_type = statusForm.separation_type;
      if (statusForm.termination_date) payload.termination_date = statusForm.termination_date;
      if (statusForm.last_day_worked) payload.last_day_worked = statusForm.last_day_worked;
      if (statusForm.leave_start_date) payload.leave_start_date = statusForm.leave_start_date;
      if (statusForm.expected_return_date) payload.expected_return_date = statusForm.expected_return_date;
      if (statusForm.rehire_eligibility) payload.rehire_eligibility = statusForm.rehire_eligibility;
      if (statusForm.rehire_eligibility_reason)
        payload.rehire_eligibility_reason = statusForm.rehire_eligibility_reason;
      const r = await changeHrEmployeeStatus(employee.id, statusForm.lifecycle_status, statusForm.reason, payload);
      // iter453.9 · differentiate noop vs real save with explicit
      // before/after labels so HR can never wonder "did it work?".
      const newStatus = r?.employee?.lifecycle_status || statusForm.lifecycle_status;
      if (r.noop) {
        toast.info(
          `${t("No changes detected")} · ${t("status was already")} ${prevStatus}`,
          { duration: 6000 },
        );
        setSaving(false);
        return;
      }
      const transitionLabel = `${prevStatus} → ${newStatus}`;
      const headline = r.playbook_fired
        ? `${t("Employee status changed")} · ${transitionLabel} · ${r.tasks_created} ${t("offboarding tasks created")}`
        : `${t("Employee status changed")} · ${transitionLabel}`;
      toast.success(headline, { duration: 6000 });
      // iter453.9 · refresh the drawer state BEFORE closing so the
      // parent table picks up the new lifecycle_status on its next
      // render cycle, then auto-close so HR sees the table row
      // visibly reflect the change.
      const s = await offboardingSummary(employee.id);
      setSummary(s);
      setEmployee(s.employee);
      setSaving(false);
      // Small delay lets the toast register in the user's eye before
      // the drawer animates closed (Sheet close animation ≈ 220 ms).
      setTimeout(() => { onClose && onClose(); }, 400);
      return;
    } catch (e) {
      toast.error(friendlyError(e, t("Status change failed")), { duration: 6000 });
    } finally { setSaving(false); }
  };

  // iter316 · reactivate / rehire action.
  const submitReactivate = async () => {
    if (!employee) return;
    setSaving(true);
    try {
      const r = await reactivateHrEmployee(employee.id, {
        lifecycle_status: reactivateForm.lifecycle_status,
        rehire_date: reactivateForm.rehire_date || undefined,
        reason: reactivateForm.reason || undefined,
      });
      toast.success(
        `${t("Reactivated")} · ${t("rehire date")}: ${r.employee?.rehire_date || "—"}`,
      );
      setReactivateOpen(false);
      const s = await offboardingSummary(employee.id);
      setSummary(s);
      setEmployee(s.employee);
    } catch (e) {
      toast.error(friendlyError(e, t("Reactivation failed")));
    } finally { setSaving(false); }
  };

  const submitEdit = async (patch) => {
    if (!employee) return;
    setSaving(true);
    try {
      const r = await patchHrEmployee(employee.id, patch);
      setEmployee(r);
      toast.success(t("Employee updated"));
    } catch (e) { toast.error(friendlyError(e, t("Update failed"))); }
    finally { setSaving(false); }
  };

  return (
    <Sheet open={!!id} onOpenChange={(v) => !v && onClose()}>
      <SheetContent side="right" className="w-full sm:max-w-xl p-0 flex flex-col" data-testid="hremp-drawer">
        {!employee ? (
          <div className="p-6 text-slate-500 text-sm">Loading…</div>
        ) : (
          <>
            <SheetHeader className="px-5 pt-5 pb-3 border-b border-slate-200">
              <SheetTitle className="font-display text-base leading-snug" data-testid="hremp-drawer-title">
                {formatEmployeeIdentity(employee) || employee.name}
              </SheetTitle>
              <div className="flex items-center gap-2 mt-2 flex-wrap text-xs">
                <StatusBadge kind="lifecycle" value={summary?.lifecycle_status} size="sm" />
                {employee.trade && <span className="text-slate-600">{employee.trade}</span>}
                {employee.employee_id && <span className="text-slate-500 font-mono text-[10px]">#{employee.employee_id}</span>}
              </div>
              {/* iter353c · View Accountability Timeline */}
              <Link
                to={`/hr/employees/${id}/accountability`}
                className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 border border-purple-300 bg-purple-50 hover:bg-purple-100 text-purple-900 rounded text-xs font-mono uppercase tracking-wider w-fit"
                data-testid="hremp-drawer-acct-link"
              >
                <ClipboardList className="w-3.5 h-3.5" /> View Accountability Timeline
              </Link>
            </SheetHeader>
            <Tabs value={tab} onValueChange={setTab} className="flex-1 flex flex-col min-h-0">
              <TabsList className="rounded-none border-b border-slate-200 px-5">
                <TabsTrigger value="details" data-testid="hremp-tab-details">Details</TabsTrigger>
                <TabsTrigger value="status" data-testid="hremp-tab-status">Status</TabsTrigger>
                <TabsTrigger value="offboarding" data-testid="hremp-tab-offboarding">Offboarding Summary</TabsTrigger>
                <TabsTrigger value="transportation" data-testid="hremp-tab-transportation">Transportation</TabsTrigger>
              </TabsList>
              <div className="flex-1 min-h-0 overflow-y-auto px-5 py-4 text-sm">
                <TabsContent value="details" className="mt-0 space-y-3">
                  {/* HR-EMPLOYEE-001 · P0 — Employee name is editable here.
                      Backend audit-trails every change as kind=name_changed
                      under employee_lifecycle_events (old_value/new_value/
                      actor/timestamp). Historical records (DRs, meetings,
                      inspections, signatures) are NOT rewritten — they keep
                      whatever name was captured at the time. */}
                  <EditField label={t("Name") + " / " + t("Legal Name")} value={employee.name} save={(v) => submitEdit({ name: v })} testid="hremp-edit-name" />
                  {/* HR-EMPLOYEE-002 · Preferred name */}
                  <EditField label={t("Preferred Name")} value={employee.preferred_name || ""} save={(v) => submitEdit({ preferred_name: v })} testid="hremp-edit-preferred-name" />
                  <div className="text-[11px] text-slate-500 -mt-1 pl-1" data-testid="hremp-pref-name-hint">
                    Preferred name is used for display/search where appropriate. Legal/current name remains the HR record.
                  </div>
                  <EditField label="Trade" value={employee.trade} save={(v) => submitEdit({ trade: v })} testid="hremp-edit-trade" />
                  <EditField label="Role / Title" value={employee.role} save={(v) => submitEdit({ role: v })} />
                  <EditField label="Crew" value={employee.crew} save={(v) => submitEdit({ crew: v })} />
                  <EditField label="Supervisor" value={employee.supervisor} save={(v) => submitEdit({ supervisor: v })} />
                  <EditField label="Department" value={employee.department} save={(v) => submitEdit({ department: v })} />
                  <EditField label="Default Project #" value={employee.default_project_number} save={(v) => submitEdit({ default_project_number: v })} />

                  {/* Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE
                      Live project assignments for this employee. */}
                  <div className="py-2 border-t border-slate-100" data-testid="hremp-project-assignments">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Project Assignments
                        {projectAssignments.loaded && (
                          <span className="ml-2 inline-block text-[10px] font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">
                            {projectAssignments.items.length}
                          </span>
                        )}
                      </span>
                    </div>
                    {!projectAssignments.loaded && (
                      <p className="text-xs text-slate-400 italic">Loading…</p>
                    )}
                    {projectAssignments.loaded && projectAssignments.items.length === 0 && (
                      <p className="text-xs text-slate-500 italic">
                        Not currently assigned to any project. Assign from{" "}
                        <a href="/admin/project-staffing" className="underline text-amber-700" data-testid="hremp-assign-link">
                          Project Staffing
                        </a>
                        {" "}or open a project&apos;s Team page.
                      </p>
                    )}
                    {projectAssignments.loaded && projectAssignments.items.length > 0 && (
                      <ul className="space-y-1 mt-1">
                        {projectAssignments.items.map((a) => (
                          <li
                            key={a.id}
                            className="text-xs flex items-center justify-between gap-2 bg-slate-50 px-2 py-1.5 rounded"
                            data-testid={`hremp-assignment-${a.id}`}
                          >
                            <div>
                              <span className="font-mono font-bold text-slate-900">{a.project_number}</span>
                              <span className="ml-2 text-slate-600">{a.role_label || a.assignment_role}</span>
                              {a.is_primary && <span className="ml-2 text-amber-600 font-medium">★ primary</span>}
                            </div>
                            <a
                              href={`/admin/jobs/${encodeURIComponent(a.project_number)}/team`}
                              className="text-amber-700 hover:text-amber-900 underline"
                              data-testid={`hremp-assignment-link-${a.id}`}
                            >
                              Manage →
                            </a>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <EditField label="Email" value={employee.email} save={(v) => submitEdit({ email: v })} />
                  <EditField label="Phone" value={employee.phone} save={(v) => submitEdit({ phone: v })} />
                  <EditField label="Hire Date" value={employee.hire_date} save={(v) => submitEdit({ hire_date: v })} />

                  <div className="pt-3 border-t border-slate-200">
                    <HelpTipBlock formKey="employee-lifecycle.lifecycle-dates" />
                  </div>
                  <EditField
                    label={t("Original Hire Date") + (employee.original_hire_date ? " · " + t("write-once · already set") : "")}
                    value={employee.original_hire_date}
                    save={(v) => submitEdit({ original_hire_date: v })}
                    testid="hremp-edit-original-hire"
                  />
                  {employee.tenure_days != null && (
                    <div className="flex items-center justify-between py-1 text-sm" data-testid="hremp-tenure">
                      <span className="text-slate-600">{t("Tenure")}</span>
                      <span className="font-mono text-slate-900 font-bold">
                        {employee.tenure_days} {t("days")}
                        {employee.tenure_days >= 365 && (
                          <span className="text-slate-500 ml-2">({Math.floor(employee.tenure_days / 365)} {t("yr")})</span>
                        )}
                      </span>
                    </div>
                  )}
                  <EditField label={t("Last Day Worked")} value={employee.last_day_worked} save={(v) => submitEdit({ last_day_worked: v })} testid="hremp-edit-last-day" />
                  <EditField label={t("Termination Date")} value={employee.termination_date} save={(v) => submitEdit({ termination_date: v })} testid="hremp-edit-term-date" />
                  <EditField label={t("Leave Start Date")} value={employee.leave_start_date} save={(v) => submitEdit({ leave_start_date: v })} testid="hremp-edit-leave-start" />
                  <EditField label={t("Expected Return Date")} value={employee.expected_return_date} save={(v) => submitEdit({ expected_return_date: v })} testid="hremp-edit-leave-return" />
                  {employee.separation_type && (
                    <div className="flex items-center justify-between py-1 text-sm" data-testid="hremp-separation-type-display">
                      <span className="text-slate-600">{t("Separation Type")}</span>
                      <span className="font-mono text-slate-900 font-bold uppercase">{t(employee.separation_type)}</span>
                    </div>
                  )}
                  {/* iter316 · Rehire eligibility display + reactivate action */}
                  {employee.rehire_eligibility && (
                    <div className="flex items-center justify-between py-1 text-sm" data-testid="hremp-rehire-eligibility-display">
                      <span className="text-slate-600">{t("Rehire Eligibility")}</span>
                      <span className={
                        "font-mono font-bold uppercase " +
                        (employee.rehire_eligibility === "eligible"
                          ? "text-emerald-700"
                          : employee.rehire_eligibility === "not_eligible"
                          ? "text-rose-700"
                          : "text-amber-700")
                      }>
                        {t(
                          employee.rehire_eligibility === "eligible" ? "Rehire Eligible"
                          : employee.rehire_eligibility === "not_eligible" ? "Not Rehire Eligible"
                          : "Review Required",
                        )}
                      </span>
                    </div>
                  )}
                  {employee.rehire_eligibility_reason && (
                    <div className="py-1 text-xs" data-testid="hremp-rehire-eligibility-reason-display">
                      <div className="text-slate-500 font-mono uppercase tracking-wider text-[10px]">{t("Rehire eligibility reason")}</div>
                      <div className="text-slate-800 mt-0.5">{employee.rehire_eligibility_reason}</div>
                    </div>
                  )}
                  {employee.rehire_date && (
                    <div className="flex items-center justify-between py-1 text-sm" data-testid="hremp-rehire-date-display">
                      <span className="text-slate-600">{t("Rehire Date")}</span>
                      <span className="font-mono text-slate-900 font-bold">{employee.rehire_date}</span>
                    </div>
                  )}
                  {["Inactive", "Terminated", "Resigned", "Retired"].includes(summary?.lifecycle_status) && (
                    <div className="pt-3 mt-3 border-t border-slate-200" data-testid="hremp-reactivate-block">
                      <Button
                        type="button"
                        size="sm"
                        className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs"
                        data-testid="hremp-reactivate-trigger"
                        onClick={() => {
                          setReactivateForm({
                            lifecycle_status: "Active",
                            rehire_date: new Date().toISOString().slice(0, 10),
                            reason: "",
                          });
                          setReactivateOpen(true);
                        }}
                      >
                        {t("Reactivate / Rehire Employee")}
                      </Button>
                      <div className="text-xs text-slate-500 mt-1.5">
                        {t("Preserves original hire date · records new rehire date · keeps prior termination in history")}
                      </div>
                    </div>
                  )}

                  {/* iter286 · Driver Qualification card */}
                  <div className="pt-3 mt-3 border-t border-slate-200" data-testid="hremp-driver-qualification">
                    <h4 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-2">{t("Driver Qualification")}</h4>
                    <HelpTipBlock formKey="driver-qualification" />
                    <HelpTipBlock formKey="driver-qualification.cdl-vs-approved" />

                    <div className="flex items-center justify-between py-2 border-b border-slate-100">
                      <Label htmlFor="cdl-holder-switch" className="text-sm">{t("CDL Holder")}</Label>
                      <Switch
                        id="cdl-holder-switch"
                        checked={Boolean(employee.cdl_holder)}
                        onCheckedChange={(v) => submitEdit({ cdl_holder: v })}
                        data-testid="hremp-cdl-holder"
                      />
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-slate-100">
                      <Label htmlFor="approved-driver-switch" className="text-sm">{t("Approved Company Driver")}</Label>
                      <Switch
                        id="approved-driver-switch"
                        checked={Boolean(employee.approved_company_driver)}
                        onCheckedChange={(v) => submitEdit({ approved_company_driver: v })}
                        data-testid="hremp-approved-driver"
                      />
                    </div>
                    {employee.approved_company_driver && (
                      <div className="py-2">
                        <Label className="text-sm">{t("Driver Status")}</Label>
                        <Select value={employee.driver_status || ""} onValueChange={(v) => submitEdit({ driver_status: v })}>
                          <SelectTrigger data-testid="hremp-driver-status"><SelectValue placeholder={t("Pick a status")} /></SelectTrigger>
                          <SelectContent>
                            {DRIVER_STATUSES.map((s) => (<SelectItem key={s} value={s}>{t(s)}</SelectItem>))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                    <EditField label={t("CDL License Number")} value={employee.cdl_license_number} save={(v) => submitEdit({ cdl_license_number: v })} testid="hremp-cdl-number" />
                    <EditField label={t("CDL State")} value={employee.cdl_state} save={(v) => submitEdit({ cdl_state: v })} testid="hremp-cdl-state" />
                    <HelpTipBlock formKey="driver-qualification.expirations" />
                    <EditField label={t("CDL Expiration Date")} value={employee.cdl_expiration_date} save={(v) => submitEdit({ cdl_expiration_date: v })} testid="hremp-cdl-exp" />
                    <EditField label={t("Medical Card Expiration Date")} value={employee.medical_card_expiration_date} save={(v) => submitEdit({ medical_card_expiration_date: v })} testid="hremp-med-card-exp" />

                    {/* iter287 · CDL Endorsements (structured codes) */}
                    <div className="pt-3 mt-3 border-t border-slate-100" data-testid="hremp-cdl-endorsements">
                      <h5 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-2">{t("CDL Endorsements")}</h5>
                      <HelpTipBlock formKey="driver-qualification.endorsements" />
                      {CDL_ENDORSEMENTS.map(({ code, label }) => {
                        const current = Array.isArray(employee.cdl_endorsements) ? employee.cdl_endorsements : [];
                        const checked = current.includes(code);
                        return (
                          <div key={code} className="flex items-center justify-between py-1.5 border-b border-slate-100">
                            <Label htmlFor={`endorsement-${code}`} className="text-sm">{t(label)}</Label>
                            <Switch
                              id={`endorsement-${code}`}
                              checked={checked}
                              onCheckedChange={(v) => {
                                const next = v ? [...current.filter((c) => c !== code), code] : current.filter((c) => c !== code);
                                submitEdit({ cdl_endorsements: next });
                              }}
                              data-testid={`hremp-endorsement-${code}`}
                            />
                          </div>
                        );
                      })}
                    </div>

                    {/* iter287 · CDL Restrictions (structured codes) */}
                    <div className="pt-3 mt-3 border-t border-slate-100" data-testid="hremp-cdl-restrictions">
                      <h5 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-2">{t("CDL Restrictions")}</h5>
                      <HelpTipBlock formKey="driver-qualification.restrictions" />
                      {CDL_RESTRICTIONS.map(({ code, label }) => {
                        const current = Array.isArray(employee.cdl_restrictions) ? employee.cdl_restrictions : [];
                        const checked = current.includes(code);
                        return (
                          <div key={code} className="flex items-center justify-between py-1.5 border-b border-slate-100">
                            <Label htmlFor={`restriction-${code}`} className="text-sm">{t(label)}</Label>
                            <Switch
                              id={`restriction-${code}`}
                              checked={checked}
                              onCheckedChange={(v) => {
                                const next = v ? [...current.filter((c) => c !== code), code] : current.filter((c) => c !== code);
                                submitEdit({ cdl_restrictions: next });
                              }}
                              data-testid={`hremp-restriction-${code}`}
                            />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </TabsContent>
                <TabsContent value="status" className="mt-0 space-y-3">
                  <HelpTipBlock formKey="employee-lifecycle.separation" />
                  {/* iter453.5 REC-3 · Lifecycle vocabulary guide (operator-approved copy) */}
                  <HelpTip
                    kind="example"
                    title="Employee Lifecycle Guide — pick the right status"
                    defaultOpen={false}
                    testId="lifecycle-vocabulary"
                    body={
                      <ul className="list-disc pl-4 space-y-0.5">
                        <li><b>Resigned</b> — Employee voluntarily quit</li>
                        <li><b>Terminated</b> — Company initiated separation</li>
                        <li><b>Layoff</b> — Workforce reduction / business decision (pick Terminated + Layoff)</li>
                        <li><b>Active</b> — Current employee</li>
                        <li><b>Leave of Absence</b> — Temporarily inactive</li>
                        <li><b>Reactivated</b> — Returned to active employment (use Reactivate button)</li>
                      </ul>
                    }
                  />
                  <div>
                    <Label>{t("New status")}</Label>
                    <Select value={statusForm.lifecycle_status} onValueChange={(v) => setStatusForm({ ...statusForm, lifecycle_status: v })}>
                      <SelectTrigger data-testid="hremp-status-new"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {LIFECYCLE_STATUSES.map((s) => (<SelectItem key={s} value={s}>{s}</SelectItem>))}
                      </SelectContent>
                    </Select>
                  </div>
                  {["Terminated", "Resigned", "Retired"].includes(statusForm.lifecycle_status) && (
                    <div data-testid="hremp-separation-section" className="space-y-2 bg-slate-50 border border-slate-200 rounded-md p-3">
                      <div>
                        <Label>{t("Separation Type")} *</Label>
                        <Select value={statusForm.separation_type} onValueChange={(v) => setStatusForm({ ...statusForm, separation_type: v })}>
                          <SelectTrigger data-testid="hremp-separation-type"><SelectValue placeholder={t("Pick a type")} /></SelectTrigger>
                          <SelectContent>
                            {SEPARATION_TYPES.map((s) => (<SelectItem key={s} value={s}>{t(s)}</SelectItem>))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
                        <div>
                          <Label>{t("Last Day Worked")}</Label>
                          <Input type="date" value={statusForm.last_day_worked} onChange={(e) => setStatusForm({ ...statusForm, last_day_worked: e.target.value })} data-testid="hremp-tx-last-day" />
                        </div>
                        <div>
                          <Label>{t("Termination Date")}</Label>
                          <Input type="date" value={statusForm.termination_date} onChange={(e) => setStatusForm({ ...statusForm, termination_date: e.target.value })} data-testid="hremp-tx-term-date" />
                        </div>
                      </div>
                      {/* iter316 · Rehire eligibility (required on offboarding transitions) */}
                      <div className="pt-2 mt-1 border-t border-slate-200">
                        <HelpTipBlock formKey="employee-lifecycle.rehire" />
                        <Label>{t("Rehire Eligibility")} *</Label>
                        <Select
                          value={statusForm.rehire_eligibility}
                          onValueChange={(v) => setStatusForm({ ...statusForm, rehire_eligibility: v })}
                        >
                          <SelectTrigger data-testid="hremp-rehire-eligibility">
                            <SelectValue placeholder={t("Pick rehire eligibility")} />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="eligible">{t("Rehire Eligible")}</SelectItem>
                            <SelectItem value="not_eligible">{t("Not Rehire Eligible")}</SelectItem>
                            <SelectItem value="review_required">{t("Review Required")}</SelectItem>
                          </SelectContent>
                        </Select>
                        {["not_eligible", "review_required"].includes(statusForm.rehire_eligibility) && (
                          <div className="mt-2">
                            <Label>{t("Reason")} *</Label>
                            <Textarea
                              rows={2}
                              value={statusForm.rehire_eligibility_reason}
                              onChange={(e) => setStatusForm({ ...statusForm, rehire_eligibility_reason: e.target.value })}
                              placeholder={t("Attendance pattern · policy violation · job abandonment · supervisor review needed · etc.")}
                              data-testid="hremp-rehire-reason"
                              maxLength={500}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  {statusForm.lifecycle_status === "Leave of Absence" && (
                    <div data-testid="hremp-leave-section" className="space-y-2 bg-slate-50 border border-slate-200 rounded-md p-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
                        <div>
                          <Label>{t("Leave Start Date")}</Label>
                          <Input type="date" value={statusForm.leave_start_date} onChange={(e) => setStatusForm({ ...statusForm, leave_start_date: e.target.value })} data-testid="hremp-tx-leave-start" />
                        </div>
                        <div>
                          <Label>{t("Expected Return Date")}</Label>
                          <Input type="date" value={statusForm.expected_return_date} onChange={(e) => setStatusForm({ ...statusForm, expected_return_date: e.target.value })} data-testid="hremp-tx-leave-return" />
                        </div>
                      </div>
                    </div>
                  )}
                  <div>
                    <Label>{t("Reason / note")}</Label>
                    <Textarea
                      rows={3}
                      value={statusForm.reason}
                      onChange={(e) => setStatusForm({ ...statusForm, reason: e.target.value })}
                      placeholder={t("Optional context recorded in status history")}
                      data-testid="hremp-status-reason"
                    />
                  </div>
                  {["Terminated", "Resigned", "Retired"].includes(statusForm.lifecycle_status) &&
                    !["Terminated", "Resigned", "Retired"].includes(summary?.lifecycle_status) && (
                    <div className="bg-amber-50 border border-amber-300 rounded-md p-3 text-xs text-amber-900" data-testid="hremp-playbook-warning">
                      <div className="font-bold flex items-center gap-1.5 mb-1">
                        <AlertOctagon className="w-3.5 h-3.5" /> Offboarding playbook will fire
                      </div>
                      This status change will create 8 follow-up tasks across HR, Shop, Admin, Safety, and PM.
                    </div>
                  )}
                  {/* iter453.7 · Save button moved to the sticky drawer footer
                     (rendered below, outside the scrollable region) so HR
                     can always reach it on laptop/tablet/mobile viewports. */}

                  {summary?.last_status_change && (
                    <div className="mt-4 pt-3 border-t border-slate-200">
                      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1.5">Recent status history</div>
                      <ul className="space-y-1.5 text-xs text-slate-600">
                        {(employee.status_history || []).slice().reverse().slice(0, 5).map((h, idx) => (
                          <li key={idx} className="font-mono">
                            <span className="text-slate-500">{formatPlatformTime(h.at)}</span>
                            {" · "}
                            {h.from && <>{h.from} → </>}
                            <span className="font-bold text-slate-900">{h.to}</span>
                            {h.reason && <span className="text-slate-500"> · {h.reason}</span>}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </TabsContent>
                <TabsContent value="offboarding" className="mt-0 space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <MiniStat label="Open tasks" value={summary?.open_tasks_count ?? 0} icon={ClipboardList} accent="amber" />
                    <MiniStat label="Documents" value={summary?.document_expirations_count ?? 0} icon={FileText} accent="rose" />
                    <MiniStat label="Equipment" value={summary?.equipment_issuances_count ?? 0} icon={Wrench} accent="blue" />
                  </div>
                  <Section title={`Open Tasks (${summary?.open_tasks_count ?? 0})`}>
                    {(summary?.open_tasks || []).length === 0 ? (
                      <Empty msg="No open tasks — clean." accent="emerald" />
                    ) : (
                      <ul className="space-y-1.5">
                        {summary.open_tasks.slice(0, 20).map((t) => (
                          <li key={t.id} className="bg-slate-50 rounded-md px-3 py-2">
                            <Link to={`/tasks?id=${t.id}`} className="text-xs font-bold text-slate-900 hover:text-red-700" data-testid={`hremp-open-task-${t.id}`}>
                              {t.title}
                            </Link>
                            <div className="font-mono text-[10px] text-slate-500 mt-0.5">{t.priority} · {t.status} · {t.source_module}</div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </Section>
                  <Section title={`Document Expirations (${summary?.document_expirations_count ?? 0})`}>
                    {(summary?.document_expirations || []).length === 0 ? (
                      <Empty msg="No tracked expirations." accent="emerald" />
                    ) : (
                      <ul className="space-y-1.5">
                        {summary.document_expirations.slice(0, 20).map((d) => (
                          <li key={d.id} className="bg-slate-50 rounded-md px-3 py-2 flex items-center justify-between">
                            <div>
                              <div className="text-xs font-bold text-slate-900">{d.document_type}</div>
                              <div className="font-mono text-[10px] text-slate-500">{d.status} · expires {d.expiration_date}</div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </Section>
                  <Section title={`Equipment Issuances (${summary?.equipment_issuances_count ?? 0})`}>
                    {(summary?.equipment_issuances || []).length === 0 ? (
                      <Empty msg="No equipment currently assigned." accent="emerald" />
                    ) : (
                      <ul className="space-y-1.5">
                        {summary.equipment_issuances.slice(0, 20).map((e) => (
                          <li key={e.id} className="bg-slate-50 rounded-md px-3 py-2 text-xs font-mono">
                            {e.unit_number || e.name || e.id}
                          </li>
                        ))}
                      </ul>
                    )}
                  </Section>
                  <Section title={`Open POs (${summary?.open_pos_count ?? 0})`}>
                    {(summary?.open_pos || []).length === 0 ? (
                      <Empty msg="No open PO requests." accent="emerald" />
                    ) : (
                      <ul className="space-y-1.5">
                        {summary.open_pos.slice(0, 20).map((p) => (
                          <li key={p.id} className="bg-slate-50 rounded-md px-3 py-2">
                            <Link to={`/po-requests?id=${p.id}`} className="text-xs font-bold text-slate-900 hover:text-red-700 font-mono" data-testid={`hremp-open-po-${p.id}`}>
                              {p.po_number || p.id.slice(0, 8)}
                            </Link>
                            <div className="font-mono text-[10px] text-slate-500">{p.vendor} · {p.status} · ${(p.approved_amount ?? p.estimated_amount ?? 0).toFixed(2)}</div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </Section>
                </TabsContent>
                <TabsContent value="transportation" className="mt-0 space-y-3">
                  <TransportationStatusPanel employeeId={employee.employee_id || employee.id} />
                </TabsContent>
              </div>
              {/* iter453.7 · Sticky drawer footer · Status tab only.
                 Pinned outside the scrollable region so HR can always
                 reach Save Status Change at every viewport (1366×768,
                 iPad landscape, mobile, mobile + keyboard). */}
              {tab === "status" && (
                <div
                  className="shrink-0 border-t border-slate-200 bg-white px-5 py-3 flex items-center justify-between gap-3"
                  data-testid="hremp-status-footer"
                >
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 hidden sm:block">
                    {saving ? "Persisting status change…" : "Commits on Save"}
                  </div>
                  <Button
                    onClick={submitStatusChange}
                    disabled={saving}
                    data-testid="hremp-status-save"
                    className="ml-auto"
                  >
                    {saving ? "Saving…" : "Save Status Change"}
                  </Button>
                </div>
              )}
            </Tabs>
            {/* iter316 · Reactivate / rehire dialog */}
            <Dialog open={reactivateOpen} onOpenChange={setReactivateOpen}>
              <DialogContent className="sm:max-w-md" data-testid="hremp-reactivate-dialog">
                <DialogHeader>
                  <DialogTitle>{t("Reactivate / Rehire Employee")}</DialogTitle>
                </DialogHeader>
                <div className="space-y-3">
                  <HelpTipBlock formKey="employee-lifecycle.rehire" />
                  <div className="bg-slate-50 border border-slate-200 rounded-md p-3 text-xs text-slate-700 space-y-1">
                    <div>
                      <span className="text-slate-500">{t("Employee")}:</span>{" "}
                      <span className="font-bold text-slate-900">{employee.name}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">{t("Original Hire Date")}:</span>{" "}
                      <span className="font-mono">{employee.original_hire_date || "—"}</span>
                      <span className="text-slate-400 ml-2">{t("(preserved · write-once)")}</span>
                    </div>
                    {employee.termination_date && (
                      <div>
                        <span className="text-slate-500">{t("Prior Termination Date")}:</span>{" "}
                        <span className="font-mono">{employee.termination_date}</span>
                      </div>
                    )}
                    {employee.rehire_eligibility && (
                      <div>
                        <span className="text-slate-500">{t("Rehire Eligibility")}:</span>{" "}
                        <span className="font-bold uppercase">{employee.rehire_eligibility}</span>
                      </div>
                    )}
                  </div>
                  <div>
                    <Label>{t("New status")} *</Label>
                    <Select
                      value={reactivateForm.lifecycle_status}
                      onValueChange={(v) => setReactivateForm({ ...reactivateForm, lifecycle_status: v })}
                    >
                      <SelectTrigger data-testid="hremp-reactivate-status">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Active">{t("Active")}</SelectItem>
                        <SelectItem value="Pending Hire">{t("Pending Hire")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>{t("Rehire Date")} *</Label>
                    <Input
                      type="date"
                      value={reactivateForm.rehire_date}
                      onChange={(e) => setReactivateForm({ ...reactivateForm, rehire_date: e.target.value })}
                      data-testid="hremp-reactivate-rehire-date"
                    />
                  </div>
                  <div>
                    <Label>{t("Reason / note")}</Label>
                    <Textarea
                      rows={2}
                      value={reactivateForm.reason}
                      onChange={(e) => setReactivateForm({ ...reactivateForm, reason: e.target.value })}
                      placeholder={t("Operational context recorded in status history")}
                      data-testid="hremp-reactivate-reason"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setReactivateOpen(false)}
                    data-testid="hremp-reactivate-cancel"
                  >
                    {t("Cancel")}
                  </Button>
                  <Button
                    onClick={submitReactivate}
                    disabled={saving}
                    className="bg-emerald-700 hover:bg-emerald-800 text-white"
                    data-testid="hremp-reactivate-confirm"
                  >
                    {saving ? t("Saving…") : t("Reactivate")}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}

function EditField({ label, value, save, testid }) {
  const [v, setV] = useState(value || "");
  useEffect(() => { setV(value || ""); }, [value]);
  const dirty = v !== (value || "");
  return (
    <div className="flex items-end gap-2">
      <div className="flex-1">
        <Label className="text-[11px]">{label}</Label>
        <Input value={v} onChange={(e) => setV(e.target.value)} className="h-9 text-xs" data-testid={testid} />
      </div>
      {dirty && (
        <Button size="sm" onClick={() => save(v)} className="h-9 text-xs">Save</Button>
      )}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1.5 flex items-center gap-1.5">
        <Briefcase className="w-3 h-3" /> {title}
      </div>
      {children}
    </div>
  );
}

function Empty({ msg, accent }) {
  const cls = accent === "emerald" ? "border-emerald-200 text-emerald-700" : "border-slate-200 text-slate-500";
  return (
    <div className={`text-center py-3 text-xs border rounded-md ${cls}`}>
      <CheckCircle2 className="w-4 h-4 inline-block mr-1 align-middle" /> {msg}
    </div>
  );
}

function MiniStat({ label, value, icon: Icon, accent }) {
  const palette = {
    amber: "border-amber-300 text-amber-900",
    rose: "border-rose-300 text-rose-900",
    blue: "border-blue-300 text-blue-900",
  }[accent] || "border-slate-300";
  return (
    <div className={`bg-white border-2 ${palette} rounded-md p-2.5`}>
      <div className="flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5 opacity-70" />
        <span className="font-mono text-[9px] uppercase tracking-[0.18em] font-bold opacity-80">{label}</span>
      </div>
      <div className="font-display text-xl font-black mt-0.5 leading-none">{value}</div>
    </div>
  );
}

// TRACK 16.11A · HR-side Transportation Status panel. Read-only.
// No controls. Mounted inside the HR Employee Drawer "Transportation"
// tab. Never writes back into Transportation.
function TransportationStatusPanel({ employeeId }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!employeeId) {
      setData(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    const API = process.env.REACT_APP_BACKEND_URL;
    const headers = {
      "X-Admin-Token": (typeof window !== "undefined" && window.localStorage)
        ? (window.localStorage.getItem("masci.admin.token") || "")
        : "",
      "X-HR-Token": (typeof window !== "undefined" && window.localStorage)
        ? (window.localStorage.getItem("masci.hr.token") || "")
        : "",
    };
    fetch(`${API}/api/admin/hr/transportation-status?employee_id=${encodeURIComponent(employeeId)}`, { headers })
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((body) => { if (!cancelled) { setData(body); setErr(null); } })
      .catch((e) => { if (!cancelled) setErr(e.message || "load failed"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [employeeId]);

  if (loading) {
    return <div data-testid="hremp-tx-loading" className="text-xs text-slate-500">Loading Transportation status…</div>;
  }
  if (err) {
    return <div data-testid="hremp-tx-error" className="text-xs text-rose-600">Couldn&apos;t load Transportation status ({err}).</div>;
  }
  if (!data || data.linked === false) {
    return (
      <div data-testid="hremp-tx-not-linked" className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
        <div className="font-semibold text-slate-800 mb-1">Transportation: not linked</div>
        <div>
          {data?.reason === "hr_employee_missing"
            ? "HR employee not found."
            : "This employee is not linked to a Transportation driver record."}
        </div>
        <div className="mt-1 text-[11px] text-slate-500">HR is the source of truth — link via Transportation admin if this employee should be dispatch-eligible.</div>
      </div>
    );
  }

  const chipPalette = {
    eligible: "bg-emerald-100 text-emerald-800 border-emerald-300",
    pending_review: "bg-amber-100 text-amber-800 border-amber-300",
    needs_correction: "bg-amber-100 text-amber-800 border-amber-300",
    suspended: "bg-rose-100 text-rose-800 border-rose-300",
    not_dispatchable: "bg-rose-100 text-rose-800 border-rose-300",
  };
  const chipClass = chipPalette[data.transport_status] || "bg-slate-100 text-slate-700 border-slate-300";

  return (
    <div data-testid="hremp-tx-panel" className="space-y-3">
      <div className="rounded-md border border-slate-200 bg-white p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-600">Transportation Eligibility</div>
          <span
            data-testid="hremp-tx-status-chip"
            className={`px-2 py-0.5 rounded-full border text-[11px] font-medium ${chipClass}`}
          >
            {(data.transport_status || "unknown").replace("_", " ")}
          </span>
        </div>
        <Row2 label="HR status" value={data.hr_status || "—"} />
        <Row2 label="Driver qualification" value={data.driver_qualification || "—"} />
        <Row2 label="Approved company driver" value={data.approved_company_driver ? "Yes" : "No"} />
        <Row2 label="Projection state" value={data.projection_state || "—"} />
        <Row2 label="Last Transportation sync" value={data.last_sync_at ? data.last_sync_at.slice(0, 19).replace("T", " ") : "—"} testid="hremp-tx-last-sync" />
        <Row2 label="Last orientation completion" value={data.last_orientation_completion ? data.last_orientation_completion.slice(0, 10) : "—"} />
        <Row2 label="Next orientation expiration" value={data.next_orientation_expiration ? data.next_orientation_expiration.slice(0, 10) : "—"} />
        {data.active_override && (
          <Row2 label="Active dispatch override" value={`Expires ${(data.active_override.expires_at || "").slice(0, 10) || "—"}`} testid="hremp-tx-override" />
        )}
        {(data.transport_reasons || []).length > 0 && (
          <div className="mt-2 text-[11px] text-slate-600">
            <div className="font-semibold text-slate-700 mb-1">Eligibility reasons</div>
            {data.transport_reasons.map((r, i) => (
              <div key={i} data-testid={`hremp-tx-reason-${i}`}>• {r}</div>
            ))}
          </div>
        )}
      </div>
      {data.view_workspace_path && (
        <Link
          to={data.view_workspace_path}
          data-testid="hremp-tx-view-workspace"
          className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
        >
          View Transportation profile →
        </Link>
      )}
      <div className="text-[10px] uppercase tracking-wide text-slate-400">
        Read-only · HR is the source of truth · Transportation is reactive
      </div>
    </div>
  );
}

function Row2({ label, value, testid }) {
  return (
    <div className="flex items-center justify-between py-1 text-[12px] text-slate-700" data-testid={testid}>
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-900">{value}</span>
    </div>
  );
}
