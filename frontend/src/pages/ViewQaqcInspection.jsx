import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Printer, Loader2, Trash2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { isAdmin } from "@/lib/adminAuth";
import { toast } from "sonner";
import { SubmitLangBadge } from "@/components/SubmitLangBadge";
import { formatDateLong } from "@/lib/utils";

const KIND_LABEL = {
  concrete_form: "Concrete Form Inspection",
  rebar: "Rebar Inspection",
  subcontractor_work: "Subcontractor Work Inspection",
};

/**
 * ViewQaqcInspection — admin / PM print-friendly read view.
 * Pattern matches ViewInspection.jsx (browser print = PDF).
 */
export default function ViewQaqcInspection() {
  const { id } = useParams();
  const { t } = useT();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.get(`/qaqc-inspections/${id}`).then((r) => setData(r.data))
      .catch((e) => setErr(e?.response?.data?.detail || "Failed to load"))
      .finally(() => setLoading(false));
  }, [id]);

  async function onDelete() {
    if (!window.confirm(t("Delete this QA/QC inspection?"))) return;
    try {
      await api.delete(`/qaqc-inspections/${id}`);
      toast.success(t("Deleted."));
      window.location.href = "/admin/qaqc";
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed");
    }
  }

  if (loading) return <Centered>{t("Loading…")}<Loader2 className="w-4 h-4 animate-spin inline-block ml-2" /></Centered>;
  if (err || !data) return <Centered>{err || t("Not found.")}</Centered>;

  const failItems = (data.checklist || []).filter((c) => c.result === "fail");

  return (
    <div className="min-h-screen blueprint-bg print:blueprint-bg-none">
      <header className="bg-slate-900 border-b-4 border-emerald-600 print:hidden">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-5 sm:px-8 py-6 print:py-0">
        <div className="flex items-center justify-between mb-4 print:hidden">
          <Link
            to={isAdmin() ? "/admin/qaqc" : "/qaqc"}
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-emerald-700 font-bold"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {isAdmin() ? "Admin · QA/QC" : "QA/QC"}
          </Link>
          <div className="flex gap-2">
            <Button onClick={() => window.print()} variant="outline" size="sm">
              <Printer className="w-4 h-4 mr-1" /> {t("Print / PDF")}
            </Button>
            {isAdmin() && (
              <Button onClick={onDelete} variant="outline" size="sm" className="text-red-700">
                <Trash2 className="w-4 h-4 mr-1" /> {t("Delete")}
              </Button>
            )}
          </div>
        </div>

        <div className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print:border-none print:p-0">
          <div className="border-b-2 border-emerald-600 pb-3 mb-5">
            <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-emerald-700 font-bold">
              QA / QC · {KIND_LABEL[data.inspection_kind] || "QA/QC Inspection"}
            </span>
            <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 leading-tight mt-1">
              {data.project_name}
            </h1>
            <div className="font-mono text-xs text-slate-500 mt-1">
              {formatDateLong(data.inspection_date)} · {data.inspection_time} · {data.location}
            </div>
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 mt-1 flex items-center gap-2 flex-wrap">
              {data.doc_id && (
                <span
                  className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-50 border border-emerald-300 text-emerald-800 font-bold tabular-nums tracking-wide"
                  data-testid="record-doc-id-badge"
                >
                  <span className="text-[9px] uppercase tracking-[0.22em] text-emerald-700">Doc ID</span>
                  {data.doc_id}
                </span>
              )}
              <span>ID · {data.id?.slice(0, 8).toUpperCase()}</span>
            </div>
            {data.submit_language === "es" && (
              <div className="mt-2"><SubmitLangBadge lang={data.submit_language} /></div>
            )}
          </div>

          {failItems.length > 0 && (
            <div className="border-2 border-red-400 bg-red-50 rounded p-3 mb-5 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-700 mt-0.5 shrink-0" />
              <div>
                <div className="font-display font-black text-red-900">
                  {failItems.length} {t("item(s) failed inspection")}
                </div>
                <div className="text-sm text-slate-800 mt-1">{data.deficiencies || t("See deficiencies below.")}</div>
              </div>
            </div>
          )}

          <KVGrid pairs={[
            [t("Project Number"), data.project_number],
            [t("Client"), data.client],
            [t("Project Manager"), data.pm_name],
            [t("Subcontractor"), data.subcontractor_name],
            [t("Crew / Company"), data.crew_company],
            [t("Inspector"), data.inspector_name],
            [t("Work Activity"), data.work_activity],
            [t("Work Area / Station"), data.work_area],
            [t("Weather"), data.weather_conditions],
            ...(data.inspection_kind === "concrete_form"
              ? [
                  [t("Mix Design"), data.mix_design],
                  [t("Yards Ordered (CY)"), data.yards_ordered],
                  [t("Concrete Vendor"), data.concrete_vendor],
                ]
              : []),
          ]} />

          <Heading>{t("Checklist")}</Heading>
          <div className="space-y-2">
            {(data.checklist || []).map((c) => (
              <div key={c.key} className="flex items-start gap-3 border-b border-slate-100 py-2">
                <span className={"font-mono text-[10px] font-bold uppercase tracking-[0.1em] px-2 py-0.5 rounded " +
                  (c.result === "pass" ? "bg-emerald-100 text-emerald-900" :
                   c.result === "fail" ? "bg-red-100 text-red-900" :
                   "bg-slate-100 text-slate-600")
                }>
                  {c.result === "pass" ? t("PASS") :
                   c.result === "fail" ? t("FAIL") :
                   t("N/A")}
                </span>
                <div className="flex-1 text-sm text-slate-900">
                  <div>{t(c.label)}</div>
                  {c.note && <div className="text-xs text-slate-500 mt-0.5">↳ {c.note}</div>}
                </div>
              </div>
            ))}
          </div>

          <KVGrid pairs={[
            [t("Pass Items"), data.pass_count],
            [t("Fail Items"), data.fail_count],
            [t("N/A Items"), data.na_count],
          ]} />

          <Heading>{t("Notes & Corrective Actions")}</Heading>
          <Para label={t("Inspection Notes")} value={data.inspection_notes} />
          <Para label={t("Deficiencies")} value={data.deficiencies} />
          <Para label={t("Corrective Actions")} value={data.corrective_actions} />

          {data.photos?.length > 0 && (
            <>
              <Heading>{t("Photos")} ({data.photos.length})</Heading>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {data.photos.map((p, i) => (
                  <img key={i} src={p} alt={`Photo ${i + 1}`} className="w-full h-32 object-cover rounded border border-slate-300" />
                ))}
              </div>
            </>
          )}

          <Heading>{t("Sign-Off")}</Heading>
          {data.inspector_signature && (
            <SigBlock label="Inspector" name={data.inspector_name} sig={data.inspector_signature} />
          )}
          {data.sub_rep_signature && (
            <SigBlock label="Subcontractor Rep" name={data.sub_rep_name} sig={data.sub_rep_signature} />
          )}
        </div>
      </main>
    </div>
  );
}

function Centered({ children }) {
  return <div className="min-h-screen flex items-center justify-center font-mono text-slate-500">{children}</div>;
}
function Heading({ children }) {
  return <h2 className="font-display text-base font-black text-slate-900 mt-5 mb-2 border-b border-slate-200 pb-1">{children}</h2>;
}
function KVGrid({ pairs }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-sm">
      {pairs.filter(([_, v]) => v !== undefined && v !== null && v !== "").map(([k, v]) => (
        <div key={k} className="flex justify-between border-b border-slate-100 py-1">
          <span className="text-slate-500 font-mono text-[10px] uppercase tracking-[0.15em]">{k}</span>
          <span className="text-slate-900 font-medium text-right">{String(v)}</span>
        </div>
      ))}
    </div>
  );
}
function Para({ label, value }) {
  if (!value) return null;
  return (
    <div className="mb-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">{label}</div>
      <div className="text-sm text-slate-900 whitespace-pre-wrap">{value}</div>
    </div>
  );
}
function SigBlock({ label, name, sig }) {
  return (
    <div className="border-t border-slate-200 pt-3 mt-2">
      <img src={sig} alt={label} className="h-16 object-contain" />
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold mt-1">
        {label} · {name}
      </div>
    </div>
  );
}
