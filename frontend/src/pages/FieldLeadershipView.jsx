// Single Field Leadership record viewer.
// Renders metadata + every detail key + photos + signatures, with a
// "Download PDF" button. Read-only; archive (admin) goes through the
// records table.

import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, FileDown, AlertTriangle, CheckCircle2, Camera } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { isAdmin } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { resolvePhotoSrc } from "@/lib/photoSrc";
import { getLeadershipToken } from "@/lib/leadershipAuth";
import { FIELD_LEADERSHIP_FORMS } from "@/lib/fieldLeadershipSchemas";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";

export default function FieldLeadershipView() {
  const { t, lang } = useT();
  const navigate = useNavigate();
  const { id } = useParams();
  const [rec, setRec] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getLeadershipToken() && !isAdmin() && !getPmToken()) {
      navigate("/leadership", { replace: true });
      return;
    }
    api.get(`/field-leadership/${id}`)
      .then((r) => setRec(r.data))
      .catch((err) => toast.error(err?.response?.data?.detail || t("Could not load record")))
      .finally(() => setLoading(false));
    // eslint-disable-next-line
  }, [id]);

  const kindLabel = (k) => {
    const f = FIELD_LEADERSHIP_FORMS.find((x) => x.kind === k);
    if (!f) return k;
    return f.title[lang] || f.title.en;
  };

  const downloadPdf = async () => {
    try {
      const r = await api.get(`/field-leadership/${id}/pdf`, { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      window.open(url, "_blank");
      setTimeout(() => URL.revokeObjectURL(url), 30000);
    } catch {
      toast.error(t("Could not open PDF"));
    }
  };

  if (loading) return <main className="min-h-screen bg-slate-50 p-8 text-center text-slate-500">{t("Loading…")}</main>;
  if (!rec) return <main className="min-h-screen bg-slate-50 p-8 text-center text-slate-500">{t("Not found")}</main>;

  const details = rec.details_en || rec.details || {};
  const meta = [
    [t("Form Type"), kindLabel(rec.kind)],
    [t("Employee"), rec.employee_name],
    [t("Position"), rec.employee_position],
    [t("Supervisor"), rec.supervisor_name],
    [t("Job"), rec.project_number ? `${rec.project_number} · ${rec.project_name || ""}` : rec.project_name],
    [t("Location"), rec.location || rec.work_area],
    [t("Assigned PM"), rec.assigned_pm],
    [t("Date / Time"), (rec.occurred_at || "").replace("T", " ").slice(0, 16)],
    [t("Submitted via"), rec.submitted_via_role],
    [t("Language"), rec.language === "es" ? "Español → English" : "English"],
  ];

  return (
    <main className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
            <Button
              onClick={downloadPdf}
              variant="outline"
              className="h-10 px-3 border-2 border-slate-600 bg-slate-800 text-white hover:border-amber-500 text-xs font-bold uppercase tracking-wide"
              data-testid="leadership-view-pdf"
            >
              <FileDown className="w-3.5 h-3.5 mr-1" />{t("Download PDF")}
            </Button>
          </div>
        </div>
      </header>

      <section className="max-w-3xl mx-auto px-5 sm:px-8 pt-6">
        <div className="mb-6 flex items-center gap-4">
          {/* iter96 — secondary back goes to the user's home portal,
              not the supervisor form-entry hub. */}
          <Link
            to="/leadership/records"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-red-700 font-bold"
            data-testid="leadership-view-back-records"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Records")}
          </Link>
          <span className="text-slate-300">·</span>
          <Link
            to={isAdmin() ? "/admin" : getPmToken() ? "/pm" : "/leadership"}
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-red-700 font-bold"
            data-testid="leadership-view-back-hub"
          >
            <ArrowLeft className="w-3.5 h-3.5" />{" "}
            {isAdmin() ? t("Admin Console") : getPmToken() ? t("PM Hub") : t("Field Leadership")}
          </Link>
        </div>

        <div className="font-mono text-xs uppercase tracking-[0.2em] text-red-700">{t("Field Leadership")}</div>
        <div className="flex items-center justify-between gap-4 flex-wrap mt-1">
          <h1 className="font-display text-3xl sm:text-4xl font-black">{kindLabel(rec.kind)}</h1>
          {rec.doc_id && (
            <div
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-red-50 border-2 border-red-300"
              data-testid="record-doc-id-badge"
            >
              <span className="font-mono text-[9px] uppercase tracking-[0.22em] text-red-700 font-bold">{t("Doc ID")}</span>
              <span className="font-mono text-base font-black text-red-800 tracking-wide tabular-nums">{rec.doc_id}</span>
            </div>
          )}
        </div>

        <Card className="mt-5 p-5">
          <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-b border-slate-200 pb-2 mb-3">{t("Summary")}</h3>
          <table className="w-full text-sm">
            <tbody>
              {meta.map(([k, v]) => (
                <tr key={k} className="border-b border-slate-100">
                  <th className="text-left py-1.5 pr-3 font-semibold text-slate-700 w-1/3">{k}</th>
                  <td className="py-1.5">{v || <span className="text-slate-400">—</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        {/* Equipment line-aware galleries — beats the generic <dl> table.
            For equipment_checkout we render each line's photos in a card.
            For equipment_return we render side-by-side ORIGINAL vs RETURN
            photos so PMs can sign off on damage in one glance. The data
            for "original" comes from the line itself (newer submissions
            from iter52+ carry original_photos forward) OR from a fresh
            lookup of the parent checkout record (older return records). */}
        {(rec.kind === "equipment_checkout" || rec.kind === "equipment_return") && (
          <EquipmentComparisonCard rec={rec} details={details} t={t} />
        )}

        {Object.keys(details).length > 0 && rec.kind !== "equipment_checkout" && rec.kind !== "equipment_return" && (
          <Card className="mt-4 p-5">
            <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-b border-slate-200 pb-2 mb-3">{t("Details")}</h3>
            <dl className="space-y-3">
              {Object.entries(details).map(([k, v]) => (
                <div key={k}>
                  <dt className="font-semibold text-sm text-slate-700">{k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</dt>
                  <dd className="text-sm text-slate-800 whitespace-pre-wrap mt-0.5">
                    {v === null || v === undefined || v === "" ? <span className="text-slate-400">—</span>
                      : typeof v === "object" ? (
                        <table className="w-full mt-1">
                          <tbody>
                            {Object.entries(v).map(([kk, vv]) => (
                              <tr key={kk}><th className="text-left text-xs text-slate-500 pr-3 py-0.5 font-mono">{kk}</th><td className="text-xs py-0.5">{String(vv)}</td></tr>
                            ))}
                          </tbody>
                        </table>
                      ) : String(v)}
                  </dd>
                </div>
              ))}
            </dl>
          </Card>
        )}

        {Array.isArray(rec.photos) && rec.photos.length > 0 && (
          <Card className="mt-4 p-5">
            <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-b border-slate-200 pb-2 mb-3">{t("Photos")}</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4">
              {rec.photos.map((p, i) => (
                <img key={i} src={resolvePhotoSrc(p)} alt={`photo ${i}`} className="w-full rounded border border-slate-200 object-contain max-h-48 bg-slate-50" />
              ))}
            </div>
          </Card>
        )}

        {(rec.supervisor_signature || rec.employee_signature || rec.witness_signature) && (
          <Card className="mt-4 p-5">
            <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-b border-slate-200 pb-2 mb-3">{t("Signatures")}</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4">
              {rec.supervisor_signature && (
                <div className="border-2 border-slate-200 rounded p-3 bg-white">
                  <div className="text-xs font-mono uppercase tracking-[0.15em] text-slate-500">{t("Supervisor")}</div>
                  <img src={resolvePhotoSrc(rec.supervisor_signature)} alt="sig" className="max-h-20 mt-1" />
                  <div className="font-bold mt-1 text-sm">{rec.supervisor_name}</div>
                </div>
              )}
              {rec.employee_refused ? (
                <div className="border-2 border-red-200 rounded p-3 bg-red-50">
                  <div className="text-xs font-mono uppercase tracking-[0.15em] text-red-700">{t("Employee Refused")}</div>
                  <div className="font-bold mt-1 text-sm">{rec.employee_name}</div>
                </div>
              ) : rec.employee_signature && (
                <div className="border-2 border-slate-200 rounded p-3 bg-white">
                  <div className="text-xs font-mono uppercase tracking-[0.15em] text-slate-500">{t("Employee")}</div>
                  <img src={resolvePhotoSrc(rec.employee_signature)} alt="sig" className="max-h-20 mt-1" />
                  <div className="font-bold mt-1 text-sm">{rec.employee_name}</div>
                </div>
              )}
              {rec.witness_signature && (
                <div className="border-2 border-slate-200 rounded p-3 bg-white">
                  <div className="text-xs font-mono uppercase tracking-[0.15em] text-slate-500">{t("Witness")}</div>
                  <img src={resolvePhotoSrc(rec.witness_signature)} alt="sig" className="max-h-20 mt-1" />
                  <div className="font-bold mt-1 text-sm">{rec.witness_name}</div>
                </div>
              )}
            </div>
          </Card>
        )}
      </section>
    </main>
  );
}

// ─────────────────────────────────────────────────────────────────────
// EquipmentComparisonCard
// ─────────────────────────────────────────────────────────────────────
// For Equipment Checkout: a per-line card with all photos in a 4-up grid.
// For Equipment Return: a side-by-side ORIGINAL vs RETURN comparison so
// admins/PMs can sign off on damage claims in one glance instead of
// downloading the PDF. If the return line lacks ``original_photos``
// (older record submitted before iter52), we transparently look up the
// parent checkout via ``checkout_id`` and pull photos by ``line_index``.

const DAMAGE_RC = ["Damaged", "Missing", "Lost"];

function PhotoLightboxLink({ src, idx, label }) {
  const resolved = resolvePhotoSrc(src);
  return (
    <a
      href={resolved}
      target="_blank"
      rel="noopener noreferrer"
      className="block aspect-square rounded overflow-hidden border border-slate-200 bg-white hover:border-amber-500 transition-colors"
      title={`${label} ${idx + 1}`}
      data-testid={`photo-${label}-${idx}`}
    >
      <img
        src={resolved}
        alt={`${label} ${idx + 1}`}
        loading="lazy"
        decoding="async"
        className="w-full h-full object-cover"
      />
    </a>
  );
}

function EquipmentComparisonCard({ rec, details, t }) {
  const lines = useMemo(
    () => Array.isArray(details?.equipment_lines) ? details.equipment_lines : [],
    [details]
  );
  // Backfill original_photos for older return records that didn't store
  // them inline. Indexed by line_index to keep the join trivial.
  const [backfill, setBackfill] = useState({});
  useEffect(() => {
    if (rec.kind !== "equipment_return") return;
    const missing = lines
      .map((ln, idx) => ({ ln, idx }))
      .filter(({ ln }) =>
        !!ln.checkout_id &&
        (!Array.isArray(ln.original_photos) || ln.original_photos.length === 0)
      );
    if (missing.length === 0) return;
    // Group by checkout_id to minimize round-trips when one return covers
    // multiple lines from the same checkout (the common case).
    const byCheckout = {};
    for (const m of missing) {
      const k = m.ln.checkout_id;
      (byCheckout[k] = byCheckout[k] || []).push(m);
    }
    let cancelled = false;
    (async () => {
      const next = {};
      for (const [checkoutId, group] of Object.entries(byCheckout)) {
        try {
          const r = await api.get(`/field-leadership/${checkoutId}`);
          const parent = r.data || {};
          const parentDetails = parent.details_en || parent.details || {};
          const parentLines = Array.isArray(parentDetails.equipment_lines)
            ? parentDetails.equipment_lines : [];
          for (const m of group) {
            const li = typeof m.ln.line_index === "number" ? m.ln.line_index : null;
            if (li !== null && parentLines[li]) {
              next[m.idx] = parentLines[li].photos || [];
            }
          }
        } catch {
          /* parent record unreachable — leave the lookup empty, UI will
             show "no original photos on file" fallback */
        }
      }
      if (!cancelled) setBackfill(next);
    })();
    return () => { cancelled = true; };
  }, [rec.kind, lines]);

  if (lines.length === 0) return null;

  // Top-line totals so admins see scope at a glance.
  const totals = lines.reduce((acc, ln) => {
    const qty = Number(ln.qty) || 0;
    const rv = Number(ln.replacement_value) || 0;
    acc.value += qty * rv;
    if (rec.kind === "equipment_return") {
      const rc = (ln.return_condition || "").trim();
      const isDamage = DAMAGE_RC.includes(rc);
      const override = ln.damage_amount === "" || ln.damage_amount === null
        || ln.damage_amount === undefined ? null : Number(ln.damage_amount);
      const dmg = override !== null && !Number.isNaN(override)
        ? override : (isDamage ? qty * rv : 0);
      acc.damage += dmg;
    }
    return acc;
  }, { value: 0, damage: 0 });

  const isReturn = rec.kind === "equipment_return";
  const fmtMoney = (n) =>
    `$${(Number(n) || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  return (
    <Card className="mt-4 p-5" data-testid="equipment-comparison-card">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-200 gap-2 flex-wrap">
        <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700 font-bold">
          {isReturn ? t("Return Comparison — Before vs. After") : t("Equipment Issued — Photos by Item")}
        </h3>
        <div className="flex items-center gap-3 text-sm">
          <div className="text-slate-600">
            {lines.length} {lines.length === 1 ? t("item") : t("items")}
          </div>
          <div className="font-mono text-xs text-slate-500">·</div>
          <div className="font-bold text-slate-900 tabular-nums">{fmtMoney(totals.value)}</div>
          {isReturn && (
            <div
              className={`px-2 py-0.5 rounded font-mono text-[10px] uppercase tracking-[0.18em] font-bold tabular-nums ${
                totals.damage > 0
                  ? "bg-red-100 text-red-800 border border-red-300"
                  : "bg-emerald-100 text-emerald-800 border border-emerald-300"
              }`}
              data-testid="equipment-comparison-damage-pill"
            >
              {totals.damage > 0
                ? `${t("Damage owed")}: ${fmtMoney(totals.damage)}`
                : t("Clean return")}
            </div>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {lines.map((ln, idx) => {
          const qty = Number(ln.qty) || 0;
          const rv = Number(ln.replacement_value) || 0;
          const lineValue = qty * rv;
          const rc = (ln.return_condition || "").trim();
          const isDamage = isReturn && DAMAGE_RC.includes(rc);
          const overrideNum = ln.damage_amount === "" || ln.damage_amount === null
            || ln.damage_amount === undefined ? null : Number(ln.damage_amount);
          const lineDamage = overrideNum !== null && !Number.isNaN(overrideNum)
            ? overrideNum : (isDamage ? lineValue : 0);
          const originalPhotos = Array.isArray(ln.original_photos) && ln.original_photos.length > 0
            ? ln.original_photos
            : (backfill[idx] || []);
          const returnPhotos = Array.isArray(ln.return_photos) ? ln.return_photos : [];
          const checkoutPhotos = Array.isArray(ln.photos) ? ln.photos : [];
          return (
            <div
              key={idx}
              className={`rounded-md border-2 p-3 sm:p-4 ${
                isDamage ? "border-red-300 bg-red-50/40" : "border-slate-200 bg-white"
              }`}
              data-testid={`equipment-comparison-line-${idx}`}
            >
              <div className="flex items-start justify-between gap-2 flex-wrap mb-3">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold">
                    {t("Item")} #{idx + 1}
                    {ln.checkout_id && isReturn && (
                      <span className="ml-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200 normal-case tracking-normal text-[9px] font-bold">
                        <CheckCircle2 className="w-2.5 h-2.5" /> {t("Matched checkout")}
                      </span>
                    )}
                    {isDamage && (
                      <span className="ml-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-red-200 text-red-900 normal-case tracking-normal text-[9px] font-bold">
                        <AlertTriangle className="w-2.5 h-2.5" /> {rc}
                      </span>
                    )}
                  </div>
                  <div className="font-display font-bold text-base text-slate-900 mt-1">
                    {[ln.manufacturer, ln.name].filter(Boolean).join(" · ") || "—"}
                  </div>
                  <div className="text-xs font-mono text-slate-500">
                    {ln.model && `${t("Model")}: ${ln.model} · `}
                    {ln.serial && `${t("S/N")}: ${ln.serial} · `}
                    {`${t("Qty")}: ${qty}`}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">{t("Replacement")}</div>
                  <div className="font-display font-bold text-base tabular-nums">{fmtMoney(lineValue)}</div>
                  {isReturn && lineDamage > 0 && (
                    <div className="text-red-700 font-mono text-xs font-bold tabular-nums mt-0.5">
                      {t("Damage")}: {fmtMoney(lineDamage)}
                    </div>
                  )}
                </div>
              </div>

              {isReturn ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                  {/* ORIGINAL */}
                  <div className="rounded border-2 border-emerald-300 bg-emerald-50 p-2.5">
                    <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-900 font-bold mb-2 flex items-center gap-1.5">
                      <Camera className="w-3.5 h-3.5" />
                      {t("Original at checkout")}
                      <span className="normal-case tracking-normal text-emerald-700 font-sans">
                        ({originalPhotos.length})
                      </span>
                    </div>
                    {ln.condition && (
                      <div className="text-xs text-emerald-900 mb-2">
                        <span className="font-mono uppercase tracking-[0.15em] text-[10px] mr-1.5">{t("Condition")}:</span>
                        <span className="font-bold">{ln.condition}</span>
                      </div>
                    )}
                    {originalPhotos.length > 0 ? (
                      <div className="grid grid-cols-2 gap-1.5">
                        {originalPhotos.slice(0, 8).map((src, pi) => (
                          <PhotoLightboxLink
                            key={pi}
                            src={src}
                            idx={pi}
                            label={`original-${idx}`}
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="text-xs text-emerald-900/70 italic font-mono px-1 py-3 text-center">
                        {ln.checkout_id
                          ? t("Looking up checkout photos…")
                          : t("No original photos on file (manual return entry)")}
                      </div>
                    )}
                  </div>

                  {/* RETURN */}
                  <div className={`rounded border-2 p-2.5 ${
                    isDamage ? "border-red-400 bg-red-50" : "border-amber-300 bg-amber-50"
                  }`}>
                    <div className={`font-mono text-[10px] uppercase tracking-[0.22em] font-bold mb-2 flex items-center gap-1.5 ${
                      isDamage ? "text-red-800" : "text-amber-900"
                    }`}>
                      <Camera className="w-3.5 h-3.5" />
                      {t("Returned condition")}
                      <span className={`normal-case tracking-normal font-sans ${
                        isDamage ? "text-red-700" : "text-amber-700"
                      }`}>
                        ({returnPhotos.length})
                      </span>
                    </div>
                    {rc && (
                      <div className={`text-xs mb-2 ${isDamage ? "text-red-900" : "text-amber-900"}`}>
                        <span className="font-mono uppercase tracking-[0.15em] text-[10px] mr-1.5">{t("Condition")}:</span>
                        <span className="font-bold">{rc}</span>
                      </div>
                    )}
                    {returnPhotos.length > 0 ? (
                      <div className="grid grid-cols-2 gap-1.5">
                        {returnPhotos.slice(0, 8).map((src, pi) => (
                          <PhotoLightboxLink
                            key={pi}
                            src={src}
                            idx={pi}
                            label={`return-${idx}`}
                          />
                        ))}
                      </div>
                    ) : (
                      <div className={`text-xs italic font-mono px-1 py-3 text-center ${
                        isDamage ? "text-red-800/70" : "text-amber-800/70"
                      }`}>
                        {t("No return photos uploaded")}
                      </div>
                    )}
                    {(ln.return_notes || "").trim() && (
                      <div className={`mt-2 pt-2 border-t text-xs ${
                        isDamage ? "border-red-200 text-red-900" : "border-amber-200 text-amber-900"
                      }`}>
                        <span className="font-mono uppercase tracking-[0.15em] text-[10px] mr-1.5">{t("Notes")}:</span>
                        {ln.return_notes}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                /* Checkout-only mode: simple per-line photo grid. */
                <div>
                  {ln.condition && (
                    <div className="text-xs text-slate-700 mb-2">
                      <span className="font-mono uppercase tracking-[0.15em] text-[10px] mr-1.5">{t("Condition")}:</span>
                      <span className="font-bold">{ln.condition}</span>
                    </div>
                  )}
                  {checkoutPhotos.length > 0 ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3">
                      {checkoutPhotos.slice(0, 8).map((src, pi) => (
                        <PhotoLightboxLink
                          key={pi}
                          src={src}
                          idx={pi}
                          label={`checkout-${idx}`}
                        />
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-slate-500 italic font-mono px-1 py-3 text-center">
                      {t("No photos uploaded for this item")}
                    </div>
                  )}
                  {(ln.notes || "").trim() && (
                    <div className="mt-2 pt-2 border-t border-slate-200 text-xs text-slate-700">
                      <span className="font-mono uppercase tracking-[0.15em] text-[10px] mr-1.5">{t("Notes")}:</span>
                      {ln.notes}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
