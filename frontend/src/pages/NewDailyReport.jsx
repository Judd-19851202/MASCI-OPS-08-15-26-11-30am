import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  Save,
  Loader2,
  MapPin,
  Plus,
  X,
  CloudSun,
  AlertTriangle,
  Camera,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { LifecycleGuide } from "@/components/LifecycleGuide";
import { MasciLogo } from "@/components/MasciLogo";
import { Section } from "@/components/Section";
import { YesNo } from "@/components/YesNo";
import { SignaturePad } from "@/components/SignaturePad";
import { CollapseCard } from "@/components/CollapseCard";
import { PhotoUpload } from "@/components/PhotoUpload";
import { JobPicker } from "@/components/JobPicker";
import { LangToggle } from "@/components/LangToggle";
import { DistributionList } from "@/components/DistributionList";
import { EquipmentCombo } from "@/components/EquipmentCombo";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { FlUserCombo } from "@/components/FlUserCombo";
import { SupplierCombo } from "@/components/SupplierCombo";
import { DailyHoursFlag } from "@/components/HoursSanityFlag";
import { useT, getLang } from "@/lib/i18n";
import { useRememberedFormValue } from "@/lib/useRememberedFilter";
import { friendlyError } from "@/lib/friendlyErrors";
import { formatApiError } from "@/lib/apiErrors";
import { buildDailyReportDefaults } from "@/lib/dailyReportSchema";
import DailyReportExcavationActivity from "@/components/trench/DailyReportExcavationActivity";
import DailyReportStatusCard from "@/components/dailyreport/DailyReportStatusCard";
import PreviousReportSuggestions from "@/components/dailyreport/PreviousReportSuggestions";
import LinkedExcavationCompliance from "@/components/dailyreport/LinkedExcavationCompliance";
import { computeDailyReportCompliance } from "@/lib/dailyReportCompliance";
import { fetchDailyWeather } from "@/lib/weather";
import { HelpTipBlock } from "@/components/HelpTip";
import { api } from "@/lib/api";
import { getFlUser, getFlToken } from "@/lib/flAuth";
import { isAdmin } from "@/lib/adminAuth";
import { translateUserInput } from "@/lib/translateOnSubmit";
import { toast } from "sonner";
import {
  getCurrentPosition,
  reverseGeocode,
  formatCoords,
} from "@/lib/geolocation";
import {
  useFormDraft, getActorId, mintIdempotencyKey, enqueueUpload,
  persistIdempotencyKey, loadIdempotencyKey, onQueueItemSettled,
  DraftStatusPill, DraftRestorePrompt, DraftRecoveryNotice,
  QuotaWarningChip, PriorUsageBanner,
  recoverArchivedDraft,
  getDeviceScopedActorId,
  hasStalePriorUsage, getPriorUsage,
} from "@/lib/resiliency";
// iter437 · Phase 31.1 · Daily Report Crew Memory Continuity.
import {
  extractSetupSnapshot, saveCrewSetup, loadCrewSetup,
  clearCrewSetup, renameCrewSetup, applySetupSnapshotToData,
  getCrewMemoryConfidence, isProjectChange,
} from "@/lib/crewMemory";
import CrewSetupRestorePrompt from "@/components/daily-report/CrewSetupRestorePrompt";
import SupportIdAffordance from "@/components/daily-report/SupportIdAffordance";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";
const inputClsTall =
  "h-14 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";

/**
 * Module-level repeating-row block.
 *
 * MUST live at module scope (NOT inside the parent component) — otherwise
 * every keystroke creates a new component reference, which makes React
 * unmount + remount every Combo on every keystroke. That's the bug behind
 * "glitchy typing" and "no employees populating in dropdowns".
 *
 * Props:
 *   - title:       row label ("Crew Member", "Subcontractor", etc.)
 *   - rows:        the array of row objects (data[list] from the parent)
 *   - helpers:     useList output { add, remove, update }
 *   - defaults:    new-row defaults
 *   - fields:      [{ key, label, type, full, placeholder, style }, ...]
 *   - testIdBase:  data-testid prefix
 *   - t:           translation fn from useT()
 */
const RepeatBlock = ({
  title,
  rows,
  helpers,
  defaults,
  fields,
  testIdBase,
  t,
}) => (
  <div className="space-y-3">
    {rows.map((row, i) => (
      <div
        key={i}
        className="border border-slate-200 rounded-md p-3 sm:p-4 space-y-2"
        data-testid={`${testIdBase}-row-${i}`}
      >
        <div className="flex items-center justify-between gap-2 mb-1">
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
            {title} {i + 1}
          </span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => helpers.remove(i)}
            className="text-slate-500 hover:text-red-600"
            data-testid={`${testIdBase}-remove-${i}`}
          >
            <X className="w-4 h-4 mr-1" /> {t("Remove")}
          </Button>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
          {fields.map((f) => (
            <div
              key={f.key}
              className={f.full ? "lg:col-span-2" : ""}
              style={f.style}
            >
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t(f.label)}
              </Label>
              {f.type === "textarea" ? (
                <Textarea
                  value={row[f.key] || ""}
                  onChange={(e) => helpers.update(i, f.key, e.target.value)}
                  className="min-h-[60px] text-base border-2 border-slate-300"
                  placeholder={f.placeholder}
                  data-testid={`${testIdBase}-${f.key}-${i}`}
                />
              ) : f.type === "equipment-combo" ? (
                <EquipmentCombo
                  value={row[f.key] || ""}
                  onChange={(v) => helpers.update(i, f.key, v)}
                  placeholder={f.placeholder}
                  testId={`${testIdBase}-${f.key}-${i}`}
                />
              ) : f.type === "employee-combo" ? (
                <EmployeeCombo
                  value={row[f.key] || ""}
                  onChange={(v) => helpers.update(i, f.key, v)}
                  placeholder={f.placeholder}
                  testId={`${testIdBase}-${f.key}-${i}`}
                />
              ) : f.type === "supplier-combo" ? (
                <SupplierCombo
                  value={row[f.key] || ""}
                  onChange={(v) => helpers.update(i, f.key, v)}
                  placeholder={f.placeholder}
                  testId={`${testIdBase}-${f.key}-${i}`}
                />
              ) : f.type === "photo" ? (
                <PhotoUpload
                  photos={row[f.key] || []}
                  onChange={(arr) => helpers.update(i, f.key, arr)}
                  testIdBase={`${testIdBase}-${f.key}-${i}`}
                />
              ) : f.type === "readonly" ? (
                <Input
                  value={row[f.key] || ""}
                  readOnly
                  className={`${inputCls} bg-slate-100 font-mono`}
                  placeholder={f.placeholder}
                  data-testid={`${testIdBase}-${f.key}-${i}`}
                />
              ) : f.type === "select" ? (
                <select
                  value={row[f.key] || (f.options && f.options[0]) || ""}
                  onChange={(e) => helpers.update(i, f.key, e.target.value)}
                  className={inputCls}
                  data-testid={`${testIdBase}-${f.key}-${i}`}
                >
                  {(f.options || []).map((opt) => (
                    <option key={opt} value={opt}>
                      {(f.optionLabels && f.optionLabels[opt]) || opt}
                    </option>
                  ))}
                </select>
              ) : (
                <Input
                  type={f.type || "text"}
                  value={row[f.key] || ""}
                  onChange={(e) => helpers.update(i, f.key, e.target.value)}
                  className={inputCls}
                  placeholder={f.placeholder}
                  data-testid={`${testIdBase}-${f.key}-${i}`}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    ))}
    <Button
      type="button"
      variant="outline"
      onClick={() => helpers.add(defaults)}
      className="w-full h-12 border-2 border-dashed border-slate-400 hover:border-red-700 hover:text-red-700 font-bold uppercase tracking-wide text-sm"
      data-testid={`${testIdBase}-add`}
    >
      <Plus className="w-4 h-4 mr-2" /> {t("Add")} {title}
    </Button>
  </div>
);

// Generic add/remove/update helpers for repeating sections
const useList = (data, set, key) => ({
  add: (defaults = {}) =>
    set((p) => ({ ...p, [key]: [...(p[key] || []), { ...defaults }] })),
  remove: (i) =>
    set((p) => ({ ...p, [key]: (p[key] || []).filter((_, idx) => idx !== i) })),
  update: (i, field, value) =>
    set((p) => ({
      ...p,
      [key]: (p[key] || []).map((row, idx) =>
        idx === i ? { ...row, [field]: value } : row
      ),
    })),
});

export default function NewDailyReport({ publicMode = false }) {
  const navigate = useNavigate();
  const { t } = useT();
  // iter148 — pre-fill last project_number from previous submission.
  // The vast majority of crews file daily reports against the same
  // project for weeks at a time, so this saves a lookup every day.
  const [lastProject, rememberLastProject] = useRememberedFormValue(
    "pm.dailyreport.last-project-number", "",
  );
  const [data, setData] = useState(() => {
    const defaults = buildDailyReportDefaults();
    if (lastProject && !defaults.project_number) {
      defaults.project_number = lastProject;
    }
    return defaults;
  });
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const [fetchingWeather, setFetchingWeather] = useState(false);
  // Phase 6 · WS2/WS3 — submit-attempt flag for attentionOpen on collapsed
  // sections that have unresolved signal-driven detail.
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);
  // iter383 · Phase 5C.1 — Smart Operational Disclosure. Each optional
  // section is now wrapped in a CollapseCard with status badge (see
  // <CollapseCard> usages below). Per-card open state is held inside
  // each CollapseCard so users can independently expand sections that
  // matter today (e.g., subs but not visitors). ZERO field deletion.
  const idempotencyKeyRef = React.useRef(null);

  // Phase V.2 · FL Role Standardization (2026-05-29).
  // Auto-populate Prepared By from the logged-in FL user when their
  // role qualifies (leadman / foreman / superintendent / sr_super)
  // AND the field is currently empty.  Foremen still get a manual
  // fallback; this only saves a tap when the form is opened in a
  // signed-in FL context.  Doctrine: DAILY_REPORT_ROLE_PICKER_ALIGNMENT.md
  useEffect(() => {
    if ((data.prepared_by || "").trim()) return;
    let flUser = null;
    try { flUser = getFlUser(); } catch { /* no-op */ }
    if (!flUser?.name) return;
    const roleRaw = (flUser.role || "").toLowerCase();
    const eligible = [
      "leadman", "foreman", "superintendent",
      "sr_superintendent", "sr. superintendent",
      "senior superintendent",
      // legacy strings still in the wild
      "general foreman", "field supervisor",
      "working supervisor", "truck boss",
    ];
    if (eligible.some((r) => roleRaw === r)) {
      set("prepared_by", flUser.name);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // iter434 · Phase 31 · Part 2 — manual draft recovery via calm prompt
  // (do NOT auto-overwrite the form). Autosave continues silently.
  // iter440 · P0 field-incident remediation — hook now returns
  // savedAt, isCrossToken, lastSavedAt, lastError for the truthful
  // pill + restore prompt.
  const actorId = React.useMemo(() => getActorId(), []);
  const {
    pendingDraft, pendingSavedAt, pendingIsCrossToken,
    loaded: draftLoaded,
    draftStatus, lastSavedAt, lastError, quotaPressure,
    restore, discard, commit,
  } = useFormDraft("daily-report-new", data, actorId);

  // TRUST-1 · TF-016 — Recovery affordance for soft-deleted drafts.
  // After the hook reports loaded=true with no pendingDraft, probe the
  // 24h archive store. If a recently-discarded draft exists we surface
  // a calm "Bring it back" affordance — the ONLY operator path to a
  // soft-deleted draft. Hidden by default; never shown when a live
  // draft is already on offer.
  const [archivedDraft, setArchivedDraft] = React.useState(null);
  React.useEffect(() => {
    if (!draftLoaded) return undefined;
    if (pendingDraft) { setArchivedDraft(null); return undefined; }
    let cancelled = false;
    (async () => {
      try {
        const arc = await recoverArchivedDraft(
          getDeviceScopedActorId(), "daily-report-new",
        );
        if (!cancelled && arc && arc.form) setArchivedDraft(arc);
      } catch { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, [draftLoaded, pendingDraft]);

  const onRecoverArchive = React.useCallback(() => {
    if (!archivedDraft || !archivedDraft.form) return;
    setData(archivedDraft.form);
    setArchivedDraft(null);
    toast.success(t("Draft brought back"));
  }, [archivedDraft, t]);

  // TRUST-1 · TF-001 — Prior-usage soft banner.
  // Shown only when (a) the live draft is absent, (b) no archive entry
  // is recoverable, AND (c) the prior-usage beacon shows this device
  // has saved before more than 24h ago. Calm reassurance, not alarm.
  const [priorUsage, setPriorUsage] = React.useState(null);
  React.useEffect(() => {
    if (!draftLoaded) return;
    if (pendingDraft || archivedDraft) { setPriorUsage(null); return; }
    try {
      if (hasStalePriorUsage("daily-report-new")) {
        setPriorUsage(getPriorUsage("daily-report-new"));
      } else {
        setPriorUsage(null);
      }
    } catch { /* ignore */ }
  }, [draftLoaded, pendingDraft, archivedDraft]);

  // iter440 — hydrate any persisted idempotency key from IDB so a
  // reload mid-offline-queue does not mint a duplicate submission.
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const k = await loadIdempotencyKey("daily-report-new");
        if (!cancelled && k && !idempotencyKeyRef.current) {
          idempotencyKeyRef.current = k;
        }
      } catch { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, []);

  const onRestoreDraft = React.useCallback(() => {
    const d = restore();
    if (d) {
      setData(d);
      toast.success(t("Draft restored"));
    }
  }, [restore, t]);

  const onDiscardDraft = React.useCallback(() => {
    discard();
    toast.message(t("Draft discarded"));
  }, [discard, t]);

  // iter437 · Phase 31.1 · Device-local crew + equipment setup memory.
  // Loaded once on mount · NEVER auto-applied · restore prompt is the
  // only path into the form. Shared-device safe by construction.
  // iter442 · adds confidence scoring + project-change guard. The
  // device_id may SUGGEST context but MUST NOT silently hard-lock
  // identity — every reuse is operator-confirmed.
  const [crewSetup, setCrewSetup] = React.useState(null);
  const [crewMemoryConfidence, setCrewMemoryConfidence] = React.useState(null);
  React.useEffect(() => {
    const rec = loadCrewSetup();
    if (rec) {
      setCrewSetup(rec);
      setCrewMemoryConfidence(getCrewMemoryConfidence());
    }
  }, []);
  const onUseCrewSetup = React.useCallback(() => {
    if (!crewSetup) return;
    // iter442 · project-change guard. If the operator has already
    // typed a project number (auto-filled from a job pick or manual),
    // and it differs from the snapshot's project, ask before applying
    // crew/equipment. Doctrine: "if project changes, confirm before
    // reusing crew/equipment."
    const current = (data?.project_number || "").trim();
    if (current && isProjectChange(crewSetup, current)) {
      const confirmed = window.confirm(
        t("This setup is from a different project. Reuse crew and equipment anyway?")
      );
      if (!confirmed) return;
    }
    setData((d) => applySetupSnapshotToData(d, crewSetup));
    setRecentlyLoadedSetup({
      nickname: crewSetup.nickname || "",
      lastUsedAt: crewSetup.lastUsedAt || Date.now(),
    });
    setCrewSetup(null);
    toast.success(t("Loaded from recent reports on this iPad."));
  }, [crewSetup, t, data?.project_number]);
  // iter442 · "Change project / foreman" — keep the saved setup
  // available but let the operator clear ONLY the project/foreman
  // fields so they can pick a different job without losing the crew
  // memory. Calm calm calm.
  const onChangeProjectFromSetup = React.useCallback(() => {
    setData((d) => ({
      ...d,
      project_name: "",
      project_number: "",
      prepared_by: "",
      superintendent: "",
    }));
    setCrewSetup(null);
    toast.message(t("Pick a project · crew and equipment can preload after."));
  }, [t]);
  const onStartBlankCrewSetup = React.useCallback(() => {
    setCrewSetup(null);
  }, []);
  const onClearCrewSetup = React.useCallback(() => {
    clearCrewSetup();
    setCrewSetup(null);
    setRecentlyLoadedSetup(null);
    toast.message(t("Saved setup cleared from this device."));
  }, [t]);
  const onRenameCrewSetup = React.useCallback((nickname) => {
    const updated = renameCrewSetup(nickname);
    if (updated) setCrewSetup(updated);
  }, []);

  // iter438 · Phase 31.1 · tiny additive read-only load-trace line.
  // Surfaces ONLY after a Use Setup click, so the operator gets a
  // soft "this came from your saved setup" reassurance — calm,
  // dismissible (Clear Saved Setup wipes it), never persisted.
  const [recentlyLoadedSetup, setRecentlyLoadedSetup] = React.useState(null);

  const set = (k, v) => setData((p) => ({ ...p, [k]: v }));
  // Phase 10D · helper for "Use yesterday's …" suggestions
  const applyPrevSuggestion = (patch) => setData((p) => ({ ...p, ...patch }));
  // Phase 10D · live compliance state (read-only — no setState in render)
  const dailyReportCompliance = computeDailyReportCompliance(data);

  // Auto-fetch the next sequential report number on mount (or when the
  // report_date changes). The user can still edit it manually if desired.
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get(
          `/daily-reports/next-number?date=${encodeURIComponent(data.report_date || "")}`
        );
        if (alive && !data.report_number) {
          setData((p) => ({ ...p, report_number: r.data.report_number }));
        }
      } catch {
        /* if it fails the field stays editable — no big deal */
      }
    })();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data.report_date]);

  // Auto-calculate per-crew-member hours from start_time / lunch / stop_time
  // whenever any of those fields change.
  const computeHours = (start, stop, lunchMin) => {
    if (!start || !stop) return "";
    const [sh, sm] = start.split(":").map(Number);
    const [eh, em] = stop.split(":").map(Number);
    if ([sh, sm, eh, em].some((n) => Number.isNaN(n))) return "";
    let mins = (eh * 60 + em) - (sh * 60 + sm);
    if (mins < 0) mins += 24 * 60; // overnight shift
    mins -= Number(lunchMin) || 0;
    if (mins < 0) mins = 0;
    return (mins / 60).toFixed(2);
  };

  // Render a single inline preview line that walks the foreman through
  // the time math the API just did, e.g.
  //   "7:00 AM → 5:30 PM · 10.5 h gross − 0.5 h lunch = 10.00 h net"
  // Catches typos like a 7-PM stop time before the report is filed.
  const fmt12h = (s) => {
    if (!s) return "";
    const [h, m] = s.split(":").map(Number);
    if (Number.isNaN(h) || Number.isNaN(m)) return s;
    const ampm = h >= 12 ? "PM" : "AM";
    const h12 = h % 12 === 0 ? 12 : h % 12;
    return `${h12}:${String(m).padStart(2, "0")} ${ampm}`;
  };
  const grossNetPreview = (start, stop, lunchMin) => {
    if (!start || !stop) return null;
    const [sh, sm] = start.split(":").map(Number);
    const [eh, em] = stop.split(":").map(Number);
    if ([sh, sm, eh, em].some((n) => Number.isNaN(n))) return null;
    let grossMin = (eh * 60 + em) - (sh * 60 + sm);
    if (grossMin < 0) grossMin += 24 * 60;
    const lunchM = Number(lunchMin) || 0;
    const netMin = Math.max(0, grossMin - lunchM);
    const hr = (m) => (m / 60).toFixed(m % 60 === 0 ? 1 : 2);
    return {
      label: `${fmt12h(start)} \u2192 ${fmt12h(stop)}`,
      math: `${hr(grossMin)} h gross \u2212 ${(lunchM / 60).toFixed(lunchM % 60 === 0 ? 1 : 2)} h lunch = ${hr(netMin)} h net`,
    };
  };

  const applyJob = (job) => {
    setData((p) => ({
      ...p,
      project_name: job ? job.project_name : "",
      project_number: job ? job.project_number : "",
      location: p.location || (job && job.location) || "",
    }));
    if (job) toast.success(`Job loaded: #${job.project_number}`);
  };

  const useGps = async () => {
    setLocating(true);
    try {
      const pos = await getCurrentPosition();
      const { latitude, longitude, accuracy } = pos.coords;
      setData((p) => ({
        ...p,
        gps_lat: latitude,
        gps_lng: longitude,
        gps_accuracy: accuracy,
      }));
      try {
        const r = await reverseGeocode(latitude, longitude);
        setData((p) => ({ ...p, location: r.display }));
      } catch {
        setData((p) => ({
          ...p,
          location: formatCoords(latitude, longitude, accuracy),
        }));
      }
      toast.success("GPS captured — fetching weather…");
      // Auto-fetch weather right after GPS lock
      try {
        setFetchingWeather(true);
        const w = await fetchDailyWeather(latitude, longitude, data.report_date);
        setData((p) => ({
          ...p,
          weather_summary: w.summary,
          weather_snapshots: w.snapshots,
        }));
        toast.success("Weather loaded");
      } catch (we) {
        console.error(we);
        toast.warning("GPS got, but weather lookup failed — fill manually");
      } finally {
        setFetchingWeather(false);
      }
    } catch (e) {
      toast.error(e?.message || "Could not get GPS location");
    } finally {
      setLocating(false);
    }
  };

  const refreshWeather = async () => {
    if (data.gps_lat == null) {
      toast.error("Capture GPS first");
      return;
    }
    setFetchingWeather(true);
    try {
      const w = await fetchDailyWeather(
        data.gps_lat,
        data.gps_lng,
        data.report_date
      );
      setData((p) => ({
        ...p,
        weather_summary: w.summary,
        weather_snapshots: w.snapshots,
      }));
      toast.success("Weather updated");
    } catch (e) {
      toast.error("Weather fetch failed");
    } finally {
      setFetchingWeather(false);
    }
  };

  const crews = useList(data, setData, "masci_crews");
  const subs = useList(data, setData, "subcontractors");
  const vis = useList(data, setData, "visitors");
  const eq = useList(data, setData, "equipment");
  const mat = useList(data, setData, "materials");
  const act = useList(data, setData, "activities");
  // Phase V.2 · Wave-1B · structured production + constraints (operator-approved).
  // Both lists are ADDITIVE · foreman workflow unchanged · 9-step contract preserved.
  // Doctrine: PRODUCTION_UI_CERTIFICATION.md · CONSTRAINT_UI_CERTIFICATION.md
  const prod = useList(data, setData, "production");
  const cons = useList(data, setData, "constraints");

  // Phase V.2 · Auto-Expand Guidance (2026-05-29) — wraps the Delays
  // / Extra Work card with a ref so the YES → expand → scroll → brief
  // highlight pattern can fire without auto-creating any row.  The
  // CollapseCard's `attentionOpen` handles the force-open; this
  // useEffect just adds the iPad-friendly "guide me to the section"
  // affordance.  Highlight clears after 1.6s.  Signal-only.  Doctrine:
  // AUTO_EXPAND_GUIDANCE_CERTIFICATION.md
  const delaysCardWrapRef = React.useRef(null);
  const prevWeatherYesRef = React.useRef(false);
  const prevDelaysYesRef  = React.useRef(false);
  const [delaysGuideHighlight, setDelaysGuideHighlight] = useState(false);
  useEffect(() => {
    const weatherYesNow = data.weather_impact === "Yes";
    const delaysYesNow  = data.schedule_delays === "Yes";
    const weatherTransitioned = weatherYesNow && !prevWeatherYesRef.current;
    const delaysTransitioned  = delaysYesNow  && !prevDelaysYesRef.current;
    prevWeatherYesRef.current = weatherYesNow;
    prevDelaysYesRef.current  = delaysYesNow;
    if (!weatherTransitioned && !delaysTransitioned) return;
    // Scroll the card into view (smooth · centered) on the next tick
    // so the CollapseCard has actually rendered its open body.
    setTimeout(() => {
      try {
        delaysCardWrapRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      } catch { /* no-op for older browsers */ }
    }, 80);
    setDelaysGuideHighlight(true);
    const tmr = setTimeout(() => setDelaysGuideHighlight(false), 1600);
    return () => clearTimeout(tmr);
  }, [data.weather_impact, data.schedule_delays]);

  const validate = () => {
    if (!data.project_name.trim()) {
      toast.error("Project Name is required");
      return false;
    }
    if (!data.location.trim()) {
      toast.error("Location is required");
      return false;
    }
    if (!data.prepared_by.trim()) {
      toast.error("Prepared By is required");
      return false;
    }
    // Phase V.2 · Field-Logic Refinement (2026-05-29):
    // when the foreman flagged Delays / Extra Work Today = Yes, at
    // least one structured Delay / Extra Work row must accompany the
    // narrative.  This stays signal-only — no RFI, no schedule entry,
    // no notifications.  The attentionOpen prop on the Delays card
    // auto-expands it when submission is blocked.
    if (
      data.schedule_delays === "Yes" &&
      (data.constraints?.length || 0) === 0
    ) {
      toast.error(
        "Add at least one Delay / Extra Work row (Type + Notes) before submitting"
      );
      return false;
    }
    // Phase V.2 · Weather Impact Cleanup (2026-05-29):
    // Weather Impact Today = Yes now feeds the structured Delays /
    // Extra Work area instead of triggering a legacy weather narrative
    // box.  Require at least one Weather-typed delay row.  Stays
    // signal-only (advisory schedule flag may still derive
    // server-side; never creates an RFI / schedule / notification).
    // Doctrine: WEATHER_IMPACT_CLEANUP_CERTIFICATION.md
    if (
      data.weather_impact === "Yes" &&
      !(data.constraints || []).some(
        (r) => (r?.constraint_type || "").toLowerCase() === "weather"
      )
    ) {
      toast.error(
        "Add a Delay / Extra Work row with cause = Weather before submitting"
      );
      return false;
    }
    // Safety-escalation gate runs BEFORE photos/signature so a stop-the-line
    // event can never be hidden behind a missing-photos toast.
    const hasAccidentOrInjury =
      data.safety_incidents_today === "Yes" ||
      data.injuries_reported === "Yes";
    if (hasAccidentOrInjury) {
      if (data.safety_notified !== "Yes") {
        toast.error(
          "Safety must be notified before this Daily Report can be submitted"
        );
        return false;
      }
      if (!data.safety_contact_person.trim()) {
        toast.error("Who Was Contacted is required");
        return false;
      }
      if (!data.safety_contact_time.trim()) {
        toast.error("Time of Contact is required");
        return false;
      }
      if (data.incident_report_filled !== "Yes") {
        toast.error(
          "An Accident/Incident Report must be filed before this Daily Report can be submitted"
        );
        return false;
      }
      if (!data.incident_report_time.trim()) {
        toast.error("Time the Incident Report was filed is required");
        return false;
      }
    }
    if ((data.photos || []).length < (data.photo_min || 6)) {
      toast.error(
        `At least ${data.photo_min || 6} photos are required (you have ${
          (data.photos || []).length
        })`
      );
      return false;
    }
    // Phase 10A-B · OMEGA Correction 1 · Excavation activity gate.
    // Mirror the backend 422 enforcement here so the foreman sees a
    // calm in-form toast instead of a generic submit-failed error.
    if (
      String(data.excavation_activity_today || "No").toLowerCase() === "yes" &&
      (data.linked_excavation_ids || []).length === 0
    ) {
      toast.error(
        "Excavation Activity Today is YES — create or link at least one Excavation Record before submitting"
      );
      return false;
    }
    if (!data.prepared_by_signature) {
      toast.error("Signature is required");
      return false;
    }
    return true;
  };

  const submit = async () => {
    if (!validate()) {
      // Phase 6 · WS2 — open any incomplete signal-driven sections.
      setAttemptedSubmit(true);
      return;
    }
    setSaving(true);
    try {
      const lang = getLang();
      let payload = data;
      if (lang === "es") {
        toast.info("Translating to English…");
        payload = await translateUserInput(data, "es");
      }
      payload = { ...payload, submit_language: lang || "en" };
      if (!idempotencyKeyRef.current) {
        idempotencyKeyRef.current = mintIdempotencyKey();
        // iter440 — persist immediately so a reload mid-queue does
        // not regenerate the key and produce a duplicate submission.
        try { await persistIdempotencyKey("daily-report-new", idempotencyKeyRef.current); }
        catch { /* ignore */ }
      }
      const r = await enqueueUpload({
        method: "POST",
        url: "/daily-reports",
        headers: getFlToken() ? { "X-FL-Token": getFlToken() } : {},
        body: payload,
        idempotencyKey: idempotencyKeyRef.current,
        formKey: "daily-report-new",
      });
      if (!r.ok && r.queued) {
        toast.message("Saved · will upload when reconnected", {
          description: "Your daily report is queued and will send automatically.",
          duration: 6000,
        });
        // TRUST-1 · TF-011 — DO NOT commit() (discard the IDB draft)
        // until the offline queue confirms a 2xx. If the queue later
        // gives up (5 retries), telemetry fires and the draft stays
        // available for restore on the next mount. Doctrine: only
        // delete the draft on confirmed delivery.
        const idemKey = idempotencyKeyRef.current;
        try {
          onQueueItemSettled(idemKey, async (outcome) => {
            try {
              if (outcome && outcome.ok) {
                await commit();
                import("@/lib/resiliency").then(({ emitDraftEvent }) =>
                  emitDraftEvent("draft.write.ok", {
                    formKey: "daily-report-new",
                    trigger: "queue.commit.confirmed",
                  })).catch(() => {});
              } else {
                import("@/lib/resiliency").then(({ emitDraftEvent }) =>
                  emitDraftEvent("draft.write.fail", {
                    formKey: "daily-report-new",
                    trigger: "queue.commit.failed",
                    errorName: "QueueExhausted",
                    error: outcome?.lastError || "queue gave up",
                  })).catch(() => {});
              }
            } catch { /* never throw from settle callback */ }
          });
        } catch { /* ignore */ }
        // iter437 · also save setup memory on the queued path so the
        // operator gets continuity even when the network was offline.
        try { saveCrewSetup(payload); } catch { /* silent */ }
        idempotencyKeyRef.current = null;
        if (payload.project_number) rememberLastProject(String(payload.project_number));
        if (publicMode || !isAdmin()) {
          navigate("/thank-you", {
            state: {
              projectName: payload.project_name,
              formType: "Daily Report",
              returnTo: "/daily/submit",
              recordId: r.data?.report_number || r.data?.id || "",
            },
            replace: true,
          });
        } else {
          navigate(`/daily`);
        }
        return;
      }
      const res = { data: r.data };
      toast.success(t("Daily report filed · PM distribution sent · visible under Daily Reports"));
      await commit();
      // iter437 · Phase 31.1 · save setup snapshot for tomorrow on this
      // device. Strips banned fields defensively · 30d TTL · rolling.
      try { saveCrewSetup(payload); } catch { /* silent · doctrine */ }
      idempotencyKeyRef.current = null;
      // iter148 — remember this project for the next visit
      if (payload.project_number) rememberLastProject(String(payload.project_number));
      // iter147 — telemetry on the daily-report flow (heaviest PM form)
      import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
        trackFormSubmit("/daily-reports", true, "daily-report-new")).catch(() => {});
      if (publicMode || !isAdmin()) {
        navigate("/thank-you", {
          state: {
            projectName: payload.project_name,
            formType: "Daily Report",
            returnTo: "/daily/submit",
            recordId: r.data?.report_number || r.data?.id || "",
          },
          replace: true,
        });
      } else {
        navigate(`/daily/${res.data.id}`);
      }
    } catch (e) {
      console.error(e);
      toast.error(friendlyError(e, formatApiError(e, "Could not save daily report")), { duration: 7000 });
      import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
        trackFormSubmit("/daily-reports", false, "daily-report-new")).catch(() => {});
    } finally {
      setSaving(false);
    }
  };

  // RepeatBlock now lives at module scope (see below) so it isn't a fresh
  // component reference on every NewDailyReport re-render. Inline definitions
  // here would unmount/remount every Combo on every keystroke, killing focus
  // and dropdown state ("glitchy typing" / "no employees populating" bug).

  const photosCount = (data.photos || []).length;
  const photoMin = data.photo_min || 6;

  // Phase 6 · WS3 — operational completion derivation for Daily Report.
  // Quiet status — no nagging. Counts which optional CollapseCard sections
  // have entries today + surfaces any signal-driven gaps (e.g., user said
  // "schedule delays Yes" but left delay description blank).
  const drSectionEntries = {
    crew: (data.masci_crews || []).length,
    subs: (data.subcontractors || []).length,
    visitors: (data.visitors || []).length,
    equipment: (data.equipment || []).length,
    materials: (data.materials || []).length,
    activities: (data.activities || []).length,
  };
  const drFilledSectionCount = Object.values(drSectionEntries).filter((c) => c > 0).length;
  const drDelayGap = data.schedule_delays === "Yes"
    && !(data.delay_description || "").trim();
  const drSafetyGap = (data.safety_incidents_today === "Yes" || data.injuries_reported === "Yes")
    && data.safety_notified !== "Yes";
  const drAttentionItems = [];
  if (drDelayGap) drAttentionItems.push(t("Delay details"));
  if (drSafetyGap) drAttentionItems.push(t("Safety escalation"));
  const drCompletionTone = drAttentionItems.length > 0
    ? "rose"
    : drFilledSectionCount >= 2
      ? "emerald"
      : "slate";
  const drCompletionLabel = drAttentionItems.length > 0
    ? `${drAttentionItems.length} ${t("section(s) need attention")} · ${drAttentionItems.join(" · ")}`
    : drFilledSectionCount >= 2
      ? `${t("Operationally complete")} · ${drFilledSectionCount} ${t("sections filled today")}`
      : t("Optional sections available · add only what applies");

  // Soft payload-size warning · iter250. Mongo's 16 MB doc-size cap is the
  // real ceiling for inline daily-report photos. We estimate total photo
  // count across DR-level + all per-row photo arrays (materials, subs)
  // and surface an amber awareness banner above the Submit button when
  // the count crosses an operator-friendly threshold. NOT a hard block —
  // just an awareness signal so foremen can split into multiple DRs if
  // they're attaching truly extreme volumes of evidence.
  const totalAttachmentCount = (
    photosCount
    + (data.materials || []).reduce(
        (n, m) => n + ((m.ticket_photos || []).length), 0
      )
    + (data.subcontractors || []).reduce(
        (n, s) => n + ((s.photos || []).length), 0
      )
  );
  // ~300 KB per compressed JPEG data URL is a fair average; this is a
  // soft estimate not a hard guarantee.
  const estimatedPayloadMB = (totalAttachmentCount * 0.3).toFixed(1);
  const payloadIsHeavy = totalAttachmentCount >= 30;

  return (
    <div className="min-h-screen bg-slate-50 pb-32">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          {publicMode ? (
            <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          ) : (
            <Link
              to="/"
              className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
              data-testid="back-link"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
            </Link>
          )}
          <MasciLogo
            variant="mark"
            size="md"
            className={publicMode ? "sm:hidden" : ""}
          homeLink="/" />
          <div className="flex items-center gap-2">
            <DraftStatusPill
              status={draftStatus}
              lastSavedAt={lastSavedAt}
              lastError={lastError}
              testId="daily-report-draft-pill"
            />
            <QuotaWarningChip
              pressure={quotaPressure}
              testId="daily-report-quota-chip"
            />
            <SupportIdAffordance testId="daily-report-support-id" />
            <LangToggle />
            <Button
              onClick={submit}
              disabled={saving}
              className="h-11 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="submit-top-btn"
            >
              {saving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-1" />
              )}
              {t("Submit")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6">
        <div className="mb-2">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
            {t("New Report")}
          </span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
            {t("Daily Job Report")}
          </h1>
          {/* iter333 · operational sub-header · iter327 voice */}
          <p className="text-sm text-slate-600 mt-1.5 max-w-2xl leading-snug">
            {t("One report per crew, per day. Capture labor, subs, materials, weather, and photos so payroll and PM coordination run clean tomorrow.")}
          </p>
        </div>

        {/* Phase 10D · Live Submit Status (decision-support, sticky at top) */}
        <DailyReportStatusCard result={dailyReportCompliance} />

        {/* Phase 10D · One-tap "Use yesterday's …" suggestions */}
        <PreviousReportSuggestions
          projectNumber={data.project_number}
          onApply={applyPrevSuggestion}
        />

        {/* iter437 · Phase 31.1 · device-local crew setup restore.
            Shown BEFORE the draft prompt because crew/equipment is the
            highest-friction repetitive entry · prompt always visible
            · NEVER silent auto-fill. */}
        <CrewSetupRestorePrompt
          snapshot={crewSetup}
          confidence={crewMemoryConfidence}
          onUseSetup={onUseCrewSetup}
          onChangeProject={onChangeProjectFromSetup}
          onStartBlank={onStartBlankCrewSetup}
          onClear={onClearCrewSetup}
          onRename={onRenameCrewSetup}
          testId="daily-report-crew-setup-prompt"
        />

        {/* iter438 · Phase 31.1 · calm read-only load-trace line ·
            renders ONLY after Use Setup. Doctrine: never surveillance ·
            just a quiet acknowledgement that the setup came from
            saved memory · operator language only. */}
        {recentlyLoadedSetup && (
          <p
            data-testid="daily-report-setup-load-trace"
            className="text-xs text-slate-500 italic -mt-1 mb-3 ml-1"
          >
            {recentlyLoadedSetup.nickname
              ? t("Loaded from {nickname} · edit anything as needed.").replace(
                  "{nickname}", recentlyLoadedSetup.nickname,
                )
              : t("Loaded from your saved setup · edit anything as needed.")}
          </p>
        )}

        {/* iter434 · Phase 31 · Part 2 — calm draft recovery prompt.
            iter440 — now shows savedAt timestamp + cross-token note. */}
        <DraftRestorePrompt
          pendingDraft={pendingDraft}
          savedAt={pendingSavedAt}
          isCrossToken={pendingIsCrossToken}
          onRestore={onRestoreDraft}
          onDiscard={onDiscardDraft}
          testId="daily-report-draft-restore-prompt"
        />

        {/* TRUST-1 · TF-016 — calm recovery for soft-deleted drafts.
            Shown only when there is no live draft on offer AND an
            archive entry exists within the 24h window. */}
        <DraftRecoveryNotice
          archive={pendingDraft ? null : archivedDraft}
          onRecover={onRecoverArchive}
          onDismiss={() => setArchivedDraft(null)}
          testId="daily-report-draft-recovery"
        />

        {/* TRUST-1 · TF-001 — calm prior-usage banner. Surfaces ONLY
            when no live draft and no archive exists AND this device has
            saved this form > 24h ago. Reassuring, not alarming. */}
        <PriorUsageBanner
          formKey="daily-report-new"
          priorUsage={pendingDraft || archivedDraft ? null : priorUsage}
          onDismiss={() => setPriorUsage(null)}
          testId="daily-report-prior-usage"
        />

        {/* 01 — Report info */}
        <HelpTipBlock formKey="daily-report" className="mb-3" showCounter />
        <Section number="01" title={t("Report Information")}>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("MASCI Job")}
            </Label>
            <div className="mt-2">
              <JobPicker
                projectName={data.project_name}
                projectNumber={data.project_number}
                onSelect={applyJob}
              />
            </div>
            <p className="text-xs text-slate-500 mt-1.5">
              {t("Pick a current job to auto-fill name + number — or choose Custom Job to type your own.")}
            </p>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Project Name *")}
              </Label>
              <Input
                value={data.project_name}
                onChange={(e) => set("project_name", e.target.value)}
                className={inputClsTall}
                data-testid="input-project-name"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Project Number")}
              </Label>
              <Input
                value={data.project_number}
                onChange={(e) => set("project_number", e.target.value)}
                className={inputClsTall}
                data-testid="input-project-number"
              />
            </div>
            <div className="lg:col-span-2">
              <div className="flex items-center justify-between gap-2 mb-1">
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  {t("Location *")}
                </Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={useGps}
                  disabled={locating}
                  className="h-9 px-3 border-2 border-slate-300 hover:border-red-500 hover:text-red-700 font-bold uppercase tracking-wide text-xs"
                  data-testid="use-gps-btn"
                >
                  {locating ? (
                    <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                  ) : (
                    <MapPin className="w-3.5 h-3.5 mr-1" />
                  )}
                  {t("Use GPS")}
                </Button>
              </div>
              <Input
                value={data.location}
                onChange={(e) => set("location", e.target.value)}
                className={inputClsTall}
                data-testid="input-location"
              />
              {data.gps_lat != null && (
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1.5 flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-red-700" />
                  GPS · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}
                </div>
              )}
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Date *")}
              </Label>
              <Input
                type="date"
                value={data.report_date}
                onChange={(e) => set("report_date", e.target.value)}
                className={inputClsTall}
                data-testid="input-report-date"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Report #")} <span className="text-slate-400">({t("auto")})</span>
              </Label>
              <Input
                value={data.report_number}
                onChange={(e) => set("report_number", e.target.value)}
                className={`${inputClsTall} bg-slate-50 font-mono`}
                placeholder="DR-YYYYMMDD-001"
                data-testid="input-report-number"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Prepared By *")}
              </Label>
              <FlUserCombo
                value={data.prepared_by}
                onChange={(v) => set("prepared_by", v)}
                placeholder={t("Foreman / Leadman / Superintendent")}
                testId="prepared-by"
                allowedRoles={[
                  "leadman",
                  "foreman",
                  "superintendent",
                  "sr_superintendent",
                ]}
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Superintendent")}
              </Label>
              <FlUserCombo
                value={data.superintendent}
                onChange={(v) => set("superintendent", v)}
                placeholder={t("Superintendent / Sr. Superintendent")}
                testId="superintendent"
                allowedRoles={[
                  "superintendent",
                  "sr_superintendent",
                ]}
              />
            </div>
          </div>
        </Section>

        {/* 02 — Weather (auto from GPS) */}
        <Section
          number="02"
          title={t("Weather")}
          aside={
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={refreshWeather}
              disabled={fetchingWeather || data.gps_lat == null}
              className="h-9 px-3 border-2 border-slate-300 hover:border-red-500 hover:text-red-700 font-bold uppercase tracking-wide text-xs"
              data-testid="refresh-weather-btn"
            >
              {fetchingWeather ? (
                <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
              ) : (
                <CloudSun className="w-3.5 h-3.5 mr-1" />
              )}
              {t("Refresh Weather")}
            </Button>
          }
        >
          <p className="text-xs text-slate-500">
            {t("Capture GPS to auto-load today's weather. Refresh anytime.")}
          </p>
          {data.weather_snapshots.length === 0 ? (
            <div className="text-sm text-slate-500 italic py-2">
              {t("No weather data yet — tap Use GPS above.")}
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4">
              {data.weather_snapshots.map((s, i) => (
                <div
                  key={i}
                  className="border border-slate-200 rounded-md p-3"
                  data-testid={`weather-snap-${i}`}
                >
                  <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-red-700 font-bold">
                    {s.time}
                  </div>
                  <div className="font-display font-bold text-2xl text-slate-900 mt-1">
                    {s.temp_f != null ? `${s.temp_f}°F` : "—"}
                  </div>
                  <div className="text-sm text-slate-700 mt-0.5">
                    {s.condition || "—"}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    {s.precip_in ?? 0}″ · {s.humidity_pct ?? "—"}% ·{" "}
                    {s.wind_mph ?? "—"} mph
                  </div>
                </div>
              ))}
            </div>
          )}
          {data.weather_summary && (
            <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-600 mt-2">
              {data.weather_summary}
            </div>
          )}
        </Section>

        {/* 03 — General Info / Flags */}
        <Section number="03" title={t("General Information")}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Delays / Extra Work Today?")}
              </Label>
              <YesNo
                value={data.schedule_delays}
                onChange={(v) => set("schedule_delays", v)}
                testId="schedule-delays"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Weather Impact?")}
              </Label>
              <YesNo
                value={data.weather_impact}
                onChange={(v) => set("weather_impact", v)}
                testId="weather-impact"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Any Accidents on Site?")}
              </Label>
              <YesNo
                value={data.safety_incidents_today}
                onChange={(v) => set("safety_incidents_today", v)}
                testId="safety-incidents"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Any Injuries Reported?")}
              </Label>
              <YesNo
                value={data.injuries_reported}
                onChange={(v) => set("injuries_reported", v)}
                testId="injuries-reported"
              />
            </div>
          </div>
          {/* Phase V.2 · Section 03 Cleanup (2026-05-29) + Weather
              Impact Cleanup (2026-05-29).  Delays YES feeds the
              structured Delays / Extra Work card.  Weather YES also
              feeds the structured card (requires a row with
              cause = Weather).  Only Accidents / Injuries still
              surface this free-text narrative box so the foreman is
              never asked to describe the same delay twice.
              Doctrine: WEATHER_IMPACT_CLEANUP_CERTIFICATION.md  */}
          {(data.safety_incidents_today === "Yes" ||
            data.injuries_reported === "Yes") && (
            <div className="bg-amber-50 border-2 border-amber-300 rounded-md p-3">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-amber-800 font-bold">
                <AlertTriangle className="w-3.5 h-3.5 inline mr-1 -mt-0.5" />
                {t("Detail any 'Yes' answers")}
              </Label>
              <Textarea
                value={data.incident_notes}
                onChange={(e) => set("incident_notes", e.target.value)}
                className="min-h-[80px] text-base border-2 border-amber-300 mt-1"
                placeholder={t("Describe accidents or injuries…")}
                data-testid="input-incident-notes"
              />
            </div>
          )}
          {/* Safety-escalation gate — fires whenever accident or injury is Yes */}
          {(data.safety_incidents_today === "Yes" ||
            data.injuries_reported === "Yes") && (
            <div
              className="bg-red-50 border-2 border-red-600 rounded-md p-4 space-y-4"
              data-testid="safety-escalation-block"
            >
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-red-700 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
                    {t("Safety Escalation Required")}
                  </div>
                  <div className="text-sm text-slate-800 mt-1">
                    {t(
                      "An accident or injury was reported today. Complete the safety escalation steps before submitting this report."
                    )}
                  </div>
                </div>
              </div>

              {/* Step 1: Was Safety Notified? */}
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-800 font-bold">
                  {t("Was Safety notified? *")}
                </Label>
                <YesNo
                  value={data.safety_notified}
                  onChange={(v) => set("safety_notified", v)}
                  testId="safety-notified"
                />
              </div>

              {/* Stop-the-line: Safety must be contacted */}
              {data.safety_notified === "No" && (
                <div
                  className="bg-red-700 text-white rounded-md p-4 border-b-4 border-red-900"
                  data-testid="safety-not-notified-warning"
                >
                  <div className="font-display font-black text-lg leading-tight">
                    {t("STOP — Contact Safety immediately.")}
                  </div>
                  <div className="text-sm mt-1 text-red-100">
                    {t(
                      "You cannot submit this Daily Report until Safety has been notified. Call your Safety Manager now, then return and mark Yes above."
                    )}
                  </div>
                </div>
              )}

              {/* Step 2: Who and when? */}
              {data.safety_notified === "Yes" && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
                  <div>
                    <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-800">
                      {t("Who Was Contacted? *")}
                    </Label>
                    <Input
                      value={data.safety_contact_person}
                      onChange={(e) =>
                        set("safety_contact_person", e.target.value)
                      }
                      placeholder={t("Name + role (e.g. Jaymn Judd, Safety Mgr)")}
                      className={inputCls}
                      data-testid="input-safety-contact-person"
                    />
                  </div>
                  <div>
                    <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-800">
                      {t("Time of Contact *")}
                    </Label>
                    <Input
                      type="time"
                      value={data.safety_contact_time}
                      onChange={(e) =>
                        set("safety_contact_time", e.target.value)
                      }
                      className={inputCls}
                      data-testid="input-safety-contact-time"
                    />
                  </div>
                </div>
              )}

              {/* Step 3: Was the Incident Report filed? */}
              {data.safety_notified === "Yes" && (
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-800 font-bold">
                    {t("Has the Accident/Incident Report been filled out? *")}
                  </Label>
                  <YesNo
                    value={data.incident_report_filled}
                    onChange={(v) => set("incident_report_filled", v)}
                    testId="incident-report-filled"
                  />
                </div>
              )}

              {/* Stop-the-line: Incident report must be filed */}
              {data.safety_notified === "Yes" &&
                data.incident_report_filled === "No" && (
                  <div
                    className="bg-red-700 text-white rounded-md p-4 border-b-4 border-red-900"
                    data-testid="incident-report-required-warning"
                  >
                    <div className="font-display font-black text-lg leading-tight">
                      {t("STOP — File the Incident Report first.")}
                    </div>
                    <div className="text-sm mt-1 text-red-100">
                      {t(
                        "An Accident/Incident Report MUST be filed before this Daily Report can be submitted."
                      )}
                    </div>
                    <Link
                      to="/incidents/new"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 mt-3 px-3 py-2 bg-white text-red-800 hover:bg-red-100 font-mono text-xs uppercase tracking-[0.2em] font-bold rounded"
                      data-testid="open-incident-form-link"
                    >
                      {t("Open Incident Report Form")}
                    </Link>
                  </div>
                )}

              {/* Step 4: Time the Incident Report was filed */}
              {data.safety_notified === "Yes" &&
                data.incident_report_filled === "Yes" && (
                  <div>
                    <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-800">
                      {t("Time Incident Report Was Filed *")}
                    </Label>
                    <Input
                      type="time"
                      value={data.incident_report_time}
                      onChange={(e) =>
                        set("incident_report_time", e.target.value)
                      }
                      className={inputCls}
                      data-testid="input-incident-report-time"
                    />
                  </div>
                )}
            </div>
          )}
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("General Notes")}
            </Label>
            <Textarea
              value={data.general_notes}
              onChange={(e) => set("general_notes", e.target.value)}
              className="min-h-[100px] text-base border-2 border-slate-300"
              placeholder={t("Anything else worth noting from today...")}
              data-testid="input-general-notes"
            />
          </div>
          {/* Phase 10A-B · OMEGA Correction 1 — Excavation Activity Gate */}
          <div className="mt-3">
            <DailyReportExcavationActivity
              value={data.excavation_activity_today}
              onChange={(v) => set("excavation_activity_today", v)}
              linkedIds={data.linked_excavation_ids || []}
              onLinkedChange={(arr) => set("linked_excavation_ids", arr)}
              projectNumber={data.project_number}
              projectName={data.project_name}
              reportDate={data.report_date}
              preparedBy={data.prepared_by}
              attemptedSubmit={attemptedSubmit}
              testId="dr-excavation-activity"
            />
            {/* Phase 10D · Live compliance summary for every linked excavation */}
            {(data.linked_excavation_ids || []).length > 0 && (
              <div className="mt-2 space-y-1.5" data-testid="dr-linked-excavation-compliance">
                {(data.linked_excavation_ids || []).map((id) => (
                  <LinkedExcavationCompliance key={id} excavationId={id} />
                ))}
              </div>
            )}
          </div>
        </Section>

        {/* 04 — MASCI Crews */}
        <Section number="04" title={t("MASCI Crews on Site")}>
          <HelpTipBlock formKey="daily-report.crew" className="mb-3" />
          {/* iter360 · operational coaching for the crew-linkage discipline */}
          <LifecycleGuide
            id="daily-report-crew-linkage"
            icon={Users}
            accent="indigo"
            title={t("Crew identity linkage")}
            summary={t("Pick each crew member from the roster suggestions when possible — linked names propagate accountability automatically.")}
            sections={[
              {
                label: t("Roles"),
                body: t("PMs and field leadership own daily-report submission. The crew names captured here feed every downstream surface that tracks who-was-where: HR accountability timelines, PM crew compliance, payroll reconciliation, and OSHA recordkeeping if an incident is later linked to today's date."),
              },
              {
                label: t("Why linkage matters"),
                body: t("Names typed without picking from the roster become EMP_LINK_UNRESOLVABLE findings in Governance Health. Names picked from the roster carry the canonical employee_id, which makes accountability propagate to the right person automatically across every portal."),
              },
              {
                label: t("Subcontractors"),
                body: t("Free-text is allowed and intentionally never blocked — subcontractors aren't in the employee master. The amber indicator below the name just tells you the linkage state so the daily report still ships fast."),
              },
              {
                label: t("Downstream visibility"),
                body: t("Linked crew rows appear inside that employee's Accountability Timeline, on the PM Crew Compliance lens for the project, and (if relevant) inside any incident investigation that references today's date."),
              },
            ]}
          />
          <div className="space-y-3 mt-3">
            {data.masci_crews.map((row, i) => {
              const auto = computeHours(row.start_time, row.stop_time, row.lunch_minutes);
              if (auto && auto !== row.hours) {
                // Keep `hours` in sync with the calculated value silently
                setTimeout(() => crews.update(i, "hours", auto), 0);
              }
              return (
                <div
                  key={i}
                  className="border border-slate-200 rounded-md p-3 sm:p-4 space-y-2"
                  data-testid={`crew-row-${i}`}
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                      {t("Crew Member")} {i + 1}
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => crews.remove(i)}
                      className="text-slate-500 hover:text-red-600"
                      data-testid={`crew-remove-${i}`}
                    >
                      <X className="w-4 h-4 mr-1" /> {t("Remove")}
                    </Button>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
                    <div className="lg:col-span-2">
                      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                        {t("Employee Name")}
                      </Label>
                      <EmployeeCombo
                        value={row.name || ""}
                        onChange={(v) => {
                          // iter360 · linkage continuity — if the user types over
                          // the name after a pick, clear the linked id so we
                          // don't carry a stale linkage.
                          crews.update(i, "name", v);
                          if (row.employee_id && v !== row.name) {
                            crews.update(i, "employee_id", "");
                          }
                        }}
                        onPick={(emp) => {
                          // iter360 · capture canonical employee_id on the
                          // crew row so this surface stops contributing to
                          // EMP_LINK_UNRESOLVABLE findings.
                          if (emp.id || emp.employee_id) {
                            crews.update(i, "employee_id", emp.id || emp.employee_id);
                          }
                          if (emp.trade && !row.trade) crews.update(i, "trade", emp.trade);
                        }}
                        testId={`crew-name-${i}`}
                      />
                      {/* Linkage status indicator — operational coaching at entry time */}
                      {(row.name || "").trim() ? (
                        row.employee_id ? (
                          <div className="mt-1 text-[10px] text-emerald-700 font-mono inline-flex items-center gap-1" data-testid={`crew-linked-${i}`}>
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                            {t("Linked to roster")}
                          </div>
                        ) : (
                          <div className="mt-1 text-[10px] text-amber-700 font-mono inline-flex items-center gap-1" data-testid={`crew-unlinked-${i}`}>
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
                            {t("Not in roster — will create governance finding")}
                          </div>
                        )
                      ) : null}
                    </div>
                    <div>
                      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                        {t("Trade / Role")}
                      </Label>
                      <Input
                        value={row.trade || ""}
                        onChange={(e) => crews.update(i, "trade", e.target.value)}
                        className={inputCls}
                        placeholder="Earthwork, Concrete, MOT..."
                        data-testid={`crew-trade-${i}`}
                      />
                    </div>
                    <div>
                      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                        {t("Hours")} <span className="text-slate-400">({t("auto")})</span>
                      </Label>
                      <Input
                        value={row.hours || ""}
                        readOnly
                        className={`${inputCls} bg-slate-100 font-mono font-bold`}
                        placeholder="0.00"
                        data-testid={`crew-hours-${i}`}
                      />
                      {/* iter100 — typo catcher: flag any single-day entry > 16 hrs */}
                      <div className="mt-1">
                        <DailyHoursFlag hours={row.hours} testId={`crew-hours-flag-${i}`} />
                      </div>
                    </div>
                    <div>
                      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                        {t("Start Time")}
                      </Label>
                      <Input
                        type="time"
                        value={row.start_time || ""}
                        onChange={(e) => crews.update(i, "start_time", e.target.value)}
                        className={inputCls}
                        data-testid={`crew-start-${i}`}
                      />
                    </div>
                    <div>
                      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                        {t("Lunch")} (min)
                      </Label>
                      <Input
                        type="number"
                        min="0"
                        value={row.lunch_minutes ?? ""}
                        onChange={(e) => crews.update(i, "lunch_minutes", e.target.value)}
                        className={inputCls}
                        placeholder="30"
                        data-testid={`crew-lunch-${i}`}
                      />
                    </div>
                    <div>
                      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                        {t("Stop Time")}
                      </Label>
                      <Input
                        type="time"
                        value={row.stop_time || ""}
                        onChange={(e) => crews.update(i, "stop_time", e.target.value)}
                        className={inputCls}
                        data-testid={`crew-stop-${i}`}
                      />
                    </div>
                    <div className="lg:col-span-2">
                      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                        {t("Work Performed")}
                      </Label>
                      <Textarea
                        value={row.work_performed || ""}
                        onChange={(e) => crews.update(i, "work_performed", e.target.value)}
                        className="min-h-[60px] text-base border-2 border-slate-300"
                        data-testid={`crew-work-${i}`}
                      />
                    </div>
                    {(() => {
                      // Live gross/net hours preview — shown only when both
                      // start + stop are set so empty rows stay clean.
                      const p = grossNetPreview(row.start_time, row.stop_time, row.lunch_minutes);
                      if (!p) return null;
                      return (
                        <div
                          className="lg:col-span-2 mt-1 px-3 py-2 rounded bg-slate-100 border-l-2 border-slate-700 font-mono text-[12px] text-slate-700 leading-snug"
                          data-testid={`crew-hours-preview-${i}`}
                        >
                          <span className="font-bold text-slate-900">{p.label}</span>
                          <span className="mx-2 text-slate-400">·</span>
                          <span>{p.math}</span>
                        </div>
                      );
                    })()}
                  </div>
                </div>
              );
            })}
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                crews.add({
                  name: "",
                  trade: "",
                  start_time: "",
                  lunch_minutes: 30,
                  stop_time: "",
                  hours: "",
                  work_performed: "",
                })
              }
              className="w-full h-12 border-2 border-dashed border-slate-400 hover:border-red-700 hover:text-red-700 font-bold uppercase tracking-wide text-sm"
              data-testid="crew-add"
            >
              <Plus className="w-4 h-4 mr-2" /> {t("Add Crew Member")}
            </Button>

            {data.masci_crews.length > 0 && (
              <div
                className="bg-slate-900 text-white rounded-md px-4 py-3 flex items-center justify-between"
                data-testid="crew-totals-bar"
              >
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-400">
                  {t("Total crew hours today")}
                </span>
                <span className="font-display text-2xl font-black">
                  {data.masci_crews
                    .reduce((sum, r) => sum + (parseFloat(r.hours) || 0), 0)
                    .toFixed(2)}{" "}
                  <span className="text-amber-400 text-sm font-mono">hrs</span>
                </span>
              </div>
            )}
          </div>
        </Section>

        {/* iter383 · Phase 5C.1 — Smart Operational Disclosure.
            Each optional section remains VISIBLE as a CollapseCard with
            a status badge ("3 entered" / "Optional" / "No entries").
            Only the expanded body collapses — section name + operational
            state are always communicated. ZERO field deletion: each card
            wraps the original Section block exactly as-is so all rich
            field configs (supplier-combo, employee-combo, ticket_photos,
            attachment_note) remain intact. */}
        <div className="space-y-2" data-testid="dr-collapse-cards">

          <CollapseCard
            title={t("Subcontractors on Site")}
            testId="dr-subcontractors"
            statusLabel={
              (data.subcontractors?.length || 0) > 0
                ? `${data.subcontractors.length} ${t("entered")}`
                : t("No subs today")
            }
            statusTone={(data.subcontractors?.length || 0) > 0 ? "emerald" : "slate"}
          >
            <RepeatBlock
              title={t("Subcontractor")}
              list="subcontractors"
              rows={data.subcontractors}
              helpers={subs}
              t={t}
              defaults={{
                company: "",
                trade: "",
                foreman: "",
                count: "",
                hours: "",
                work_performed: "",
                attachment_note: "",
                photos: [],
              }}
              fields={[
                { key: "company", label: "Company", full: true, type: "supplier-combo" },
                { key: "trade", label: "Trade" },
                { key: "foreman", label: "Subcontractor Foreman / Lead",
                  placeholder: "e.g. John Doe (sub crew lead)" },
                { key: "count", label: "# of Workers", type: "number" },
                { key: "hours", label: "Hours Worked", type: "number" },
                {
                  key: "work_performed",
                  label: "Work Performed",
                  full: true,
                  type: "textarea",
                },
                {
                  key: "attachment_note",
                  label: "Attachment Note (optional)",
                  full: true,
                  placeholder: "e.g. Flagger tickets — AM shift · Signed labor slips · QC issue",
                },
                { key: "photos", label: "Photos / Tickets", full: true, type: "photo" },
              ]}
              testIdBase="sub"
            />
          </CollapseCard>

          <CollapseCard
            title={t("Site Visitors")}
            testId="dr-visitors"
            statusLabel={
              (data.visitors?.length || 0) > 0
                ? `${data.visitors.length} ${t("entered")}`
                : t("No visitors today")
            }
            statusTone={(data.visitors?.length || 0) > 0 ? "emerald" : "slate"}
          >
            <RepeatBlock
              title={t("Visitor")}
              list="visitors"
              rows={data.visitors}
              helpers={vis}
              t={t}
              defaults={{
                name: "",
                company: "",
                time_in: "",
                time_out: "",
                purpose: "",
              }}
              fields={[
                { key: "name", label: "Name" },
                { key: "company", label: "Company / Agency" },
                { key: "time_in", label: "Time In", type: "time" },
                { key: "time_out", label: "Time Out", type: "time" },
                { key: "purpose", label: "Purpose / Notes", full: true },
              ]}
              testIdBase="visitor"
            />
          </CollapseCard>

          <CollapseCard
            title={t("Equipment Log")}
            testId="dr-equipment"
            statusLabel={
              (data.equipment?.length || 0) > 0
                ? `${data.equipment.length} ${t("entered")}`
                : t("Optional")
            }
            statusTone={(data.equipment?.length || 0) > 0 ? "emerald" : "slate"}
          >
            <HelpTipBlock formKey="daily-report.equipment" className="mb-3" />
            <RepeatBlock
              title={t("Equipment")}
              list="equipment"
              rows={data.equipment}
              helpers={eq}
              t={t}
              defaults={{
                description: "",
                hours_used: "",
                time_delivered: "",
                time_removed: "",
                notes: "",
              }}
              fields={[
                { key: "description", label: "Unit / Equipment", full: true, type: "equipment-combo" },
                { key: "hours_used", label: "Hours Used", type: "number" },
                { key: "time_delivered", label: "Time Delivered", type: "time" },
                { key: "time_removed", label: "Time Removed", type: "time" },
                { key: "notes", label: "Notes", full: true, type: "textarea" },
              ]}
              testIdBase="equipment"
            />
          </CollapseCard>

          <CollapseCard
            title={t("Material Deliveries")}
            testId="dr-materials"
            statusLabel={
              (data.materials?.length || 0) > 0
                ? `${data.materials.length} ${t("entered")}`
                : t("No deliveries today")
            }
            statusTone={(data.materials?.length || 0) > 0 ? "emerald" : "slate"}
          >
            <HelpTipBlock formKey="daily-report.materials" className="mb-3" />
            <RepeatBlock
              title={t("Material")}
              list="materials"
              rows={data.materials}
              helpers={mat}
              t={t}
              defaults={{
                description: "",
                quantity: "",
                unit: "",
                supplier: "",
                ticket_number: "",
                notes: "",
                ticket_photos: [],
              }}
              fields={[
                { key: "description", label: "Description", full: true },
                { key: "quantity", label: "Quantity" },
                { key: "unit", label: "Unit", placeholder: "ton, cy, ea, lf" },
                { key: "supplier", label: "Supplier", full: true, type: "supplier-combo" },
                { key: "ticket_number", label: "Ticket #" },
                { key: "notes", label: "Notes", full: true, type: "textarea" },
                { key: "ticket_photos", label: "Ticket Photo(s)", full: true, type: "photo" },
              ]}
              testIdBase="material"
            />
          </CollapseCard>

          <CollapseCard
            title={t("Activity / Production Log")}
            testId="dr-activities"
            statusLabel={
              (data.activities?.length || 0) > 0
                ? `${data.activities.length} ${t("entered")}`
                : t("Optional")
            }
            statusTone={(data.activities?.length || 0) > 0 ? "emerald" : "slate"}
          >
            <HelpTipBlock formKey="daily-report.narrative" className="mb-3" />
            <RepeatBlock
              title={t("Activity")}
              list="activities"
              rows={data.activities}
              helpers={act}
              t={t}
              defaults={{
                activity: "",
                percent_complete: "",
                station_from: "",
                station_to: "",
                notes: "",
              }}
              fields={[
                { key: "activity", label: "Activity", full: true },
                { key: "percent_complete", label: "% Complete", type: "number" },
                { key: "station_from", label: "Station / Loc From" },
                { key: "station_to", label: "Station / Loc To" },
                { key: "notes", label: "Notes", full: true, type: "textarea" },
              ]}
              testIdBase="activity"
            />
          </CollapseCard>

          {/* Phase V.2 · Wave-1B · Structured Production rows.
              ADDITIVE · operator-approved · 7-unit closed enum.
              Doctrine: PRODUCTION_UI_CERTIFICATION.md */}
          <CollapseCard
            title={t("Production Quantities")}
            testId="dr-production"
            statusLabel={
              (data.production?.length || 0) > 0
                ? `${data.production.length} ${t("rows")}`
                : t("Optional")
            }
            statusTone={(data.production?.length || 0) > 0 ? "emerald" : "slate"}
          >
            <RepeatBlock
              title={t("Production")}
              list="production"
              rows={data.production || []}
              helpers={prod}
              t={t}
              defaults={{
                description: "",
                quantity: "",
                unit: "OTHER",
                custom_unit_label: "",
                station_from: "",
                station_to: "",
                notes: "",
              }}
              fields={[
                { key: "description", label: "Description", full: true,
                  placeholder: "e.g. RCP install, Type S-III mat, MH set" },
                { key: "quantity", label: "Quantity", type: "number" },
                { key: "unit", label: "Unit", type: "select",
                  options: ["LF", "SY", "CY", "TON", "EA", "ACRE", "OTHER"] },
                { key: "custom_unit_label", label: "Custom Unit (when OTHER)",
                  placeholder: "permit, days, lot…" },
                { key: "station_from", label: "Station / Loc From",
                  placeholder: "12+50" },
                { key: "station_to", label: "Station / Loc To",
                  placeholder: "13+00" },
                { key: "notes", label: "Notes", full: true, type: "textarea" },
              ]}
              testIdBase="production"
            />
          </CollapseCard>

          {/* Phase V.2 · Wave-1B · Structured Constraint rows (chip-style).
              ADDITIVE · operator-approved · 11-type closed enum.
              Advisory flags derived server-side · UI displays them calmly.
              Field-language refinement (post-Wave-1B/1C validation
              directive 2026-05-29): user-facing labels speak
              construction ("delays / extra work") while backend
              models / enums / APIs keep "constraint" terminology.
              Doctrine: CONSTRAINT_UI_CERTIFICATION.md */}
          {(() => {
            // Phase V.2 · Weather Impact Cleanup — merged-gate logic.
            // The Delays / Extra Work card surfaces attention when
            // EITHER directive 03 question is YES and the matching
            // constraint row is missing.  Wrap in IIFE so the
            // derived flags stay co-located with the JSX they steer.
            const rows = data.constraints || [];
            const hasWeatherRow = rows.some(
              (r) => (r?.constraint_type || "").toLowerCase() === "weather"
            );
            const delaysGateUnmet =
              data.schedule_delays === "Yes" && rows.length === 0;
            const weatherGateUnmet =
              data.weather_impact === "Yes" && !hasWeatherRow;
            const gateUnmet = delaysGateUnmet || weatherGateUnmet;
            let statusLabel;
            let statusTone;
            if (rows.length > 0 && !gateUnmet) {
              statusLabel = `${rows.length} ${t("logged")}`;
              statusTone = "emerald";
            } else if (weatherGateUnmet && !delaysGateUnmet) {
              statusLabel = t("Add a row with cause = Weather (required)");
              statusTone = "amber";
            } else if (gateUnmet) {
              statusLabel = t("Add at least one delay (required)");
              statusTone = "amber";
            } else {
              statusLabel = t("No delays today");
              statusTone = "slate";
            }
            return (
              <div
                ref={delaysCardWrapRef}
                className={`rounded-md transition-shadow duration-700 ${
                  delaysGuideHighlight
                    ? "ring-2 ring-amber-400 shadow-[0_0_0_4px_rgba(251,191,36,0.15)]"
                    : ""
                }`}
              >
              <CollapseCard
                title={t("Delays / Extra Work")}
                testId="dr-constraints"
                attentionOpen={
                  // Phase V.2 · Auto-Expand Guidance: open whenever
                  // EITHER trigger is YES, OR submit was blocked on a
                  // gate.  CollapseCard.attentionOpen is "one-way" —
                  // user can still collapse the card after expansion
                  // without re-triggering anything.
                  data.weather_impact === "Yes" ||
                  data.schedule_delays === "Yes" ||
                  (attemptedSubmit && gateUnmet)
                }
                statusLabel={statusLabel}
                statusTone={statusTone}
              >
            <div
              className="mb-3 text-xs text-slate-500 leading-snug"
              data-testid="constraints-helper"
            >
              {t("Tap a delay cause to document impacts to today's work. Signal only — never creates an RFI or schedule entry.")}
            </div>
            {/* Chip grid · single-tap to insert a new constraint row */}
            <div className="mb-4 flex flex-wrap gap-2" data-testid="constraint-chips">
              {[
                { key: "weather", label: "Weather" },
                { key: "utility", label: "Utility" },
                { key: "survey", label: "Survey" },
                { key: "material", label: "Material" },
                { key: "equipment", label: "Equipment" },
                { key: "trucking", label: "Trucking" },
                { key: "mot", label: "MOT" },
                { key: "cei_inspection", label: "CEI / Inspection" },
                { key: "owner_engineer", label: "Owner / Engineer" },
                { key: "safety", label: "Safety" },
                { key: "other", label: "Other" },
              ].map((c) => (
                <button
                  key={c.key}
                  type="button"
                  data-testid={`constraint-chip-${c.key}`}
                  onClick={() =>
                    cons.add({
                      constraint_type: c.key,
                      hours_impact: "",
                      notes: "",
                    })
                  }
                  className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 hover:border-slate-400 transition-colors"
                >
                  + {t(c.label)}
                </button>
              ))}
            </div>
            <RepeatBlock
              title={t("Delay")}
              list="constraints"
              rows={data.constraints || []}
              helpers={cons}
              t={t}
              defaults={{
                constraint_type: "other",
                hours_impact: "",
                notes: "",
              }}
              fields={[
                { key: "constraint_type", label: "Type", type: "select",
                  options: ["weather", "utility", "survey", "material",
                            "equipment", "trucking", "mot",
                            "cei_inspection", "owner_engineer",
                            "safety", "other"],
                  optionLabels: {
                    weather: "Weather",
                    utility: "Utility",
                    survey: "Survey",
                    material: "Material",
                    equipment: "Equipment",
                    trucking: "Trucking",
                    mot: "MOT",
                    cei_inspection: "CEI / Inspection",
                    owner_engineer: "Owner / Engineer",
                    safety: "Safety",
                    other: "Other",
                  } },
                { key: "hours_impact", label: "Lost Hours", type: "number",
                  placeholder: "0.0" },
                { key: "notes", label: "Notes", full: true, type: "textarea",
                  placeholder: "What happened and where" },
              ]}
              testIdBase="constraint"
            />
          </CollapseCard>
              </div>
          );
          })()}

        </div>
        {/* iter383 · End of Smart Operational Disclosure cards. */}

        {/* 10 — Photos (min 6) */}
        <Section
          number="10"
          title={`${t("Photos")} (${photosCount}/${photoMin}${
            photosCount > photoMin ? "+" : ""
          })`}
        >
          <HelpTipBlock formKey="daily-report.photos" className="mb-3" />
          <div
            className={`px-3 py-2 rounded-md border-2 ${
              photosCount >= photoMin
                ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                : "border-amber-300 bg-amber-50 text-amber-900"
            } font-mono text-xs uppercase tracking-[0.15em] font-bold`}
            data-testid="photos-status"
          >
            {photosCount >= photoMin
              ? t("Photo minimum met. Add more if helpful.")
              : `${t("Add at least")} ${photoMin - photosCount} ${t("more photo(s)")}`}
          </div>
          <PhotoUpload
            photos={data.photos}
            onChange={(photos) => set("photos", photos)}
          />
        </Section>

        {/* 11 — Sign-off */}
        <Section number="11" title={t("Sign-Off")}>
          <div>
            <DistributionList
              value={data.distribution_list}
              onChange={(v) => set("distribution_list", v)}
              testIdPrefix="daily-dist"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Prepared By Signature")} *
            </Label>
            <SignaturePad
              value={data.prepared_by_signature}
              onChange={(v) => set("prepared_by_signature", v)}
              label={t("Prepared By")}
              testId="prepared-by-sig"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Superintendent Signature")}
            </Label>
            <SignaturePad
              value={data.superintendent_signature}
              onChange={(v) => set("superintendent_signature", v)}
              label={t("Superintendent")}
              testId="superintendent-sig"
            />
          </div>
        </Section>

        <div className="pt-4">
          {/* Phase 6 · WS3 — operational completion indicator. Quiet voice.
              Only goes rose when there's a signal-driven gap (delays said
              Yes but no detail; safety incident said Yes but not notified). */}
          <div
            className={`mb-3 rounded-md border-2 px-3 py-2 text-sm flex items-start gap-2 ${
              drCompletionTone === "rose"
                ? "border-rose-300 bg-rose-50 text-rose-900"
                : drCompletionTone === "emerald"
                  ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                  : "border-slate-200 bg-slate-50 text-slate-700"
            }`}
            data-testid="daily-completion-summary"
          >
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold shrink-0 mt-0.5">
              {drCompletionTone === "rose" ? t("Attention") : t("Status")}
            </span>
            <div className="flex-1 leading-snug">
              {drCompletionLabel}
              {drAttentionItems.length > 0 && (
                <div className="text-xs mt-1">
                  {t("Complete the highlighted section or mark it not used today.")}
                </div>
              )}
            </div>
          </div>
          {payloadIsHeavy && (
            <div
              className="mb-3 rounded-md border-2 border-amber-300 bg-amber-50 p-3 text-amber-900 text-sm flex items-start gap-2"
              data-testid="daily-payload-soft-warning"
            >
              <span className="font-mono text-[10px] uppercase tracking-[0.18em] font-black bg-amber-200 px-1.5 py-0.5 rounded shrink-0">
                heads-up
              </span>
              <div>
                {t("This report has")} <strong>{totalAttachmentCount}</strong>{" "}
                {t("photo(s) attached (≈")}{estimatedPayloadMB} MB{t(" estimated).")}{" "}
                {t("Still submittable. For very large evidence sets consider splitting into multiple reports so each stays well under the size limit.")}
              </div>
            </div>
          )}
          {photosCount < photoMin && (
            <p
              className="text-center text-sm text-red-700 font-bold mb-2"
              data-testid="daily-submit-photos-hint"
            >
              <Camera className="w-4 h-4 inline-block mr-1 -mt-0.5" />
              {t("Add")}{" "}
              <span className="font-mono">{photoMin - photosCount}</span>{" "}
              {photoMin - photosCount === 1
                ? t("more photo to submit")
                : t("more photos to submit")}
            </p>
          )}
          <Button
            onClick={submit}
            disabled={saving || photosCount < photoMin}
            className="w-full h-16 bg-red-700 hover:bg-red-800 disabled:bg-slate-300 disabled:text-slate-500 disabled:cursor-not-allowed text-white font-bold uppercase tracking-wide text-base sm:text-lg border-b-4 border-red-900 disabled:border-slate-400"
            data-testid="submit-bottom-btn"
          >
            {saving ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />{" "}
                {t("Saving Report...")}
              </>
            ) : photosCount < photoMin ? (
              <>
                <Camera className="w-5 h-5 mr-2" />{" "}
                {t("Need")} {photoMin} {t("photos to submit")}
              </>
            ) : (
              <>
                <Save className="w-5 h-5 mr-2" /> {t("Submit Daily Report")}
              </>
            )}
          </Button>
        </div>
      </main>

      {/* iter500 · Rank #1 · Human-Operability sticky footer.
          Always-visible submit anchor pinned to the viewport bottom so the
          primary action is reachable on every form length and every device
          without scroll-hunting. Mirrors the iter453.7 + iter453.9 pattern
          proven on HrEmployees. The existing top/bottom Submit buttons are
          retained for redundancy; this footer is the always-on path. */}
      <div
        className="fixed bottom-0 inset-x-0 z-30 bg-white/95 backdrop-blur border-t-2 border-red-700 shadow-[0_-4px_12px_rgba(0,0,0,0.08)]"
        data-testid="submit-sticky-footer"
      >
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 hidden sm:block">
            {saving
              ? t("Submitting daily report…")
              : photosCount < photoMin
                ? `${t("Need")} ${photoMin - photosCount} ${t("more photo(s)")}`
                : t("Ready to submit · PM distribution will send")}
          </div>
          <Button
            onClick={submit}
            disabled={saving || photosCount < photoMin}
            className="ml-auto h-12 px-6 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900 disabled:opacity-60"
            data-testid="submit-sticky-btn"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            {saving ? t("Saving…") : t("Submit Daily Report")}
          </Button>
        </div>
      </div>
    </div>
  );
}
