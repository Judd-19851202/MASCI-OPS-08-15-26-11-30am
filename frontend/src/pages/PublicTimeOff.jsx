// Public Time Off Request form (iter101)
//
// Token-gated public URL: /time-off/public/:token
//
// HR generates one of these from the HR Portal for office staff who don't
// have a platform login. The token is valid 7 days OR until first submit.

import React from "react";
import { useParams } from "react-router-dom";
import { CalendarOff, CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from "@/components/ui/select";
import { toast } from "sonner";
import { SignaturePad } from "@/components/SignaturePad";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { translateUserInput } from "@/lib/translateOnSubmit";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const REASONS = [
  "Vacation", "Sick Leave", "Medical Appointment", "Family Emergency",
  "Bereavement", "Jury Duty", "Military Leave", "Personal", "Other",
];

export default function PublicTimeOff() {
  const { t, lang } = useT();
  const { token } = useParams();
  const [meta, setMeta] = React.useState(null);
  const [loadErr, setLoadErr] = React.useState("");
  const [submitted, setSubmitted] = React.useState(null);

  const [reason, setReason] = React.useState("");
  const [reasonOther, setReasonOther] = React.useState("");
  const [payType, setPayType] = React.useState("Paid");
  const [startDate, setStartDate] = React.useState("");
  const [endDate, setEndDate] = React.useState("");
  const [halfStart, setHalfStart] = React.useState(false);
  const [halfEnd, setHalfEnd] = React.useState(false);
  const [returnDate, setReturnDate] = React.useState("");
  const [contactPhone, setContactPhone] = React.useState("");
  const [coverage, setCoverage] = React.useState("");
  const [notes, setNotes] = React.useState("");
  const [signature, setSignature] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API}/public/time-off/${token}`);
        if (!r.ok) {
          const d = await r.json().catch(() => ({}));
          setLoadErr(d.detail || `Status ${r.status}`);
          return;
        }
        setMeta(await r.json());
      } catch (e) {
        setLoadErr("Network error — please try again.");
      }
    })();
  }, [token]);

  // Auto-calc total days
  const totalDays = React.useMemo(() => {
    if (!startDate || !endDate) return 0;
    const a = new Date(startDate);
    const b = new Date(endDate);
    if (Number.isNaN(a.getTime()) || Number.isNaN(b.getTime())) return 0;
    const diff = Math.round((b - a) / 86400000) + 1;
    if (diff <= 0) return 0;
    let d = diff;
    if (halfStart) d -= 0.5;
    if (halfEnd) d -= 0.5;
    return Math.max(d, 0.5);
  }, [startDate, endDate, halfStart, halfEnd]);

  const submit = async () => {
    if (!reason) { toast.error("Please pick a reason"); return; }
    if (reason === "Other" && !reasonOther.trim()) { toast.error("Please describe the reason"); return; }
    if (!startDate || !endDate) { toast.error("Start and end dates are required"); return; }
    if (new Date(endDate) < new Date(startDate)) { toast.error("End date is before start date"); return; }
    setBusy(true);
    try {
      // Build the user-typed payload (only freeform fields go through the
      // ES→EN translator — dates, numbers, signatures, enum values are
      // skipped by translateOnSubmit's SKIP_KEY_RE).
      const userPayload = {
        reason: reason === "Other" ? `Other: ${reasonOther.trim()}` : reason,
        reason_other: reasonOther.trim(),
        coverage_plan: coverage,
        notes,
      };
      const translated = await translateUserInput(userPayload, lang);
      const resp = await fetch(`${API}/public/time-off/${token}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: translated.reason,
          pay_type: payType,
          start_date: startDate,
          end_date: endDate,
          half_day_start: halfStart,
          half_day_end: halfEnd,
          total_days: totalDays,
          return_to_work_date: returnDate,
          contact_phone: contactPhone,
          coverage_plan: translated.coverage_plan,
          notes: translated.notes,
          employee_signature: signature,
          submit_language: lang,
        }),
      });
      if (!resp.ok) {
        const d = await resp.json().catch(() => ({}));
        throw new Error(d.detail || "Submit failed");
      }
      const d = await resp.json();
      setSubmitted(d);
    } catch (e) {
      toast.error(e.message || "Submit failed");
    } finally {
      setBusy(false);
    }
  };

  if (loadErr) {
    return (
      <PublicShell t={t}>
        <Card className="p-8 text-center border-red-300">
          <AlertTriangle className="w-12 h-12 mx-auto text-red-600 mb-3" />
          <h1 className="font-display text-2xl font-black">{t("Link unavailable")}</h1>
          <p className="text-slate-600 mt-2">{loadErr}</p>
          <p className="text-slate-500 text-sm mt-3">{t("Contact HR for a fresh link.")}</p>
        </Card>
      </PublicShell>
    );
  }

  if (!meta) {
    return (
      <PublicShell t={t}>
        <div className="text-center py-12 text-slate-500">
          <Loader2 className="w-8 h-8 mx-auto animate-spin mb-2" /> {t("Loading form…")}
        </div>
      </PublicShell>
    );
  }

  if (submitted) {
    return (
      <PublicShell t={t}>
        <Card className="p-8 text-center border-emerald-300 bg-emerald-50">
          <CheckCircle2 className="w-12 h-12 mx-auto text-emerald-700 mb-3" />
          <h1 className="font-display text-2xl font-black">{t("Submitted!")}</h1>
          <p className="text-slate-700 mt-2">
            {t("HR has been notified. You'll get an email when your request is reviewed.")}
          </p>
          {submitted.doc_id && (
            <p className="font-mono text-sm text-slate-500 mt-3">{t("Reference:")} {submitted.doc_id}</p>
          )}
        </Card>
      </PublicShell>
    );
  }

  return (
    <PublicShell t={t}>
      <div className="mb-4">
        <div className="font-mono text-[10px] sm:text-xs uppercase tracking-[0.2em] text-cyan-700 font-bold">
          <CalendarOff className="w-3.5 h-3.5 inline mr-1" /> {t("MASCI · Time Off Request")}
        </div>
        <h1 className="font-display text-2xl sm:text-3xl font-black mt-1">{t("Hello,")} {meta.employee_name}.</h1>
        <p className="text-slate-600 mt-2 text-sm sm:text-base">
          {meta.note || t("Fill out this form to request time off. HR will review and email you a decision.")}
        </p>
      </div>

      <Card className="p-4 sm:p-5 space-y-4 pb-24 sm:pb-5" data-testid="public-time-off-form">
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label={t("Position")}>
            <Input value={meta.employee_position || ""} disabled className="bg-slate-100 h-12" />
          </Field>
          <Field label={t("Department")}>
            <Input value={meta.department || ""} disabled className="bg-slate-100 h-12" />
          </Field>
        </div>

        <Field label={t("Reason *")}>
          <Select value={reason} onValueChange={setReason}>
            <SelectTrigger className="h-12" data-testid="public-reason"><SelectValue placeholder={t("Pick a reason…")} /></SelectTrigger>
            <SelectContent>
              {REASONS.map((r) => <SelectItem key={r} value={r}>{t(r)}</SelectItem>)}
            </SelectContent>
          </Select>
        </Field>
        {reason === "Other" && (
          <Field label={t("If Other, please explain *")}>
            <Input value={reasonOther} onChange={(e) => setReasonOther(e.target.value)} className="h-12" />
          </Field>
        )}

        <Field label={t("Pay Type")}>
          <Select value={payType} onValueChange={setPayType}>
            <SelectTrigger className="h-12"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="Paid">{t("Paid")}</SelectItem>
              <SelectItem value="Unpaid">{t("Unpaid")}</SelectItem>
            </SelectContent>
          </Select>
        </Field>

        <div className="grid sm:grid-cols-2 gap-3">
          <Field label={t("Start Date *")}>
            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="h-12" data-testid="public-start-date" />
          </Field>
          <Field label={t("End Date *")}>
            <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="h-12" data-testid="public-end-date" />
          </Field>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="flex items-center gap-2 text-sm py-2 px-1 cursor-pointer min-h-11">
            <input type="checkbox" checked={halfStart} onChange={(e) => setHalfStart(e.target.checked)} className="w-5 h-5" />
            {t("Half day on start")}
          </label>
          <label className="flex items-center gap-2 text-sm py-2 px-1 cursor-pointer min-h-11">
            <input type="checkbox" checked={halfEnd} onChange={(e) => setHalfEnd(e.target.checked)} className="w-5 h-5" />
            {t("Half day on end")}
          </label>
        </div>

        <div className="bg-cyan-50 border border-cyan-200 rounded p-3 font-mono text-sm">
          {t("Total Days Requested:")} <span className="font-bold text-cyan-900 text-lg">{totalDays}</span>
        </div>

        <div className="grid sm:grid-cols-2 gap-3">
          <Field label={t("Return to Work Date")}>
            <Input type="date" value={returnDate} onChange={(e) => setReturnDate(e.target.value)} className="h-12" />
          </Field>
          <Field label={t("Contact Phone During Leave")}>
            <Input type="tel" inputMode="tel" value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} className="h-12" />
          </Field>
        </div>

        <Field label={t("Coverage Plan / Who's Covering")}>
          <Textarea rows={2} value={coverage} onChange={(e) => setCoverage(e.target.value)} className="text-base" />
        </Field>
        <Field label={t("Notes / Additional Detail")}>
          <Textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} className="text-base" />
        </Field>

        <div>
          <Label className="font-mono text-[10px] sm:text-xs uppercase mb-1 block">{t("Employee Signature")}</Label>
          <SignaturePad value={signature} onChange={setSignature} />
        </div>

        {/* Desktop submit (hidden on mobile — replaced by sticky bar below) */}
        <Button onClick={submit} disabled={busy} className="hidden sm:flex w-full h-12 bg-cyan-700 hover:bg-cyan-800 text-white font-bold uppercase tracking-wide" data-testid="public-submit">
          {busy ? t("Submitting…") : t("Submit Time Off Request")}
        </Button>
      </Card>

      {/* Mobile-only sticky submit bar */}
      <div className="sm:hidden fixed bottom-0 left-0 right-0 bg-white border-t-2 border-cyan-700 px-3 py-3 shadow-lg z-50" style={{paddingBottom: 'max(0.75rem, env(safe-area-inset-bottom))'}}>
        <Button onClick={submit} disabled={busy}
          className="w-full h-14 bg-cyan-700 hover:bg-cyan-800 text-white font-bold uppercase tracking-wide text-base"
          data-testid="public-submit-mobile"
        >
          {busy ? t("Submitting…") : t("Submit Time Off Request")}
        </Button>
      </div>
    </PublicShell>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <Label className="font-mono text-xs uppercase tracking-wider mb-1 block">{label}</Label>
      {children}
    </div>
  );
}

function PublicShell({ children, t }) {
  return (
    <div className="min-h-screen bg-slate-50 pb-16">
      <header className="bg-slate-900 border-b-4 border-cyan-700">
        <div className="max-w-2xl mx-auto px-5 py-4 flex items-center justify-between gap-3">
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <span className="hidden sm:inline font-mono text-[10px] uppercase tracking-widest text-cyan-300">
              {t ? t("Public Form") : "Public Form"}
            </span>
          </div>
        </div>
      </header>
      <main className="max-w-2xl mx-auto px-5 py-6">{children}</main>
      <footer className="text-center font-mono text-[10px] uppercase tracking-widest text-slate-500 mt-8">
        Generated through MASCI Operations Platform — Powered by ForgedOps™ | © 2026 ForgedOps™
      </footer>
    </div>
  );
}
