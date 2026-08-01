import React, { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { Printer, Loader2, Trash2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { DetailPageHero } from "@/components/detail/DetailPageHero";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { isAdmin } from "@/lib/adminAuth";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";
import { SubmitLangBadge } from "@/components/SubmitLangBadge";
import { formatDateLong } from "@/lib/utils";
import { resolvePhotoSrc } from "@/lib/photoSrc";
import { QaqcLifecyclePanel } from "@/components/QaqcLifecyclePanel";

const KIND_LABEL = {
  concrete_form: "Concrete Form Inspection",
  rebar: "Rebar Inspection",
  subcontractor_work: "Subcontractor Work Inspection",
};

function CenterState({ message, loading = false, testId = "view-qaqc-state" }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe no-print" />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
        <div className="wp17-panel flex min-h-[18rem] items-center justify-center text-center text-slate-500" data-testid={testId}>
          <div>
            {loading ? <Loader2 className="w-6 h-6 animate-spin mx-auto mb-3" /> : null}
            <div className="font-mono text-xs uppercase tracking-[0.18em]">QA / QC</div>
            <div className="mt-2 text-sm sm:text-base text-slate-600">{message}</div>
          </div>
        </div>
      </main>
    </div>
  );
}

function Heading({ children }) {
  return <h2 className="font-display text-base font-black text-slate-900 mt-5 mb-2 border-b border-slate-200 pb-1">{children}</h2>;
}

function KVGrid({ pairs }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-sm">
      {pairs.filter(([_, v]) => v !== undefined && v !== null && v !== "").map(([k, v]) => (
        <div key={k} className="flex justify-between border-b border-slate-100 py-1 gap-4">
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

function wrapWithAdminShell(isAdminRoute, data, children) {
  if (!isAdminRoute) return children;
  return (
    <AdminRouteShell
      pageTitle="QA / QC Inspection"
      subtitle="Admin review for field quality evidence, checklist outcomes, and sign-off state."
      portalRole="Admin · QA / QC"
      crumbs={[{ label: "Field Operations" }, { label: "QA / QC" }, { label: data?.project_name || data?.id?.slice?.(0, 8)?.toUpperCase() || "Inspection" }]}
      showShellHeader={false}
      showBreadcrumbs={false}
      contentClassName="px-0 py-0"
      testId="admin-view-qaqc-shell"
    >
      {children}
    </AdminRouteShell>
  );
}

export default function ViewQaqcInspection() {
  const { id } = useParams();
  const { pathname } = useLocation();
  const { t } = useT();
  const isAdminRoute = pathname.startsWith("/admin/");
  const listUrl = isAdminRoute ? "/admin/qaqc" : "/qaqc";
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let alive = true;
    api.get(`/qaqc-inspections/${id}`)
      .then((r) => {
        if (alive) setData(r.data);
      })
      .catch((e) => {
        if (alive) setErr(e?.response?.data?.detail || "Failed to load");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [id]);

  async function onDelete() {
    if (!window.confirm(t("Delete this QA/QC inspection?"))) return;
    try {
      await api.delete(`/qaqc-inspections/${id}`);
      toast.success(t("Deleted."));
      window.location.href = "/admin/qaqc";
    } catch (e) {
      toast.error(operationalError(
        e,
        t("Delete temporarily unavailable. Try again in a moment."),
        t("Your session expired. Please sign in again."),
      ));
    }
  }

  if (loading) {
    return wrapWithAdminShell(isAdminRoute, null, <CenterState message={t("Loading inspection…")} loading testId="view-qaqc-loading" />);
  }

  if (err || !data) {
    return wrapWithAdminShell(isAdminRoute, null, <CenterState message={err || t("Inspection not found.")} testId="view-qaqc-error" />);
  }

  const failItems = (data.checklist || []).filter((c) => c.result === "fail");
  const inspectionKind = KIND_LABEL[data.inspection_kind] || "QA/QC Inspection";

  const heroChips = (
    <>
      <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-800">
        {t(inspectionKind)}
      </span>
      {data.doc_id ? (
        <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-800" data-testid="record-doc-id-badge">
          <span className="text-[9px] uppercase tracking-[0.22em] text-emerald-700">{t("Doc ID")}</span>
          {data.doc_id}
        </span>
      ) : null}
      <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
        {t("Report ID")} · {data.id?.slice(0, 8).toUpperCase()}
      </span>
      {data.submit_language === "es" ? <SubmitLangBadge lang={data.submit_language} /> : null}
    </>
  );

  const heroDescription = [
    data.project_name,
    data.location,
    data.inspection_date ? formatDateLong(data.inspection_date) : null,
    data.inspection_time,
  ].filter(Boolean).join(" · ");

  const content = (
    <div className="min-h-screen bg-slate-50 print:bg-white">
      <div className="caution-stripe no-print" />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 print-page">
        <DetailPageHero
          backHref={listUrl}
          backLabel={isAdminRoute ? t("Admin · QA / QC") : t("QA / QC")}
          kicker={t("Field Operations · QA / QC Review")}
          title={t("QA / QC Inspection Report")}
          description={heroDescription || t("Review checklist outcomes, deficiency history, and sign-off evidence for this field quality record.")}
          actions={heroChips}
          toolbar={(
            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={() => window.print()} variant="outline" className="h-11 px-4 border-slate-300 bg-white text-slate-700 hover:border-red-500 hover:text-red-700 font-bold uppercase tracking-wide text-sm" data-testid="print-btn">
                <Printer className="w-4 h-4 mr-1" /> {t("Print / PDF")}
              </Button>
              {isAdmin() ? (
                <Button onClick={onDelete} variant="outline" className="h-11 px-4 border-slate-300 bg-white text-red-700 hover:border-red-500 hover:text-red-800 font-bold uppercase tracking-wide text-sm" data-testid="delete-btn">
                  <Trash2 className="w-4 h-4 mr-1" /> {t("Delete")}
                </Button>
              ) : null}
            </div>
          )}
          testId="view-qaqc-hero"
        />

        <section className="wp17-panel p-4 print:hidden" data-testid="view-qaqc-lifecycle-panel">
          <QaqcLifecyclePanel inspectionId={data.id} />
        </section>

        <section className="bg-white border border-slate-200 rounded-[1.5rem] p-5 sm:p-7 print:border-none print:rounded-none print:p-0" data-testid="view-qaqc-content">
          {failItems.length > 0 ? (
            <div className="border-2 border-red-400 bg-red-50 rounded-xl p-4 mb-5 flex items-start gap-3" data-testid="view-qaqc-fail-summary">
              <AlertTriangle className="w-5 h-5 text-red-700 mt-0.5 shrink-0" />
              <div>
                <div className="font-display font-black text-red-900">
                  {failItems.length} {t("item(s) failed inspection")}
                </div>
                <div className="text-sm text-slate-800 mt-1">{data.deficiencies || t("See deficiencies below.")}</div>
              </div>
            </div>
          ) : null}

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
          <div className="space-y-2" data-testid="view-qaqc-checklist">
            {(data.checklist || []).map((c) => (
              <div key={c.key} className="flex items-start gap-3 border-b border-slate-100 py-2">
                <span className={"font-mono text-[10px] font-bold uppercase tracking-[0.1em] px-2 py-0.5 rounded " + (
                  c.result === "pass"
                    ? "bg-emerald-100 text-emerald-900"
                    : c.result === "fail"
                      ? "bg-red-100 text-red-900"
                      : "bg-slate-100 text-slate-600"
                )}>
                  {c.result === "pass" ? t("PASS") : c.result === "fail" ? t("FAIL") : t("N/A")}
                </span>
                <div className="flex-1 text-sm text-slate-900">
                  <div>{t(c.label)}</div>
                  {c.note ? <div className="text-xs text-slate-500 mt-0.5">↳ {c.note}</div> : null}
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

          {data.photos?.length > 0 ? (
            <>
              <Heading>{t("Photos")} ({data.photos.length})</Heading>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4" data-testid="view-qaqc-photos">
                {data.photos.map((p, i) => (
                  <img key={i} src={resolvePhotoSrc(p)} alt={`Photo ${i + 1}`} loading="lazy" decoding="async" className="w-full h-32 object-cover rounded border border-slate-300" />
                ))}
              </div>
            </>
          ) : null}

          <Heading>{t("Sign-Off")}</Heading>
          {data.inspector_signature ? <SigBlock label="Inspector" name={data.inspector_name} sig={data.inspector_signature} /> : null}
          {data.sub_rep_signature ? <SigBlock label="Subcontractor Rep" name={data.sub_rep_name} sig={data.sub_rep_signature} /> : null}
        </section>
      </main>
    </div>
  );

  return wrapWithAdminShell(isAdminRoute, data, content);
}