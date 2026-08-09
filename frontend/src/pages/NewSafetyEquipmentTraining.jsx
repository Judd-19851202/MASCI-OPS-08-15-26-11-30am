import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Save,
  Loader2,
  GraduationCap,
  Plus,
  Trash2,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import EmployeeRosterField from "@/components/EmployeeRosterField";
import { HelpTipBlock } from "@/components/HelpTip";
import { JobPicker } from "@/components/JobPicker";
import { SignaturePad } from "@/components/SignaturePad";
import { SearchableSelect } from "@/components/SearchableSelect";
import FormShell from "@/components/FormShell";
import { useT, getLang } from "@/lib/i18n";
import { api } from "@/lib/api";
import { isSafetyForms } from "@/lib/safetyFormsAuth";
import { isSafety } from "@/lib/safetyAuth";
import { isAdmin } from "@/lib/adminAuth";
import {
  ITEM_TYPES,
  TRAINING_TYPES,
  TRAINING_TOPICS,
  blankTrainingItem,
  buildTrainingDefaults,
  rememberSupervisor,
} from "@/lib/safetyFormsSchema";
import { toast } from "sonner";
import {
  useFormDraft,
  getDeviceScopedActorId,
  DraftStatusPill,
  DraftRestorePrompt,
  getActivePublicDraftSession,
  ensureActivePublicDraftSession,
  clearActivePublicDraftSession,
  buildPublicDraftSessionScope,
  hasMeaningfulPublicDraft,
} from "@/lib/resiliency";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700 focus-visible:ring-offset-2";
const TRAINING_FORM_BASE = "safety-equipment-training";

export default function NewSafetyEquipmentTraining() {
  const { t, lang } = useT();
  const navigate = useNavigate();
  const [data, setData] = useState(buildTrainingDefaults());
  const [saving, setSaving] = useState(false);
  const actorId = React.useMemo(() => getDeviceScopedActorId(), []);
  const [draftSessionId, setDraftSessionId] = React.useState(() => getActivePublicDraftSession(TRAINING_FORM_BASE));
  const draftPayload = React.useMemo(() => ({
    ...data,
    draft_session_id: draftSessionId || "",
  }), [data, draftSessionId]);
  const draftScope = React.useMemo(() => buildPublicDraftSessionScope(draftSessionId), [draftSessionId]);
  const {
    pendingDraft, draftStatus, restore, discard, commit,
  } = useFormDraft(TRAINING_FORM_BASE, draftPayload, actorId, {
    scope: draftScope,
    publicAnonymous: true,
  });

  React.useEffect(() => {
    if (draftSessionId) return;
    if (!hasMeaningfulPublicDraft(draftPayload, ["draft_session_id", "training_date"])) return;
    setDraftSessionId(ensureActivePublicDraftSession(TRAINING_FORM_BASE));
  }, [draftPayload, draftSessionId]);

  const onRestoreDraft = React.useCallback(() => {
    const restored = restore();
    if (!restored) return;
    const restoredSessionId = ensureActivePublicDraftSession(TRAINING_FORM_BASE, restored.draft_session_id || draftSessionId);
    const { draft_session_id: _draftSessionId, ...next } = restored;
    setDraftSessionId(restoredSessionId);
    setData(next);
    toast.success(t("Draft restored"));
  }, [restore, t, draftSessionId]);

  const onDiscardDraft = React.useCallback(async () => {
    await discard();
    clearActivePublicDraftSession(TRAINING_FORM_BASE, draftSessionId);
    setDraftSessionId("");
    toast.message(t("Draft discarded"));
  }, [discard, t, draftSessionId]);

  // iter332 · Safety Portal Form-Entry continuity. See sibling page.
  const fromRecords = (typeof window !== "undefined" &&
    new URLSearchParams(window.location.search).get("from") === "records");
  const backPath = fromRecords && authed ? "/safety-portal/forms-records" : "/safety/forms";

  // iter323 · Safety Forms ownership — Safety Portal + Admin + legacy.
  const authed = isSafety() || isAdmin() || isSafetyForms();

  const update = (patch) => setData((d) => ({ ...d, ...patch }));

  const applyJob = (job) => {
    update({
      project_name: job?.project_name || "",
      project_number: job?.project_number || "",
    });
  };

  const updateItem = (idx, patch) => {
    setData((d) => ({
      ...d,
      items: d.items.map((it, i) => (i === idx ? { ...it, ...patch } : it)),
    }));
  };

  const addItem = () => setData((d) => ({ ...d, items: [...d.items, blankTrainingItem()] }));
  const removeItem = (idx) =>
    setData((d) => ({ ...d, items: d.items.filter((_, i) => i !== idx) }));

  const toggleTopic = (key) => {
    setData((d) => {
      const has = d.topics.includes(key);
      return { ...d, topics: has ? d.topics.filter((k) => k !== key) : [...d.topics, key] };
    });
  };

  async function onSubmit(e) {
    e.preventDefault();
    if (saving) return;
    const fails = [];
    if (!data.employee_name.trim()) fails.push(t("Employee name required"));
    if (!data.instructor_name.trim()) fails.push(t("Instructor name required"));
    if (!data.training_date) fails.push(t("Training date required"));
    if (!data.items.length) fails.push(t("Add at least one equipment item"));
    for (const it of data.items) {
      if (!it.equipment_type) fails.push(t("Each item needs equipment type"));
      if (it.equipment_type === "Other" && !(it.equipment_type_other || "").trim())
        fails.push(t("Specify the 'Other' equipment"));
      if (!it.training_type) fails.push(t("Each item needs training type"));
    }
    if (data.topics.length === 0) fails.push(t("Select at least one topic covered"));
    if (data.topics.includes("other") && !(data.topic_other || "").trim())
      fails.push(t("Specify 'Other' topic"));
    if (!data.acknowledgment) fails.push(t("Acknowledgment required"));
    if (!data.employee_signature) fails.push(t("Employee signature required"));
    if (!data.instructor_signature) fails.push(t("Instructor signature required"));
    if (fails.length) {
      toast.error(fails[0]);
      return;
    }

    setSaving(true);
    try {
      rememberSupervisor(data.instructor_name);
      let payload = { ...data, lang };
      const submitLang = getLang();
      if (submitLang === "es") {
        toast.info(t("Translating to English…"));
        const { translateUserInput } = await import("@/lib/translateOnSubmit");
        payload = await translateUserInput(payload, "es");
      }
      payload = { ...payload, submit_language: submitLang || "en" };
      const res = await api.post("/safety-forms/equipment-trainings", payload);
      await commit();
      clearActivePublicDraftSession(TRAINING_FORM_BASE, draftSessionId);
      setDraftSessionId("");
      // TRACK 14.0-S1 — Preserve original Spanish in the bilingual sidecar.
      if (submitLang === "es" && res?.data?.id) {
        const { persistBilingualSidecar } = await import("@/lib/translateOnSubmit");
        await persistBilingualSidecar("safety_form", res.data.id, payload);
      }
      toast.success(t("Training filed · PDF emailed to Safety · visible in Safety Forms Records"));
      navigate("/thank-you", {
        state: {
          workflowKey: "safety-training",
          project: data.project_name || data.project_number || "",
          documentNumber: res.data?.doc_id || res.data?.id || "",
          submittedAt: new Date().toISOString(),
          submittedBy: data.instructor_name || "",
          contextItems: [{ label: "Employee", value: data.employee_name || "" }],
          openRecordTo: authed && res.data?.id ? `/safety/forms/equipment-training/${res.data.id}` : undefined,
          returnTo: fromRecords && authed ? "/safety-portal/forms-records" : "/safety/forms",
          startAnotherTo: "/safety/forms/equipment-training/new",
        },
      });
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not submit"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <FormShell
      kicker={t("MASCI · Safety Forms")}
      title={t("Equipment Use & Care Training Documentation")}
      subtitle={t("Document operator training, topics covered, signatures, and the equipment involved in one shared safety workflow.")}
      backLink={backPath}
      backLabel={fromRecords && authed ? t("Back to Review") : t("Safety Forms")}
      widthClass="max-w-4xl"
      containerTestId="trn-form-shell"
      draftSlot={<DraftStatusPill status={draftStatus} testId="trn-draft-pill" />}
      stickyFooter={(
        <div className="flex justify-between items-center shadow-none gap-3" data-testid="trn-form-actions">
          <div className="text-xs font-mono text-slate-600 truncate">
            <ShieldCheck className="w-4 h-4 inline-block mr-1 text-amber-700" />
            {t("Auto-emails Safety dept on submit")}
          </div>
          <Button
            type="submit"
            form="trn-form"
            disabled={saving}
            className="bg-amber-600 hover:bg-amber-700 h-12 px-6 font-bold uppercase tracking-wide"
            data-testid="trn-submit"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Submitting…")}
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" /> {t("Submit & Email PDF")}
              </>
            )}
          </Button>
        </div>
      )}
    >
      {pendingDraft ? (
        <DraftRestorePrompt
          pendingDraft={pendingDraft}
          onRestore={onRestoreDraft}
          onDiscard={onDiscardDraft}
          label={pendingDraft.project_name || pendingDraft.project_number || pendingDraft.employee_name || t("Safety equipment training")}
          updatedAt={pendingDraft.savedAt}
          testId="trn-draft-restore"
        />
      ) : null}
      <div className="mb-6 flex items-start gap-3 rounded-2xl border border-amber-100 bg-white/85 p-4 shadow-sm" data-testid="trn-form-summary">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-amber-600 text-white shrink-0">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-amber-700 font-bold">
              {t("Safety Forms")}
            </span>
            <p className="mt-1 text-sm text-slate-600" data-testid="trn-form-intro">
              {t("Capture who was trained, what equipment was covered, and how the safety expectations were acknowledged.")}
            </p>
          </div>
        </div>

        <form id="trn-form" onSubmit={onSubmit} className="space-y-5" data-testid="trn-form">
          {/* concise workflow coaching */}
          <HelpTipBlock formKey="equipment-training" className="mb-3" showCounter />
          <Section title={t("Employee")}>
            <Row>
              <Field label={t("Employee Name")} required>
                <EmployeeRosterField
                  value={{
                    id: data.employee_id || "",
                    name: data.employee_name || "",
                    linked: !!data.employee_id,
                  }}
                  onChange={({ id, name }) => {
                    update({ employee_name: name, employee_id: id });
                  }}
                  label=""
                  placeholder={t("Search the roster by employee name")}
                  required
                  testId="trn-employee-roster"
                />
              </Field>
            </Row>
            <Row>
              <Field label={t("Position")}>
                <Input
                  className={inputCls}
                  value={data.position}
                  onChange={(e) => update({ position: e.target.value })}
                  data-testid="trn-position"
                />
              </Field>
              <Field label={t("Project")}>
                <JobPicker
                  projectName={data.project_name}
                  projectNumber={data.project_number}
                  publicFallback
                  onSelect={applyJob}
                />
              </Field>
            </Row>
          </Section>

          <Section title={t("Training Information")}>
            <HelpTipBlock formKey="equipment-training.context" className="mb-3" />
            <Row>
              <Field label={t("Training Date")} required>
                <Input
                  type="date"
                  className={inputCls}
                  value={data.training_date}
                  onChange={(e) => update({ training_date: e.target.value })}
                  data-testid="trn-date"
                />
              </Field>
              <Field label={t("Instructor Name")} required>
                <Input
                  className={inputCls}
                  value={data.instructor_name}
                  onChange={(e) => update({ instructor_name: e.target.value })}
                  data-testid="trn-instructor"
                />
              </Field>
            </Row>
            <Field label={t("Training Location")}>
              <Input
                className={inputCls}
                value={data.training_location}
                onChange={(e) => update({ training_location: e.target.value })}
                data-testid="trn-location"
              />
            </Field>
          </Section>

          <Section title={t("Equipment Trained")} desc={t("Add every piece of equipment covered in this session.")}>
            <div className="space-y-3">
              {data.items.map((it, idx) => {
                const isOther = it.equipment_type === "Other";
                return (
                  <div
                    key={idx}
                    className="border border-slate-200 rounded-md p-3 bg-slate-50"
                    data-testid={`trn-item-${idx}`}
                  >
                    <div className="grid grid-cols-1 sm:grid-cols-12 gap-2 items-end">
                      <div className="lg:col-span-3">
                        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                          {t("Equipment")}
                        </Label>
                        <SearchableSelect
                          value={it.equipment_type}
                          onChange={(v) => updateItem(idx, { equipment_type: v })}
                          options={ITEM_TYPES}
                          placeholder={t("Select equipment")}
                          searchPlaceholder={t("Type to filter…")}
                          testId={`trn-item-${idx}-type`}
                        />
                      </div>
                      {isOther && (
                        <div className="lg:col-span-3">
                          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                            {t("Specify Other")}
                          </Label>
                          <Input
                            className={inputCls}
                            value={it.equipment_type_other}
                            onChange={(e) => updateItem(idx, { equipment_type_other: e.target.value })}
                            data-testid={`trn-item-${idx}-other`}
                          />
                        </div>
                      )}
                      <div className={isOther ? "lg:col-span-3" : "sm:col-span-4"}>
                        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                          {t("Description")}
                        </Label>
                        <Input
                          className={inputCls}
                          value={it.description}
                          onChange={(e) => updateItem(idx, { description: e.target.value })}
                          data-testid={`trn-item-${idx}-desc`}
                        />
                      </div>
                      <div className="lg:col-span-3">
                        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                          {t("Training Type")}
                        </Label>
                        <select
                          value={it.training_type}
                          onChange={(e) => updateItem(idx, { training_type: e.target.value })}
                          className="w-full h-12 border-2 border-slate-300 rounded px-2 text-base"
                          data-testid={`trn-item-${idx}-tt`}
                        >
                          {TRAINING_TYPES.map((x) => (
                            <option key={x} value={x}>{t(x)}</option>
                          ))}
                        </select>
                      </div>
                      <div className={isOther ? "sm:col-span-12 sm:col-start-1" : "lg:col-span-2"}>
                        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                          {t("Mfr / Model")}
                        </Label>
                        <Input
                          className={inputCls}
                          value={it.manufacturer_model}
                          onChange={(e) => updateItem(idx, { manufacturer_model: e.target.value })}
                          data-testid={`trn-item-${idx}-mfr`}
                        />
                      </div>
                    </div>
                    <div className="mt-2">
                      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                        {t("Notes")}
                      </Label>
                      <Textarea
                        className="border-2 border-slate-300 min-h-[60px]"
                        value={it.notes}
                        onChange={(e) => updateItem(idx, { notes: e.target.value })}
                        data-testid={`trn-item-${idx}-notes`}
                      />
                    </div>
                    {data.items.length > 1 && (
                      <div className="flex justify-end mt-2 pt-2 border-t border-slate-200">
                        <button
                          type="button"
                          onClick={() => removeItem(idx)}
                          className="inline-flex items-center gap-1 text-xs font-bold text-red-700 hover:text-red-900 uppercase tracking-wide"
                          data-testid={`trn-item-${idx}-remove`}
                        >
                          <Trash2 className="w-3.5 h-3.5" /> {t("Remove")}
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <div className="flex items-center justify-start mt-3">
              <Button
                type="button"
                variant="outline"
                onClick={addItem}
                className="h-10 border-2 border-slate-300 hover:border-amber-600 hover:text-amber-700 font-bold uppercase tracking-wide text-xs"
                data-testid="trn-add-item"
              >
                <Plus className="w-4 h-4 mr-1" /> {t("Add Equipment")}
              </Button>
            </div>
          </Section>

          <Section title={t("Topics Covered")} desc={t("Select every topic discussed during training.")}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
              {TRAINING_TOPICS.map((tp) => {
                const checked = data.topics.includes(tp.key);
                return (
                  <label
                    key={tp.key}
                    className={`flex items-center gap-2 px-3 py-2 border-2 rounded cursor-pointer ${
                      checked ? "border-amber-600 bg-amber-50" : "border-slate-200 bg-white"
                    }`}
                    data-testid={`trn-topic-${tp.key}`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleTopic(tp.key)}
                      className="w-4 h-4 accent-amber-600"
                    />
                    <span className="text-sm font-medium text-slate-900">{t(tp.label)}</span>
                  </label>
                );
              })}
            </div>
            {data.topics.includes("other") && (
              <div className="mt-3">
                <Field label={t("Specify Other Topic")} required>
                  <Input
                    className={inputCls}
                    value={data.topic_other}
                    onChange={(e) => update({ topic_other: e.target.value })}
                    data-testid="trn-topic-other"
                  />
                </Field>
              </div>
            )}
          </Section>

          <Section title={t("Acknowledgment")}>
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={data.acknowledgment}
                onChange={(e) => update({ acknowledgment: e.target.checked })}
                className="w-5 h-5 mt-0.5 accent-red-700"
                data-testid="trn-ack"
              />
              <span className="text-sm font-bold text-slate-900 leading-snug">
                {t("I acknowledge that I have received training on the equipment listed above and understand proper use, inspection, and safety requirements.")}
              </span>
            </label>
          </Section>

          {/* Optional employee email for CC */}
          <Section
            title={t("Email a Copy to Employee (optional)")}
            desc={t("If provided, the employee will receive a copy of the signed PDF along with the Safety Department.")}
          >
            <Field label={t("Employee Email")}>
              <Input
                type="email"
                inputMode="email"
                autoComplete="off"
                placeholder="name@example.com"
                className={inputCls}
                value={data.employee_email}
                onChange={(e) => update({ employee_email: e.target.value })}
                data-testid="trn-employee-email"
              />
            </Field>
          </Section>

          <Section title={t("Signatures")}>
            <HelpTipBlock formKey="equipment-training.signatures" className="mb-3" />
            <Field label={t("Employee Signature")} required>
              <SignaturePad
                value={data.employee_signature}
                onChange={(v) => update({ employee_signature: v })}
              />
            </Field>
            <Field label={t("Instructor Signature")} required>
              <SignaturePad
                value={data.instructor_signature}
                onChange={(v) => update({ instructor_signature: v })}
              />
            </Field>
          </Section>

          <div className="rounded-xl border border-amber-100 bg-amber-50/60 px-4 py-3 text-xs font-mono text-slate-600" data-testid="trn-submit-note">
            <ShieldCheck className="w-4 h-4 inline-block mr-1 text-amber-700" />
            {t("Safety receives the signed PDF automatically after submission.")}
          </div>
        </form>
    </FormShell>
  );
}

function Section({ title, children, desc }) {
  return (
    <section className="bg-white border border-slate-200 rounded-md p-4 sm:p-5">
      <h2 className="font-display text-lg sm:text-xl font-black text-slate-900 mb-1">{title}</h2>
      {desc && <p className="text-xs text-slate-500 mb-3">{desc}</p>}
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function Row({ children }) {
  return <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">{children}</div>;
}

function Field({ label, children, required }) {
  return (
    <div>
      <Label className="block font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1">
        {label} {required && <span className="text-red-700">*</span>}
      </Label>
      {children}
    </div>
  );
}
