// Track 19.16 · Phase B2 · Public Near-Miss Kiosk.
// ----------------------------------------------------
// Public no-auth 20-second near-miss submission. Route: /near-miss
//
// Never claims "submitted" unless the server actually confirms.
// Never fakes identity. Never masks emergency guidance.

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useT } from "@/lib/i18n";
import {
  flushQueue,
  isOnline,
  submitPublicNearMiss,
  watchOnline,
} from "@/lib/incidentOfflineQueue";
import { AlertTriangle, Check, Camera, Wifi, WifiOff, ShieldAlert } from "lucide-react";
import { OperationalPageFrame } from "@/components/public/OperationalPageFrame";
import { OperationalOutcomeFrame } from "@/components/public/OperationalOutcomeFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import SubmissionConfirmation from "@/components/submission/SubmissionConfirmation";
import { buildSubmissionConfirmation } from "@/lib/submissionConfirmation";

function EmergencyAlert() {
  const { t } = useT();
  return (
    <div
      role="alert"
      data-testid="near-miss-immediate-danger-alert"
      className="rounded-xl border-2 border-red-500 bg-red-50 p-4 flex gap-3"
    >
      <div className="rounded-full bg-red-600 text-white h-10 w-10 flex items-center justify-center shrink-0" aria-hidden>
        <ShieldAlert className="w-5 h-5" />
      </div>
      <div>
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-800">
          {t("Immediate danger")}
        </div>
        <div className="font-display text-base font-black text-red-900">
          {t("This form is not a replacement for emergency action.")}
        </div>
        <ul className="mt-2 space-y-1 text-sm text-red-900 list-disc pl-4">
          <li>{t("Move people away from the hazard now.")}</li>
          <li>{t("Notify a supervisor immediately.")}</li>
          <li>{t("Call 911 if there is an active emergency.")}</li>
        </ul>
      </div>
    </div>
  );
}

function CapturePhotoField({ value, onChange, testId }) {
  const { t } = useT();
  const ref = useRef(null);
  const onFile = (e) => {
    const f = (e.target.files || [])[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      const item = {
        data_url: reader.result,
        name: f.name,
        size: f.size,
        mime: f.type,
        captured_at: new Date().toISOString(),
      };
      // Fetch GPS best-effort.
      if (navigator?.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => onChange({ ...item, gps: { lat: pos.coords.latitude, lng: pos.coords.longitude } }),
          () => onChange(item),
          { timeout: 2500, maximumAge: 60000 },
        );
      } else {
        onChange(item);
      }
    };
    reader.readAsDataURL(f);
  };
  return (
    <div className="space-y-2" data-testid={testId}>
      {value && (
        <div className="relative rounded-md overflow-hidden border border-slate-200 max-w-xs" data-testid={`${testId}-preview`}>
          <img src={value.data_url} alt={t("Attached photo")} className="w-full h-40 object-cover" />
          <button
            type="button"
            onClick={() => onChange(null)}
            className="absolute top-1 right-1 h-7 w-7 rounded-full bg-white/95 text-red-700 text-sm font-bold shadow"
            data-testid={`${testId}-remove`}
            aria-label={t("Remove photo")}
          >×</button>
        </div>
      )}
      <input
        ref={ref}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={onFile}
        data-testid={`${testId}-input`}
        aria-label={t("Attach a photo")}
      />
      <button
        type="button"
        onClick={() => ref.current && ref.current.click()}
        className="h-11 rounded-md border-2 border-dashed border-slate-400 text-slate-800 w-full font-medium hover:border-slate-700 inline-flex items-center justify-center gap-1"
        data-testid={`${testId}-capture`}
      >
        <Camera className="w-4 h-4" aria-hidden /> {t("Add photo (optional)")}
      </button>
    </div>
  );
}

export default function NearMissKiosk() {
  const { t, lang } = useT();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    what_almost_happened: "",
    location_label: "",
    immediate_danger: false,
    submitter_name: "",
    submitter_contact: "",
    submitter_company: "",
    photo: null,
    gps: null,
  });
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null); // { status, case_number?, case_id?, idempotency_key }
  const [online, setOnline] = useState(isOnline());
  const [error, setError] = useState("");

  useEffect(() => {
    // Attempt a queue flush on mount + subscribe to online events.
    flushQueue().catch(() => {});
    const off = watchOnline(() => {
      setOnline(true);
      flushQueue().catch(() => {});
    });
    const goOffline = () => setOnline(false);
    window.addEventListener("offline", goOffline);
    return () => { off(); window.removeEventListener("offline", goOffline); };
  }, []);

  const setField = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const captureGps = () => {
    if (!navigator?.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (p) => setField("gps", { lat: p.coords.latitude, lng: p.coords.longitude }),
      () => {},
      { timeout: 3000, maximumAge: 60000 },
    );
  };

  const canSubmit = form.what_almost_happened.trim().length >= 4 && form.location_label.trim().length >= 2;

  const submit = async (e) => {
    e?.preventDefault?.();
    if (!canSubmit || busy) return;
    setBusy(true); setError("");
    try {
      const payload = {
        what_almost_happened: form.what_almost_happened,
        location_label: form.location_label,
        immediate_danger: form.immediate_danger,
        submitter_name: form.submitter_name,
        submitter_contact: form.submitter_contact,
        submitter_company: form.submitter_company,
        location_gps: form.gps || null,
        photo_data_url: form.photo?.data_url || "",
        photo_metadata: form.photo ? {
          size: form.photo.size,
          mime: form.photo.mime,
          captured_at: form.photo.captured_at,
          gps: form.photo.gps || null,
        } : {},
        language: lang,
      };
      const out = await submitPublicNearMiss(payload);
      setResult(out);
    } catch (err) {
      setError(err?.message || "submit_failed");
    } finally {
      setBusy(false);
    }
  };

  // ── Success screens ────────────────────────────────────────────────
  if (result?.status === "submitted") {
    const confirmation = buildSubmissionConfirmation({
      workflowKey: "near-miss",
      documentNumber: result.case_number || result.case_id || "",
      submittedAt: new Date().toISOString(),
      submittedBy: form.submitter_name || "",
      note: result.duplicate ? "We noticed this report was already submitted. The system kept one filed copy only." : "",
      startAnother: {
        label: "Start Another",
        onClick: () => {
          setResult(null);
          setForm({ what_almost_happened: "", location_label: "", immediate_danger: false, submitter_name: "", submitter_contact: "", submitter_company: "", photo: null, gps: null });
        },
      },
      returnToPortal: { label: "Return to Portal", to: "/" },
    });
    return <SubmissionConfirmation confirmation={confirmation} />;
  }
  if (result?.status === "queued") {
    const confirmation = buildSubmissionConfirmation({
      workflowKey: "near-miss",
      submittedAt: new Date().toISOString(),
      submittedBy: form.submitter_name || "",
      queued: true,
      successStatus: "Saved on this device",
      description: "This report is stored on this device and will retry automatically when internet service returns.",
      followUpRequired: "Keep this device online so the report can send automatically.",
      expectedProcessingStatus: "Waiting for connection before routing to Safety",
      startAnother: {
        label: "Start Another",
        onClick: () => {
          setResult(null);
          setForm({ what_almost_happened: "", location_label: "", immediate_danger: false, submitter_name: "", submitter_contact: "", submitter_company: "", photo: null, gps: null });
        },
      },
      returnToPortal: { label: "Return to Portal", to: "/" },
    });
    return <SubmissionConfirmation confirmation={confirmation} />;
  }

  return (
    <OperationalPageFrame
      testId="near-miss-kiosk"
      accent="red"
      familyLabel={t("Safety Operations")}
      familyMeta={t("Public near-miss workflow")}
      mainWidthClass="max-w-4xl"
      heroIcon={AlertTriangle}
      kicker={t("Public Near-Miss Reporting")}
      title={t("Report a near miss")}
      description={t("No login needed. Describe what almost happened, where it happened, and whether anyone is still in immediate danger.")}
      heroMeta={(
        <>
          <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-[11px] font-mono uppercase tracking-[0.14em] border ${online ? "border-emerald-300 text-emerald-800 bg-emerald-50" : "border-amber-400 text-amber-800 bg-amber-50"}`} data-testid={online ? "near-miss-online" : "near-miss-offline"} aria-live="polite">
            {online ? <Wifi className="w-3 h-3" aria-hidden /> : <WifiOff className="w-3 h-3" aria-hidden />}
            {online ? t("Online") : t("Offline")}
          </span>
          <OperationalStatusBadge tone="red" testId="near-miss-emergency-badge">{t("Emergency action first")}</OperationalStatusBadge>
        </>
      )}
      heroAside={(
        <div className="wp17-panel p-4" data-testid="near-miss-hero-aside">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-2">{t("What needs attention now")}</div>
          <div className="text-sm text-slate-700 leading-6">{t("If the hazard is still active, move people away, alert supervision, and call emergency services when needed before you complete this report.")}</div>
        </div>
      )}
      footerText={t("MASCI Operations Platform · Public near-miss workflow")}
    >
      <div className="max-w-2xl mx-auto space-y-4">

        <form onSubmit={submit} className="space-y-4" aria-describedby="near-miss-help">
          <div className="space-y-1">
            <label htmlFor="what_almost_happened" className="block text-sm font-semibold text-slate-800">
              {t("What almost happened?")} <span className="text-red-700" aria-hidden>*</span>
            </label>
            <textarea
              id="what_almost_happened"
              required
              rows={4}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-slate-700"
              value={form.what_almost_happened}
              onChange={(e) => setField("what_almost_happened", e.target.value)}
              placeholder={t("Example: forklift almost struck a worker walking through the yard.")}
              data-testid="near-miss-what-happened"
              aria-required="true"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="location_label" className="block text-sm font-semibold text-slate-800">
              {t("Where did it happen?")} <span className="text-red-700" aria-hidden>*</span>
            </label>
            <input
              id="location_label"
              type="text"
              required
              className="w-full h-11 rounded-md border border-slate-300 px-3 text-base focus:outline-none focus:ring-2 focus:ring-slate-700"
              value={form.location_label}
              onChange={(e) => setField("location_label", e.target.value)}
              placeholder={t("Job site, area, or intersection")}
              data-testid="near-miss-location"
              aria-required="true"
            />
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={captureGps}
                className="h-9 px-3 rounded-md border border-slate-300 text-slate-700 text-sm hover:border-slate-500"
                data-testid="near-miss-gps"
              >
                {form.gps ? `${form.gps.lat.toFixed(4)}, ${form.gps.lng.toFixed(4)}` : t("Capture location (optional)")}
              </button>
            </div>
          </div>

          <div className="space-y-1">
            <label className="block text-sm font-semibold text-slate-800">
              {t("Is anyone in immediate danger right now?")}
            </label>
            <div className="flex gap-2" role="radiogroup" aria-label={t("Is anyone in immediate danger right now?")}>
              <button
                type="button"
                onClick={() => setField("immediate_danger", false)}
                aria-pressed={form.immediate_danger === false}
                className={`h-11 px-4 rounded-md border-2 font-bold ${form.immediate_danger === false ? "bg-slate-900 text-white border-transparent" : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"}`}
                data-testid="near-miss-danger-no"
              >{t("No")}</button>
              <button
                type="button"
                onClick={() => setField("immediate_danger", true)}
                aria-pressed={form.immediate_danger === true}
                className={`h-11 px-4 rounded-md border-2 font-bold ${form.immediate_danger === true ? "bg-red-700 text-white border-transparent" : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"}`}
                data-testid="near-miss-danger-yes"
              >{t("Yes")}</button>
            </div>
          </div>

          {form.immediate_danger && <EmergencyAlert />}

          <details className="rounded-lg border border-slate-200 bg-white p-3">
            <summary className="cursor-pointer font-semibold text-slate-800" data-testid="near-miss-optional-toggle">
              {t("Add your name or a photo (optional)")}
            </summary>
            <div className="mt-3 space-y-3">
              <div className="grid gap-2 sm:grid-cols-3">
                <input
                  type="text"
                  className="h-11 rounded-md border border-slate-300 px-3 text-base"
                  value={form.submitter_name}
                  onChange={(e) => setField("submitter_name", e.target.value)}
                  placeholder={t("Your name")}
                  data-testid="near-miss-name"
                  aria-label={t("Your name")}
                />
                <input
                  type="text"
                  className="h-11 rounded-md border border-slate-300 px-3 text-base"
                  value={form.submitter_contact}
                  onChange={(e) => setField("submitter_contact", e.target.value)}
                  placeholder={t("Phone or email")}
                  data-testid="near-miss-contact"
                  aria-label={t("Phone or email")}
                />
                <input
                  type="text"
                  className="h-11 rounded-md border border-slate-300 px-3 text-base"
                  value={form.submitter_company}
                  onChange={(e) => setField("submitter_company", e.target.value)}
                  placeholder={t("Company (optional)")}
                  data-testid="near-miss-company"
                  aria-label={t("Company")}
                />
              </div>
              <CapturePhotoField
                value={form.photo}
                onChange={(p) => setField("photo", p)}
                testId="near-miss-photo"
              />
            </div>
          </details>

          {error && (
            <div className="rounded-md border-2 border-red-400 bg-red-50 p-3 text-sm text-red-900" role="alert" data-testid="near-miss-error">
              {t("We could not submit. Please try again.")} — {error}
            </div>
          )}

          <button
            type="submit"
            disabled={!canSubmit || busy}
            className="w-full h-14 rounded-md bg-red-700 text-white text-base font-black tracking-wide hover:bg-red-800 disabled:bg-slate-300 disabled:cursor-not-allowed"
            data-testid="near-miss-submit"
          >
            {busy ? t("Sending…") : (online ? t("Submit near-miss report") : t("Save & queue"))}
          </button>

          <p id="near-miss-help" className="text-[11px] font-mono uppercase tracking-[0.12em] text-slate-500 text-center">
            {t("Anonymous submissions are welcome. Nothing is shared with your employer beyond Safety.")}
          </p>
        </form>
      </div>
    </OperationalPageFrame>
  );
}
