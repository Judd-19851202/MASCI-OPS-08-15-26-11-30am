// Track 13.33ABC · Asset Care & Readiness Command Center
// Operational home for the Asset Administrator. Mounted on the Shop side.

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Loader2, RefreshCw, Plus, FileText, AlertTriangle, CheckCircle2,
  ShieldAlert, Calendar, Search, Settings, Download, ArrowRight,
  ClipboardList, Bell, Wrench,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { PortalShell } from "@/design-system";

const STATUS_COLORS = {
  "Not Ready":    "bg-red-100 text-red-900 border-red-300",
  "Warning":      "bg-amber-100 text-amber-900 border-amber-300",
  "Needs Review": "bg-sky-100 text-sky-900 border-sky-300",
  "Ready":        "bg-emerald-100 text-emerald-900 border-emerald-300",
};

const SEV_COLORS = {
  critical: "bg-red-100 text-red-900 border-red-300",
  high:     "bg-amber-100 text-amber-900 border-amber-300",
  medium:   "bg-sky-100 text-sky-900 border-sky-300",
  low:      "bg-slate-100 text-slate-700 border-slate-300",
  info:     "bg-slate-100 text-slate-700 border-slate-300",
};

export default function ShopAssetCare() {
  const [summary, setSummary] = useState(null);
  const [readiness, setReadiness] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [work, setWork] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("Not Ready");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [s, r, a, w] = await Promise.all([
        api.get("/asset-care/summary"),
        api.get("/asset-care/readiness?limit=200"),
        api.get("/asset-care/alerts"),
        api.get("/asset-care/work-queue"),
      ]);
      setSummary(s.data); setReadiness(r.data.items || []);
      setAlerts(a.data.items || []); setWork(w.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load Asset Care. Try again.");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const downloadCsv = useCallback(async (path, fname) => {
    try {
      const r = await api.get(path, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a"); a.href = url; a.download = fname; a.click();
      URL.revokeObjectURL(url);
    } catch { toast.error("Export failed. Try again, or contact your administrator if it keeps failing."); }
  }, []);

  const filtered = readiness.filter((r) => r.readiness_status === filter);

  if (loading) {
    return (
      <div className="p-10 text-center text-slate-500" data-testid="asset-care-loading">
        <Loader2 className="w-6 h-6 mx-auto animate-spin" />
        <div className="font-mono text-xs uppercase tracking-[0.16em] mt-2">Loading Asset Care…</div>
      </div>
    );
  }

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Shop Operations"
      pageTitle="Asset Care"
      subtitle="Readiness · documents · renewals · alerts across the asset spine."
      showBack
      backHref="/shop"
      portalSwitcherCurrent="shop"
      primaryActions={
        <div className="flex items-center gap-2">
          <Link to="/admin/asset-admin?tab=queue">
            <Button variant="outline" size="sm" data-testid="ac-open-admin">
              <Settings className="w-3.5 h-3.5 mr-1" /> Open Asset Administration
            </Button>
          </Link>
          <Button variant="outline" size="sm" onClick={reload} data-testid="ac-refresh">
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
          </Button>
        </div>
      }
    >
      <div data-testid="asset-care-home" className="space-y-5">
        {/* KPI snapshot */}
        <section className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2" data-testid="ac-kpi-snapshot">
          <Kpi label="Total Assets" value={summary?.total_assets} testid="ac-kpi-total" />
          <Kpi label="Ready"        value={summary?.readiness?.Ready}        accent="emerald" testid="ac-kpi-ready" />
          <Kpi label="Warning"      value={summary?.readiness?.Warning}      accent="amber"   testid="ac-kpi-warning" />
          <Kpi label="Not Ready"    value={summary?.readiness?.["Not Ready"]} accent="red"    testid="ac-kpi-not-ready" />
          <Kpi label="Needs Review" value={summary?.readiness?.["Needs Review"]} accent="sky" testid="ac-kpi-needs-review" />
          <Kpi label="Expired Renewals" value={summary?.renewals?.expired}    accent="red"    testid="ac-kpi-expired" />
          <Kpi label="Missing Docs" value={summary?.missing_documents_total}  accent="amber"  testid="ac-kpi-missing" />
        </section>

        {/* Quick actions */}
        <section className="flex flex-wrap gap-2" data-testid="ac-quick-actions">
          <Link to="/admin/asset-admin"><Button size="sm" className="bg-red-700 hover:bg-red-800 text-white" data-testid="ac-action-add-asset"><Plus className="w-3.5 h-3.5 mr-1" /> Add Asset</Button></Link>
          <Button size="sm" variant="outline" onClick={() => downloadCsv("/asset-spine/exports/assets.csv", "MASCI_Asset_Inventory.csv")} data-testid="ac-action-csv-inventory"><Download className="w-3.5 h-3.5 mr-1" /> Inventory CSV</Button>
          <Button size="sm" variant="outline" onClick={() => downloadCsv("/asset-spine/exports/renewals.csv", "MASCI_Asset_Renewals.csv")} data-testid="ac-action-csv-renewals"><Download className="w-3.5 h-3.5 mr-1" /> Renewals CSV</Button>
          <Button size="sm" variant="outline" onClick={() => downloadCsv("/asset-spine/exports/missing-documents.csv", "MASCI_Missing_Documents.csv")} data-testid="ac-action-csv-missing"><Download className="w-3.5 h-3.5 mr-1" /> Missing CSV</Button>
          <Link to="/admin/asset-admin?tab=required-docs"><Button size="sm" variant="outline" data-testid="ac-action-required-docs"><ClipboardList className="w-3.5 h-3.5 mr-1" /> Documentation Requirements</Button></Link>
        </section>

        {/* Renewal alerts */}
        <section className="bg-white rounded border border-slate-200" data-testid="ac-alerts">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.18em] text-slate-700 font-bold">
              <Bell className="w-3.5 h-3.5" /> Renewal Alerts · {alerts.length}
            </div>
            <div className="flex items-center gap-1 text-[10px] font-mono uppercase tracking-[0.16em]">
              {Object.entries(summary?.renewals || {}).map(([k, v]) => (
                <span key={k} className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700" data-testid={`ac-alert-bucket-${k}`}>
                  {k === "expired" ? "Expired" : `${k}d`}: {v}
                </span>
              ))}
            </div>
          </div>
          {alerts.length === 0 ? (
            <div className="p-6 text-center text-emerald-700 text-sm" data-testid="ac-alerts-empty">
              All asset renewals current.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
              {alerts.slice(0, 30).map((a, i) => (
                <div key={`${a.asset_id}-${a.renewal_type}-${i}`} className="px-4 py-2 flex items-center gap-2 text-sm" data-testid={`ac-alert-row-${i}`}>
                  <span className={`px-1.5 py-0.5 rounded border font-mono text-[10px] uppercase tracking-[0.14em] font-bold ${SEV_COLORS[a.severity]}`}>
                    {a.bucket}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-slate-900 truncate">{a.unit_number} · {a.renewal_type}</div>
                    <div className="text-xs text-slate-500 truncate">{a.asset_type || "—"} · {a.recommended_action}</div>
                  </div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-700">
                    {a.expiration_date}{a.days_remaining < 0 ? ` · ${-a.days_remaining}d ago` : ` · ${a.days_remaining}d`}
                  </div>
                  <Link to={a.open_asset_profile} className="text-xs text-red-700 hover:underline font-bold" data-testid={`ac-alert-open-${i}`}>
                    Open <ArrowRight className="w-3 h-3 inline" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Readiness queue */}
        <section className="bg-white rounded border border-slate-200" data-testid="ac-readiness">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.18em] text-slate-700 font-bold">
              <ShieldAlert className="w-3.5 h-3.5" /> Readiness · {filtered.length} {filter}
            </div>
            <div className="flex items-center gap-1">
              {["Not Ready", "Warning", "Needs Review", "Ready"].map((s) => (
                <button
                  key={s} onClick={() => setFilter(s)}
                  className={`px-2 py-1 rounded border font-mono text-[10px] uppercase tracking-[0.14em] font-bold ${
                    filter === s ? STATUS_COLORS[s] : "bg-white border-slate-300 text-slate-500"
                  }`}
                  data-testid={`ac-readiness-tab-${s.replace(/\s+/g, "-").toLowerCase()}`}
                >
                  {s} · {summary?.readiness?.[s] ?? 0}
                </button>
              ))}
            </div>
          </div>
          {filtered.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-sm" data-testid="ac-readiness-empty">
              No assets in this state.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
              {filtered.slice(0, 100).map((r) => (
                <div key={r.asset_id} className="px-4 py-2 flex items-center gap-2 text-sm" data-testid={`ac-readiness-row-${r.asset_id}`}>
                  <span className={`px-1.5 py-0.5 rounded border font-mono text-[10px] uppercase tracking-[0.14em] font-bold ${STATUS_COLORS[r.readiness_status]}`}>
                    {r.readiness_status}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-slate-900 truncate">{r.unit_number}</div>
                    <div className="text-xs text-slate-500 truncate">
                      {r.asset_class || "—"} · {r.asset_type || "Needs Review"}
                      {r.reasons.length > 0 && ` · ${r.reasons[0]}`}
                    </div>
                  </div>
                  <Link to={`/admin/assets/${r.asset_id}`} className="text-xs text-red-700 hover:underline font-bold" data-testid={`ac-readiness-open-${r.asset_id}`}>
                    Open Profile <ArrowRight className="w-3 h-3 inline" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Work queue */}
        {work && (
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2" data-testid="ac-work-queue">
            <WorkBucket label="Needs Classification Review" items={work.needs_classification_review} testid="ac-wq-needs-classification" />
            <WorkBucket label="Missing Required Documents" items={work.missing_required_documents} testid="ac-wq-missing-docs" />
            <WorkBucket label="GPS / Survey / Tech Review" items={work.gps_survey_tech_review} testid="ac-wq-gst-review" />
            <WorkBucket label="Open Defects (Awareness)" items={work.open_defects} testid="ac-wq-defects" />
          </section>
        )}
      </div>
    </PortalShell>
  );
}

function Kpi({ label, value, accent = "slate", testid }) {
  const accents = {
    slate: "bg-white border-slate-200 text-slate-900",
    emerald: "bg-emerald-50 border-emerald-200 text-emerald-900",
    amber: "bg-amber-50 border-amber-200 text-amber-900",
    red: "bg-red-50 border-red-200 text-red-900",
    sky: "bg-sky-50 border-sky-200 text-sky-900",
  };
  return (
    <div data-testid={testid} className={`rounded border-2 p-3 ${accents[accent]}`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.16em] font-bold">{label}</div>
      <div className="text-2xl font-black tabular-nums mt-0.5">{value ?? "—"}</div>
    </div>
  );
}

function WorkBucket({ label, items, testid }) {
  return (
    <div data-testid={testid} className="bg-white rounded border border-slate-200 p-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.16em] font-bold text-slate-700">{label}</div>
      <div className="text-3xl font-black text-slate-900 tabular-nums mt-1">{items?.length || 0}</div>
      <div className="text-[11px] text-slate-500 mt-1 truncate">
        {items?.length ? items.slice(0, 2).map((i) => i.unit_number).join(" · ") : "All clear"}
      </div>
    </div>
  );
}
