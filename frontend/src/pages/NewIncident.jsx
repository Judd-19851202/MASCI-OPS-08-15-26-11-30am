import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  Save,
  Loader2,
  MapPin,
  UserPlus,
  X,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MasciLogo } from "@/components/MasciLogo";
import { Section } from "@/components/Section";
import { CollapseCard } from "@/components/CollapseCard";
import { YesNo } from "@/components/YesNo";
import { SignaturePad } from "@/components/SignaturePad";
import { PhotoUpload } from "@/components/PhotoUpload";
import { JobPicker } from "@/components/JobPicker";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { SupplierCombo } from "@/components/SupplierCombo";
import MasterLookupCombobox from "@/components/MasterLookupCombobox";
import EmployeeRosterField from "@/components/EmployeeRosterField";
import { LangToggle } from "@/components/LangToggle";
import { DistributionList } from "@/components/DistributionList";
import { useT, getLang } from "@/lib/i18n";
import { friendlyError } from "@/lib/friendlyErrors";
import { HelpTip } from "@/components/ui/HelpTip";
import { HelpTipBlock } from "@/components/HelpTip";
import { formatApiError } from "@/lib/apiErrors";
import {
  INCIDENT_TYPES,
  SEVERITY_LEVELS,
  BODY_PARTS,
  INJURY_NATURES,
  ROOT_CAUSE_CATEGORIES,
  buildIncidentDefaults,
} from "@/lib/incidentSchema";
import { api } from "@/lib/api";
import { isAdmin } from "@/lib/adminAuth";
import { toast } from "sonner";
import {
  getCurrentPosition,
  reverseGeocode,
  formatCoords,
} from "@/lib/geolocation";
import { cn } from "@/lib/utils";
import {
  useFormDraft, getActorId, mintIdempotencyKey, enqueueUpload,
  persistIdempotencyKey, loadIdempotencyKey,
  DraftStatusPill, DraftRestorePrompt,
} from "@/lib/resiliency";

const inputCls =
  "h-14 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2";

export default function NewIncident({ publicMode = false }) {
  const navigate = useNavigate();
  const { t } = useT();
  const [data, setData] = useState(buildIncidentDefaults());
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const idempotencyKeyRef = React.useRef(null);

  // iter383 · Phase 5C.1 — Smart Operational Disclosure for Incident
  // Tier-2 (sections 05–08). Each follow-up section is wrapped in a
  // CollapseCard with forceOpen + lockOpen tied to isSeriousIncident.
  //
  // SAFETY NET (non-negotiable): for severity ∈ {medical, restricted,
  // lost_time, fatality}, every Tier-2 CollapseCard auto-opens and the
  // toggle is locked. Under-classification cannot bypass the OSHA-grade
  // fields. See OPERATIONAL_ADOPTION_PROTECTION_PLAN.md.
  const SERIOUS_SEVERITIES = ["medical", "restricted", "lost_time", "fatality"];
  const isSeriousIncident = SERIOUS_SEVERITIES.includes(data.severity);

  // Phase 6 · WS2/WS3 — submit-attempt flag drives attentionOpen on Tier-2
  // CollapseCards. Reset whenever the user changes severity or types into
  // any Tier-2 section so the cards don't stay artificially flagged after
  // the user starts completing them.
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);

  // Phase 6 · WS3 — operational completion derivation.
  // For SERIOUS incidents, follow-up sections are required (already
  // locked-open). The summary tells the user what is filled and what is
  // still bare so they know whether the report is operationally complete
  // before they tap submit. Stays quiet for low-severity events.
  const rootCauseCount = Object.values(data.root_causes || {}).filter(Boolean).length;
  const witnessCount = (data.witnesses || []).length;
  const correctiveFilled =
    (data.corrective_actions || "").trim().length > 0 ||
    (data.responsible_party || "").trim().length > 0;
  const notificationsTracked = [
    data.notified_safety_manager, data.notified_pm, data.notified_gc,
    data.notified_owner, data.notified_osha, data.notified_other,
  ].filter((v) => v && v !== "no" && v !== "No").length > 0;

  const incidentMissingSections = [];
  if (isSeriousIncident) {
    if (rootCauseCount === 0) incidentMissingSections.push("Root cause");
    if (!correctiveFilled) incidentMissingSections.push("Corrective actions");
    if (!notificationsTracked) incidentMissingSections.push("Notifications");
  }
  const incidentCompletionTone =
    incidentMissingSections.length > 0 ? "rose" :
    isSeriousIncident ? "emerald" :
    rootCauseCount > 0 || correctiveFilled || witnessCount > 0 ? "emerald" :
    "slate";
  const incidentCompletionLabel =
    incidentMissingSections.length > 0
      ? `${incidentMissingSections.length} ${t("section(s) need attention")}`
      : isSeriousIncident
        ? t("Operationally complete · ready to submit")
        : (rootCauseCount + (correctiveFilled ? 1 : 0) + (witnessCount > 0 ? 1 : 0)) > 0
          ? t("Optional sections completed")
          : t("Ready to submit · follow-up optional for this severity");

  // iter434 · Phase 31 · Part 2 — manual draft recovery via calm prompt
  // (do NOT auto-overwrite the form). Autosave continues silently.
  const actorId = React.useMemo(() => getActorId(), []);
  const {
    pendingDraft, draftStatus, restore, discard, commit,
  } = useFormDraft("incident-new", data, actorId);

  // TRUST-1 · TF-002 — hydrate any persisted idempotency key from IDB
  // so a reload mid-offline-queue does not mint a duplicate incident.
  // Mirrors the NewDailyReport iter440 pattern.
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const k = await loadIdempotencyKey("incident-new");
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

  const set = (k, v) => setData((p) => ({ ...p, [k]: v }));
  const setMap = (mapKey, key, value) =>
    setData((p) => ({ ...p, [mapKey]: { ...p[mapKey], [key]: value } }));

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
        toast.success("Location captured from GPS");
      } catch {
        setData((p) => ({
          ...p,
          location: formatCoords(latitude, longitude, accuracy),
        }));
        toast.warning("Got GPS coordinates, but couldn't look up address");
      }
    } catch (e) {
      toast.error(e?.message || "Could not get GPS location");
    } finally {
      setLocating(false);
    }
  };

  const addWitness = () =>
    setData((p) => ({
      ...p,
      witnesses: [...p.witnesses, { name: "", statement: "" }],
    }));
  const updateWitness = (i, k, v) =>
    setData((p) => ({
      ...p,
      witnesses: p.witnesses.map((w, idx) =>
        idx === i ? { ...w, [k]: v } : w
      ),
    }));
  const removeWitness = (i) =>
    setData((p) => ({
      ...p,
      witnesses: p.witnesses.filter((_, idx) => idx !== i),
    }));

  const validate = () => {
    const required = [
      ["project_name", "Project Name"],
      ["location", "Location"],
      ["incident_date", "Incident Date"],
      ["incident_time", "Incident Time"],
      ["reported_by", "Reported By"],
      ["incident_type", "Incident Type"],
      ["severity", "Severity"],
      ["description", "Description / What Happened"],
    ];
    for (const [k, l] of required) {
      if (!String(data[k] || "").trim()) {
        toast.error(`${l} is required`);
        return false;
      }
    }
    if (!data.reporter_signature) {
      toast.error("Reporter signature is required");
      return false;
    }
    // Photos required — incidents are documentation-heavy by nature
    // (OSHA, insurance, root-cause). 4-photo minimum mirrors site
    // inspections.
    if ((data.photos || []).length < 4) {
      toast.error(
        `${t("Minimum 4 photos required.")} (${(data.photos || []).length}/4)`
      );
      return false;
    }
    return true;
  };

  const submit = async () => {
    if (!validate()) {
      // Phase 6 · WS2 — surface attention to missing Tier-2 sections.
      setAttemptedSubmit(true);
      return;
    }
    // Phase 6 — for serious incidents, refuse to submit until every
    // required Tier-2 section has minimal operational content. Severity
    // escalation must not be bypassable by a clean Section 01 alone.
    if (isSeriousIncident && incidentMissingSections.length > 0) {
      setAttemptedSubmit(true);
      toast.error(
        `${t("Complete the highlighted section or mark it not used today.")} · ${incidentMissingSections.join(" · ")}`,
        { duration: 6000 },
      );
      return;
    }
    setSaving(true);
    try {
      const lang = getLang();
      let payload = data;
      if (lang === "es") {
        toast.info("Translating to English…");
        const { translateUserInput } = await import("@/lib/translateOnSubmit");
        payload = await translateUserInput(data, "es");
      }
      // iter139 — strip FE-only display fields; only persist the master IDs
      const { employee_master_label, equipment_master_label, ...persistPayload } = payload;
      payload = { ...persistPayload, submit_language: lang || "en" };
      // Phase J — single idempotency key per "session" attempt: a fresh
      // one per submit click, but persisted across in-form retries via
      // the queue so the server treats them as the same logical write.
      if (!idempotencyKeyRef.current) {
        idempotencyKeyRef.current = mintIdempotencyKey();
        // TRUST-1 · TF-002 — persist immediately so a reload mid-queue
        // does not regenerate the key and produce a duplicate.
        try { await persistIdempotencyKey("incident-new", idempotencyKeyRef.current); }
        catch { /* ignore */ }
      }
      const r = await enqueueUpload({
        method: "POST",
        url: "/incidents",
        body: payload,
        idempotencyKey: idempotencyKeyRef.current,
        formKey: "incident-new",
      });
      if (!r.ok && r.queued) {
        toast.message("Saved · will upload when reconnected", {
          description: "Your incident report is queued and will send automatically.",
          duration: 6000,
        });
        await commit();
        idempotencyKeyRef.current = null;
        if (publicMode || !isAdmin()) {
          navigate("/thank-you", {
            state: {
              projectName: payload.project_name,
              formType: "Incident Report",
              returnTo: "/incidents/submit",
              recordId: r.data?.incident_number || r.data?.id || "",
            },
            replace: true,
          });
        } else {
          navigate(`/incidents`);
        }
        return;
      }
      const res = { data: r.data };
      toast.success(t("Incident report filed · Safety + PM notified · visible under Incidents"));
      await commit();
      idempotencyKeyRef.current = null;
      // iter147 — telemetry on the most-used safety form
      import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
        trackFormSubmit("/incidents", true, "incident-new")).catch(() => {});
      if (publicMode || !isAdmin()) {
        navigate("/thank-you", {
          state: {
            projectName: payload.project_name,
            formType: "Incident Report",
            returnTo: "/incidents/submit",
            recordId: r.data?.incident_number || r.data?.id || "",
          },
          replace: true,
        });
      } else {
        navigate(`/incidents/${res.data.id}`);
      }
    } catch (e) {
      console.error(e);
      toast.error(friendlyError(e, formatApiError(e, "Could not save incident report")), { duration: 7000 });
      // iter147 — record the failure for analytics
      import("@/lib/usageTracker").then(({ trackFormSubmit }) =>
        trackFormSubmit("/incidents", false, "incident-new")).catch(() => {});
    } finally {
      setSaving(false);
    }
  };

  const isInjury =
    data.incident_type === "Injury / Illness" ||
    ["first_aid", "medical", "restricted", "lost_time", "fatality"].includes(
      data.severity
    );

  return (
    <div className="min-h-screen bg-slate-50 pb-32 overflow-x-hidden">
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
              <ArrowLeft className="w-4 h-4 mr-1" /> Home
            </Link>
          )}
          <MasciLogo
            variant="mark"
            size="md"
            className={publicMode ? "sm:hidden" : ""}
          homeLink="/" />
          <div className="flex items-center gap-2">
            <DraftStatusPill status={draftStatus} testId="incident-draft-pill" />
            <LangToggle />
            <Button
              onClick={submit}
              disabled={saving || (data.photos || []).length < 4}
              className="h-11 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900 disabled:opacity-60"
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
            {t("Accident / Incident Report")}
          </h1>
          {/* iter333 · operational sub-header · iter327 capability-forward voice */}
          <p className="text-sm text-slate-600 mt-1.5 max-w-2xl leading-snug">
            {t("Every detail filed here protects the crew, the project, and the company. Write it the way you'd want to read it six months from now.")}
          </p>
          <div className="mt-3 flex items-start gap-2 p-3 border-2 border-amber-300 bg-amber-50 rounded-md">
            <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
            <p className="text-sm text-amber-900 leading-snug">
              <span className="font-bold">{t("First, secure the scene and the injured.")}</span>{" "}
              {t("Call 911 if anyone is seriously hurt. Document this report once the immediate response is complete.")}
            </p>
          </div>
        </div>

        {/* iter434 · Phase 31 · Part 2 — calm draft recovery prompt.
            Shown ONLY when an unsent draft was loaded on mount. */}
        <DraftRestorePrompt
          pendingDraft={pendingDraft}
          onRestore={onRestoreDraft}
          onDiscard={onDiscardDraft}
          testId="incident-draft-restore-prompt"
        />

        {/* Section 01 — Report Info */}
        <HelpTipBlock formKey="incident" className="mb-3" showCounter />
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
              Pick a current job to auto-fill name + number — or choose Custom Job to type your own.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Project Name *
              </Label>
              <Input
                value={data.project_name}
                onChange={(e) => set("project_name", e.target.value)}
                className={inputCls}
                placeholder="e.g. I-95 Resurfacing - Phase 2"
                data-testid="input-project-name"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Project Number
              </Label>
              <Input
                value={data.project_number}
                onChange={(e) => set("project_number", e.target.value)}
                className={inputCls}
                data-testid="input-project-number"
              />
            </div>
            <div className="sm:col-span-2">
              <div className="flex items-center justify-between gap-2 mb-1">
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Location *
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
                  Use GPS
                </Button>
              </div>
              <Input
                value={data.location}
                onChange={(e) => set("location", e.target.value)}
                className={inputCls}
                placeholder="Specific location on site (station, lane, structure...)"
                data-testid="input-location"
              />
              {data.gps_lat != null && (
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1.5 flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-red-700" />
                  GPS · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}
                </div>
              )}
              <HelpTipBlock formKey="incident.location" className="mt-3" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Incident Date *
              </Label>
              <Input
                type="date"
                value={data.incident_date}
                onChange={(e) => set("incident_date", e.target.value)}
                className={inputCls}
                data-testid="input-incident-date"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Incident Time *
              </Label>
              <Input
                type="time"
                value={data.incident_time}
                onChange={(e) => set("incident_time", e.target.value)}
                className={inputCls}
                data-testid="input-incident-time"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Date Reported
              </Label>
              <Input
                type="date"
                value={data.reported_date}
                onChange={(e) => set("reported_date", e.target.value)}
                className={inputCls}
                data-testid="input-reported-date"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Reported By *
              </Label>
              <EmployeeCombo
                value={data.reported_by}
                onChange={(v) => set("reported_by", v)}
                placeholder="Your name"
                testId="input-reported-by"
              />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Supervisor / Foreman On-Site
              </Label>
              <EmployeeCombo
                value={data.supervisor_name}
                onChange={(v) => set("supervisor_name", v)}
                testId="input-supervisor-name"
              />
            </div>
          </div>
        </Section>

        {/* Section 02 — Classification & Severity */}
        <Section number="02" title={t("Classification & Severity")}>
          <HelpTipBlock formKey="incident.severity" className="mb-3" />
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700 flex items-center gap-1.5">
              {t("Incident Type *")}
              <HelpTip
                label={t("How do I pick the right incident type?")}
                body={t("Pick the category that BEST DESCRIBES THE EVENT — not the body part injured. Use Near Miss for events with no actual harm. Property Damage for asset-only impact. Use one type per report; file a second report if multiple distinct events occurred.")}
                testId="incident-help-type"
              />
            </Label>
            <Select
              value={data.incident_type}
              onValueChange={(v) => set("incident_type", v)}
            >
              <SelectTrigger
                className={inputCls}
                data-testid="select-incident-type"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {INCIDENT_TYPES.map((it) => (
                  <SelectItem
                    key={it}
                    value={it}
                    data-testid={`incident-type-${it}`}
                  >
                    {t(it)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Severity Tier *")}
            </Label>
            <p className="text-xs text-slate-500 mt-1 mb-2">
              {t("Pick the actual outcome. For a near miss, choose Near Miss even if the potential was severe — note the potential in the description.")}
            </p>
            <div
              className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4"
              data-testid="severity-grid"
            >
              {SEVERITY_LEVELS.map((s) => {
                const active = data.severity === s.key;
                return (
                  <button
                    key={s.key}
                    type="button"
                    onClick={() => set("severity", s.key)}
                    className={cn(
                      "text-left border-2 rounded-md p-3 transition-colors duration-150",
                      active
                        ? "border-red-700 bg-red-50"
                        : "border-slate-200 bg-white hover:border-red-300"
                    )}
                    data-testid={`severity-${s.key}`}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 ${s.color} text-white text-[10px] font-mono uppercase tracking-wider rounded font-bold`}
                      >
                        {t(s.label)}
                      </span>
                      {active && (
                        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">
                          {t("Selected")}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-600 mt-1.5 leading-snug">
                      {t(s.desc)}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("OSHA Recordable?")}
              </Label>
              <YesNo
                value={data.osha_recordable}
                onChange={(v) => set("osha_recordable", v)}
                options={["Yes", "No", "Unsure"]}
                testId="osha-recordable"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Was Work Stopped?")}
              </Label>
              <YesNo
                value={data.work_stopped}
                onChange={(v) => set("work_stopped", v)}
                testId="work-stopped"
              />
            </div>
          </div>
        </Section>

        {/* Section 03 — Person involved (only if injury-related) */}
        {isInjury && (
          <Section number="03" title={t("Person Involved")}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
              <div className="sm:col-span-2">
                {/* iter359 · Unified roster-first selector with operational
                    coaching baked in. Free-text fallback preserved for
                    subcontractors / non-employees, but the downstream
                    consequence (EMP_LINK_UNRESOLVABLE finding) is visible
                    at entry time, not after the fact. */}
                <EmployeeRosterField
                  label={t("Name") + " · " + t("Linked to employee master")}
                  value={{
                    id: data.employee_master_id || "",
                    name: data.person_name || "",
                    linked: !!data.employee_master_id,
                  }}
                  onChange={({ id, name, linked }) => {
                    set("person_name", name);
                    set("employee_master_id", linked ? id : "");
                    set("employee_master_label", linked ? name : "");
                  }}
                  placeholder={t("Type name to search roster")}
                  required
                  testId="input-person-roster"
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Role / Trade
                </Label>
                <Input
                  value={data.person_role}
                  onChange={(e) => set("person_role", e.target.value)}
                  className={inputCls}
                  placeholder="Laborer, Operator, Foreman..."
                  data-testid="input-person-role"
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Employer
                </Label>
                <SupplierCombo
                  value={data.person_employer}
                  onChange={(v) => set("person_employer", v)}
                  placeholder="MASCI / subcontractor name"
                  testId="input-person-employer"
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Years Experience
                </Label>
                <Input
                  value={data.person_years_experience}
                  onChange={(e) =>
                    set("person_years_experience", e.target.value)
                  }
                  className={inputCls}
                  data-testid="input-person-experience"
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Body Part Affected
                </Label>
                <Select
                  value={data.body_part}
                  onValueChange={(v) => set("body_part", v)}
                >
                  <SelectTrigger
                    className={inputCls}
                    data-testid="select-body-part"
                  >
                    <SelectValue placeholder="Select body part..." />
                  </SelectTrigger>
                  <SelectContent className="max-h-[60vh]">
                    {BODY_PARTS.map((b) => (
                      <SelectItem key={b} value={b}>
                        {b}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Nature of Injury / Illness
                </Label>
                <Select
                  value={data.injury_nature}
                  onValueChange={(v) => set("injury_nature", v)}
                >
                  <SelectTrigger
                    className={inputCls}
                    data-testid="select-injury-nature"
                  >
                    <SelectValue placeholder="Select..." />
                  </SelectTrigger>
                  <SelectContent className="max-h-[60vh]">
                    {INJURY_NATURES.map((n) => (
                      <SelectItem key={n} value={n}>
                        {n}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="sm:col-span-2">
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Treatment Provided
                </Label>
                <Textarea
                  value={data.treatment_provided}
                  onChange={(e) => set("treatment_provided", e.target.value)}
                  className="min-h-[80px] text-base border-2 border-slate-300"
                  placeholder="First aid given, EMS called, transported by..."
                  data-testid="input-treatment"
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Medical Facility
                </Label>
                <Input
                  value={data.medical_facility}
                  onChange={(e) => set("medical_facility", e.target.value)}
                  className={inputCls}
                  placeholder="Clinic / hospital, if applicable"
                  data-testid="input-medical-facility"
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  Sent Home / Off Site?
                </Label>
                <YesNo
                  value={data.sent_home}
                  onChange={(v) => set("sent_home", v)}
                  testId="sent-home"
                />
              </div>
            </div>
          </Section>
        )}

        {/* Section 04 — Description */}
        <Section number="04" title={t("What Happened")}>
          <HelpTipBlock formKey="incident.narrative" className="mb-3" />
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Description of Incident *
            </Label>
            <Textarea
              value={data.description}
              onChange={(e) => set("description", e.target.value)}
              className="min-h-[160px] text-base border-2 border-slate-300"
              placeholder={t("What happened, who was involved, what equipment or materials were present, and what was done in the moment. Write it like you'd brief the Safety Manager on a phone call.")}
              data-testid="input-description"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Immediate Cause
            </Label>
            <Textarea
              value={data.immediate_cause}
              onChange={(e) => set("immediate_cause", e.target.value)}
              className="min-h-[80px] text-base border-2 border-slate-300"
              placeholder="What was the unsafe act or condition that triggered the event?"
              data-testid="input-immediate-cause"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Contributing Factors
            </Label>
            <Textarea
              value={data.contributing_factors}
              onChange={(e) => set("contributing_factors", e.target.value)}
              className="min-h-[80px] text-base border-2 border-slate-300"
              placeholder="Weather, fatigue, training, equipment condition, schedule pressure..."
              data-testid="input-contributing"
            />
          </div>
          {/* iter139 — bind to specific equipment master record if any */}
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Equipment involved (optional)
            </Label>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Link to a specific MASCI equipment unit. Improves traceability for the Safety team's corrective-action lookup.
            </p>
            <div className="mt-1">
              <MasterLookupCombobox
                kind="equipment"
                value={data.equipment_master_id}
                displayValue={data.equipment_master_label}
                onPick={(item) => { set("equipment_master_id", item.id); set("equipment_master_label", item.label); }}
                onClear={() => { set("equipment_master_id", ""); set("equipment_master_label", ""); }}
                placeholder="Search by unit number / make / VIN"
                testIdPrefix="input-equipment-master"
              />
            </div>
          </div>
        </Section>

        {/* iter383 · Phase 5C.1 — Smart Operational Disclosure for
            Incident Tier-2 (sections 05–08). Each follow-up section is a
            visible CollapseCard with operational status. AUTO-EXPAND +
            LOCK when severity ≥ medical (forceOpen + lockOpen). ZERO
            field deletion — full payload preserved.

            DO NOT TOUCH: severity auto-escalation, OSHA-grade enforcement,
            CAPA lifecycle hooks. This refactor only changes awareness. */}
        {isSeriousIncident && (
          <div
            className="border-l-4 border-rose-600 bg-rose-50/60 rounded-md p-3 text-sm text-rose-900"
            data-testid="incident-tier2-locked-banner"
          >
            <span className="font-mono text-[11px] uppercase tracking-[0.2em] font-bold">
              {t("Required")}
            </span>
            {" · "}
            {t("Severity is Medical or higher — follow-up sections are open and required before submit.")}
          </div>
        )}

        <CollapseCard
          title={t("Root Cause Analysis")}
          testId="incident-root-cause"
          statusLabel={
            isSeriousIncident
              ? t("Required")
              : Object.values(data.root_causes || {}).filter(Boolean).length > 0
                ? `${Object.values(data.root_causes || {}).filter(Boolean).length} ${t("selected")}`
                : t("Optional · add if cause is known")
          }
          statusTone={
            isSeriousIncident
              ? "rose"
              : Object.values(data.root_causes || {}).filter(Boolean).length > 0
                ? "emerald"
                : "slate"
          }
          forceOpen={isSeriousIncident}
          lockOpen={isSeriousIncident}
          attentionOpen={attemptedSubmit && isSeriousIncident && rootCauseCount === 0}
        >
        <Section number="05" title="Root Cause Analysis">
          <p className="text-sm text-slate-600">
            Check every category that contributed. Pick all that apply.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            {ROOT_CAUSE_CATEGORIES.map((opt) => (
              <label
                key={opt.key}
                className="flex items-center gap-3 p-3 border border-slate-200 rounded-md hover:border-red-500 cursor-pointer"
                data-testid={`root-cause-${opt.key}`}
              >
                <Checkbox
                  checked={!!data.root_causes[opt.key]}
                  onCheckedChange={(v) => setMap("root_causes", opt.key, !!v)}
                />
                <span className="text-base text-slate-800">{opt.label}</span>
              </label>
            ))}
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Notes / Additional Detail
            </Label>
            <Textarea
              value={data.root_cause_notes}
              onChange={(e) => set("root_cause_notes", e.target.value)}
              className="min-h-[80px] text-base border-2 border-slate-300"
              data-testid="input-root-cause-notes"
            />
          </div>
        </Section>
        </CollapseCard>

        <CollapseCard
          title={t("Witnesses")}
          testId="incident-witnesses"
          statusLabel={
            (data.witnesses?.length || 0) > 0
              ? `${data.witnesses.length} ${t("entered")}`
              : isSeriousIncident
                ? t("Recommended")
                : t("Optional · none today")
          }
          statusTone={
            (data.witnesses?.length || 0) > 0
              ? "emerald"
              : isSeriousIncident
                ? "amber"
                : "slate"
          }
          forceOpen={isSeriousIncident}
          lockOpen={isSeriousIncident}
        >
        {/* Section 06 — Witnesses */}
        <Section number="06" title={t("Witnesses")}>
          <HelpTipBlock formKey="incident.witnesses" className="mb-3" />
          <p className="text-sm text-slate-600">
            Add anyone who saw the event. Capture short statements while it's
            fresh.
          </p>
          {data.witnesses.map((w, i) => (
            <div
              key={i}
              className="border border-slate-200 rounded-md p-4 space-y-3"
              data-testid={`witness-${i}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                  Witness {i + 1}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeWitness(i)}
                  className="text-slate-500 hover:text-red-600"
                  data-testid={`witness-remove-${i}`}
                >
                  <X className="w-4 h-4 mr-1" /> Remove
                </Button>
              </div>
              <EmployeeCombo
                value={w.name}
                onChange={(v) => updateWitness(i, "name", v)}
                placeholder="Name"
                testId={`witness-name-${i}`}
              />
              <Textarea
                value={w.statement}
                onChange={(e) => updateWitness(i, "statement", e.target.value)}
                className="min-h-[80px] text-base border-2 border-slate-300"
                placeholder="What they saw, in their words."
                data-testid={`witness-statement-${i}`}
              />
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            onClick={addWitness}
            className="w-full h-12 border-2 border-dashed border-slate-400 hover:border-red-700 hover:text-red-700 font-bold uppercase tracking-wide text-sm"
            data-testid="witness-add"
          >
            <UserPlus className="w-4 h-4 mr-2" /> Add Witness
          </Button>
        </Section>
        </CollapseCard>

        <CollapseCard
          title={t("Corrective Actions & Follow-Up")}
          testId="incident-corrective"
          statusLabel={
            (data.corrective_actions || "").trim().length > 0 ||
            (data.responsible_party || "").trim().length > 0
              ? t("In progress")
              : isSeriousIncident
                ? t("Required")
                : t("Optional · add if known")
          }
          statusTone={
            (data.corrective_actions || "").trim().length > 0 ||
            (data.responsible_party || "").trim().length > 0
              ? "emerald"
              : isSeriousIncident
                ? "rose"
                : "slate"
          }
          forceOpen={isSeriousIncident}
          lockOpen={isSeriousIncident}
          attentionOpen={attemptedSubmit && isSeriousIncident && !correctiveFilled}
        >
        {/* Section 07 — Corrective actions */}
        <Section number="07" title={t("Corrective Actions & Follow-Up")}>
          <HelpTipBlock formKey="incident.corrective" className="mb-3" />
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Immediate Actions Taken (on-site, today)
            </Label>
            <Textarea
              value={data.immediate_actions_taken}
              onChange={(e) =>
                set("immediate_actions_taken", e.target.value)
              }
              className="min-h-[100px] text-base border-2 border-slate-300"
              placeholder="What was done immediately to make the area safe?"
              data-testid="input-immediate-actions"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Long-Term Corrective Actions
            </Label>
            <Textarea
              value={data.corrective_actions}
              onChange={(e) => set("corrective_actions", e.target.value)}
              className="min-h-[100px] text-base border-2 border-slate-300"
              placeholder={t("Specific changes that prevent this from happening again — training, procedure updates, equipment fixes, supervision changes.")}
              data-testid="input-corrective"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Responsible Party
              </Label>
              <Input
                value={data.responsible_party}
                onChange={(e) => set("responsible_party", e.target.value)}
                className={inputCls}
                placeholder="Who owns the follow-up?"
                data-testid="input-responsible"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Target Completion Date
              </Label>
              <Input
                type="date"
                value={data.target_completion_date}
                onChange={(e) =>
                  set("target_completion_date", e.target.value)
                }
                className={inputCls}
                data-testid="input-target-date"
              />
            </div>
          </div>
        </Section>
        </CollapseCard>

        <CollapseCard
          title={t("Notifications Made")}
          testId="incident-notifications"
          statusLabel={
            [
              data.notified_safety_manager,
              data.notified_pm,
              data.notified_gc,
              data.notified_owner,
              data.notified_osha,
              data.notified_other,
            ].filter((v) => v && v !== "no" && v !== "No").length > 0
              ? t("Tracked")
              : isSeriousIncident
                ? t("Required")
                : t("Optional · platform notifies automatically on submit")
          }
          statusTone={
            [
              data.notified_safety_manager,
              data.notified_pm,
              data.notified_gc,
              data.notified_owner,
              data.notified_osha,
              data.notified_other,
            ].filter((v) => v && v !== "no" && v !== "No").length > 0
              ? "emerald"
              : isSeriousIncident
                ? "rose"
                : "slate"
          }
          forceOpen={isSeriousIncident}
          lockOpen={isSeriousIncident}
          attentionOpen={attemptedSubmit && isSeriousIncident && !notificationsTracked}
        >
        {/* Section 08 — Notifications */}
        <Section number="08" title={t("Notifications Made")}>
          <p className="text-sm text-slate-600">
            Confirm who was notified about this incident.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Safety Manager
              </Label>
              <YesNo
                value={data.notified_safety_manager}
                onChange={(v) => set("notified_safety_manager", v)}
                testId="notified-safety"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Project Manager
              </Label>
              <YesNo
                value={data.notified_pm}
                onChange={(v) => set("notified_pm", v)}
                testId="notified-pm"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                General Contractor
              </Label>
              <YesNo
                value={data.notified_gc}
                onChange={(v) => set("notified_gc", v)}
                testId="notified-gc"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Owner / Agency
              </Label>
              <YesNo
                value={data.notified_owner}
                onChange={(v) => set("notified_owner", v)}
                testId="notified-owner"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                OSHA (if catastrophic)
              </Label>
              <YesNo
                value={data.notified_osha}
                onChange={(v) => set("notified_osha", v)}
                testId="notified-osha"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Other (free text)
              </Label>
              <Input
                value={data.notified_other}
                onChange={(e) => set("notified_other", e.target.value)}
                className={inputCls}
                placeholder="Insurance, EAP, family..."
                data-testid="input-notified-other"
              />
            </div>
          </div>
          <div className="mt-5 pt-5 border-t-2 border-slate-100">
            <DistributionList
              value={data.distribution_list}
              onChange={(v) => set("distribution_list", v)}
              testIdPrefix="incident-dist"
            />
          </div>
        </Section>
        </CollapseCard>
        {/* iter383 · End of Smart Operational Disclosure Tier-2 cards. */}

        <Section number="09" title={t("Photos / Evidence")}>
          <p className="text-xs text-slate-600 -mt-2 mb-2">
            {t("Photos: ")}
            <span
              className={
                (data.photos || []).length >= 4
                  ? "text-emerald-700 font-bold"
                  : "text-red-700 font-bold"
              }
              data-testid="incident-photo-count"
            >
              {(data.photos || []).length}
            </span>{" "}
            / <span className="font-mono">{t("min 4 required")}</span>
          </p>
          <PhotoUpload
            photos={data.photos}
            onChange={(photos) => set("photos", photos)}
          />
        </Section>

        <Section number="10" title={t("Signatures")}>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Reporter Signature *
            </Label>
            <SignaturePad
              value={data.reporter_signature}
              onChange={(v) => set("reporter_signature", v)}
              label="Reporter"
              testId="reporter-sig"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Supervisor Signature
            </Label>
            <SignaturePad
              value={data.supervisor_signature}
              onChange={(v) => set("supervisor_signature", v)}
              label="Supervisor"
              testId="supervisor-sig"
            />
          </div>
        </Section>

        <div className="pt-4">
          {/* Phase 6 · WS3 — operational completion indicator. Field-direct
              wording; no gamification; reflects severity-driven follow-up
              expectations without nagging on low-severity reports. */}
          <div
            className={`mb-3 rounded-md border-2 px-3 py-2 text-sm flex items-start gap-2 ${
              incidentCompletionTone === "rose"
                ? "border-rose-300 bg-rose-50 text-rose-900"
                : incidentCompletionTone === "emerald"
                  ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                  : "border-slate-200 bg-slate-50 text-slate-700"
            }`}
            data-testid="incident-completion-summary"
          >
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold shrink-0 mt-0.5">
              {incidentCompletionTone === "rose" ? t("Attention") : t("Status")}
            </span>
            <div className="flex-1">
              <div className="leading-snug">{incidentCompletionLabel}</div>
              {isSeriousIncident && incidentMissingSections.length > 0 && (
                <div className="text-xs mt-1 leading-snug">
                  {t("Complete the highlighted section or mark it not used today.")}
                </div>
              )}
            </div>
          </div>
          {(data.photos || []).length < 4 && (
            <p className="text-xs text-red-700 font-bold text-center mb-2 font-mono uppercase tracking-[0.15em]">
              {t("Need")} {4 - (data.photos || []).length} {t("more photo(s) before you can submit")}
            </p>
          )}
          <Button
            onClick={submit}
            disabled={saving || (data.photos || []).length < 4}
            className="w-full h-16 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-base sm:text-lg border-b-4 border-red-900 disabled:opacity-60"
            data-testid="submit-bottom-btn"
          >
            {saving ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" /> {t("Saving Report...")}
              </>
            ) : (
              <>
                <Save className="w-5 h-5 mr-2" /> {t("Submit Incident Report")}
              </>
            )}
          </Button>
        </div>
      </main>
    </div>
  );
}
