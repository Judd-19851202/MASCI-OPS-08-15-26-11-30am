import React, { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  FileText,
  Loader2,
  Download,
  CheckCircle2,
  PackageCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { RefKicker } from "@/components/RefKicker";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api, API } from "@/lib/api";
import { isSafetyForms, getSafetyFormsToken } from "@/lib/safetyFormsAuth";
import { isAdmin, getAdminToken } from "@/lib/adminAuth";
import { isSafety, getSafetyToken } from "@/lib/safetyAuth";
import { fmtMoney } from "@/lib/safetyFormsSchema";
import { formatDateLong } from "@/lib/utils";
import { resolvePhotoSrc } from "@/lib/photoSrc";
import { toast } from "sonner";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const STATUS_TONES = {
  returned: { bg: "bg-emerald-100", fg: "text-emerald-800", border: "border-emerald-300", label: "Returned OK" },
  damaged: { bg: "bg-amber-100", fg: "text-amber-800", border: "border-amber-300", label: "Damaged" },
  lost: { bg: "bg-red-100", fg: "text-red-800", border: "border-red-300", label: "Lost" },
};

/**
 * Single shared view page for both Safety Forms record types.
 * Determined by the `kind` prop ("issuance" | "training") wired up in
 * App.js. Renders a clean print-friendly summary plus a Download PDF
 * button that streams the WeasyPrint output from the backend.
 */
export default function ViewSafetyForm({ kind = "issuance" }) {
  const { id } = useParams();
  const { t } = useT();
  const [doc, setDoc] = useState(null);
  const [err, setErr] = useState("");
  const [downloading, setDownloading] = useState(false);

  // iter323 · Safety Forms ownership — Safety Portal users are now
  // a first-class auth identity on this detail viewer. Admin still
  // works (global); legacy Safety-Forms token still works (backwards
  // compat). PM intentionally NOT included (preserves boundary).
  const authed = isSafety() || isSafetyForms() || isAdmin();
  const isTraining = kind === "training";
  const apiBase = isTraining
    ? "/safety-forms/equipment-trainings"
    : "/safety-forms/equipment-issuances";

  useEffect(() => {
    if (!authed) return;
    api
      .get(`${apiBase}/${id}`)
      .then((r) => setDoc(r.data))
      .catch((e) => setErr(e?.response?.data?.detail || "Not found"));
  }, [authed, apiBase, id]);

  if (!authed) {
    // iter323 · route unauthenticated bounces to the Safety Portal
    // login (the new owner) — NOT the legacy /safety/forms/login
    // (which EnforcePortalScope would treat as a portal-login path
    // and wipe an unrelated Safety token from an in-flight race).
    return <Navigate to="/safety-portal/login?from=safety-forms" replace />;
  }

  const downloadPdf = async (subPath = "/pdf", suffix = "") => {
    setDownloading(true);
    try {
      const headers = {};
      const adminTok = getAdminToken();
      const sfTok = getSafetyFormsToken();
      const safetyTok = getSafetyToken();
      if (adminTok) headers["X-Admin-Token"] = adminTok;
      if (sfTok) headers["X-Safety-Forms-Token"] = sfTok;
      // iter323 · include Safety Portal token so PDF downloads work
      // for signed-in Safety reviewers (backend already accepts it).
      if (safetyTok) headers["X-Safety-Token"] = safetyTok;
      const res = await fetch(`${API}${apiBase}/${id}${subPath}`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const cd = res.headers.get("content-disposition") || "";
      const m = /filename="?([^";]+)"?/i.exec(cd);
      a.href = url;
      a.download = m ? m[1] : `MASCI_safety_form${suffix}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error(e?.message || t("Could not download PDF"));
    } finally {
      setDownloading(false);
    }
  };

  if (err) {
    return (
      <div className="min-h-screen blueprint-bg p-8">
        <div className="max-w-2xl mx-auto bg-white border-2 border-red-300 rounded-md p-6">
          <h1 className="font-display text-2xl font-black">{t("Not found")}</h1>
          <p className="text-slate-600">{err}</p>
          <Link to="/safety/forms" className="text-red-700 font-bold underline">{t("Back")}</Link>
        </div>
      </div>
    );
  }
  if (!doc) {
    return (
      <div className="min-h-screen blueprint-bg flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-red-700" />
      </div>
    );
  }

  const items = doc.items || [];
  const total = (items || []).reduce(
    (sum, it) => sum + (parseFloat(it.quantity) || 0) * (parseFloat(it.unit_value) || 0),
    0,
  );

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700 print:hidden">
        <div className="max-w-4xl mx-auto px-3 sm:px-8 py-4 flex items-center justify-between gap-2 flex-wrap">
          <Link
            to="/safety/forms"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="view-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Back")}
          </Link>
          <MasciLogo variant="mark" size="md" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="sm" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-5 sm:px-8 py-8">
        <div className="mb-4 inline-flex items-center gap-2 px-3 py-1.5 rounded bg-emerald-50 border-2 border-emerald-300 text-emerald-800 font-mono text-xs uppercase tracking-wide font-bold">
          <CheckCircle2 className="w-4 h-4" /> {t("Submitted")}
        </div>

        <div className="bg-white border border-slate-200 rounded-md p-6 sm:p-8">
          <div className="flex items-start justify-between gap-4 border-b-4 border-red-700 pb-4 mb-5">
            <div>
              <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
                {t("Safety Department")}
              </span>
              {/* iter336 · review-side reference continuity · positioned
                  ABOVE the H1 to match the other 6 detail surfaces
                  (unified pattern). */}
              <RefKicker
                recordId={doc.issuance_number || doc.training_number || doc.id}
                testId="view-safety-form-ref"
                className="mt-1"
              />
              <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 leading-tight mt-1">
                {isTraining
                  ? t("Equipment Use & Care Training")
                  : t("Safety Equipment Issuance & Accountability")}
              </h1>
            </div>
            <Button
              onClick={() => downloadPdf("/pdf")}
              disabled={downloading}
              className="bg-red-700 hover:bg-red-800 h-10 font-bold uppercase tracking-wide text-xs"
              data-testid="view-download-pdf"
            >
              {downloading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Download className="w-4 h-4 mr-1" />}
              {t("Download PDF")}
            </Button>
          </div>

          {/* Employee */}
          <KvBlock title={t("Employee")} rows={[
            [t("Name"), doc.employee_name],
            [t("Employee ID"), doc.employee_id || "—"],
            [t("Position"), doc.position || "—"],
            [t("Project"), [doc.project_name, doc.project_number].filter(Boolean).join(" · ") || "—"],
          ]} />

          {isTraining ? (
            <KvBlock title={t("Training")} rows={[
              [t("Date"), formatDateLong(doc.training_date)],
              [t("Instructor"), doc.instructor_name],
              [t("Location"), doc.training_location || "—"],
            ]} />
          ) : (
            <KvBlock title={t("Issuance")} rows={[
              [t("Date Issued"), formatDateLong(doc.issued_date)],
              [t("Issued By"), doc.issued_by],
              [t("Location"), doc.location || "—"],
              [t("Condition"), <span key="c"><b>{doc.condition}</b>{doc.condition?.toLowerCase()==="damaged" && doc.condition_note ? <span className="text-red-700"> — {doc.condition_note}</span> : null}</span>],
            ]} />
          )}

          {/* Items table */}
          <h2 className="font-display text-lg font-black text-slate-900 mt-6 mb-2">
            {isTraining ? t("Equipment Trained") : t("Equipment Issued")}
          </h2>
          <div className="overflow-x-auto border border-slate-200 rounded">
            <table className="w-full text-sm">
              <thead className="bg-slate-100">
                <tr className="text-left font-mono text-[10px] uppercase tracking-wide text-slate-700">
                  <th className="px-3 py-2">#</th>
                  <th className="px-3 py-2">{t("Item")}</th>
                  <th className="px-3 py-2">{t("Description")}</th>
                  {isTraining ? (
                    <>
                      <th className="px-3 py-2">{t("Type")}</th>
                      <th className="px-3 py-2">{t("Mfr/Model")}</th>
                      <th className="px-3 py-2">{t("Notes")}</th>
                    </>
                  ) : (
                    <>
                      <th className="px-3 py-2">{t("Asset/Serial")}</th>
                      <th className="px-3 py-2 text-right">{t("Qty")}</th>
                      <th className="px-3 py-2 text-right">{t("Unit $")}</th>
                      <th className="px-3 py-2 text-right">{t("Line $")}</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {items.map((it, i) => {
                  const itemKey = isTraining ? "equipment_type" : "item_type";
                  const otherKey = isTraining ? "equipment_type_other" : "item_type_other";
                  const itemLabel =
                    it[itemKey] === "Other" && it[otherKey] ? `Other — ${it[otherKey]}` : it[itemKey];
                  return (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="px-3 py-2">{i + 1}</td>
                      <td className="px-3 py-2 font-medium">{itemLabel}</td>
                      <td className="px-3 py-2">{it.description || "—"}</td>
                      {isTraining ? (
                        <>
                          <td className="px-3 py-2">{it.training_type}</td>
                          <td className="px-3 py-2">{it.manufacturer_model || "—"}</td>
                          <td className="px-3 py-2 text-slate-600 text-xs">{it.notes || ""}</td>
                        </>
                      ) : (
                        <>
                          <td className="px-3 py-2">{it.asset_id || "—"}</td>
                          <td className="px-3 py-2 text-right">{it.quantity}</td>
                          <td className="px-3 py-2 text-right">{fmtMoney(it.unit_value)}</td>
                          <td className="px-3 py-2 text-right font-bold">
                            {fmtMoney((parseFloat(it.quantity) || 0) * (parseFloat(it.unit_value) || 0))}
                          </td>
                        </>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {!isTraining && (
            <div className="flex justify-end mt-2">
              <div className="bg-red-50 border-2 border-red-700 rounded px-4 py-2 text-right">
                <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-red-900 font-bold">
                  {t("Total Issued Value")}
                </div>
                <div className="font-display text-xl font-black text-slate-900">{fmtMoney(total)}</div>
              </div>
            </div>
          )}

          {/* Check-In / Return — issuance only */}
          {!isTraining && !doc.return && (
            <div className="mt-6 p-4 rounded-md border-2 border-emerald-300 bg-emerald-50 flex items-center justify-between gap-3 flex-wrap">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-emerald-900 font-bold">
                  {t("Equipment Out")}
                </div>
                <div className="text-sm text-slate-700 mt-0.5">
                  {t("When this gear comes back, log the check-in to close the loop.")}
                </div>
              </div>
              <Link
                to={`/safety/forms/equipment-issuance/${id}/return`}
                className="inline-flex items-center gap-2 h-10 px-4 rounded-md bg-emerald-700 hover:bg-emerald-800 text-white font-bold uppercase tracking-wide text-xs border-b-2 border-emerald-900"
                data-testid="view-checkin-btn"
              >
                <PackageCheck className="w-4 h-4" /> {t("Start Check-In / Return")}
              </Link>
            </div>
          )}

          {/* Return summary — issuance only, when already returned */}
          {!isTraining && doc.return && (
            <div className="mt-6 p-5 rounded-md border-2 border-slate-300 bg-white">
              <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-emerald-700 font-bold inline-flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> {t("Returned")}
                  </div>
                  <h2 className="font-display text-lg font-black text-slate-900 mt-1">
                    {t("Check-In Receipt")}
                  </h2>
                  <p className="text-xs text-slate-600 mt-0.5">
                    {formatDateLong(doc.return.check_in_date)} · {t("Received by")} {doc.return.received_by}
                  </p>
                </div>
                <Button
                  onClick={() => downloadPdf("/return/pdf", "_return")}
                  disabled={downloading}
                  variant="outline"
                  className="h-9 border-2 border-emerald-600 text-emerald-700 hover:bg-emerald-50 font-bold uppercase tracking-wide text-xs"
                  data-testid="view-download-return-pdf"
                >
                  {downloading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Download className="w-4 h-4 mr-1" />}
                  {t("Download Return PDF")}
                </Button>
              </div>

              <div className="overflow-x-auto border border-slate-200 rounded">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr className="text-left font-mono text-[10px] uppercase tracking-wide text-slate-700">
                      <th className="px-3 py-2">{t("Item")}</th>
                      <th className="px-3 py-2 text-right">{t("Issued")}</th>
                      <th className="px-3 py-2 text-right">{t("Returned")}</th>
                      <th className="px-3 py-2">{t("Status")}</th>
                      <th className="px-3 py-2 text-right">{t("Chargeback")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(doc.return.items || []).map((it, i) => {
                      const tone = STATUS_TONES[it.status] || STATUS_TONES.returned;
                      const sq = parseFloat(it.source_quantity) || 0;
                      const rq = parseFloat(it.returned_quantity) || 0;
                      const uv = parseFloat(it.source_unit_value) || 0;
                      const cb =
                        it.status === "lost" ? sq * uv :
                        it.status === "damaged" ? sq * uv :
                        it.status === "returned" && rq < sq ? (sq - rq) * uv : 0;
                      const itemLabel =
                        it.source_item_type === "Other" && it.source_item_type_other
                          ? `Other — ${it.source_item_type_other}`
                          : it.source_item_type;
                      return (
                        <tr key={i} className="border-t border-slate-100 align-top">
                          <td className="px-3 py-2">
                            <div className="font-medium">{itemLabel}</div>
                            <div className="text-xs text-slate-500">{it.source_description}</div>
                          </td>
                          <td className="px-3 py-2 text-right">{sq}</td>
                          <td className="px-3 py-2 text-right">{rq}</td>
                          <td className="px-3 py-2">
                            <span className={`inline-block px-2 py-0.5 rounded font-mono text-[10px] font-bold uppercase tracking-wide border ${tone.bg} ${tone.fg} ${tone.border}`}>
                              {t(tone.label)}
                            </span>
                            {it.note ? <div className="text-xs text-slate-600 mt-1">{it.note}</div> : null}
                          </td>
                          <td className={`px-3 py-2 text-right font-bold ${cb > 0 ? "text-red-700" : "text-slate-600"}`}>
                            {fmtMoney(cb)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-between items-end mt-3 flex-wrap gap-3">
                {doc.return.return_notes ? (
                  <div className="text-xs text-slate-600 max-w-md">
                    <span className="font-mono text-[9px] uppercase tracking-[0.2em] font-bold text-slate-500">
                      {t("Notes")}:
                    </span>{" "}
                    {doc.return.return_notes}
                  </div>
                ) : <span />}
                <div
                  className={`border-2 rounded px-4 py-2 text-right ${
                    (doc.return.chargeback?.total || 0) > 0 ? "bg-red-50 border-red-700" : "bg-emerald-50 border-emerald-600"
                  }`}
                >
                  <div className={`font-mono text-[9px] uppercase tracking-[0.25em] font-bold ${
                    (doc.return.chargeback?.total || 0) > 0 ? "text-red-900" : "text-emerald-900"
                  }`}>
                    {t("Total Chargeback")}
                  </div>
                  <div className="font-display text-xl font-black text-slate-900">
                    {fmtMoney(doc.return.chargeback?.total || 0)}
                  </div>
                  <div className="font-mono text-[9px] text-slate-600 mt-0.5">
                    {t("Lost")} {fmtMoney(doc.return.chargeback?.lost || 0)} · {t("Damaged")} {fmtMoney(doc.return.chargeback?.damaged || 0)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {isTraining && (doc.topics || []).length > 0 && (
            <>
              <h2 className="font-display text-lg font-black text-slate-900 mt-6 mb-2">{t("Topics Covered")}</h2>
              <div className="flex flex-wrap gap-2">
                {(doc.topics || []).map((k) => (
                  <span key={k} className="px-2 py-1 rounded bg-amber-100 text-amber-900 font-mono text-[10px] uppercase tracking-wide font-bold">
                    {k.replace(/_/g, " ")}
                    {k === "other" && doc.topic_other ? ` — ${doc.topic_other}` : ""}
                  </span>
                ))}
              </div>
            </>
          )}

          {!isTraining && (doc.photos || []).length > 0 && (
            <>
              <h2 className="font-display text-lg font-black text-slate-900 mt-6 mb-2">{t("Photos")}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
                {(doc.photos || []).map((p, i) => (
                  <img key={i} src={resolvePhotoSrc(p)} alt="" loading="lazy" decoding="async" className="w-full h-32 object-cover rounded border border-slate-200" />
                ))}
              </div>
            </>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-8 pt-6 border-t-2 border-slate-200">
            <SigBlock label={t("Employee Signature") + " · " + (doc.employee_name || "")} sig={doc.employee_signature} />
            <SigBlock
              label={
                (isTraining ? t("Instructor Signature") : t("Supervisor Signature")) +
                " · " +
                (isTraining ? doc.instructor_name : doc.issued_by) || ""
              }
              sig={isTraining ? doc.instructor_signature : doc.supervisor_signature}
            />
          </div>

          <p className="text-[10px] font-mono text-slate-400 uppercase tracking-[0.2em] text-center mt-8 pt-4 border-t border-slate-100">
            {t("Generated")} {doc.created_at ? formatPlatformTime(doc.created_at) : ""} ·
            {" "}MASCI General Contractors Inc. · {t("Confidential")}
          </p>
        </div>
      </main>
    </div>
  );
}

function KvBlock({ title, rows }) {
  return (
    <div className="mb-4">
      <h2 className="font-display text-lg font-black text-slate-900 mt-6 mb-2 border-b-2 border-slate-200 pb-1">{title}</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
        {rows.map(([k, v], i) => (
          <div key={i} className="flex gap-2">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold w-32 shrink-0 pt-0.5">{k}</span>
            <span className="text-slate-900">{v ?? "—"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SigBlock({ label, sig }) {
  return (
    <div>
      {sig ? (
        <img src={sig} alt="" className="max-h-24 max-w-full border-b-2 border-slate-900 pb-1" />
      ) : (
        <div className="border-b-2 border-slate-900 h-20" />
      )}
      <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-slate-600 mt-2">{label}</div>
    </div>
  );
}
