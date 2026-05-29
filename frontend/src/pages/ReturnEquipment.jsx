import React, { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Save,
  Loader2,
  PackageCheck,
  CheckCircle2,
  AlertTriangle,
  XOctagon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { SignaturePad } from "@/components/SignaturePad";
import { useT, getLang } from "@/lib/i18n";
import { api } from "@/lib/api";
import { isSafetyForms } from "@/lib/safetyFormsAuth";
import { isAdmin } from "@/lib/adminAuth";
import { isSafety } from "@/lib/safetyAuth";
import {
  RETURN_STATUSES,
  buildReturnDefaults,
  computeChargeback,
  rememberSupervisor,
  fmtMoney,
} from "@/lib/safetyFormsSchema";
import { toast } from "sonner";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700 focus-visible:ring-offset-2";

/**
 * ReturnEquipment — paired check-in form for an existing issuance.
 *
 * Designed to be dead-simple in the field:
 *   1. Open the original issuance (already signed)
 *   2. For each item, tap one of three giant pills (Returned / Damaged / Lost)
 *   3. Add a note when required (Damaged or Lost)
 *   4. Sign × 2, submit
 * The chargeback total recomputes live as you tap.
 */
export default function ReturnEquipment() {
  const { id } = useParams();
  const { t, lang } = useT();
  const navigate = useNavigate();
  // iter323 · Safety Forms ownership — Safety Portal + Admin + legacy.
  const authed = isSafety() || isSafetyForms() || isAdmin();

  const [issuance, setIssuance] = useState(null);
  const [data, setData] = useState(null);
  const [loadErr, setLoadErr] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!authed) return;
    api
      .get(`/safety-forms/equipment-issuances/${id}`)
      .then((r) => {
        const doc = r.data;
        setIssuance(doc);
        if (doc.return) {
          // Already returned — bounce back to view page
          toast.info(t("This issuance has already been checked in."));
          navigate(`/safety/forms/equipment-issuance/${id}`, { replace: true });
          return;
        }
        setData(buildReturnDefaults(doc));
      })
      .catch((e) => setLoadErr(e?.response?.data?.detail || "Not found"));
  }, [authed, id, navigate, t]);

  const cb = useMemo(() => computeChargeback(data?.items || []), [data]);

  if (!authed) return <Navigate to="/safety-portal/login?from=safety-forms" replace />;
  if (loadErr) {
    return (
      <div className="min-h-screen blueprint-bg p-8">
        <div className="max-w-2xl mx-auto bg-white border-2 border-red-300 rounded-md p-6">
          <h1 className="font-display text-2xl font-black">{t("Not found")}</h1>
          <p className="text-slate-600">{loadErr}</p>
          <Link to="/safety/forms" className="text-red-700 font-bold underline">
            {t("Back")}
          </Link>
        </div>
      </div>
    );
  }
  if (!data || !issuance) {
    return (
      <div className="min-h-screen blueprint-bg flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-red-700" />
      </div>
    );
  }

  const update = (patch) => setData((d) => ({ ...d, ...patch }));
  const updateItem = (idx, patch) =>
    setData((d) => ({
      ...d,
      items: d.items.map((it, i) => (i === idx ? { ...it, ...patch } : it)),
    }));

  async function onSubmit(e) {
    e.preventDefault();
    if (saving) return;

    const fails = [];
    if (!data.received_by.trim()) fails.push(t("Received By required"));
    for (const it of data.items) {
      const s = (it.status || "").toLowerCase();
      if (!["returned", "damaged", "lost"].includes(s))
        fails.push(t("Each item needs a status"));
      if ((s === "damaged" || s === "lost") && !(it.note || "").trim())
        fails.push(t("Note required for Damaged or Lost items"));
      if (s === "returned") {
        const rq = parseFloat(it.returned_quantity);
        const sq = parseFloat(it.source_quantity);
        if (Number.isNaN(rq) || rq < 0 || rq > sq)
          fails.push(t("Returned qty must be between 0 and issued qty"));
      }
    }
    if (!data.acknowledgment) fails.push(t("Acknowledgment required"));
    if (!data.employee_signature) fails.push(t("Employee signature required"));
    if (!data.supervisor_signature) fails.push(t("Supervisor signature required"));
    if (fails.length) {
      toast.error(fails[0]);
      return;
    }

    setSaving(true);
    try {
      rememberSupervisor(data.received_by);
      let payload = { ...data, lang };
      const submitLang = getLang();
      if (submitLang === "es") {
        toast.info(t("Translating to English…"));
        const { translateUserInput } = await import("@/lib/translateOnSubmit");
        payload = await translateUserInput(payload, "es");
      }
      payload = { ...payload, submit_language: submitLang || "en" };
      await api.post(`/safety-forms/equipment-issuances/${id}/return`, payload);
      toast.success(t("Check-in saved — PDF emailed to Safety"));
      navigate(`/safety/forms/equipment-issuance/${id}`);
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
            onClick={() => navigate(`/safety/forms/equipment-issuance/${id}`)}
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="ret-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Back")}
          </button>
          <MasciLogo variant="mark" size="md" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="sm" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-5 sm:px-8 py-8">
        <div className="mb-6 flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-emerald-700 text-white shrink-0">
            <PackageCheck className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-emerald-700 font-bold">
              {t("Safety Forms · Check-In")}
            </span>
            <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 leading-tight mt-1">
              {t("Equipment Check-In & Return")}
            </h1>
            <p className="text-sm text-slate-600 mt-2">
              {t("Reviewing")}{" "}
              <strong>{issuance.employee_name}</strong>
              {issuance.project_name ? <> · <span className="text-slate-700">{issuance.project_name}</span></> : null}
              {" "}— {t("issued")}{" "}
              <span className="font-mono">{issuance.issued_date}</span>
            </p>
          </div>
        </div>

        <form onSubmit={onSubmit} className="space-y-5" data-testid="ret-form">
          <Section title={t("Check-In")}>
            <Row>
              <Field label={t("Date Returned")} required>
                <Input
                  type="date"
                  className={inputCls}
                  value={data.check_in_date}
                  onChange={(e) => update({ check_in_date: e.target.value })}
                  data-testid="ret-date"
                />
              </Field>
              <Field label={t("Received By")} required>
                <Input
                  className={inputCls}
                  value={data.received_by}
                  onChange={(e) => update({ received_by: e.target.value })}
                  data-testid="ret-received-by"
                />
              </Field>
            </Row>
            <Field label={t("Notes (optional)")}>
              <Textarea
                className="border-2 border-slate-300 min-h-[60px]"
                value={data.return_notes}
                onChange={(e) => update({ return_notes: e.target.value })}
                data-testid="ret-notes"
              />
            </Field>
          </Section>

          <Section title={t("Per-Item Return")} desc={t("Tap a status pill for each item. Notes required for Damaged or Lost.")}>
            <div className="space-y-3">
              {data.items.map((it, idx) => {
                const isOther = it.source_item_type === "Other";
                const itemLabel =
                  isOther && it.source_item_type_other
                    ? `Other — ${it.source_item_type_other}`
                    : it.source_item_type;
                const requireNote = it.status === "damaged" || it.status === "lost";
                const lineCb = (() => {
                  const s = (it.status || "").toLowerCase();
                  const sq = parseFloat(it.source_quantity) || 0;
                  const rq = parseFloat(it.returned_quantity) || 0;
                  const uv = parseFloat(it.source_unit_value) || 0;
                  if (s === "lost" || s === "damaged") return sq * uv;
                  if (s === "returned" && rq < sq) return (sq - rq) * uv;
                  return 0;
                })();
                return (
                  <div
                    key={idx}
                    className="border border-slate-200 rounded-md p-3 bg-white"
                    data-testid={`ret-item-${idx}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="font-display text-base font-black text-slate-900 truncate">{itemLabel}</div>
                        <div className="text-xs text-slate-600">
                          {it.source_description || "—"}
                          {it.source_asset_id ? <span className="font-mono ml-1">· {it.source_asset_id}</span> : null}
                        </div>
                        <div className="font-mono text-[10px] uppercase tracking-wide text-slate-500 mt-1">
                          {t("Issued")}: <strong className="text-slate-800">{it.source_quantity}</strong> @ {fmtMoney(it.source_unit_value)}
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-500">{t("Chargeback")}</div>
                        <div
                          className={`font-display text-lg font-black ${lineCb > 0 ? "text-red-700" : "text-emerald-700"}`}
                          data-testid={`ret-item-${idx}-cb`}
                        >
                          {fmtMoney(lineCb)}
                        </div>
                      </div>
                    </div>

                    {/* Status pills — giant tap targets */}
                    <div className="grid grid-cols-3 gap-2 mt-3">
                      {RETURN_STATUSES.map((st) => {
                        const active = it.status === st.key;
                        const Icon =
                          st.key === "returned" ? CheckCircle2 :
                          st.key === "damaged" ? AlertTriangle : XOctagon;
                        const baseTone =
                          st.tone === "emerald"
                            ? "border-emerald-600 text-emerald-700"
                            : st.tone === "amber"
                            ? "border-amber-600 text-amber-700"
                            : "border-red-700 text-red-700";
                        const activeTone =
                          st.tone === "emerald"
                            ? "bg-emerald-600 text-white border-emerald-700"
                            : st.tone === "amber"
                            ? "bg-amber-600 text-white border-amber-700"
                            : "bg-red-700 text-white border-red-900";
                        return (
                          <button
                            key={st.key}
                            type="button"
                            onClick={() => updateItem(idx, { status: st.key })}
                            className={`h-12 rounded-md border-2 font-bold uppercase tracking-wide text-xs flex flex-col items-center justify-center gap-0.5 transition-colors ${
                              active ? activeTone : `bg-white ${baseTone} hover:bg-slate-50`
                            }`}
                            data-testid={`ret-item-${idx}-status-${st.key}`}
                          >
                            <Icon className="w-4 h-4" />
                            <span className="text-[10px]">{t(st.label)}</span>
                          </button>
                        );
                      })}
                    </div>

                    {/* Returned qty (only if "returned" + > 1 issued) */}
                    {it.status === "returned" && parseFloat(it.source_quantity) > 1 && (
                      <div className="mt-2 grid grid-cols-2 gap-2 items-end">
                        <Field label={t("Qty Returned (of {n})").replace("{n}", String(it.source_quantity))}>
                          <Input
                            type="number"
                            min="0"
                            max={it.source_quantity}
                            step="1"
                            className={inputCls}
                            value={it.returned_quantity}
                            onChange={(e) => updateItem(idx, { returned_quantity: e.target.value })}
                            data-testid={`ret-item-${idx}-qty`}
                          />
                        </Field>
                        <p className="text-[11px] text-slate-500 leading-snug pb-3">
                          {t("Any not-returned units will be billed as Lost.")}
                        </p>
                      </div>
                    )}

                    {/* Note (required for damaged/lost) */}
                    {requireNote && (
                      <div className="mt-2">
                        <Field
                          label={
                            it.status === "damaged"
                              ? t("Damage description")
                              : t("Lost / not-returned reason")
                          }
                          required
                        >
                          <Textarea
                            className="border-2 border-amber-400 min-h-[50px]"
                            placeholder={t("Describe what happened")}
                            value={it.note}
                            onChange={(e) => updateItem(idx, { note: e.target.value })}
                            data-testid={`ret-item-${idx}-note`}
                          />
                        </Field>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Live chargeback total */}
            <div className="flex justify-end mt-3">
              <div
                className={`border-2 rounded px-4 py-2 text-right ${
                  cb.total > 0 ? "bg-red-50 border-red-700" : "bg-emerald-50 border-emerald-600"
                }`}
              >
                <div
                  className={`font-mono text-[9px] uppercase tracking-[0.25em] font-bold ${
                    cb.total > 0 ? "text-red-900" : "text-emerald-900"
                  }`}
                >
                  {t("Total Chargeback")}
                </div>
                <div
                  className="font-display text-2xl font-black text-slate-900"
                  data-testid="ret-total-chargeback"
                >
                  {fmtMoney(cb.total)}
                </div>
                <div className="font-mono text-[9px] text-slate-600 mt-0.5">
                  {t("Lost")} {fmtMoney(cb.lost)} · {t("Damaged")} {fmtMoney(cb.damaged)}
                </div>
              </div>
            </div>
          </Section>

          <Section title={t("Acknowledgment")}>
            <div className="bg-amber-50 border-l-4 border-amber-600 p-4 rounded">
              <p className="text-sm text-slate-800 leading-relaxed">
                {t("Any reimbursement or payroll deduction will be handled in accordance with applicable Florida law and the Fair Labor Standards Act (FLSA), and will not occur without proper authorization where required.")}
              </p>
            </div>
            <label className="flex items-start gap-3 cursor-pointer mt-3">
              <input
                type="checkbox"
                checked={data.acknowledgment}
                onChange={(e) => update({ acknowledgment: e.target.checked })}
                className="w-5 h-5 mt-0.5 accent-red-700"
                data-testid="ret-ack"
              />
              <span className="text-sm font-bold text-slate-900 leading-snug">
                {t("Both parties confirm the above return outcome is accurate and complete.")}
              </span>
            </label>
          </Section>

          {/* Optional employee email for CC */}
          <Section
            title={t("Email a Copy to Employee (optional)")}
            desc={
              issuance?.employee_email
                ? t("Pre-filled from the original issuance. Edit or clear to change.")
                : t("If provided, the employee will receive a copy of the signed receipt along with the Safety Department.")
            }
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
                data-testid="ret-employee-email"
              />
            </Field>
          </Section>

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

          <div className="sticky bottom-0 bg-white border-t-2 border-emerald-700 -mx-5 sm:-mx-8 px-5 sm:px-8 py-3 flex justify-between items-center shadow-lg gap-3">
            <div className="text-xs font-mono text-slate-600 truncate">
              <PackageCheck className="w-4 h-4 inline-block mr-1 text-emerald-700" />
              {t("Auto-emails Safety dept on submit")}
            </div>
            <Button
              type="submit"
              disabled={saving}
              className="bg-emerald-700 hover:bg-emerald-800 h-12 px-6 font-bold uppercase tracking-wide"
              data-testid="ret-submit"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Submitting…")}
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" /> {t("Save Check-In & Email PDF")}
                </>
              )}
            </Button>
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
  return <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">{children}</div>;
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
