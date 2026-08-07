import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Save, Loader2, MapPin, UserPlus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Section } from "@/components/Section";
import { SignaturePad } from "@/components/SignaturePad";
import { PhotoUpload } from "@/components/PhotoUpload";
import { TopicPicker } from "@/components/TopicPicker";
import { JobPicker } from "@/components/JobPicker";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import { AttendeeBulkAddDialog } from "@/components/AttendeeBulkAddDialog";
import { BilingualConsent } from "@/components/BilingualConsent";
import FormShell from "@/components/FormShell";
import { useT, getLang } from "@/lib/i18n";
import { formatApiError } from "@/lib/apiErrors";
import { TOPIC_CATEGORIES, SHIFT_OPTIONS, WEATHER_OPTIONS, buildMeetingDefaults } from "@/lib/meetingSchema";
import { TOPIC_LIBRARY, CUSTOM_TOPIC_KEY, findTopic } from "@/lib/topics";
import { TOPIC_LIBRARY_ES } from "@/lib/topics/index.es";
import { getDomainLabel } from "@/components/TopicPicker";
import { composeIncidentScaffold } from "@/lib/composeIncidentScaffold";
import { splitIncidentScaffold } from "@/lib/splitIncidentScaffold";
// TRACK 19.13 · HelpTipBlock retired from Safety Meeting — all 6
// stacked coaching bands consolidated into the HelpDrawer below.
// TRACK 19.13 · Safety Meeting modernization consumes the four
// reusable platform primitives established in Track 19.11 MAIN and
// proven at scale by DVIR (Track 19.12). Doctrine: configuration,
// not reinvention. Topic Auto Load remains flagship — untouched.
import { HelpDrawer } from "@/components/HelpDrawer";
import { FormSection } from "@/components/FormSection";
import { ProgressRail } from "@/components/ProgressRail";
import { SubmitReviewPanel } from "@/components/SubmitReviewPanel";
import { api } from "@/lib/api";
import { isAdmin } from "@/lib/adminAuth";
import { toast } from "sonner";
import {
  getCurrentPosition,
  reverseGeocode,
  formatCoords,
} from "@/lib/geolocation";
// TRACK 15.60 · P0 field-trust fix — Safety Meeting draft autosave.
// Mirrors the iter440 pattern used by NewIncident, NewDailyReport,
// NewInspection. The field reported losing a 15–20 person meeting
// mid-entry because this surface had no draft persistence. Wired the
// shared resiliency layer with no schema changes.
import {
  useFormDraft, getActorId,
  DraftStatusPill, DraftRestorePrompt,
} from "@/lib/resiliency";

const inputCls =
  "h-14 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2";

export default function NewMeeting({ publicMode = false }) {
  const navigate = useNavigate();
  const { t, lang } = useT();
  const [data, setData] = useState(buildMeetingDefaults());
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const [templateKey, setTemplateKey] = useState(CUSTOM_TOPIC_KEY);
  // TRACK 19.13 · consolidated HelpDrawer state.
  const [helpDrawerOpen, setHelpDrawerOpen] = useState(false);

  // TRACK 15.60 · Safety Meeting draft autosave (P0 field-trust fix).
  // Wires the shared resiliency layer (`useFormDraft`) so the entire
  // form — attendees, topic, photos, signature, notes — autosaves
  // to IndexedDB every 800 ms and on every iOS lifecycle event
  // (visibilitychange, pagehide, beforeunload). Survives refresh,
  // navigation, accidental close, and transient network failure.
  // Field-incident reproduction: 20-attendee meeting + Request-to-Add
  // failure + refresh → previously lost everything; now restores.
  const actorId = React.useMemo(() => getActorId(), []);
  const {
    pendingDraft, draftStatus, restore, discard, commit,
  } = useFormDraft("meeting-new", data, actorId);

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

  const applyJob = (job) => {
    setData((p) => ({
      ...p,
      project_name: job ? job.project_name : "",
      project_number: job ? job.project_number : "",
      // Only prefill location if user hasn't entered one yet
      location: p.location || (job && job.location) || "",
    }));
    if (job) toast.success(t("Job loaded: #{n}").replace("{n}", job.project_number));
  };

  const applyTemplate = (key) => {
    setTemplateKey(key);
    if (key === CUSTOM_TOPIC_KEY) {
      // Clear prefilled fields so they can write their own
      setData((p) => ({
        ...p,
        topic: "",
        topic_category: "Hazard-Specific",
        hazards_reviewed: "",
        discussion_notes: "",
        references_cited: "",
        action_items: "",
        topic_template_key: CUSTOM_TOPIC_KEY,
      }));
      toast.info(t("Custom topic — all topic fields cleared."));
      return;
    }
    const tpl = findTopic(key);
    if (!tpl) return;
    // Use Spanish version if user is in ES, else English canonical.
    const es = lang === "es" ? TOPIC_LIBRARY_ES[key] : null;
    // If the topic carries an incident_pattern, prepend it to the
    // discussion notes as a labelled "real-world pattern" paragraph
    // so the driver/foreman reads the story before the bullets.
    // The field stays freely editable in the textarea below.
    const enNotes = composeIncidentScaffold(
      tpl.incident_pattern,
      tpl.discussion_notes,
      false
    );
    const esNotes = es
      ? composeIncidentScaffold(es.incident_pattern, es.discussion_notes, true)
      : null;
    setData((p) => ({
      ...p,
      topic: es?.title || tpl.title,
      topic_category: tpl.category,
      hazards_reviewed: es?.hazards_reviewed || tpl.hazards_reviewed,
      discussion_notes: esNotes || enNotes,
      references_cited: es?.references_cited || tpl.references_cited,
      action_items: es?.action_items || tpl.action_items,
      topic_template_key: tpl.key,
    }));
    toast.success(
      lang === "es" && es
        ? `Cargado "${es.title}" — todos los campos editables.`
        : `Loaded "${tpl.title}" — all fields are editable.`
    );
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
        toast.success(t("Location captured from GPS"));
      } catch {
        setData((p) => ({
          ...p,
          location: formatCoords(latitude, longitude, accuracy),
        }));
        toast.warning(t("Got GPS coordinates, but couldn't look up address"));
      }
    } catch (e) {
      toast.error(e?.message || t("Could not get GPS location"));
    } finally {
      setLocating(false);
    }
  };

  const addAttendee = () => {
    // TRACK 15.55 · field workflow restoration.
    // A superintendent must be able to add every attendee row up-front
    // (name + company) and then walk around to collect signatures as
    // people arrive. Blocking per-row completeness here inverted the
    // real-world flow. The completeness gate now lives ONLY at submit
    // time (see validate()), where it correctly enforces "every row
    // must have a signature + acknowledgement before the meeting is
    // recorded" without blocking the row-building step itself.
    setData((p) => ({
      ...p,
      attendees: [...p.attendees, {
        name: "", employee_id: "", non_masci: false,
        // Track 15.73 Slice 2 · default company to MASCI (the OurCo
        // canonical name). User toggling "Non-OurCo / Subcontractor"
        // clears it. Backend `normalize_meeting_attendees` is still
        // the final authority on the saved value.
        company: "MASCI", trade: "", signature: "",
        acknowledged: false, acknowledged_at: "",
        // Track 15.73 Slice 2 · identity hints (backend re-derives).
        attendee_type: "manual",
        source: "manual",
        is_masci_employee: false,
        is_subcontractor: false,
        is_manual: true,
      }],
    }));
  };
  const updateAttendee = (i, k, v) =>
    setData((p) => ({
      ...p,
      attendees: p.attendees.map((a, idx) => (idx === i ? { ...a, [k]: v } : a)),
    }));
  const removeAttendee = (i) =>
    setData((p) => ({
      ...p,
      attendees: p.attendees.filter((_, idx) => idx !== i),
    }));

  // SAFETY-MEETING-CERT · attendee completeness gate.
  // Returns "" when complete, otherwise the human-readable missing-field label.
  const isAttendeeIncomplete = (a) => {
    if (!a) return "";
    if (!String(a.name || "").trim()) return t("name");
    if (!String(a.company || "").trim()) return t("company");
    if (!a.signature) return t("signature");
    if (!a.acknowledged) return t("acknowledgement");
    return "";
  };

  const validate = () => {
    const required = [
      ["project_name", "Project Name"],
      ["location", "Location"],
      ["meeting_date", "Date"],
      ["meeting_time", "Time"],
      ["conducted_by", "Conducted By"],
      ["topic", "Topic"],
    ];
    for (const [k, l] of required) {
      if (!String(data[k] || "").trim()) {
        toast.error(t("{field} is required").replace("{field}", t(l)));
        return false;
      }
    }
    if (!data.conductor_signature) {
      toast.error(t("Conductor signature is required"));
      return false;
    }
    if (data.attendees.length === 0) {
      toast.error(t("Add at least one attendee"));
      return false;
    }
    // SAFETY-MEETING-CERT · every attendee row must be complete.
    for (let i = 0; i < data.attendees.length; i += 1) {
      const missing = isAttendeeIncomplete(data.attendees[i]);
      if (missing) {
        toast.error(t("Attendee {n}: {field} required").replace("{n}", i + 1).replace("{field}", missing));
        return false;
      }
    }
    // Photos required — toolbox-talk photos confirm the meeting actually
    // happened (group shot + topic board). 2-photo minimum.
    if ((data.photos || []).length < 2) {
      toast.error(
        `${t("Minimum 2 photos required.")} (${(data.photos || []).length}/2)`
      );
      return false;
    }
    return true;
  };

  const submit = async () => {
    if (!validate()) return;
    setSaving(true);

    // If a template is loaded AND user is in ES, swap unedited Spanish
    // template content back to the English canonical so the saved record
    // stays English. User-edited fields are preserved as typed.
    let payload = data;
    if (templateKey !== CUSTOM_TOPIC_KEY) {
      const tpl = findTopic(templateKey);
      const es = TOPIC_LIBRARY_ES[templateKey];
      if (tpl && es) {
        const swapIfPristine = (currentVal, esVal, enVal) =>
          currentVal === esVal ? enVal : currentVal;
        // Mirror the scaffold composition used at template-load time so
        // an unedited bilingual discussion_notes (with the incident
        // pattern header prepended) swaps cleanly back to the English
        // canonical composed form on submit.
        const esComposedNotes = composeIncidentScaffold(
          es.incident_pattern,
          es.discussion_notes,
          true
        );
        const enComposedNotes = composeIncidentScaffold(
          tpl.incident_pattern,
          tpl.discussion_notes,
          false
        );
        payload = {
          ...data,
          topic: swapIfPristine(data.topic, es.title, tpl.title),
          hazards_reviewed: swapIfPristine(
            data.hazards_reviewed,
            es.hazards_reviewed,
            tpl.hazards_reviewed
          ),
          discussion_notes: swapIfPristine(
            data.discussion_notes,
            esComposedNotes,
            enComposedNotes
          ),
          references_cited: swapIfPristine(
            data.references_cited,
            es.references_cited,
            tpl.references_cited
          ),
          action_items: swapIfPristine(
            data.action_items,
            es.action_items,
            tpl.action_items
          ),
        };
      }
    }

    try {
      const lang = getLang();
      if (lang === "es") {
        toast.info(t("Translating to English…"));
        const { translateUserInput } = await import("@/lib/translateOnSubmit");
        payload = await translateUserInput(payload, "es");
      }
      payload = { ...payload, submit_language: lang || "en" };
      const res = await api.post("/meetings", payload);
      toast.success(t("Meeting saved"));
      // TRACK 15.60 · clear the IDB draft once the server confirms
      // persistence, so the next visit starts clean. Do this BEFORE
      // navigate() to avoid stale-draft restoration on the return.
      try { await commit(); } catch { /* never break submit success */ }
      // TRACK 14.0-S1 Amendment A — preserve original-language strings
      // in the bilingual_records sidecar collection. Fire-and-forget;
      // a failure here must not break the user's flow.
      if (lang === "es" && payload._originals) {
        try {
          const { persistBilingualSidecar } = await import("@/lib/translateOnSubmit");
          await persistBilingualSidecar(
            "meeting",
            res.data?.id || res.data?.meeting_number || "",
            payload,
          );
        } catch { /* sidecar best-effort */ }
      }
      navigate("/thank-you", {
        state: {
          workflowKey: "meeting",
          project: payload.project_name,
          documentNumber: res.data?.doc_id || res.data?.meeting_number || res.data?.id || "",
          submittedAt: res.data?.created_at || new Date().toISOString(),
          submittedBy: payload.conducted_by || "",
          openRecordTo: !publicMode && isAdmin() && res.data?.id ? `/meetings/${res.data.id}` : undefined,
          returnTo: "/meetings",
          startAnotherTo: "/meetings/submit",
        },
        replace: true,
      });
    } catch (e) {
      console.error(e);
      toast.error(formatApiError(e, t("Could not save meeting")), { duration: 7000 });
    } finally {
      setSaving(false);
    }
  };

  // 5:30 AM iPad rule · derive a short, human hint of what's blocking Submit
  // so the sticky top button and the bottom CTA never sit silently disabled.
  const missingHint = (() => {
    if (saving) return "";
    const need = [];
    const fields = [
      ["project_name", "Project Name"],
      ["location", "Location"],
      ["meeting_date", "Date"],
      ["meeting_time", "Time"],
      ["conducted_by", "Conducted By"],
      ["topic", "Topic"],
    ];
    for (const [k, l] of fields) {
      if (!String(data[k] || "").trim()) need.push(t(l));
    }
    if (!data.conductor_signature) need.push(t("Conductor Signature"));
    if (!data.attendees || data.attendees.length === 0) need.push(t("Attendees"));
    const photoCount = (data.photos || []).length;
    if (photoCount < 2) need.push(`${t("Photos")} ${photoCount}/2`);
    if (need.length === 0) return "";
    return need.slice(0, 3).join(" · ") + (need.length > 3 ? ` +${need.length - 3}` : "");
  })();

  return (
    <FormShell
      kicker={t("MASCI · Safety Meetings")}
      title={t("Site Safety Meeting")}
      subtitle={t("Document the topic, attendees, acknowledgements, and proof in one shared meeting workflow.")}
      backLink="/"
      backLabel={t("Home")}
      draftSlot={<DraftStatusPill status={draftStatus} testId="meeting-draft-pill" />}
      widthClass="max-w-4xl"
      containerTestId="meeting-form-shell"
      stickyFooter={(
        <div className="flex items-center justify-between gap-3" data-testid="meeting-form-actions">
          <div className="hidden sm:flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-slate-500">
            {missingHint ? (
              <span data-testid="meeting-submit-missing-hint">{t("Missing")}: {missingHint}</span>
            ) : (
              <span>{t("Ready to submit · attendance and photos locked in")}</span>
            )}
          </div>
          <Button
            onClick={submit}
            disabled={saving}
            title={missingHint ? `${t("To submit, complete")}: ${missingHint}` : ""}
            className="ml-auto h-12 px-6 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900 disabled:opacity-60"
            data-testid="submit-sticky-btn"
          >
            {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
            {saving ? t("Saving…") : t("Submit Meeting")}
          </Button>
        </div>
      )}
    >
      <div className="space-y-6 pb-24" data-testid="meeting-modernized">
        <div className="mb-2">
          <div className="rounded-2xl border border-red-100 bg-white/85 p-4 shadow-sm" data-testid="meeting-form-summary">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
              {t("New Report")}
            </span>
            <div className="mt-1 flex items-center gap-2">
            <span
              className="inline-flex items-center rounded-full border border-slate-300 bg-white px-2.5 py-0.5 text-[10px] font-mono uppercase tracking-[0.18em] text-slate-600"
              data-testid="toolbox-talk-alias-chip"
            >
              {t("Also known as: Toolbox Talk")}
            </span>
            </div>
          {/* TRACK 19.13 · HelpDrawer — SINGLE coaching surface for
              Safety Meeting. Bands consolidated from HelpTipBlock
              defaults. Topic Auto Load remains untouched below. */}
            <div className="mt-3">
            <HelpDrawer
              open={helpDrawerOpen}
              onOpenChange={setHelpDrawerOpen}
              triggerLabel={t("Open help")}
              title={t("Safety Meeting · Guidance")}
              testIdPrefix="meeting-help-drawer"
              sections={[
                {
                  title: t("Why this meeting matters"),
                  body: t("Safety meetings are the field's frontline training. They document that the crew was warned, taught, and heard — before they picked up the tool. Do it right and everyone goes home."),
                },
                {
                  title: t("Who receives this"),
                  body: t("Safety, the PM, and (for high-risk topics) the safety director see every meeting. Attendance and acknowledgements become part of each attendee's training record."),
                },
                {
                  title: t("How attendance is documented"),
                  body: t("Every attendee acknowledges the topic and hazards. Their name, timestamp, and (when signed) signature become the permanent training record."),
                },
                {
                  title: t("How knowledge is retained"),
                  body: t("Pick a Knowledge Check question at the end. It's not graded — it's a quick reinforcement that gives the crew one thing to remember on the walk to their truck."),
                },
                {
                  title: t("Legal documentation"),
                  body: t("If an incident happens, this meeting record is the evidence that the crew was trained on the exact hazard. Photos, references, and acknowledgements matter — attach them."),
                },
                {
                  title: t("Common meeting mistakes"),
                  body: t("Skipping the topic-specific hazards, marking attendees without their acknowledgement, and not attaching photos of the whiteboard or job hazard reviewed. Every meeting deserves at least 2 photos."),
                },
                {
                  title: t("Supervisor best practices"),
                  body: t("Read the topic aloud. Ask two crew members to share a real example. Point at the hazard on the job. Sign the record only after every acknowledgement box is ticked."),
                },
                {
                  title: t("Crew engagement tips"),
                  body: t("Ask the newest crew member what surprised them. Ask the oldest what has almost hurt them. Real stories beat generic bullet points every time."),
                },
              ]}
            />
            </div>
          </div>
        </div>

        {/* TRACK 19.13 · ProgressRail — 6-step compact flow tracker.
            State-derived; primitive is stateless. */}
        <ProgressRail
          steps={[
            { key: "info", label: t("Info") },
            { key: "context", label: t("Context") },
            { key: "topic", label: t("Topic") },
            { key: "attendees", label: t("Attendees") },
            { key: "photos", label: t("Photos") },
            { key: "sign", label: t("Sign") },
          ]}
          currentIndex={(() => {
            if (!data.project_name?.trim() || !data.conducted_by?.trim() || !data.category) return 0;
            if (!data.crew_size) return 1;
            if (!data.topic?.trim() && !(data.hazards_reviewed?.trim())) return 2;
            if (!data.attendees || data.attendees.length === 0) return 3;
            if ((data.photos || []).length < 2) return 4;
            if (!data.conductor_signature) return 5;
            return 5;
          })()}
          testId="meeting-progress-rail"
        />

        {/* TRACK 15.60 · P0 field-trust fix — calm draft recovery prompt.
            Shown ONLY when an unsent meeting draft was found in IDB on
            mount. The operator picks Restore or Discard — we never
            silently overwrite the form. */}
        <DraftRestorePrompt
          pendingDraft={pendingDraft}
          onRestore={onRestoreDraft}
          onDiscard={onDiscardDraft}
          testId="meeting-draft-restore-prompt"
        />

        <Section number="01" title={t("Meeting Information")}>
          {/* TRACK 19.13 · HelpTipBlock default RETIRED. Consolidated
              into the HelpDrawer above. Main screen = action;
              drawer = explanation. */}
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Job")}
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
                className={inputCls}
                placeholder="e.g. I-95 Resurfacing - Phase 2"
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
                className={inputCls}
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
                  className="min-h-11 px-3 border-2 border-slate-300 hover:border-red-500 hover:text-red-700 font-bold uppercase tracking-wide text-xs"
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
                className={inputCls}
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
                value={data.meeting_date}
                onChange={(e) => set("meeting_date", e.target.value)}
                className={inputCls}
                data-testid="input-date"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Time *")}
              </Label>
              <Input
                type="time"
                value={data.meeting_time}
                onChange={(e) => set("meeting_time", e.target.value)}
                className={inputCls}
                data-testid="input-time"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Conducted By *")}
              </Label>
              <Input
                value={data.conducted_by}
                onChange={(e) => set("conducted_by", e.target.value)}
                className={inputCls}
                placeholder={t("Foreman / Supervisor")}
                data-testid="input-conducted-by"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Topic Category *")}
              </Label>
              <Select
                value={data.topic_category}
                onValueChange={(v) => set("topic_category", v)}
              >
                <SelectTrigger className={inputCls} data-testid="select-category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TOPIC_CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {t(c)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-[10px] font-mono text-slate-500 mt-1">
                {t("Auto-fills when you pick a topic below")}
              </p>
            </div>
          </div>

          {/* E1 · operational context captures (crew, shift, weather,
              subcontractor, high-risk flag). Lightweight, single-tap. */}
          {/* TRACK 19.13 · HelpTipBlock "meeting.context" RETIRED — drawer. */}
          <div
            className="mt-2 pt-6 border-t border-slate-200 grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4"
            data-testid="meeting-context-row"
          >
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Crew Size")}
              </Label>
              <Input
                type="number"
                min="0"
                inputMode="numeric"
                value={data.crew_size ?? ""}
                onChange={(e) => {
                  const v = e.target.value;
                  set("crew_size", v === "" ? null : Math.max(0, parseInt(v, 10) || 0));
                }}
                className={inputCls}
                placeholder={t("Total on crew today")}
                data-testid="input-crew-size"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Shift")}
              </Label>
              <Select value={data.shift || ""} onValueChange={(v) => set("shift", v)}>
                <SelectTrigger className={inputCls} data-testid="select-shift">
                  <SelectValue placeholder={t("Select shift")} />
                </SelectTrigger>
                <SelectContent>
                  {SHIFT_OPTIONS.map((s) => (
                    <SelectItem key={s} value={s}>
                      {lang === "es"
                        ? { Day: "Día", Swing: "Tarde", Night: "Noche" }[s]
                        : s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="sm:col-span-1 flex items-end">
              <label
                className="flex items-center gap-2 h-14 cursor-pointer select-none"
                data-testid="toggle-high-risk-label"
              >
                <input
                  type="checkbox"
                  checked={!!data.high_risk_activity}
                  onChange={(e) => set("high_risk_activity", e.target.checked)}
                  className="w-5 h-5 accent-red-700"
                  data-testid="toggle-high-risk"
                />
                <span className="text-sm font-medium text-slate-900">
                  {t("High-risk activity today")}
                </span>
              </label>
            </div>
          </div>

          {/* Weather chip row */}
          <div className="mt-4">
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Weather")}
            </Label>
            <div
              className="mt-2 flex flex-wrap gap-2"
              data-testid="meeting-weather-chips"
            >
              {WEATHER_OPTIONS.map((w) => {
                const active = (data.weather || []).includes(w.key);
                return (
                  <button
                    key={w.key}
                    type="button"
                    onClick={() => {
                      const cur = data.weather || [];
                      set(
                        "weather",
                        active
                          ? cur.filter((k) => k !== w.key)
                          : [...cur, w.key]
                      );
                    }}
                    className={
                      "px-3 py-1.5 rounded-full text-sm font-medium border transition-colors " +
                      (active
                        ? "bg-red-700 text-white border-red-700"
                        : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50")
                    }
                    data-testid={`weather-chip-${w.key}`}
                  >
                    {lang === "es" ? w.es : w.en}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Subcontractor toggle + optional name */}
          <div className="mt-4">
            <label
              className="flex items-center gap-2 cursor-pointer select-none"
              data-testid="toggle-sub-label"
            >
              <input
                type="checkbox"
                checked={!!data.subcontractor_present}
                onChange={(e) => {
                  set("subcontractor_present", e.target.checked);
                  if (!e.target.checked) set("subcontractor_name", "");
                }}
                className="w-5 h-5 accent-red-700"
                data-testid="toggle-sub"
              />
              <span className="text-sm font-medium text-slate-900">
                {t("Subcontractor crew present")}
              </span>
            </label>
            {data.subcontractor_present && (
              <Input
                value={data.subcontractor_name}
                onChange={(e) => set("subcontractor_name", e.target.value)}
                className={inputCls + " mt-2"}
                placeholder={t("Subcontractor name (optional)")}
                data-testid="input-sub-name"
              />
            )}
          </div>
        </Section>

        <Section number="02" title={t("Topic & Discussion")}>
          {/* TRACK 19.13 · HelpTipBlock "meeting.topic" RETIRED — drawer. */}
          <div className="bg-red-50 border-2 border-red-200 rounded-md p-4">
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold flex items-center gap-2">
              <span className="inline-flex w-5 h-5 items-center justify-center rounded bg-red-700 text-white text-[10px] font-black">
                1
              </span>
              {t("Pick a topic — Category & all fields below auto-fill")}
            </Label>
            <TopicPicker
              value={templateKey}
              onChange={applyTemplate}
              topics={TOPIC_LIBRARY}
              customKey={CUSTOM_TOPIC_KEY}
              placeholder={t("Search or pick a topic...")}
            />
            <p className="text-xs text-slate-600 mt-2 leading-relaxed">
              {TOPIC_LIBRARY.length}+ {t("heavy civil / highway topics with prefilled hazards, key points, references, and action items. Type to search — or choose")}{" "}
              <span className="font-bold">{t("Custom Topic")}</span> {t("to write your own.")}
            </p>
            {/* iter270 · K6 coaching strip removed — `meeting.topic` HelpTipBlock above
                this Section already delivers the WHAT-HAPPENS-first coaching with
                richer kinds (why/mistake/example/next/escalate). */}
            {/* iter269 · Sprint 2 · K7 · domain breadcrumb (shown only when a library topic is loaded) */}
            {templateKey && templateKey !== CUSTOM_TOPIC_KEY && (() => {
              const tpl = findTopic(templateKey);
              if (!tpl?.domain) return null;
              return (
                <div
                  className="mt-3 inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.22em] font-mono text-slate-500"
                  data-testid="meeting-domain-breadcrumb"
                >
                  <span>{t("Domain")}</span>
                  <span className="text-slate-900 font-bold">
                    {getDomainLabel(tpl.domain, lang)}
                  </span>
                </div>
              );
            })()}
          </div>

          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Topic / Subject *")}
            </Label>
            <Input
              value={data.topic}
              onChange={(e) => set("topic", e.target.value)}
              className={inputCls}
              placeholder="e.g. Heat Stress Prevention, Trench Safety, Silica Awareness"
              data-testid="input-topic"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Hazards Reviewed")}
            </Label>
            <Textarea
              value={data.hazards_reviewed}
              onChange={(e) => set("hazards_reviewed", e.target.value)}
              className="min-h-[100px] text-base border-2 border-slate-300"
              placeholder={t("What specific hazards were discussed?")}
              data-testid="input-hazards-reviewed"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Discussion Notes / Minutes")}
            </Label>
            {/* iter269 · Sprint 2 · K4 · visual separation of CONTEXT (incident pattern)
                from ACTION (bullets). Read-only callout · the textarea below still
                holds the full scaffold for free editing. */}
            {(() => {
              const split = splitIncidentScaffold(data.discussion_notes);
              if (!split.header || !split.pattern) return null;
              return (
                <div
                  className="mt-2 mb-2 rounded-md border-2 border-red-200 bg-red-50/60 p-3"
                  data-testid="incident-context-block"
                >
                  <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold mb-1">
                    {split.header.trim()}
                  </div>
                  <p className="text-sm text-slate-900 leading-snug whitespace-pre-wrap">
                    {split.pattern}
                  </p>
                  <div className="font-mono text-[9px] uppercase tracking-[0.22em] text-slate-500 mt-2">
                    {t("Context for the crew · the bullets below are the action drill")}
                  </div>
                </div>
              );
            })()}
            <Textarea
              value={data.discussion_notes}
              onChange={(e) => set("discussion_notes", e.target.value)}
              className="min-h-[140px] text-base border-2 border-slate-300"
              placeholder={t("Key points, questions, lessons learned...")}
              data-testid="input-discussion-notes"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("References Cited")}
            </Label>
            <Textarea
              value={data.references_cited}
              onChange={(e) => set("references_cited", e.target.value)}
              className="min-h-[80px] text-base border-2 border-slate-300"
              placeholder={t("OSHA standards, SDS reviewed, site procedures...")}
              data-testid="input-references"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Action Items / Follow-Up")}
            </Label>
            <Textarea
              value={data.action_items}
              onChange={(e) => set("action_items", e.target.value)}
              className="min-h-[80px] text-base border-2 border-slate-300"
              placeholder={t("What needs to happen next? Who owns it?")}
              data-testid="input-action-items"
            />
          </div>
        </Section>

        <Section number="03" title={t("Attendees")}>
          {/* iter270 · Section 03 attendees coaching */}
          {/* TRACK 19.13 · HelpTipBlock "meeting.attendees" RETIRED — drawer. */}
          <p className="text-sm text-slate-600">
            {t("Add every person who attended. Each attendee signs to confirm they were present and understood the topic.")}
          </p>
          {data.attendees.map((a, i) => (
            <div
              key={i}
              className="border border-slate-200 rounded-md p-4 space-y-3"
              data-testid={`attendee-${i}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold">
                  {t("Attendee")} {i + 1}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeAttendee(i)}
                  className="min-h-11 px-3 text-slate-500 hover:text-red-600"
                  data-testid={`attendee-remove-${i}`}
                >
                  <X className="w-4 h-4 mr-1" /> {t("Remove")}
                </Button>
              </div>

              {/* SAFETY-MEETING-CERT · MASCI vs Non-MASCI / Subcontractor toggle */}
              <div className="flex items-center gap-3 text-xs">
                <label className="inline-flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!!a.non_masci}
                    onChange={(e) => {
                      const non = e.target.checked;
                      updateAttendee(i, "non_masci", non);
                      if (non) {
                        // Clear MASCI binding so HR roster is not polluted
                        updateAttendee(i, "employee_id", "");
                        // Don't auto-fill company; user must type it.
                        if (a.company === "MASCI") updateAttendee(i, "company", "");
                        // Track 15.73 Slice 2 · identity flags follow toggle.
                        updateAttendee(i, "attendee_type", "subcontractor");
                        updateAttendee(i, "source", "subcontractor_directory");
                        updateAttendee(i, "is_masci_employee", false);
                        updateAttendee(i, "is_subcontractor", true);
                        updateAttendee(i, "is_manual", false);
                      } else {
                        // Returning to MASCI path — default company
                        if (!a.company) updateAttendee(i, "company", "MASCI");
                        // Track 15.73 Slice 2 · revert identity flags;
                        // backend re-derives the final classification.
                        updateAttendee(i, "attendee_type", a.employee_id ? "employee" : "manual");
                        updateAttendee(i, "source", a.employee_id ? "employee_master" : "manual");
                        updateAttendee(i, "is_masci_employee", !!a.employee_id);
                        updateAttendee(i, "is_subcontractor", false);
                        updateAttendee(i, "is_manual", !a.employee_id);
                      }
                    }}
                    data-testid={`attendee-nonmasci-${i}`}
                  />
                  <span className="font-mono uppercase tracking-wide text-slate-600">
                    {t("Non-OurCo / Subcontractor")}
                  </span>
                </label>
              </div>

              {a.non_masci ? (
                <Input
                  value={a.name}
                  onChange={(e) => updateAttendee(i, "name", e.target.value)}
                  placeholder={t("Type subcontractor's full name")}
                  className={inputCls}
                  data-testid={`attendee-name-${i}`}
                />
              ) : (
                <EmployeeCombo
                  value={a.name}
                  onChange={(v) => {
                    updateAttendee(i, "name", v);
                    if (a.employee_id && v !== a.name) {
                      updateAttendee(i, "employee_id", "");
                      // Track 15.73 Slice 2 · clearing the identity drops
                      // the row back to manual until the user picks
                      // again from the roster.
                      updateAttendee(i, "attendee_type", "manual");
                      updateAttendee(i, "source", "manual");
                      updateAttendee(i, "is_masci_employee", false);
                      updateAttendee(i, "is_manual", true);
                    }
                  }}
                  onPick={(emp) => {
                    // iter362 + SAFETY-MEETING-CERT · capture canonical id +
                    // auto-fill company (MASCI) and trade from HR record.
                    // Track 15.73 Slice 2 · also set canonical identity
                    // flags so downstream analytics can classify without
                    // re-deriving. Backend normalize_meeting_attendees
                    // re-asserts these at submit time.
                    if (emp.id || emp.employee_id) {
                      updateAttendee(i, "employee_id", emp.id || emp.employee_id);
                    }
                    updateAttendee(i, "company", "MASCI");
                    const trade = emp.trade || emp.role || emp.position || emp.job_title || "";
                    if (trade) updateAttendee(i, "trade", trade);
                    updateAttendee(i, "attendee_type", "employee");
                    updateAttendee(i, "source", "employee_master");
                    updateAttendee(i, "is_masci_employee", true);
                    updateAttendee(i, "is_subcontractor", false);
                    updateAttendee(i, "is_manual", false);
                  }}
                  placeholder={t("Type or pick an employee…")}
                  testId={`attendee-name-${i}`}
                />
              )}
              {(a.name || "").trim() && !a.non_masci ? (
                a.employee_id ? (
                  <div className="text-[10px] text-emerald-700 font-mono inline-flex items-center gap-1" data-testid={`attendee-linked-${i}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    {t("Linked to roster")}
                  </div>
                ) : (
                  <div className="text-[10px] text-amber-700 font-mono inline-flex items-center gap-1" data-testid={`attendee-unlinked-${i}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
                    {t("Not in roster — needs roster follow-up")}
                  </div>
                )
              ) : null}

              {/* SAFETY-MEETING-CERT · Company + Trade fields */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label className="text-xs font-mono uppercase tracking-wide text-slate-600">
                    {t("Company")} *
                  </Label>
                  <Input
                    value={a.company || ""}
                    onChange={(e) => updateAttendee(i, "company", e.target.value)}
                    disabled={!a.non_masci && !!a.employee_id}
                    placeholder={a.non_masci ? t("Subcontractor company") : "MASCI"}
                    className={inputCls}
                    data-testid={`attendee-company-${i}`}
                  />
                </div>
                <div>
                  <Label className="text-xs font-mono uppercase tracking-wide text-slate-600">
                    {t("Trade / Role")}
                  </Label>
                  <Input
                    value={a.trade || ""}
                    onChange={(e) => updateAttendee(i, "trade", e.target.value)}
                    placeholder={t("e.g. Foreman, Laborer, Pipe Layer")}
                    className={inputCls}
                    data-testid={`attendee-trade-${i}`}
                  />
                </div>
              </div>

              <BilingualConsent variant="meeting" />
              <SignaturePad
                value={a.signature}
                onChange={(v) => updateAttendee(i, "signature", v)}
                label={t("Signature") + " *"}
                testId={`attendee-sig-${i}`}
              />

              {/* SAFETY-MEETING-CERT · explicit acknowledgement */}
              <label className="flex items-start gap-2 cursor-pointer p-2 rounded-md border border-slate-200 bg-slate-50">
                <input
                  type="checkbox"
                  checked={!!a.acknowledged}
                  onChange={(e) => {
                    const v = e.target.checked;
                    updateAttendee(i, "acknowledged", v);
                    updateAttendee(i, "acknowledged_at", v ? new Date().toISOString() : "");
                  }}
                  className="mt-0.5 w-4 h-4"
                  data-testid={`attendee-ack-${i}`}
                />
                <span className="text-sm text-slate-700">
                  <strong>{t("I acknowledge")}</strong>{" — "}
                  {t("I was present, understood the topic and the hazards, and agree to the safe-work commitments discussed.")}
                </span>
              </label>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            onClick={addAttendee}
            className="w-full h-12 border-2 border-dashed border-slate-400 hover:border-red-700 hover:text-red-700 font-bold uppercase tracking-wide text-sm"
            data-testid="attendee-add"
          >
            <UserPlus className="w-4 h-4 mr-2" /> {t("Add Attendee")}
          </Button>
          {/* TRACK 15.46 · FR-07 · Bulk multi-select from the certified
              employees roster. Removes ~5-10 clicks per meeting for
              typical 10-person crews. */}
          <AttendeeBulkAddDialog
            existing={data.attendees}
            onAdd={(additions) =>
              setData((p) => ({
                ...p,
                attendees: [...p.attendees, ...additions],
              }))
            }
          />
        </Section>

        <Section number="04" title={t("Photos")}>
          {/* TRACK 19.13 · HelpTipBlock "meeting.photos" RETIRED — drawer. */}
          <p className="text-xs text-slate-600 -mt-2 mb-2">
            {t("Photos: ")}
            <span
              className={
                (data.photos || []).length >= 2
                  ? "text-emerald-700 font-bold"
                  : "text-red-700 font-bold"
              }
              data-testid="meeting-photo-count"
            >
              {(data.photos || []).length}
            </span>{" "}
            / <span className="font-mono">{t("min 2 required")}</span>
          </p>
          <PhotoUpload
            photos={data.photos}
            onChange={(photos) => set("photos", photos)}
          />
        </Section>

        <Section number="05" title={t("Conductor Signature")}>
          {/* TRACK 19.13 · HelpTipBlock "meeting.signoff" RETIRED — drawer. */}
          <p className="text-sm text-slate-600">
            {t("The person who ran the meeting signs to confirm the record is accurate.")}
          </p>
          {/* D1 · conducted_by is captured in Section 01. Show read-only
              here so foreman doesn't retype on mobile. */}
          <div
            className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3"
            data-testid="conducted-by-readonly"
          >
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
              {t("Conducted By")}
            </div>
            <div className="mt-1 text-base font-medium text-slate-900">
              {data.conducted_by || (
                <span className="italic text-slate-400">
                  {t("— enter in Section 01 —")}
                </span>
              )}
            </div>
          </div>
          <BilingualConsent variant="meeting" />
          <SignaturePad
            value={data.conductor_signature}
            onChange={(v) => set("conductor_signature", v)}
            label={t("Conductor Signature") + " *"}
            testId="conductor-sig"
          />
        </Section>

        {/* TRACK 19.13 · Review & Submit — SubmitReviewPanel surfaces
            attendance + photos + topic + downstream commitment before
            the conductor signs and submits. Non-technical, operational
            language. */}
        <FormSection
          number="R"
          title={t("Review & Submit")}
          subtitle={t("Confirm the meeting summary before you submit. What happens next is listed below.")}
          testId="meeting-review-section"
        >
          <SubmitReviewPanel
            passCount={(data.attendees || []).filter((a) => a && a.acknowledged).length}
            failCount={(data.attendees || []).filter((a) => a && !a.acknowledged).length}
            naCount={(data.photos || []).length}
            outOfService={false}
            extraSummaryRows={[
              data.topic?.trim()
                ? t("Topic: ") + data.topic
                : t("Topic pending."),
              (data.attendees || []).length > 0
                ? `${(data.attendees || []).length} ${t("attendees on the record")}`
                : t("No attendees recorded yet."),
              (data.photos || []).length >= 2
                ? `${(data.photos || []).length} ${t("photos attached")}`
                : t("At least 2 photos required."),
              data.conductor_signature
                ? t("Conductor signature captured.")
                : t("Conductor signature pending."),
            ]}
            commitments={[
              { label: t("Attendance will be recorded in the training history.") },
              { label: t("Safety and the PM will be notified per project routing.") },
              { label: t("Each attendee's training history is updated.") },
              { label: t("The meeting is archived for legal and DOT/OSHA audit purposes.") },
              { label: t("A PDF record is generated for downstream distribution.") },
              { label: t("A permanent audit record is created.") },
            ]}
            testId="meeting-review-panel"
          />
        </FormSection>

        <div className="pt-4 rounded-xl border border-red-100 bg-red-50/60 px-4 py-3">
          {missingHint && (
            <p
              data-testid="meeting-submit-missing-hint-bottom"
              className="text-xs text-red-700 font-bold mb-2 font-mono uppercase tracking-[0.15em]"
            >
              {t("To submit, complete")}: {missingHint}
            </p>
          )}
          <p className="text-xs text-slate-500 font-mono uppercase tracking-[0.2em]">
            {t("Submit from the sticky action bar once every attendee, acknowledgement, and photo is complete.")}
          </p>
        </div>
      </div>
    </FormShell>
  );
}
