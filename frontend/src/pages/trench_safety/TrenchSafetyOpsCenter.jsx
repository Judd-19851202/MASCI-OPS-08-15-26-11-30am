// Trench Safety · Phase 7.5B + Phase 7 — Operations Center
// ──────────────────────────────────────────────────────────────────────
// One shared module hosting:
//   • SafetyRepairReview  — review queue + verify / reject / require additional repair
//   • SafetyFieldReports  — incoming public reports inbox + actions
//   • QRManagementPanel   — generate / download / reprint QR + history
//   • PhotoManagementPanel — upload / categorise / set visibility / delete
//   • DailyPosturePanel    — top-of-portal posture strip
//
// Every component is consumed by both the Safety Portal and Admin Portal
// routes (the backend `safety_or_admin` gate accepts either token).
//
// Visibility rules:
//   • Public QR view only shows photos with visibility ∈ {Field Safe, Public}.
//   • Internal photos NEVER appear on a public surface.
//   • Repair Complete ≠ Safe To Use — UI never auto-clears Inspection Hold.
import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  Loader2, ShieldAlert, AlertTriangle, CheckCircle2, ArrowRight,
  Wrench, FileWarning, ScanLine, Camera, Eye, EyeOff, Trash2, Download,
  Printer, History, Activity, Filter, RefreshCw, Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";

const PHOTO_CATEGORIES = [
  "Front", "Rear", "Left", "Right",
  "Serial Plate", "Manufacturer Plate",
  "Inspection", "Damage", "Repair", "Certification", "Other",
];
const PHOTO_VISIBILITIES = ["Internal Only", "Field Safe", "Public"];
const REPORT_KINDS = ["Damage", "Unsafe Condition", "Missing Pins", "Missing Labels", "Certification Concern", "Other"];

function extractErr(e, fallback) {
  return e?.response?.data?.detail || e?.message || fallback;
}

// ═════════════════════════════════════════════════════════════════════
// Daily Posture Panel — top of Safety Portal / Admin Portal
// ═════════════════════════════════════════════════════════════════════
export function DailyPosturePanel({ adminPortal = false }) {
  const { t } = useT();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const nav = useNavigate();
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get("/trench-safety/dashboard");
        if (!cancelled) setData(r.data || {});
      } catch (e) {
        if (!cancelled) toast.error(extractErr(e, t("Posture load failed.")));
      } finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [t]);
  const base = adminPortal ? "/admin/trench-safety" : "/safety/trench-safety";
  const tile = (key, label, value, tone, to) => (
    <button
      key={key}
      type="button"
      onClick={() => nav(to)}
      className={`bg-white border rounded-md p-3 text-left hover:shadow transition ${
        tone === "danger" ? "border-red-300 hover:border-red-500"
        : tone === "warn" ? "border-amber-300 hover:border-amber-500"
        : "border-slate-200 hover:border-cyan-600"
      }`}
      data-testid={`posture-${key}`}
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className={`font-display text-2xl font-black leading-none mt-1 ${
        tone === "danger" ? "text-red-700" : tone === "warn" ? "text-amber-700" : "text-slate-900"
      }`}>{value ?? 0}</div>
    </button>
  );
  if (loading) {
    return <div className="text-xs text-slate-400 py-2" data-testid="posture-loading">{t("Loading posture…")}</div>;
  }
  const a = data?.alerts || {};
  const c = data?.counts_by_status || {};
  return (
    <section className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-2" data-testid="daily-posture">
      {tile("safety-holds",   t("Safety Holds"),         c["Safety Hold"] || 0,  "danger", `${base}/assets?status=Safety+Hold`)}
      {tile("insp-holds",     t("Inspection Holds"),     c["Inspection Hold"] || 0, "warn", `${base}/assets?status=Inspection+Hold`)}
      {tile("cert-holds",     t("Certification Holds"),  c["Certification Hold"] || 0, "warn", `${base}/assets?status=Certification+Hold`)}
      {tile("await-verify",   t("Awaiting Verification"), a.repairs_awaiting_verification || 0, "warn", `${base}/repair-review?status=awaiting`)}
      {tile("crit-repairs",   t("Critical Repairs"),     a.critical_repairs || 0,    "danger", `${base}/repair-review?severity=Critical`)}
      {tile("fail-insp-7",    t("Failed Insp. 7d"),      a.failed_inspections_7d || 0,   "warn",   `${base}/assets?needs_review=yes`)}
      {tile("damage-reports", t("Damage Reports"),       a.new_damage_reports_7d || 0, "warn", `${base}/field-reports`)}
      {tile("cert-exp-30",    t("Cert Exp. 30d"),        a.expiring_certifications_30d || 0, "warn", `${base}/assets?needs_review=yes`)}
      {tile("oos",            t("Out Of Service"),       (c["Maintenance Hold"]||0) + (c["Retired"]||0), "default", `${base}/assets`)}
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════
// Safety Repair Review
// ═════════════════════════════════════════════════════════════════════
const REPAIR_FILTERS = [
  { key: "all",       label: "All Open" },
  { key: "awaiting",  label: "Awaiting Verification" },
  { key: "critical",  label: "Critical" },
  { key: "vendor",    label: "Vendor Repairs" },
  { key: "completed", label: "Completed" },
  { key: "closed",    label: "Closed" },
];

function VerifyRepairDialog({ open, onOpenChange, repair, onDone }) {
  const { t } = useT();
  const [decision, setDecision] = useState("approve");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  if (!repair) return null;
  async function go() {
    setSaving(true);
    try {
      const passed = decision === "approve";
      await api.post(`/trench-safety/repairs/${repair.id}/verify`, {
        reinspection_passed: passed,
        notes: notes || (passed ? "Verified by Safety" : "Returned for additional repair"),
      });
      toast.success(passed ? t("Repair verified — Inspection Hold released.") : t("Returned to Shop for additional repair."));
      onOpenChange(false);
      onDone?.();
    } catch (e) {
      toast.error(extractErr(e, t("Verification failed.")));
    } finally { setSaving(false); }
  }
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg" data-testid="verify-repair-dialog">
        <DialogHeader><DialogTitle>{t("Verify Repair")} · {repair.asset_id}</DialogTitle></DialogHeader>
        <div className="bg-amber-50 border border-amber-300 rounded p-2 text-xs text-amber-900">
          <ShieldAlert className="w-3.5 h-3.5 inline -mt-0.5 mr-1" />
          {t("Repair Complete does not mean Safe To Use. Verification is what releases the Inspection Hold. Safety Holds and Certification Holds are never auto-cleared.")}
        </div>
        <div className="text-xs text-slate-600">
          <strong>{t("Issue:")}</strong> {repair.issue_description || "—"}<br />
          <strong>{t("Vendor:")}</strong> {repair.repair_vendor || "—"}<br />
          <strong>{t("Severity:")}</strong> {repair.severity_at_creation || "—"}
        </div>
        <div>
          <Label className="text-xs font-bold">{t("Decision")}</Label>
          <Select value={decision} onValueChange={setDecision}>
            <SelectTrigger data-testid="verify-decision"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="approve">{t("Approve · Release Inspection Hold")}</SelectItem>
              <SelectItem value="reject">{t("Reject · Return to Shop")}</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-xs font-bold">{t("Notes")}</Label>
          <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} data-testid="verify-notes" />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>{t("Cancel")}</Button>
          <Button onClick={go} disabled={saving} className={decision === "approve" ? "bg-emerald-700 hover:bg-emerald-800" : "bg-amber-600 hover:bg-amber-700"} data-testid="verify-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : (decision === "approve" ? t("Approve Repair") : t("Return to Shop"))}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function SafetyRepairReview({ adminPortal = false }) {
  const { t } = useT();
  const [search] = useSearchParams();
  const initial = search.get("status") || "all";
  const [filter, setFilter] = useState(initial);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const params = { include_closed: filter === "closed", limit: 200 };
        if (filter === "critical") params.severity = "Critical";
        if (filter === "vendor") params.repair_kind = "Vendor Repair";
        if (filter === "completed") params.status = "Completed";
        if (filter === "awaiting") {
          params.status = "Completed";
          params.requires_reinspection = true;
        }
        const r = await api.get("/trench-safety/shop/repairs", { params });
        if (!cancelled) setItems(r.data?.items || []);
      } catch (e) {
        if (!cancelled) toast.error(extractErr(e, t("Repair queue load failed.")));
      } finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [filter, reloadKey, t]);

  const base = adminPortal ? "/admin/trench-safety" : "/safety/trench-safety";
  return (
    <div className="space-y-3" data-testid="safety-repair-review">
      <div className="flex flex-wrap items-center gap-2">
        {REPAIR_FILTERS.map((f) => (
          <button key={f.key} type="button" onClick={() => setFilter(f.key)}
            className={`text-xs font-bold uppercase tracking-[0.1em] px-3 py-1.5 rounded border ${filter === f.key ? "bg-cyan-700 text-white border-cyan-700" : "bg-white text-slate-700 border-slate-300 hover:border-cyan-600"}`}
            data-testid={`filter-${f.key}`}>{t(f.label)}</button>
        ))}
        <Button size="sm" variant="outline" onClick={() => setReloadKey((k) => k + 1)} data-testid="refresh-repairs">
          <RefreshCw className="w-3 h-3 mr-1" /> {t("Refresh")}
        </Button>
      </div>
      <div className="bg-amber-50 border border-amber-300 rounded p-3 text-xs text-amber-900" data-testid="rr-coaching">
        <strong>{t("Coaching:")}</strong>{" "}
        {t("Purpose: review every repair Shop completes before releasing the Inspection Hold. Why it matters: a finished repair is not a safe asset until Safety verifies. What happens next: Approve releases the Inspection Hold; Reject sends the repair back to Shop with a note.")}
      </div>
      {loading ? (
        <div className="text-sm text-slate-400" data-testid="rr-loading">{t("Loading…")}</div>
      ) : items.length === 0 ? (
        <div className="text-sm text-slate-400 py-4 text-center bg-white border border-slate-200 rounded" data-testid="rr-empty">{t("No repairs in this view.")}</div>
      ) : (
        <ul className="divide-y divide-slate-100 bg-white border border-slate-200 rounded" data-testid="rr-list">
          {items.map((r) => {
            const awaiting = r.status === "Completed" && r.requires_reinspection;
            return (
              <li key={r.id} className="p-3 flex flex-wrap items-start justify-between gap-2" data-testid={`rr-row-${r.id}`}>
                <div className="flex-1 min-w-[260px]">
                  <div className="flex items-center gap-2">
                    <Link to={`${base}/assets/${r.asset_id}`} className="font-display font-bold text-slate-900 hover:text-cyan-700">{r.asset_id}</Link>
                    <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-[0.08em] ${
                      r.status === "Completed" ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                      : r.status === "Closed After Verification" ? "bg-slate-100 text-slate-600 border-slate-300"
                      : "bg-amber-50 text-amber-800 border-amber-300"
                    }`}>{t(r.status)}</span>
                    {r.severity_at_creation && (
                      <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-[0.08em] ${
                        r.severity_at_creation === "Critical" ? "bg-red-50 text-red-800 border-red-300" : "bg-amber-50 text-amber-800 border-amber-300"
                      }`}>{t(r.severity_at_creation)}</span>
                    )}
                    {awaiting && (
                      <span className="px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-[0.08em] bg-purple-50 text-purple-800 border-purple-300">
                        {t("Awaiting Verification")}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-slate-700 mt-1">{r.issue_description || "—"}</div>
                  <div className="text-[10px] uppercase tracking-[0.14em] font-mono text-slate-500 mt-1">
                    {r.opened_at?.slice(0, 16)} {r.repair_vendor ? `· ${r.repair_vendor}` : ""}
                  </div>
                </div>
                {awaiting && (
                  <Button size="sm" onClick={() => setVerifying(r)} className="bg-emerald-700 hover:bg-emerald-800" data-testid={`rr-verify-${r.id}`}>
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> {t("Verify")}
                  </Button>
                )}
              </li>
            );
          })}
        </ul>
      )}
      <VerifyRepairDialog open={Boolean(verifying)} onOpenChange={(v) => !v && setVerifying(null)} repair={verifying} onDone={() => setReloadKey((k) => k + 1)} />
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// Field Report Inbox
// ═════════════════════════════════════════════════════════════════════
export function SafetyFieldReports({ adminPortal = false }) {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [kindFilter, setKindFilter] = useState("__all");
  const [reloadKey, setReloadKey] = useState(0);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        // Field reports surface as repair rows with source=Public QR Damage Report
        const r = await api.get("/trench-safety/shop/repairs", { params: { include_closed: true, limit: 200 } });
        const all = (r.data?.items || []).filter((x) => (x.source || "").includes("Public") || x.public_intake_id);
        const filtered = kindFilter === "__all" ? all : all.filter((x) => (x.report_kind || "").toLowerCase() === kindFilter.toLowerCase());
        if (!cancelled) setItems(filtered);
      } catch (e) {
        if (!cancelled) toast.error(extractErr(e, t("Field reports load failed.")));
      } finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [reloadKey, kindFilter, t]);

  async function closeReport(r) {
    const note = window.prompt(t("Close this report with what note?"));
    if (!note) return;
    try {
      await api.patch(`/trench-safety/repairs/${r.id}`, {
        status: "Closed After Verification",
        completion_notes: `Field Report closed by Safety: ${note}`,
      });
      toast.success(t("Field report closed."));
      setReloadKey((k) => k + 1);
    } catch (e) { toast.error(extractErr(e, t("Close failed."))); }
  }

  const base = adminPortal ? "/admin/trench-safety" : "/safety/trench-safety";
  return (
    <div className="space-y-3" data-testid="safety-field-reports">
      <div className="bg-amber-50 border border-amber-300 rounded p-3 text-xs text-amber-900">
        <strong>{t("Coaching:")}</strong>{" "}
        {t("Purpose: review every report a crew member submits from the field. Why it matters: reports are the leading indicator of unsafe conditions. What happens next: open the asset, convert to inspection or repair, or close with a note.")}
      </div>
      <div className="flex items-center gap-2">
        <Filter className="w-3.5 h-3.5 text-slate-500" />
        <Select value={kindFilter} onValueChange={setKindFilter}>
          <SelectTrigger className="w-[260px]" data-testid="fr-kind-filter"><SelectValue placeholder={t("All Report Types")} /></SelectTrigger>
          <SelectContent>
            <SelectItem value="__all">{t("All Report Types")}</SelectItem>
            {REPORT_KINDS.map((k) => <SelectItem key={k} value={k}>{t(k)}</SelectItem>)}
          </SelectContent>
        </Select>
        <Button size="sm" variant="outline" onClick={() => setReloadKey((k) => k + 1)}>
          <RefreshCw className="w-3 h-3 mr-1" /> {t("Refresh")}
        </Button>
      </div>
      {loading ? (
        <div className="text-sm text-slate-400" data-testid="fr-loading">{t("Loading…")}</div>
      ) : items.length === 0 ? (
        <div className="text-sm text-slate-400 py-4 text-center bg-white border border-slate-200 rounded" data-testid="fr-empty">{t("No field reports in this view.")}</div>
      ) : (
        <ul className="divide-y divide-slate-100 bg-white border border-slate-200 rounded" data-testid="fr-list">
          {items.map((r) => (
            <li key={r.id} className="p-3 flex flex-wrap items-start justify-between gap-2" data-testid={`fr-row-${r.id}`}>
              <div className="flex-1 min-w-[260px]">
                <div className="flex items-center gap-2">
                  <Link to={`${base}/assets/${r.asset_id}`} className="font-display font-bold text-slate-900 hover:text-cyan-700">{r.asset_id}</Link>
                  <span className="px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-[0.08em] bg-amber-50 text-amber-800 border-amber-300">
                    {t(r.report_kind || "Damage")}
                  </span>
                  <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-[0.08em] ${
                    r.status === "Closed After Verification" ? "bg-slate-100 text-slate-600 border-slate-300" : "bg-cyan-50 text-cyan-800 border-cyan-300"
                  }`}>{t(r.status)}</span>
                </div>
                <div className="text-sm text-slate-700 mt-1">{r.issue_description || "—"}</div>
                <div className="text-[10px] uppercase tracking-[0.14em] font-mono text-slate-500 mt-1">
                  {r.opened_at?.slice(0, 16)} · {r.reported_by || "anonymous"}
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <Button size="sm" variant="outline" asChild data-testid={`fr-open-${r.id}`}>
                  <Link to={`${base}/assets/${r.asset_id}`}>
                    <ArrowRight className="w-3 h-3 mr-1" /> {t("Open Asset")}
                  </Link>
                </Button>
                {r.status !== "Closed After Verification" && (
                  <Button size="sm" variant="outline" onClick={() => closeReport(r)} data-testid={`fr-close-${r.id}`}>
                    <CheckCircle2 className="w-3 h-3 mr-1" /> {t("Close")}
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// QR Management Panel (Asset Detail)
// ═════════════════════════════════════════════════════════════════════
export function QRManagementPanel({ asset }) {
  const { t } = useT();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);
  const pngUrl = `${BACKEND}/api/trench-safety/assets/${asset.asset_id}/qr-label.png`;
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get(`/trench-safety/assets/${asset.asset_id}/audit`, { params: { limit: 100, kind_prefix: "trench_asset_qr_label" } });
        if (!cancelled) setHistory((r.data?.items || []).filter((x) => (x.kind || "").includes("qr_label")));
      } catch { /* swallow */ }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [asset.asset_id, reloadKey]);
  async function logReprint() {
    try {
      await api.post(`/trench-safety/assets/${asset.asset_id}/qr-label/audit`, { action: "reprint", note: "Reprint logged by Safety/Admin" });
      toast.success(t("Reprint logged."));
      setReloadKey((k) => k + 1);
    } catch (e) { toast.error(extractErr(e, t("Reprint log failed."))); }
  }
  function printNow() {
    const w = window.open(pngUrl, "_blank");
    if (w) w.focus();
  }
  return (
    <section className="bg-white border border-slate-200 rounded-md p-4" data-testid="qr-mgmt-panel">
      <div className="flex items-center justify-between mb-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1">
          <ScanLine className="w-3.5 h-3.5" /> {t("QR Management")}
        </div>
      </div>
      <div className="flex flex-wrap items-start gap-4">
        <a href={pngUrl} target="_blank" rel="noreferrer" className="block border border-slate-200 rounded p-2 bg-white" data-testid="qr-img-link">
          <img src={pngUrl} alt="QR label" className="w-40 h-auto" />
        </a>
        <div className="flex-1 min-w-[220px]">
          <div className="text-xs text-slate-600 mb-2">
            {t("QR label is MASCI-branded and embeds the asset ID, serial, last inspection, and current status.")}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" asChild data-testid="qr-download">
              <a href={pngUrl} download={`${asset.asset_id}-qr.png`}>
                <Download className="w-3.5 h-3.5 mr-1" /> {t("Download")}
              </a>
            </Button>
            <Button size="sm" variant="outline" onClick={printNow} data-testid="qr-print">
              <Printer className="w-3.5 h-3.5 mr-1" /> {t("Print")}
            </Button>
            <Button size="sm" variant="outline" onClick={logReprint} data-testid="qr-log-reprint">
              <History className="w-3.5 h-3.5 mr-1" /> {t("Log Reprint")}
            </Button>
          </div>
          <div className="mt-3">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-1">{t("QR History")}</div>
            {loading ? <div className="text-xs text-slate-400">{t("Loading…")}</div>
              : history.length === 0 ? <div className="text-xs text-slate-400" data-testid="qr-history-empty">{t("No QR activity yet.")}</div>
              : (
                <ul className="text-xs text-slate-600 space-y-0.5 max-h-32 overflow-y-auto" data-testid="qr-history-list">
                  {history.slice(0, 10).map((h) => (
                    <li key={h.id}>
                      <span className="font-mono">{h.ts?.slice(0, 16)}</span> · {h.kind?.replace(/_/g, " ")} · {h.actor}
                    </li>
                  ))}
                </ul>
              )}
          </div>
        </div>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════
// Photo Management Panel (Asset Detail)
// ═════════════════════════════════════════════════════════════════════
function PhotoUploadDialog({ open, onOpenChange, asset, onUploaded }) {
  const { t } = useT();
  const [file, setFile] = useState(null);
  const [category, setCategory] = useState("Other");
  const [visibility, setVisibility] = useState("Internal Only");
  const [caption, setCaption] = useState("");
  const [saving, setSaving] = useState(false);
  async function go() {
    if (!file) { toast.error(t("Choose a photo first.")); return; }
    setSaving(true);
    try {
      // Read as data URL
      const dataUrl = await new Promise((res, rej) => {
        const r = new FileReader();
        r.onerror = rej;
        r.onload = () => res(r.result);
        r.readAsDataURL(file);
      });
      await api.post(`/trench-safety/assets/${asset.asset_id}/photos`, {
        category, visibility, caption,
        image_data_url: dataUrl,
        source: "Inspection",
      });
      toast.success(t("Photo uploaded."));
      onOpenChange(false);
      onUploaded?.();
      setFile(null); setCaption(""); setCategory("Other"); setVisibility("Internal Only");
    } catch (e) {
      toast.error(extractErr(e, t("Upload failed.")));
    } finally { setSaving(false); }
  }
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg" data-testid="photo-upload-dialog">
        <DialogHeader><DialogTitle>{t("Upload Photo")} · {asset?.asset_id}</DialogTitle></DialogHeader>
        <div className="bg-cyan-50 border border-cyan-200 rounded p-2 text-xs text-cyan-900">
          {t("Internal Only stays inside the Safety Portal. Field Safe + Public are surfaced on the public QR view.")}
        </div>
        <div>
          <Label className="text-xs font-bold">{t("File")}</Label>
          <Input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] || null)} data-testid="photo-file" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label className="text-xs font-bold">{t("Category")}</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger data-testid="photo-category"><SelectValue /></SelectTrigger>
              <SelectContent>{PHOTO_CATEGORIES.map((c) => <SelectItem key={c} value={c}>{t(c)}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs font-bold">{t("Visibility")}</Label>
            <Select value={visibility} onValueChange={setVisibility}>
              <SelectTrigger data-testid="photo-visibility"><SelectValue /></SelectTrigger>
              <SelectContent>{PHOTO_VISIBILITIES.map((v) => <SelectItem key={v} value={v}>{t(v)}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        </div>
        <div>
          <Label className="text-xs font-bold">{t("Caption")}</Label>
          <Input value={caption} onChange={(e) => setCaption(e.target.value)} data-testid="photo-caption" />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>{t("Cancel")}</Button>
          <Button onClick={go} disabled={saving} className="bg-cyan-700 hover:bg-cyan-800" data-testid="photo-save">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Upload")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function PhotoManagementPanel({ asset }) {
  const { t } = useT();
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openUpload, setOpenUpload] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get(`/trench-safety/assets/${asset.asset_id}/photos`);
        if (!cancelled) setPhotos(r.data?.items || []);
      } catch { /* swallow */ }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [asset.asset_id, reloadKey]);
  async function del(p) {
    if (!window.confirm(t("Delete this photo?"))) return;
    try {
      await api.delete(`/trench-safety/photos/${p.id}`);
      toast.success(t("Photo deleted."));
      setReloadKey((k) => k + 1);
    } catch (e) { toast.error(extractErr(e, t("Delete failed."))); }
  }
  return (
    <section className="bg-white border border-slate-200 rounded-md p-4" data-testid="photo-mgmt-panel">
      <div className="flex items-center justify-between mb-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1">
          <Camera className="w-3.5 h-3.5" /> {t("Photos")}
        </div>
        <Button size="sm" variant="outline" onClick={() => setOpenUpload(true)} data-testid="photo-upload-btn">
          <Upload className="w-3 h-3 mr-1" /> {t("Upload")}
        </Button>
      </div>
      {loading ? <div className="text-xs text-slate-400">{t("Loading photos…")}</div>
        : photos.length === 0 ? <div className="text-xs text-slate-400" data-testid="photo-empty">{t("No photos yet.")}</div>
        : (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2" data-testid="photo-grid">
            {photos.map((p) => (
              <div key={p.id} className="border border-slate-200 rounded p-2" data-testid={`photo-row-${p.id}`}>
                {p.image_data_url && (
                  <img src={p.image_data_url} alt={p.caption || "photo"} className="w-full h-32 object-cover rounded" />
                )}
                <div className="text-xs font-bold text-slate-900 mt-1">{t(p.category || "Other")}</div>
                <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-mono">
                  {p.visibility === "Internal Only" ? <><EyeOff className="w-3 h-3 inline -mt-0.5 mr-0.5" />{t("Internal Only")}</>
                    : <><Eye className="w-3 h-3 inline -mt-0.5 mr-0.5" />{t(p.visibility)}</>}
                </div>
                {p.caption && <div className="text-xs text-slate-600 mt-0.5 line-clamp-2">{p.caption}</div>}
                <button type="button" onClick={() => del(p)} className="text-[10px] uppercase tracking-[0.1em] font-bold text-red-600 hover:text-red-800 mt-1" data-testid={`photo-delete-${p.id}`}>
                  <Trash2 className="w-3 h-3 inline -mt-0.5 mr-0.5" /> {t("Delete")}
                </button>
              </div>
            ))}
          </div>
        )}
      <PhotoUploadDialog open={openUpload} onOpenChange={setOpenUpload} asset={asset} onUploaded={() => setReloadKey((k) => k + 1)} />
    </section>
  );
}
