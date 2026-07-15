// Phase 10A · Safety/Admin Excavation Oversight Surface
// Phase 10A-B · OMEGA Correction Directive integration:
//   • Reinspection Queue tab (Correction 10)
//   • Spanish ↔ English notes toggle (Correction 9)
//   • Daily Report linkage display (Correction 1)
//   • Personnel + job linkage display (Corrections 2 + 3)
// FV-7.5 · Superintendent Oversight Chips (top row)
// FV-7.6 · Safety OSHA Rollup Chips (second row) — single-tap filter,
//          no drill-down maze.
import React, { useEffect, useMemo, useState } from "react";
import { Loader2, AlertTriangle, CheckCircle2, MessageSquare, Languages, CalendarClock, Link2, Siren, ShieldCheck, ShieldAlert, HardHat, Box, Layers, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import TrenchSafetyShell from "@/pages/trench_safety/TrenchSafetyShell";

const STATUSES = ["Submitted", "Needs Review", "Action Required", "Pending Verification", "Reviewed", "Closed", "Reopened"];
const TABS = [
  { key: "all", label: "All Records" },
  { key: "reinspection", label: "Reinspection Queue" },
];

// FV-7.5 · Superintendent chips (operational status at a glance)
const SUPER_CHIPS = [
  { key: "open",         label: "Open Excavations",      Icon: Activity,    tone: "cyan" },
  { key: "reinspection", label: "Reinspection Required", Icon: CalendarClock, tone: "amber" },
  { key: "no_cp",        label: "No Competent Person",   Icon: HardHat,     tone: "red" },
  { key: "no_ps",        label: "No Protective System",  Icon: ShieldAlert, tone: "red" },
  { key: "trench_box",   label: "Trench Boxes Deployed", Icon: Box,         tone: "slate" },
  { key: "road_plate",   label: "Road Plates Deployed",  Icon: Layers,      tone: "slate" },
  { key: "emergency",    label: "Emergency Excavations", Icon: Siren,       tone: "red" },
];

// FV-7.6 · Safety OSHA rollup chips (deterministic flag rollups)
const SAFETY_CHIPS = [
  { key: "flag_no_cp",        label: "No Competent Person",      Icon: HardHat,     tone: "red" },
  { key: "flag_protective",   label: "Protective System Issue",  Icon: ShieldAlert, tone: "red" },
  { key: "flag_depth",        label: "Depth Validation Issue",   Icon: AlertTriangle, tone: "amber" },
  { key: "flag_road_plate",   label: "Road Plate Validation Issue", Icon: Layers,   tone: "amber" },
  { key: "flag_reinspection", label: "Reinspection Required",    Icon: CalendarClock, tone: "amber" },
];

const TONE_CLS = {
  cyan:  { idle: "border-cyan-300 bg-cyan-50 text-cyan-900 hover:bg-cyan-100",   on: "border-cyan-700 bg-cyan-700 text-white" },
  amber: { idle: "border-amber-300 bg-amber-50 text-amber-900 hover:bg-amber-100", on: "border-amber-700 bg-amber-700 text-white" },
  red:   { idle: "border-red-300 bg-red-50 text-red-900 hover:bg-red-100",         on: "border-red-700 bg-red-700 text-white" },
  slate: { idle: "border-slate-300 bg-slate-50 text-slate-800 hover:bg-slate-100", on: "border-slate-800 bg-slate-800 text-white" },
};

function ChipRow({ title, chips, counts, activeChip, onClick, testId }) {
  const { t } = useT();
  return (
    <div className="mb-2" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1">{t(title)}</div>
      <div className="flex flex-wrap gap-2">
        {chips.map(({ key, label, Icon, tone }) => {
          const on = activeChip === key;
          const cls = TONE_CLS[tone] || TONE_CLS.slate;
          const n = counts?.[key];
          return (
            <button
              key={key}
              type="button"
              onClick={() => onClick(on ? null : key)}
              className={"inline-flex items-center gap-1.5 px-2.5 h-8 rounded-full border text-[11px] font-bold uppercase tracking-[0.08em] transition " + (on ? cls.on : cls.idle)}
              data-testid={`${testId}-${key}`}
              data-active={on ? "true" : "false"}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{t(label)}</span>
              <span className={"px-1.5 py-0.5 rounded text-[10px] font-mono " + (on ? "bg-white/20" : "bg-white border border-current/20")}
                data-testid={`${testId}-${key}-count`}>
                {n ?? "—"}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function ExcavationOversight() {
  const { t } = useT();
  const [tab, setTab] = useState("all");
  const [state, setState] = useState({ items: [], loading: true });
  const { items, loading } = state;
  const [filters, setFilters] = useState({});
  const [activeChip, setActiveChip] = useState(null);
  const [chipCounts, setChipCounts] = useState({});
  const [reviewing, setReviewing] = useState(null);
  const filterParamsKey = useMemo(() => JSON.stringify(filters || {}), [filters]);

  // FV-7.5/7.6 · Load chip counts (single deterministic call)
  useEffect(() => {
    let alive = true;
    api.get("/trench-safety/excavations/oversight-chips")
      .then((r) => { if (alive) setChipCounts(r.data || {}); })
      .catch(() => { if (alive) setChipCounts({}); });
    return () => { alive = false; };
  }, [state._bust]);

  useEffect(() => {
    let alive = true;
    const fetchData = async () => {
      try {
        let r;
        if (tab === "reinspection") {
          r = await api.get("/trench-safety/excavations/reinspection-queue");
        } else {
          const rawFilters = filterParamsKey ? JSON.parse(filterParamsKey) : {};
          const params = {};
          Object.entries(rawFilters).forEach(([k, v]) => { if (v) params[k] = v; });
          if (activeChip) params.chip = activeChip;
          r = await api.get("/trench-safety/excavations", { params });
        }
        if (alive) setState({ items: r.data?.items || [], loading: false });
      } catch {
        if (alive) setState({ items: [], loading: false });
      }
    };
    fetchData();
    return () => { alive = false; };
  }, [activeChip, filterParamsKey, state._bust, tab]);

  const reload = () => setState((s) => ({ ...s, loading: true, _bust: Math.random() }));

  return (
    <TrenchSafetyShell active="excavations" title={t("Excavation Oversight")} kicker={t("Public field submissions · review and close · reinspection queue")}>
      <p className="text-slate-700 mb-3 text-sm">{t("Field crews submit excavation records from the Public Safety Tile. Coaching language. No punitive vocabulary.")}</p>

      {/* FV-7.5 · Superintendent Oversight Chips */}
      <ChipRow
        title="Superintendent Oversight · Single Tap Filter"
        chips={SUPER_CHIPS}
        counts={chipCounts}
        activeChip={activeChip}
        onClick={(k) => { setActiveChip(k); setTab("all"); }}
        testId="super-chips"
      />
      {/* FV-7.6 · Safety OSHA Rollup Chips */}
      <ChipRow
        title="Safety OSHA Rollup · Single Tap Filter"
        chips={SAFETY_CHIPS}
        counts={chipCounts}
        activeChip={activeChip}
        onClick={(k) => { setActiveChip(k); setTab("all"); }}
        testId="safety-chips"
      />

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200 mb-3 mt-2" data-testid="exc-tabs">
        {TABS.map((tabDef) => (
          <button
            key={tabDef.key}
            type="button"
            onClick={() => setTab(tabDef.key)}
            className={"px-3 py-2 text-xs font-bold uppercase tracking-[0.12em] border-b-2 transition " +
              (tab === tabDef.key ? "border-cyan-700 text-cyan-900" : "border-transparent text-slate-500 hover:text-slate-900")}
            data-testid={`exc-tab-${tabDef.key}`}
          >
            {tabDef.key === "reinspection" && <CalendarClock className="w-3.5 h-3.5 inline mr-1 -mt-0.5" />}
            {t(tabDef.label)}
          </button>
        ))}
      </div>

      {tab === "all" && (
        <div className="bg-white border border-slate-200 rounded p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2" data-testid="exc-filters">
          <Input placeholder={t("Project name")} value={filters.project_name || ""} onChange={(e) => setFilters({ ...filters, project_name: e.target.value })} data-testid="exc-filter-project" />
          <Input placeholder={t("Supervisor")} value={filters.supervisor_name || ""} onChange={(e) => setFilters({ ...filters, supervisor_name: e.target.value })} data-testid="exc-filter-supervisor" />
          <Select value={filters.status || "__all"} onValueChange={(v) => setFilters({ ...filters, status: v === "__all" ? "" : v })}>
            <SelectTrigger data-testid="exc-filter-status"><SelectValue placeholder={t("Status")} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="__all">{t("All Statuses")}</SelectItem>
              {STATUSES.map((s) => <SelectItem key={s} value={s}>{t(s)}</SelectItem>)}
            </SelectContent>
          </Select>
          <Input type="number" placeholder={t("Min depth ft")} value={filters.depth_min || ""} onChange={(e) => setFilters({ ...filters, depth_min: e.target.value })} data-testid="exc-filter-depth" />
          <Button variant="outline" size="sm" onClick={() => setFilters({})} data-testid="exc-filter-reset">{t("Reset")}</Button>
        </div>
      )}

      <div className="mt-3" data-testid="exc-list">
        {loading ? <Loader2 className="w-5 h-5 animate-spin text-cyan-700" /> :
          items.length === 0 ? <div className="text-sm italic text-slate-500" data-testid="exc-list-empty">— {t(tab === "reinspection" ? "no open reinspections" : "no excavation records")} —</div> :
          <ul className="space-y-2">
            {items.map((d) => (
              <li key={d.id} className="bg-white border border-slate-200 rounded p-3" data-testid={`exc-row-${d.id}`}>
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="flex-1 min-w-0">
                    <div className="font-mono font-black text-lg text-slate-900">{d.id}</div>
                    <div className="text-sm text-slate-700">
                      {d.project_name || "—"}
                      {d.project_number && <span className="font-mono text-xs text-slate-500"> · #{d.project_number}</span>}
                    </div>
                    <div className="text-xs text-slate-600">
                      {[
                        d.foreman_name && `Foreman: ${d.foreman_name}`,
                        d.superintendent_name && `Super: ${d.superintendent_name}`,
                        d.competent_person_name && `CP: ${d.competent_person_name}`,
                        d.date_of_work,
                      ].filter(Boolean).join(" · ")}
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {t("Depth")}: {d.depth_ft ?? "—"} ft · {t("Protective")}: {d.protective_system} · {t("Soil")}: {d.soil_classification}
                    </div>
                    {(d.assigned_asset_ids?.length || d.road_plate_ids?.length) > 0 && (
                      <div className="text-[11px] mt-1 text-cyan-800 flex flex-wrap gap-1" data-testid={`exc-row-${d.id}-assets`}>
                        {(d.assigned_asset_ids || []).map((a) => <span key={a} className="bg-cyan-100 px-1.5 py-0.5 rounded font-mono">{a}</span>)}
                        {(d.road_plate_ids || []).map((a) => <span key={a} className="bg-amber-100 text-amber-900 px-1.5 py-0.5 rounded font-mono">{a}</span>)}
                      </div>
                    )}
                    {d.daily_report_links?.length > 0 && (
                      <div className="text-[11px] mt-1 text-emerald-800 inline-flex items-center gap-1" data-testid={`exc-row-${d.id}-dr-links`}>
                        <Link2 className="w-3 h-3" /> {t("Daily Report:")} {d.daily_report_links.map((l) => l.report_number || l.daily_report_id).join(", ")}
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <div className={"text-[10px] uppercase tracking-[0.12em] px-2 py-0.5 rounded border font-bold " +
                      (d.status === "Action Required" ? "border-red-300 bg-red-50 text-red-800" :
                       d.status === "Needs Review" ? "border-amber-300 bg-amber-50 text-amber-800" :
                       d.status === "Closed" ? "border-emerald-300 bg-emerald-50 text-emerald-800" :
                       "border-slate-300 bg-slate-50 text-slate-700")}>{t(d.status)}</div>
                    {d.reinspection_required && !d.reinspection_completed && (
                      <div className="mt-1 inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.12em] font-bold text-amber-800" data-testid={`exc-row-${d.id}-reinspection-flag`}>
                        <CalendarClock className="w-3 h-3" /> {t("Reinspection")}
                      </div>
                    )}
                    <Button size="sm" variant="outline" onClick={() => setReviewing(d)} data-testid={`exc-review-${d.id}`} className="mt-2"><MessageSquare className="w-3.5 h-3.5 mr-1" /> {t("Review")}</Button>
                  </div>
                </div>
                {d.flags?.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {d.flags.map((fl, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs">
                        <AlertTriangle className="w-3 h-3 mt-0.5 text-amber-700 shrink-0" />
                        <span><b className="text-amber-900">{t(fl.level)}</b> · {t(fl.message)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        }
      </div>
      <ReviewDialog rec={reviewing} onClose={(refresh) => { setReviewing(null); if (refresh) reload(); }} />
    </TrenchSafetyShell>
  );
}

function ReviewDialog({ rec, onClose }) {
  const { t } = useT();
  const [note, setNote] = useState("");
  const [reinspectReason, setReinspectReason] = useState("Rain Event");
  const [ackReason, setAckReason] = useState("");
  const [ackTabulated, setAckTabulated] = useState(false);
  const [transText, setTransText] = useState("");
  const [showTranslated, setShowTranslated] = useState(false);
  const [savedTranslation, setSavedTranslation] = useState("");
  const [busy, setBusy] = useState(false);
  if (!rec) return null;

  async function act(action) {
    setBusy(true);
    try {
      await api.post(`/trench-safety/excavations/${rec.id}/review`, { action, coaching_note: note });
      toast.success(t("Saved"));
      onClose(true);
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed");
    } finally { setBusy(false); }
  }

  async function triggerReinspection() {
    setBusy(true);
    try {
      await api.post(`/trench-safety/excavations/${rec.id}/reinspection-trigger`, {
        reason: reinspectReason, note,
      });
      toast.success(t("Reinspection triggered"));
      onClose(true);
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed");
    } finally { setBusy(false); }
  }

  async function saveTranslation() {
    setBusy(true);
    try {
      await api.post(`/trench-safety/excavations/${rec.id}/translate-notes`, { translated_text: transText });
      toast.success(t("Translation saved"));
      setSavedTranslation(transText);
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed");
    } finally { setBusy(false); }
  }

  async function acknowledgeRatedDepth() {
    setBusy(true);
    try {
      await api.post(`/trench-safety/excavations/${rec.id}/rated-depth-acknowledge`, {
        reason: ackReason, tabulated_data_exception: ackTabulated,
      });
      toast.success(t("Rated-depth override recorded"));
      onClose(true);
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed");
    } finally { setBusy(false); }
  }

  const translatedText = savedTranslation || rec.field_notes_translated_text || "";
  const isSpanish = (rec.field_notes_original_language || rec.language || "").toLowerCase() === "es";
  const displayedNotes = showTranslated && translatedText ? translatedText : (rec.field_notes_original_text || rec.field_notes || "");

  return (
    <Dialog open={true} onOpenChange={() => onClose(false)}>
      <DialogContent className="max-w-2xl" data-testid="exc-review-dialog">
        <DialogHeader><DialogTitle>{rec.id} · {t("Review")}</DialogTitle></DialogHeader>
        <div className="space-y-3 text-sm max-h-[60vh] overflow-y-auto pr-2">
          <div className="text-xs text-slate-600 grid grid-cols-2 gap-2">
            <div><b>{t("Project")}:</b> {rec.project_name}</div>
            <div><b>{t("Project #")}:</b> {rec.project_number || "—"}</div>
            <div><b>{t("Foreman")}:</b> {rec.foreman_name || rec.supervisor_name || "—"}</div>
            <div><b>{t("Superintendent")}:</b> {rec.superintendent_name || "—"}</div>
            <div><b>{t("Competent Person")}:</b> {rec.competent_person_name || "—"}</div>
            <div><b>{t("Date")}:</b> {rec.date_of_work || "—"}</div>
            <div><b>{t("Customer")}:</b> {rec.customer || "—"}</div>
            <div><b>{t("PM")}:</b> {rec.project_manager || "—"}</div>
          </div>

          {/* Field notes with EN/ES toggle */}
          {(rec.field_notes_original_text || rec.field_notes) && (
            <div className="bg-slate-50 border border-slate-200 rounded p-2" data-testid="exc-review-notes">
              <div className="flex items-center justify-between mb-1">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold inline-flex items-center gap-1">
                  <Languages className="w-3 h-3" /> {t("Field Notes")} ({isSpanish ? "ES" : "EN"})
                </div>
                {translatedText && (
                  <button type="button" onClick={() => setShowTranslated((p) => !p)}
                    className="text-[10px] uppercase tracking-[0.12em] font-bold text-cyan-700 hover:text-cyan-900"
                    data-testid="exc-review-toggle-translation">
                    {showTranslated ? t("Show Original") : t("Show Translated")}
                  </button>
                )}
              </div>
              <div className="text-xs text-slate-800 whitespace-pre-wrap">{displayedNotes}</div>
            </div>
          )}

          {/* Translation override (Correction 9) */}
          {isSpanish && (
            <details className="bg-amber-50 border border-amber-300 rounded p-2" data-testid="exc-review-translate-panel">
              <summary className="cursor-pointer text-xs font-bold uppercase tracking-[0.12em] text-amber-900">{t("Add / Update English Translation")}</summary>
              <Textarea
                className="mt-2"
                value={transText}
                onChange={(e) => setTransText(e.target.value)}
                placeholder={t("English translation (original Spanish is preserved)")}
                rows={3}
                data-testid="exc-review-translation-input"
              />
              <Button size="sm" onClick={saveTranslation} disabled={busy || !transText.trim()} className="mt-2 bg-cyan-700 hover:bg-cyan-800" data-testid="exc-review-translation-save">{t("Save Translation")}</Button>
            </details>
          )}

          {/* Coaching note */}
          <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder={t("Coaching note (optional)")} rows={2} data-testid="exc-review-note" />

          {/* Reinspection trigger */}
          <div className="bg-cyan-50 border border-cyan-200 rounded p-2" data-testid="exc-review-reinspect-panel">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-1">{t("Trigger Reinspection")}</div>
            <div className="flex items-stretch gap-2">
              <Select value={reinspectReason} onValueChange={setReinspectReason}>
                <SelectTrigger className="flex-1" data-testid="exc-review-reinspect-reason"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {["Rain Event", "Water Intrusion", "Cave-In", "Protective System Changed", "Utility Conflict", "Near Miss", "Other"].map((r) => (
                    <SelectItem key={r} value={r}>{t(r)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button size="sm" variant="outline" onClick={triggerReinspection} disabled={busy} data-testid="exc-review-reinspect-trigger">
                <CalendarClock className="w-3.5 h-3.5 mr-1" /> {t("Trigger")}
              </Button>
            </div>
          </div>

          {/* FV-7.1 · Trench-box rated-depth Safety override / acknowledgement */}
          {(rec.flags || []).some((fl) => fl.code === "TRENCH_BOX_DEPTH" && fl.level === "Action Required") && (
            <div className="bg-red-50 border border-red-300 rounded p-2" data-testid="exc-review-rdack-panel">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-red-800 font-bold mb-1 inline-flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> {t("Rated-Depth Safety Override")}
              </div>
              <p className="text-[11px] text-red-900 mb-1.5 leading-snug">
                {t("Stacked boxes, engineered systems, and approved tabulated-data exceptions can legitimately exceed a simple rated-depth comparison. Record the justification — never silently.")}
              </p>
              <Textarea value={ackReason} onChange={(e) => setAckReason(e.target.value)} rows={2}
                placeholder={t("Required reason (stacked configuration, engineered shoring, tabulated data ref…)")}
                data-testid="exc-review-rdack-reason" />
              <label className="flex items-center gap-2 mt-1 text-[11px] text-red-900">
                <input type="checkbox" checked={ackTabulated} onChange={(e) => setAckTabulated(e.target.checked)} data-testid="exc-review-rdack-tabulated" />
                {t("Approved tabulated-data exception (manufacturer or PE-stamped engineering)")}
              </label>
              <Button size="sm" onClick={acknowledgeRatedDepth} disabled={busy || (!ackReason.trim() && !ackTabulated)}
                className="mt-2 bg-red-700 hover:bg-red-800" data-testid="exc-review-rdack-save">
                <ShieldCheck className="w-3.5 h-3.5 mr-1" /> {t("Record Safety Override")}
              </Button>
              {rec.rated_depth_acknowledged && (
                <div className="mt-2 text-[10px] text-emerald-800 inline-flex items-center gap-1" data-testid="exc-review-rdack-existing">
                  <CheckCircle2 className="w-3 h-3" /> {t("Existing override on file")} · {rec.rated_depth_acknowledged_by || "—"} · {rec.rated_depth_acknowledged_at || ""}
                </div>
              )}
            </div>
          )}
        </div>
        <DialogFooter className="flex-wrap gap-2">
          <Button variant="outline" onClick={() => act("request_clarification")} disabled={busy} data-testid="exc-action-clarify">{t("Request Clarification")}</Button>
          <Button variant="outline" onClick={() => act("review")} disabled={busy} data-testid="exc-action-review">{t("Mark Reviewed")}</Button>
          <Button onClick={() => act("close")} disabled={busy} className="bg-cyan-700 hover:bg-cyan-800" data-testid="exc-action-close"><CheckCircle2 className="w-4 h-4 mr-1" /> {t("Close")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
