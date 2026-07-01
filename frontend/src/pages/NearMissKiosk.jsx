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

function LangToggleMini({ lang, onLang }) {
  return (
    <div className="inline-flex rounded-md border border-slate-300 bg-white overflow-hidden" role="group" aria-label="Language">
      <button
        type="button"
        onClick={() => onLang("en")}
        aria-pressed={lang === "en"}
        className={`px-3 h-9 text-xs font-mono uppercase tracking-widest ${lang === "en" ? "bg-slate-900 text-white" : "text-slate-700"}`}
        data-testid="near-miss-lang-en"
      >EN</button>
      <button
        type="button"
        onClick={() => onLang("es")}
        aria-pressed={lang === "es"}
        className={`px-3 h-9 text-xs font-mono uppercase tracking-widest ${lang === "es" ? "bg-slate-900 text-white" : "text-slate-700"}`}
        data-testid="near-miss-lang-es"
      >ES</button>
    </div>
  );
}

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
  const { t, lang, setLang } = useT();
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
    return (
      <div className="min-h-screen bg-emerald-50 flex flex-col items-center justify-center p-6" data-testid="near-miss-success">
        <div className="max-w-md w-full bg-white rounded-2xl border-2 border-emerald-300 p-6 space-y-4 shadow-lg">
          <div className="rounded-full bg-emerald-100 w-14 h-14 flex items-center justify-center" aria-hidden>
            <Check className="w-8 h-8 text-emerald-700" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-800">{t("Report submitted")}</div>
            <h2 className="mt-1 font-display text-2xl font-black text-slate-900">
              {t("Thank you. Safety has received your report.")}
            </h2>
          </div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3" data-testid="near-miss-case-number">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-emerald-800">{t("Case number")}</div>
            <div className="font-mono text-lg font-black text-emerald-900">{result.case_number || result.case_id}</div>
          </div>
          {result.duplicate && (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-2 text-xs text-slate-700" data-testid="near-miss-duplicate">
              {t("We noticed this report was already submitted. We're keeping just one copy.")}
            </div>
          )}
          <button
            type="button"
            onClick={() => { setResult(null); setForm({ what_almost_happened: "", location_label: "", immediate_danger: false, submitter_name: "", submitter_contact: "", submitter_company: "", photo: null, gps: null }); }}
            className="w-full h-12 rounded-md bg-emerald-700 text-white font-bold hover:bg-emerald-800"
            data-testid="near-miss-submit-another"
          >{t("Submit another report")}</button>
        </div>
      </div>
    );
  }
  if (result?.status === "queued") {
    return (
      <div className="min-h-screen bg-amber-50 flex flex-col items-center justify-center p-6" data-testid="near-miss-queued">
        <div className="max-w-md w-full bg-white rounded-2xl border-2 border-amber-400 p-6 space-y-4 shadow-lg">
          <div className="rounded-full bg-amber-100 w-14 h-14 flex items-center justify-center" aria-hidden>
            <WifiOff className="w-7 h-7 text-amber-800" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-800">{t("Saved and queued")}</div>
            <h2 className="mt-1 font-display text-2xl font-black text-slate-900">
              {t("This will submit when connection returns.")}
            </h2>
          </div>
          <p className="text-sm text-slate-800">
            {t("Your report is saved on this device. Do not close this tab if possible — we will submit it automatically when the internet returns.")}
          </p>
          <button
            type="button"
            onClick={() => { setResult(null); }}
            className="w-full h-12 rounded-md bg-amber-700 text-white font-bold hover:bg-amber-800"
            data-testid="near-miss-queued-ok"
          >{t("OK")}</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="near-miss-kiosk">
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("Public Near-Miss Reporting")}
          </div>
          <h1 className="font-display text-lg sm:text-xl font-black text-slate-900">
            {t("Report a near miss")}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-mono uppercase tracking-[0.14em] border ${online ? "border-emerald-300 text-emerald-800 bg-emerald-50" : "border-amber-400 text-amber-800 bg-amber-50"}`}
            data-testid={online ? "near-miss-online" : "near-miss-offline"}
            aria-live="polite"
          >
            {online ? <Wifi className="w-3 h-3" aria-hidden /> : <WifiOff className="w-3 h-3" aria-hidden />}
            {online ? t("Online") : t("Offline")}
          </span>
          <LangToggleMini lang={lang} onLang={setLang} />
        </div>
      </header>

      <main className="max-w-2xl mx-auto p-4 sm:p-6 space-y-4">
        <p className="text-sm text-slate-700">
          {t("No login needed. Tell us what almost happened. It takes 20 seconds.")}
        </p>

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
      </main>
    </div>
  );
}
