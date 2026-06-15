import React, { useEffect, useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import {
  ArrowLeft,
  Save,
  Loader2,
  HardHat,
  Plus,
  Trash2,
  MapPin,
  ShieldCheck,
  Camera,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import EmployeeRosterField from "@/components/EmployeeRosterField";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { HelpTipBlock } from "@/components/HelpTip";
import { JobPicker } from "@/components/JobPicker";
import { SignaturePad } from "@/components/SignaturePad";
import { PhotoUpload } from "@/components/PhotoUpload";
import { SearchableSelect } from "@/components/SearchableSelect";
import { useT, getLang } from "@/lib/i18n";
import { api } from "@/lib/api";
import { isSafetyForms } from "@/lib/safetyFormsAuth";
import { isSafety } from "@/lib/safetyAuth";
import { isAdmin } from "@/lib/adminAuth";
import {
  ITEM_TYPES,
  CONDITIONS,
  ISSUANCE_LEGAL,
  ISSUANCE_RESPONSIBILITY,
  PRICE_BOOK,
  isUnitValueLocked,
  resolveUnitValue,
  blankIssuanceItem,
  buildIssuanceDefaults,
  rememberSupervisor,
  totalIssuanceValue,
  fmtMoney,
} from "@/lib/safetyFormsSchema";
import {
  getCurrentPosition,
  reverseGeocode,
  formatCoords,
} from "@/lib/geolocation";
import { toast } from "sonner";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700 focus-visible:ring-offset-2";

export default function NewSafetyEquipmentIssuance() {
  const { t, lang } = useT();
  const navigate = useNavigate();
  const [data, setData] = useState(buildIssuanceDefaults());
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const [employees, setEmployees] = useState([]);

  // iter332 · Safety Portal Form-Entry continuity. When the user starts
  // this form from the Safety Portal Records review surface, we honor
  // `?from=records` so Back + post-submit navigation return them to the
  // review surface (closing the workflow loop: review → start → submit
  // → see new record in review).
  const fromRecords = (typeof window !== "undefined" &&
    new URLSearchParams(window.location.search).get("from") === "records");
  const backPath = fromRecords ? "/safety-portal/forms-records" : "/safety/forms";

  // iter323 · Safety Forms ownership — Safety Portal + Admin + legacy.
  const authed = isSafety() || isAdmin() || isSafetyForms();

  useEffect(() => {
    if (!authed) return;
    api
      .get("/employees")
      .then((r) => setEmployees(r.data?.items || r.data || []))
      .catch(() => setEmployees([]));
  }, [authed]);

  if (!authed) {
    return <Navigate to="/safety-portal/login?from=safety-forms" replace />;
  }

  // When the form-level condition changes, re-apply the price book to
  // every item so locked values snap to the catalog price (or unlock).
  const update = (patch) => {
    setData((d) => {
      const next = { ...d, ...patch };
      if ("condition" in patch) {
        next.items = (d.items || []).map((it) => ({
          ...it,
          unit_value: resolveUnitValue(it.item_type, next.condition, it.unit_value),
        }));
      }
      return next;
    });
  };

  const applyJob = (job) => {
    update({
      project_name: job?.project_name || "",
      project_number: job?.project_number || "",
      location: job?.location || data.location,
    });
  };

  const useGps = async () => {
    setLocating(true);
    try {
      const pos = await getCurrentPosition();
      const txt = await reverseGeocode(pos);
      update({
        location: txt || formatCoords(pos.coords.latitude, pos.coords.longitude),
      });
    } catch (e) {
      toast.error(e?.message || t("Could not get GPS location"));
    } finally {
      setLocating(false);
    }
  };

  // When item_type changes, snap unit_value to the price book if the
  // current condition locks it; otherwise leave the user's value alone.
  const updateItem = (idx, patch) => {
    setData((d) => ({
      ...d,
      items: d.items.map((it, i) => {
        if (i !== idx) return it;
        const merged = { ...it, ...patch };
        if ("item_type" in patch) {
          // Switching to a price-book item under a locked condition →
          // overwrite. Switching to "Other" → drop to 0 so the field is
          // visibly empty for manual entry.
          if (isUnitValueLocked(merged.item_type, d.condition)) {
            merged.unit_value = PRICE_BOOK[merged.item_type];
          } else if (merged.item_type === "Other") {
            merged.unit_value = 0;
          }
        }
        return merged;
      }),
    }));
  };

  const addItem = () => setData((d) => ({ ...d, items: [...d.items, blankIssuanceItem()] }));
  const removeItem = (idx) =>
    setData((d) => ({ ...d, items: d.items.filter((_, i) => i !== idx) }));

  const total = totalIssuanceValue(data.items);

  async function onSubmit(e) {
    e.preventDefault();
    if (saving) return;
    const fails = [];
    if (!data.employee_name.trim()) fails.push(t("Employee name required"));
    if (!data.issued_by.trim()) fails.push(t("Issued By required"));
    if (!data.items.length) fails.push(t("Add at least one item"));
    for (const it of data.items) {
      if (!it.item_type) fails.push(t("Each item needs a type"));
      if (it.item_type === "Other" && !(it.item_type_other || "").trim())
        fails.push(t("Specify the 'Other' item"));
      if ((parseFloat(it.quantity) || 0) <= 0) fails.push(t("Quantity must be > 0"));
    }
    if ((data.condition || "").toLowerCase() === "damaged" && !(data.condition_note || "").trim()) {
      fails.push(t("Damage note required when condition is Damaged"));
    }
    if (data.photos.length < 1) fails.push(t("At least 1 photo required"));
    if (!data.acknowledgment) fails.push(t("You must acknowledge the terms"));
    if (!data.employee_signature) fails.push(t("Employee signature required"));
    if (!data.supervisor_signature) fails.push(t("Supervisor signature required"));
    if (fails.length) {
      toast.error(fails[0]);
      return;
    }

    setSaving(true);
    try {
      rememberSupervisor(data.issued_by);
      let payload = { ...data, lang };
      // Match the rest of the Hub: any free-text typed in Spanish is
      // auto-translated back to English so the office records stay
      // canonical. Signatures, photos, numerics, and price-book item
      // names are skipped by the walker. The original language is
      // preserved as `submit_language` for the audit trail.
      const submitLang = getLang();
      if (submitLang === "es") {
        toast.info(t("Translating to English…"));
        const { translateUserInput } = await import("@/lib/translateOnSubmit");
        payload = await translateUserInput(payload, "es");
      }
      payload = { ...payload, submit_language: submitLang || "en" };
      const res = await api.post("/safety-forms/equipment-issuances", payload);
      // TRACK 14.0-S1 — Preserve original Spanish in the bilingual sidecar.
      if (submitLang === "es" && res?.data?.id) {
        const { persistBilingualSidecar } = await import("@/lib/translateOnSubmit");
        await persistBilingualSidecar("safety_form", res.data.id, payload);
      }
      toast.success(t("Issuance filed · PDF emailed to Safety · visible in Safety Forms Records"));
      if (fromRecords) {
        navigate("/safety-portal/forms-records");
      } else {
        navigate(`/safety/forms/equipment-issuance/${res.data.id}`);
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not submit"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-4xl mx-auto px-3 sm:px-8 py-4 flex items-center justify-between gap-2 flex-wrap">
          <button
            onClick={() => navigate(backPath)}
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="iss-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {fromRecords ? t("Back to Review") : t("Back")}
          </button>
          <MasciLogo variant="mark" size="md" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="sm" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-5 sm:px-8 py-8">
        <div className="mb-6 flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white shrink-0">
            <HardHat className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
              {t("Safety Forms")}
            </span>
            <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 leading-tight mt-1">
              {t("Safety Equipment Issuance & Accountability")}
            </h1>
          </div>
        </div>

        <form onSubmit={onSubmit} className="space-y-5" data-testid="iss-form">
          {/* iter275 · form-root coaching · canonical 4 kinds */}
          <HelpTipBlock formKey="equipment-issuance" className="mb-3" showCounter />
          {/* Employee */}
          <Section title={t("Employee")}>
            <HelpTipBlock formKey="equipment-issuance.employee" className="mb-3" />
            <Row>
              <Field label={t("Employee Name")} required>
                {/* iter361 · linkage continuity — atomic name + employee_id
                    capture with downstream-consequence coaching at entry time. */}
                <EmployeeRosterField
                  value={{
                    id: data.employee_id || "",
                    name: data.employee_name || "",
                    linked: !!data.employee_id,
                  }}
                  onChange={({ id, name }) => {
                    update({
                      employee_name: name,
                      employee_id: id,
                    });
                  }}
                  label=""
                  placeholder={t("Type name to search roster")}
                  required
                  testId="iss-employee-roster"
                />
              </Field>
            </Row>
            <Row>
              <Field label={t("Position")}>
                <Input
                  className={inputCls}
                  value={data.position}
                  onChange={(e) => update({ position: e.target.value })}
                  data-testid="iss-position"
                />
              </Field>
              <Field label={t("Issued By")} required>
                <Input
                  className={inputCls}
                  value={data.issued_by}
                  onChange={(e) => update({ issued_by: e.target.value })}
                  data-testid="iss-issued-by"
                />
              </Field>
            </Row>
          </Section>

          {/* Project */}
          <Section title={t("Project / Location")}>
            <JobPicker
              projectName={data.project_name}
              projectNumber={data.project_number}
              onSelect={applyJob}
            />
            <Row>
              <Field label={t("Location")}>
                <div className="flex gap-2">
                  <Input
                    className={inputCls + " flex-1"}
                    value={data.location}
                    onChange={(e) => update({ location: e.target.value })}
                    data-testid="iss-location"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={useGps}
                    disabled={locating}
                    title={t("Use GPS")}
                    className="h-12 border-2 border-slate-300 hover:border-red-700 hover:text-red-700 shrink-0"
                  >
                    {locating ? <Loader2 className="w-4 h-4 animate-spin" /> : <MapPin className="w-4 h-4" />}
                  </Button>
                </div>
              </Field>
              <Field label={t("Date Issued")}>
                <Input
                  type="date"
                  className={inputCls}
                  value={data.issued_date}
                  onChange={(e) => update({ issued_date: e.target.value })}
                  data-testid="iss-date"
                />
              </Field>
            </Row>
          </Section>

          {/* Items */}
          <Section title={t("Equipment")} desc={t("Add every item being issued. Other allows a write-in description.")}>
            <div className="space-y-3">
              {data.items.map((it, idx) => {
                const isOther = it.item_type === "Other";
                const line = (parseFloat(it.quantity) || 0) * (parseFloat(it.unit_value) || 0);
                return (
                  <div
                    key={idx}
                    className="border border-slate-200 rounded-md p-3 bg-slate-50"
                    data-testid={`iss-item-${idx}`}
                  >
                    <div className="grid grid-cols-1 sm:grid-cols-12 gap-2 items-end">
                      <div className="lg:col-span-3">
                        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                          {t("Item Type")}
                        </Label>
                        <SearchableSelect
                          value={it.item_type}
                          onChange={(v) => updateItem(idx, { item_type: v })}
                          options={ITEM_TYPES}
                          placeholder={t("Select item")}
                          searchPlaceholder={t("Type to filter…")}
                          testId={`iss-item-${idx}-type`}
                        />
                      </div>
                      {isOther && (
                        <div className="lg:col-span-3">
                          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                            {t("Specify Other")}
                          </Label>
                          <Input
                            className={inputCls}
                            value={it.item_type_other}
                            onChange={(e) => updateItem(idx, { item_type_other: e.target.value })}
                            data-testid={`iss-item-${idx}-other`}
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
                          data-testid={`iss-item-${idx}-desc`}
                        />
                      </div>
                      <div className="sm:col-span-1">
                        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                          {t("Qty")}
                        </Label>
                        <Input
                          type="number"
                          min="0"
                          step="1"
                          className={inputCls}
                          value={it.quantity}
                          onChange={(e) => updateItem(idx, { quantity: e.target.value })}
                          data-testid={`iss-item-${idx}-qty`}
                        />
                      </div>
                      <div className="lg:col-span-2">
                        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                          {t("Unit $")}
                          {isUnitValueLocked(it.item_type, data.condition) && (
                            <span className="ml-1 text-emerald-700 normal-case tracking-normal">
                              · {t("auto")}
                            </span>
                          )}
                        </Label>
                        <Input
                          type="number"
                          min="0"
                          step="0.01"
                          readOnly={isUnitValueLocked(it.item_type, data.condition)}
                          className={
                            inputCls +
                            (isUnitValueLocked(it.item_type, data.condition)
                              ? " bg-slate-100 text-slate-700 cursor-not-allowed"
                              : "")
                          }
                          value={it.unit_value}
                          onChange={(e) => updateItem(idx, { unit_value: e.target.value })}
                          data-testid={`iss-item-${idx}-unit`}
                          title={
                            isUnitValueLocked(it.item_type, data.condition)
                              ? t("Auto-filled from price book — change condition to Fair or Damaged to edit")
                              : ""
                          }
                        />
                      </div>
                      <div className={isOther ? "sm:col-span-12 sm:col-start-1" : "lg:col-span-2"}>
                        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 block">
                          {t("Asset / Serial #")}
                        </Label>
                        <Input
                          className={inputCls}
                          value={it.asset_id}
                          onChange={(e) => updateItem(idx, { asset_id: e.target.value })}
                          data-testid={`iss-item-${idx}-asset`}
                        />
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-200">
                      <span className="text-xs font-mono text-slate-600">
                        {t("Line total")}:{" "}
                        <strong className="text-slate-900">{fmtMoney(line)}</strong>
                      </span>
                      {data.items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeItem(idx)}
                          className="inline-flex items-center gap-1 text-xs font-bold text-red-700 hover:text-red-900 uppercase tracking-wide"
                          data-testid={`iss-item-${idx}-remove`}
                        >
                          <Trash2 className="w-3.5 h-3.5" /> {t("Remove")}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex items-center justify-between mt-3">
              <Button
                type="button"
                variant="outline"
                onClick={addItem}
                className="h-10 border-2 border-slate-300 hover:border-red-700 hover:text-red-700 font-bold uppercase tracking-wide text-xs"
                data-testid="iss-add-item"
              >
                <Plus className="w-4 h-4 mr-1" /> {t("Add Item")}
              </Button>
              <div className="bg-red-50 border-2 border-red-700 rounded px-4 py-2 text-right">
                <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-red-900 font-bold">
                  {t("Total Issued Value")}
                </div>
                <div className="font-display text-2xl font-black text-slate-900" data-testid="iss-total">
                  {fmtMoney(total)}
                </div>
              </div>
            </div>
          </Section>

          {/* Condition */}
          <Section
            title={t("Condition at Issuance")}
            desc={t("New / Good auto-prices from the catalog. Fair / Damaged unlocks Unit $ so you can enter a depreciated value.")}
          >
            <Row>
              <Field label={t("Condition")} required>
                <select
                  value={data.condition}
                  onChange={(e) => update({ condition: e.target.value })}
                  className="w-full h-12 border-2 border-slate-300 rounded px-2 text-base"
                  data-testid="iss-condition"
                >
                  {CONDITIONS.map((c) => (
                    <option key={c} value={c}>{t(c)}</option>
                  ))}
                </select>
              </Field>
              {data.condition === "Damaged" && (
                <Field label={t("Damage Note")} required>
                  <Input
                    className={inputCls}
                    value={data.condition_note}
                    onChange={(e) => update({ condition_note: e.target.value })}
                    placeholder={t("Describe the damage")}
                    data-testid="iss-condition-note"
                  />
                </Field>
              )}
            </Row>
          </Section>

          {/* Photos */}
          <Section title={t("Photos")} desc={t("Required — capture serial number and/or condition.")}>
            <HelpTipBlock formKey="equipment-issuance.photos" className="mb-3" />
            <PhotoUpload
              photos={data.photos}
              onChange={(photos) => update({ photos })}
            />
            <p className="text-[11px] text-slate-500 mt-1">
              {t("Uploaded:")}{" "}
              <span
                className={
                  data.photos.length >= 1 ? "text-emerald-700 font-bold" : "text-red-700 font-bold"
                }
                data-testid="iss-photo-count"
              >
                {data.photos.length}
              </span>{" "}
              / <span className="font-mono">{t("min 1 required")}</span>
            </p>
          </Section>

          {/* Acknowledgment */}
          <Section title={t("Acknowledgment & Legal")}>
            <HelpTipBlock formKey="equipment-issuance.acknowledgment" className="mb-3" />
            <div className="bg-amber-50 border-l-4 border-amber-600 p-4 rounded space-y-3">
              <p className="text-sm text-slate-800 leading-relaxed">
                {t(ISSUANCE_LEGAL)}
              </p>
              <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-line">
                {t(ISSUANCE_RESPONSIBILITY)}
              </p>
            </div>
            <label className="flex items-start gap-3 cursor-pointer mt-3">
              <input
                type="checkbox"
                checked={data.acknowledgment}
                onChange={(e) => update({ acknowledgment: e.target.checked })}
                className="w-5 h-5 mt-0.5 accent-red-700"
                data-testid="iss-ack"
              />
              <span className="text-sm font-bold text-slate-900 leading-snug">
                {t("I acknowledge receipt of the listed equipment and accept responsibility.")}
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
                data-testid="iss-employee-email"
              />
            </Field>
          </Section>

          {/* Signatures */}
          <Section title={t("Signatures")}>
            <Field label={t("Employee Signature")} required>
              <SignaturePad
                value={data.employee_signature}
                onChange={(v) => update({ employee_signature: v })}
              />
            </Field>
            <Field label={t("Supervisor Signature")} required>
              <SignaturePad
                value={data.supervisor_signature}
                onChange={(v) => update({ supervisor_signature: v })}
              />
            </Field>
          </Section>

          <div className="sticky bottom-0 bg-white border-t-2 border-red-700 -mx-5 sm:-mx-8 px-5 sm:px-8 py-3 shadow-lg">
            {data.photos.length < 1 && (
              <p
                className="text-xs text-red-700 font-bold mb-2 text-right"
                data-testid="iss-submit-photos-hint"
              >
                <Camera className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" />
                {t("Add at least 1 photo to submit")}
              </p>
            )}
            <div className="flex justify-between items-center gap-3">
              <div className="text-xs font-mono text-slate-600 truncate">
                <ShieldCheck className="w-4 h-4 inline-block mr-1 text-red-700" />
                {t("Auto-emails Safety dept on submit")}
              </div>
              <Button
                type="submit"
                disabled={saving || data.photos.length < 1}
                className="bg-red-700 hover:bg-red-800 disabled:bg-slate-300 disabled:text-slate-500 disabled:cursor-not-allowed h-12 px-6 font-bold uppercase tracking-wide"
                data-testid="iss-submit"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Submitting…")}
                  </>
                ) : data.photos.length < 1 ? (
                  <>
                    <Camera className="w-4 h-4 mr-2" /> {t("Photo required")}
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" /> {t("Submit & Email PDF")}
                  </>
                )}
              </Button>
            </div>
          </div>
        </form>
      </main>
    </div>
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
