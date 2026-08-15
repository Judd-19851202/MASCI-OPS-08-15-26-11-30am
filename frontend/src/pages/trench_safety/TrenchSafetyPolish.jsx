// Trench Safety · Phase 8B Polish Modules
// ─────────────────────────────────────────────────────────────────────
// Operational adoption polish that consumes the certified architecture
// without introducing parallel systems. Every component speaks to the
// SAME endpoints the rest of the Trench Safety surface uses:
//   • GET  /trench-safety/dashboard      — counts + alerts + recent activity
//   • GET  /trench-safety/assets/next-id — RP/TB/EP/... permanent IDs
//   • POST /trench-safety/assets         — same create path as the full form
//   • POST /trench-safety/assets/import/preview  — Phase 8B CSV preview
//   • POST /trench-safety/assets/import          — Phase 8B CSV commit
//
// Exported pieces:
//   • QuickAddAssetDialog     — minimum-field create + auto ID
//   • OperationalSummaryPanel — Executive summary + status/type breakdown + alerts
//   • TrenchAssetFilterChips  — one-tap status + type chip strip (mobile-safe)
//   • CSVImportDialog         — file upload → preview → commit
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Loader2, Plus, Upload, AlertTriangle, ShieldAlert, Boxes,
  FileWarning, CheckCircle2, Wrench, Camera, MapPin, ScanLine,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { ASSET_TYPES, CONDITIONS } from "@/pages/trench_safety/TrenchSafetyActions";

const PREFIX_BY_TYPE = {
  "Trench Box": "TB",
  "End Panel": "EP",
  "Spreader Bar": "SP",
  "Hydraulic Shore": "HS",
  "Slide Rail System": "SR",
  "Trench Jack": "TJ",
  "Ladder": "LD",
  "Road Plate": "RP",
  "Accessory": "AC",
};

const ALL_STATUSES = [
  { key: "Available",          short: "Available",   color: "emerald" },
  { key: "Assigned",           short: "Assigned",    color: "blue" },
  { key: "In Transport",       short: "Transport",   color: "cyan" },
  { key: "Safety Hold",        short: "Safety",      color: "red" },
  { key: "Inspection Hold",    short: "Inspection",  color: "amber" },
  { key: "Maintenance Hold",   short: "Maint",       color: "orange" },
  { key: "Certification Hold", short: "Cert",        color: "purple" },
  { key: "Retired",            short: "Retired",     color: "slate" },
];

function extractErr(e, fallback) {
  return e?.response?.data?.detail || e?.message || fallback;
}

// ═════════════════════════════════════════════════════════════════════
// Quick Add Asset Dialog — Phase 8B Feature 1
// ═════════════════════════════════════════════════════════════════════
export function QuickAddAssetDialog({ open, onOpenChange, onCreated }) {
  const { t } = useT();
  if (!open) return null;
  return <QuickAddAssetDialogInner onOpenChange={onOpenChange} onCreated={onCreated} t={t} />;
}

function QuickAddAssetDialogInner({ onOpenChange, onCreated, t }) {
  const [assetType, setAssetType] = useState("Trench Box");
  const [suggestedId, setSuggestedId] = useState("");
  const [assetId, setAssetId] = useState("");
  const [serial, setSerial] = useState("");
  const [size, setSize] = useState("");
  const [condition, setCondition] = useState("Good");
  const [manufacturer, setManufacturer] = useState("");
  const [saving, setSaving] = useState(false);

  // Fetch next-id whenever the asset_type changes.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get("/trench-safety/assets/next-id", { params: { asset_type: assetType } });
        if (!cancelled && r.data?.next_id) {
          setSuggestedId(r.data.next_id);
          setAssetId(r.data.next_id);
        }
      } catch { /* user can type their own */ }
    })();
    return () => { cancelled = true; };
  }, [assetType]);

  async function save() {
    if (!assetId.trim()) {
      toast.error(t("Asset ID is required."));
      return;
    }
    setSaving(true);
    try {
      const payload = {
        asset_id: assetId.trim().toUpperCase(),
        asset_type: assetType,
        condition,
        serial_number: serial,
        size,
        manufacturer,
      };
      const r = await api.post("/trench-safety/assets", payload);
      toast.success(t("Asset created.") + ` · ${payload.asset_id}`);
      onOpenChange(false);
      onCreated?.(r.data);
    } catch (e) {
      toast.error(extractErr(e, t("Create failed.")));
    } finally {
      setSaving(false);
    }
  }

  const prefix = PREFIX_BY_TYPE[assetType] || "AS";

  return (
    <Dialog open={true} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md" data-testid="quick-add-asset-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="w-5 h-5 text-cyan-700" />
            {t("Quick Add Asset")}
          </DialogTitle>
        </DialogHeader>
        <div className="text-xs text-slate-600 -mt-2 mb-2">
          {t("Pick a type — the system suggests the next permanent ID. Fill the essentials, save, and refine later.")}
        </div>

        <div className="space-y-3">
          <div>
            <Label className="text-xs font-bold">{t("Asset Type")} *</Label>
            <Select value={assetType} onValueChange={setAssetType}>
              <SelectTrigger data-testid="quick-add-type"><SelectValue /></SelectTrigger>
              <SelectContent>
                {ASSET_TYPES.map((x) => (
                  <SelectItem key={x} value={x}>
                    <span className="font-mono text-cyan-700 mr-2">{PREFIX_BY_TYPE[x] || "AS"}</span>
                    {t(x)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-xs font-bold">{t("Asset ID")} *</Label>
            <Input
              value={assetId}
              onChange={(e) => setAssetId(e.target.value.toUpperCase())}
              placeholder={suggestedId || `${prefix}-001`}
              className="font-mono uppercase font-black text-lg h-12"
              data-testid="quick-add-asset-id"
            />
            <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 mt-1 font-mono">
              {t("Suggested")}: <span className="text-cyan-700 font-bold">{suggestedId || "—"}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs font-bold">{t("Serial #")}</Label>
              <Input value={serial} onChange={(e) => setSerial(e.target.value)} className="font-mono" data-testid="quick-add-serial" />
            </div>
            <div>
              <Label className="text-xs font-bold">{t("Size")}</Label>
              <Input value={size} onChange={(e) => setSize(e.target.value)} placeholder={assetType === "Trench Box" ? "6x24" : ""} data-testid="quick-add-size" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs font-bold">{t("Manufacturer")}</Label>
              <Input value={manufacturer} onChange={(e) => setManufacturer(e.target.value)} data-testid="quick-add-mfr" />
            </div>
            <div>
              <Label className="text-xs font-bold">{t("Condition")}</Label>
              <Select value={condition} onValueChange={setCondition}>
                <SelectTrigger data-testid="quick-add-condition"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {CONDITIONS.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} data-testid="quick-add-cancel">{t("Cancel")}</Button>
          <Button onClick={save} disabled={saving} className="bg-cyan-700 hover:bg-cyan-800" data-testid="quick-add-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : (<><Plus className="w-4 h-4 mr-1" /> {t("Create Asset")}</>)}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ═════════════════════════════════════════════════════════════════════
// Operational Summary Panel — Phase 8B Features 2 + 5 + 9
// ═════════════════════════════════════════════════════════════════════
function Stat({ label, value, tone = "default", testId, href }) {
  const toneClass = {
    default: "bg-white border-slate-200 text-slate-900",
    info: "bg-cyan-50 border-cyan-300 text-cyan-900",
    warn: "bg-amber-50 border-amber-300 text-amber-900",
    danger: "bg-red-50 border-red-300 text-red-900",
    ok: "bg-emerald-50 border-emerald-300 text-emerald-900",
  }[tone];
  const inner = (
    <div className={`border rounded-md px-3 py-2 ${toneClass}`} data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-70">{label}</div>
      <div className="font-display text-2xl sm:text-3xl font-black leading-none mt-1">{value ?? 0}</div>
    </div>
  );
  return href ? <Link to={href} className="block hover:opacity-90 transition">{inner}</Link> : inner;
}

function AlertRow({ icon: Icon, label, count, tone, href, testId }) {
  const dim = !count;
  const toneClass = {
    danger: "border-red-300 bg-red-50 text-red-900",
    warn:   "border-amber-300 bg-amber-50 text-amber-900",
    info:   "border-cyan-300 bg-cyan-50 text-cyan-900",
  }[tone] || "border-slate-200 bg-slate-50 text-slate-700";
  const dimClass = "border-slate-200 bg-slate-50 text-slate-500";
  const row = (
    <div className={`flex items-center justify-between gap-3 px-3 py-2 rounded border ${dim ? dimClass : toneClass}`} data-testid={testId}>
      <span className="inline-flex items-center gap-2">
        <Icon className="w-4 h-4" />
        <span className="text-sm font-bold">{label}</span>
      </span>
      <span className="font-mono text-sm font-black">{count ?? 0}</span>
    </div>
  );
  return href && count ? <Link to={href} className="block hover:opacity-90 transition">{row}</Link> : row;
}

export function OperationalSummaryPanel({ assetsBasePath = "/safety/trench-safety/assets" }) {
  const { t } = useT();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get("/trench-safety/dashboard");
        if (!cancelled) setData(r.data || null);
      } catch (e) {
        if (!cancelled) setErr(e?.response?.data?.detail || e?.message || "Failed to load summary");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const cs = data?.counts_by_status || {};
  const csa = data?.counts_by_status_active || {};
  const ct = data?.counts_by_type || {};
  const al = data?.alerts || {};
  const total = data?.total_active_assets ?? 0;
  const totalAll = data?.total_all_assets ?? 0;
  const recent = data?.recent_activity_7d ?? 0;

  if (loading) {
    return (
      <section className="bg-white border border-slate-200 rounded-md p-4" data-testid="ops-summary-loading">
        <Loader2 className="w-5 h-5 animate-spin text-cyan-700" />
      </section>
    );
  }
  if (err) {
    return <div className="p-3 border border-red-300 bg-red-50 rounded text-red-900 text-sm" data-testid="ops-summary-error">{err}</div>;
  }

  return (
    <section className="space-y-4" data-testid="ops-summary">
      {/* Executive summary — ALL figures below are scoped to IN-SERVICE
          (is_active) assets so they reconcile with Active Assets; the
          all-lifecycle breakdown is the "Count by Status" card. Recent
          Activity is an audit-event count (distinct entity/window). */}
      <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold" data-testid="ops-summary-executive-scope">
        <Boxes className="w-3.5 h-3.5" /> {t("In-service view")} <span className="text-slate-400 normal-case tracking-normal font-normal">· {t("active assets only")} ({total} {t("of")} {totalAll} {t("total including retired")})</span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2" data-testid="ops-summary-executive">
        <Stat label={t("Active Assets")}         value={total}                       testId="ops-stat-total" />
        <Stat label={t("Available")}            value={csa["Available"]   ?? 0} tone="ok"     testId="ops-stat-available" />
        <Stat label={t("Assigned")}             value={csa["Assigned"]    ?? 0} tone="info"   testId="ops-stat-assigned" />
        <Stat label={t("On Hold")}              value={al.on_hold        ?? 0} tone={(al.on_hold ?? 0) > 0 ? "danger" : "default"} testId="ops-stat-on-hold" />
        <Stat label={t("Open Repairs")}         value={al.open_repairs   ?? 0} tone={(al.open_repairs ?? 0) > 0 ? "warn" : "default"} testId="ops-stat-repairs" />
        <Stat label={t("Inspections Due")}      value={al.inspections_due ?? 0} tone={(al.inspections_due ?? 0) > 0 ? "warn" : "default"} testId="ops-stat-inspections" />
        <Stat label={t("Recent Events · 7d")} value={recent}                  tone="info" testId="ops-stat-recent" />
      </div>

      {/* Asset Count Command Cards — by status + type */}
      <div className="bg-white border border-slate-200 rounded-md p-4" data-testid="ops-summary-status-cards">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
          <Boxes className="w-3.5 h-3.5" /> {t("Count by Status")} <span className="text-slate-400 normal-case tracking-normal font-normal">· {t("all lifecycle states, including retired")}</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2" data-testid="ops-status-grid">
          {ALL_STATUSES.map((s) => (
            <Stat
              key={s.key}
              label={t(s.short)}
              value={cs[s.key] ?? 0}
              tone={s.color === "red" ? "danger" : s.color === "amber" || s.color === "orange" || s.color === "purple" ? "warn" : s.color === "emerald" ? "ok" : "info"}
              testId={`ops-status-${s.key.replace(/\s/g, "-").toLowerCase()}`}
            />
          ))}
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-4" data-testid="ops-summary-type-cards">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
          <Boxes className="w-3.5 h-3.5" /> {t("Count by Type")}
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-9 gap-2" data-testid="ops-type-grid">
          {ASSET_TYPES.map((typ) => (
            <Stat
              key={typ}
              label={t(typ)}
              value={ct[typ] ?? 0}
              testId={`ops-type-${(PREFIX_BY_TYPE[typ] || "AS").toLowerCase()}`}
            />
          ))}
        </div>
      </div>

      {/* Operational Alerts — count + severity + click-through */}
      <div className="bg-white border border-slate-200 rounded-md p-4" data-testid="ops-summary-alerts">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
          <AlertTriangle className="w-3.5 h-3.5" /> {t("Operational Alerts")}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          <AlertRow icon={ShieldAlert} label={t("On Hold")}                        count={al.on_hold ?? 0}                   tone="danger" testId="ops-alert-onhold" />
          <AlertRow icon={FileWarning} label={t("Inspections Due")}                count={al.inspections_due ?? 0}           tone="warn"   testId="ops-alert-inspdue" />
          <AlertRow icon={Wrench}      label={t("Open Repairs")}                   count={al.open_repairs ?? 0}              tone="warn"   testId="ops-alert-repairs" />
          <AlertRow icon={Camera}      label={t("Missing Photos")}                 count={al.missing_photos ?? 0}            tone="info"   testId="ops-alert-photos" />
          <AlertRow icon={FileWarning} label={t("Missing Serial Number")}          count={al.missing_serial_number ?? 0}     tone="warn"   testId="ops-alert-serial" />
          <AlertRow icon={MapPin}      label={t("No Project Assignment")}          count={al.no_project_assignment ?? 0}     tone="info"   testId="ops-alert-noproj" />
          <AlertRow icon={CheckCircle2} label={t("Needs Review")}                  count={al.needs_review ?? 0}              tone="warn"   testId="ops-alert-review" />
          <AlertRow icon={ScanLine}    label={t("Road Plates Missing Capacity")}   count={al.road_plate_missing_capacity ?? 0} tone="info" testId="ops-alert-rp-capacity" />
          <AlertRow icon={FileWarning} label={t("Tabulated Data Missing")}         count={al.missing_tabulated_data ?? 0}    tone="info"   testId="ops-alert-tabdata" />
        </div>
        <div className="mt-3 text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">
          <Link to={assetsBasePath} className="hover:text-cyan-700" data-testid="ops-summary-open-assets">
            → {t("Open Asset Roster")}
          </Link>
        </div>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════
// Asset Filter Chips — Phase 8B Feature 4 (mobile, no horizontal scroll)
// ═════════════════════════════════════════════════════════════════════
export function TrenchAssetFilterChips({ value, onChange }) {
  const { t } = useT();
  // value is the same shape used by TrenchSafetyAssetsList: {status, type}
  const status = value?.status || "__all";
  const type = value?.type || "__all";
  const setStatus = (s) => onChange?.({ ...value, status: s });
  const setType = (ty) => onChange?.({ ...value, type: ty });

  const statusChips = [
    { key: "__all",                 label: t("All"),        color: "slate" },
    { key: "Available",             label: t("Available"),  color: "emerald" },
    { key: "Assigned",              label: t("Assigned"),   color: "blue" },
    { key: "In Transport",          label: t("Transport"),  color: "cyan" },
    { key: "Safety Hold",           label: t("Safety"),     color: "red" },
    { key: "Inspection Hold",       label: t("Inspection"), color: "amber" },
    { key: "Maintenance Hold",      label: t("Maint"),      color: "orange" },
    { key: "Retired",               label: t("Retired"),    color: "slate" },
  ];

  const typeChips = [
    { key: "__all", label: t("All Types") },
    ...Object.entries(PREFIX_BY_TYPE).map(([k, p]) => ({ key: k, label: p })),
  ];

  return (
    <div className="space-y-2" data-testid="trench-filter-chips">
      <div className="flex flex-wrap gap-1.5" data-testid="trench-filter-chips-status">
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 self-center mr-1">
          {t("Status")}
        </span>
        {statusChips.map((c) => (
          <button
            key={c.key}
            onClick={() => setStatus(c.key)}
            data-testid={`chip-status-${c.key.replace(/\s/g, "-").toLowerCase()}`}
            className={
              "px-3 h-8 rounded-full border text-xs font-bold uppercase tracking-[0.08em] transition " +
              (status === c.key
                ? "border-cyan-700 bg-cyan-700 text-white"
                : "border-slate-300 bg-white text-slate-700 hover:border-cyan-500")
            }
          >
            {c.label}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-1.5" data-testid="trench-filter-chips-type">
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 self-center mr-1">
          {t("Type")}
        </span>
        {typeChips.map((c) => (
          <button
            key={c.key}
            onClick={() => setType(c.key)}
            data-testid={`chip-type-${c.label.replace(/\s/g, "-").toLowerCase()}`}
            className={
              "px-3 h-8 rounded-full border text-xs font-bold uppercase tracking-[0.08em] font-mono transition " +
              (type === c.key
                ? "border-cyan-700 bg-cyan-700 text-white"
                : "border-slate-300 bg-white text-slate-700 hover:border-cyan-500")
            }
          >
            {c.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// CSV Import Dialog — Phase 8B Feature 7
// ═════════════════════════════════════════════════════════════════════
export function CSVImportDialog({ open, onOpenChange, onImported }) {
  const { t } = useT();
  if (!open) return null;
  return <CSVImportDialogInner onOpenChange={onOpenChange} onImported={onImported} t={t} />;
}

const SAMPLE_CSV = `asset_id,asset_type,manufacturer,model,serial_number,size,color,condition,yard_location
RP-101,Road Plate,Acme Steel,RP-Standard,SN-12345,96x48,Yellow,Good,MASCI Yard
EP-101,End Panel,Trench Tech,EP-200,SN-67890,7x8,Orange,Good,MASCI Yard`;

function CSVImportDialogInner({ onOpenChange, onImported, t }) {
  const [csvText, setCsvText] = useState("");
  const [preview, setPreview] = useState(null);
  const [previewing, setPreviewing] = useState(false);
  const [committing, setCommitting] = useState(false);

  async function onFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    const text = await f.text();
    setCsvText(text);
    setPreview(null);
  }

  async function runPreview() {
    if (!csvText.trim()) { toast.error(t("Paste or upload a CSV first.")); return; }
    setPreviewing(true);
    try {
      const r = await api.post("/trench-safety/assets/import/preview", { csv_text: csvText });
      setPreview(r.data);
    } catch (e) {
      toast.error(extractErr(e, t("Preview failed.")));
    } finally { setPreviewing(false); }
  }

  async function runCommit() {
    if (!preview || !(preview.counts?.will_insert > 0)) {
      toast.error(t("Nothing to import. Preview shows zero valid rows."));
      return;
    }
    setCommitting(true);
    try {
      const r = await api.post("/trench-safety/assets/import", { csv_text: csvText });
      toast.success(`${t("Imported")} ${r.data.inserted_count} · ${t("Skipped")} ${r.data.skipped_count}`);
      onOpenChange(false);
      onImported?.(r.data);
    } catch (e) {
      toast.error(extractErr(e, t("Import failed.")));
    } finally { setCommitting(false); }
  }

  const diag = preview?.diagnoses || [];
  const okCount = preview?.counts?.will_insert ?? 0;
  const dupCount = preview?.counts?.duplicate ?? 0;
  const errCount = preview?.counts?.error ?? 0;

  return (
    <Dialog open={true} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="csv-import-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5 text-cyan-700" />
            {t("Import Assets · CSV")}
          </DialogTitle>
        </DialogHeader>

        <div className="text-xs text-slate-600">
          {t("Upload a CSV or paste rows below. Preview validates every row against the certified registry — duplicates and bad rows are blocked.")}
        </div>

        <div className="border-2 border-dashed border-slate-300 rounded p-3 text-sm">
          <div className="flex items-center gap-3 flex-wrap">
            <label className="cursor-pointer inline-flex items-center gap-2 px-3 py-1.5 border border-slate-300 bg-white rounded hover:border-cyan-600 text-xs font-bold uppercase tracking-[0.08em]" data-testid="csv-import-file-label">
              <Upload className="w-3.5 h-3.5" /> {t("Choose CSV File")}
              <input type="file" accept=".csv,text/csv" onChange={onFile} className="hidden" data-testid="csv-import-file" />
            </label>
            <button
              type="button"
              className="text-xs text-cyan-700 underline"
              onClick={() => setCsvText(SAMPLE_CSV)}
              data-testid="csv-import-sample"
            >
              {t("Load sample")}
            </button>
            <span className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">
              {t("Limit 500 rows per file")}
            </span>
          </div>
          <Textarea
            value={csvText}
            onChange={(e) => { setCsvText(e.target.value); setPreview(null); }}
            placeholder="asset_id,asset_type,manufacturer,..."
            rows={6}
            className="mt-2 font-mono text-xs"
            data-testid="csv-import-textarea"
          />
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={runPreview} disabled={previewing || !csvText.trim()} variant="outline" data-testid="csv-import-preview-btn">
            {previewing ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Preview")}
          </Button>
          <Button onClick={runCommit} disabled={committing || !preview || okCount === 0} className="bg-cyan-700 hover:bg-cyan-800" data-testid="csv-import-commit-btn">
            {committing ? <Loader2 className="w-4 h-4 animate-spin" /> : (<><Plus className="w-4 h-4 mr-1" /> {t("Commit Import")}</>)}
          </Button>
        </div>

        {preview && (
          <div data-testid="csv-import-preview">
            <div className="flex flex-wrap gap-2 mt-1">
              <span className="px-2 py-0.5 rounded border border-emerald-300 bg-emerald-50 text-emerald-900 text-xs font-bold uppercase tracking-[0.08em]" data-testid="csv-preview-count-ok">
                {okCount} {t("will insert")}
              </span>
              <span className="px-2 py-0.5 rounded border border-amber-300 bg-amber-50 text-amber-900 text-xs font-bold uppercase tracking-[0.08em]" data-testid="csv-preview-count-dup">
                {dupCount} {t("duplicate")}
              </span>
              <span className="px-2 py-0.5 rounded border border-red-300 bg-red-50 text-red-900 text-xs font-bold uppercase tracking-[0.08em]" data-testid="csv-preview-count-err">
                {errCount} {t("error")}
              </span>
            </div>
            <div className="mt-2 max-h-64 overflow-y-auto border border-slate-200 rounded">
              <table className="w-full text-xs">
                <thead className="bg-slate-50 sticky top-0">
                  <tr className="text-left font-mono uppercase tracking-[0.12em] text-slate-600">
                    <th className="px-2 py-1.5">{t("Row")}</th>
                    <th className="px-2 py-1.5">{t("Asset ID")}</th>
                    <th className="px-2 py-1.5">{t("Type")}</th>
                    <th className="px-2 py-1.5">{t("Status")}</th>
                    <th className="px-2 py-1.5">{t("Errors")}</th>
                  </tr>
                </thead>
                <tbody>
                  {diag.map((d) => (
                    <tr key={d.row_index} className="border-t border-slate-100" data-testid={`csv-preview-row-${d.row_index}`}>
                      <td className="px-2 py-1.5 font-mono">{d.row_index}</td>
                      <td className="px-2 py-1.5 font-mono font-bold">{d.asset_id || "—"}</td>
                      <td className="px-2 py-1.5">{t(d.asset_type)}</td>
                      <td className={"px-2 py-1.5 font-bold uppercase text-[10px] tracking-[0.08em] " + (
                        d.status === "will_insert" ? "text-emerald-700"
                        : d.status === "duplicate" ? "text-amber-700"
                        : "text-red-700"
                      )}>{d.status}</td>
                      <td className="px-2 py-1.5 text-red-700">{(d.errors || []).join("; ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} data-testid="csv-import-close">{t("Close")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
