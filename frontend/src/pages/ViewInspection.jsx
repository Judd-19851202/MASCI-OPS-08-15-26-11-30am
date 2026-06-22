import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { Printer, Loader2, AlertTriangle, Trash2, MapPin, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { brandSlug } from "@/lib/brandFilename";
import { useBranding } from "@/lib/BrandingProvider";
import { RefKicker } from "@/components/RefKicker";
import BackLink from "@/components/BackLink";
import { useHubHome } from "@/components/HubBackLink";
import { useReturnContext } from "@/lib/returnContext";
import { getInspectionCapabilities } from "@/lib/inspectionCapabilities";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { getCompanyInfo } from "@/lib/companyInfo";
import { computeGrade } from "@/lib/grading";
import { GradeBanner } from "@/components/Grade";
import { formatCoords } from "@/lib/geolocation";
import { MapThumbnail } from "@/components/MapThumbnail";
import { printReport, maybeAutoPrint } from "@/lib/printReport";
import { PrintWatermark } from "@/components/PrintWatermark";
import { PhotoLightbox } from "@/components/PhotoLightbox";
import { PhotoZipDownload } from "@/components/PhotoZipDownload";
import { resolvePhotoSrc } from "@/lib/photoSrc";
import { EmailReportDialog } from "@/components/EmailReportDialog";
import { EditProjectDialog } from "@/components/EditProjectDialog";
import {
  PPE_ITEMS,
  SITE_HAZARD_ITEMS,
  CONDITIONAL_SECTIONS,
} from "@/lib/inspectionSchema";
import { formatDateLong } from "@/lib/utils";
import { SubmitLangBadge } from "@/components/SubmitLangBadge";
import { useT } from "@/lib/i18n";
import { SiteInspectionLifecyclePanel } from "@/components/SiteInspectionLifecyclePanel";

const StatusBadge = ({ value }) => {
  const v = (value || "").toString().toLowerCase();
  let cls = "bg-slate-200 text-slate-700 print-status-yes";
  if (v === "yes") cls = "bg-green-700 text-white print-status-yes";
  if (v === "no") cls = "bg-red-600 text-white print-status-no";
  if (v === "n/a") cls = "bg-slate-500 text-white print-status-yes";
  if (!value) {
    cls = "bg-slate-100 text-slate-500 print-status-yes";
    value = "—";
  }
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded text-xs font-bold uppercase tracking-wider min-w-[44px] justify-center ${cls}`}
    >
      {value}
    </span>
  );
};

const ReadRow = ({ label, value, autoFail = false }) => {
  const failed = autoFail && (value || "").toString().toLowerCase() === "no";
  return (
    <div
      className={`flex items-start justify-between gap-4 py-2 border-b border-slate-100 last:border-b-0 print-row ${
        failed ? "bg-red-50 -mx-2 px-2 rounded" : ""
      }`}
    >
      <span className="text-sm text-slate-700 leading-snug flex items-start gap-2 flex-1">
        <span>{label}</span>
        {autoFail && (
          <span className="shrink-0 inline-flex items-center px-1.5 py-0.5 mt-0.5 bg-red-600 text-white text-[9px] font-mono font-bold uppercase tracking-wider rounded">
            Auto-Fail
          </span>
        )}
      </span>
      <StatusBadge value={value} />
    </div>
  );
};

const KV = ({ label, value, full = false }) => (
  <div className={full ? "lg:col-span-2" : ""}>
    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
      {label}
    </div>
    <div className="text-base text-slate-900 mt-1 whitespace-pre-wrap">
      {value || "—"}
    </div>
  </div>
);

const ReportSection = ({ number, title, children }) => (
  <section
    className="bg-white border border-slate-200 rounded-md p-5 sm:p-7 print-section"
    data-testid={`view-section-${number}`}
  >
    <div className="flex items-baseline gap-3 mb-4 pb-2 border-b-2 border-slate-200">
      <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700">
        Section {number}
      </span>
      <h2 className="font-display text-xl sm:text-2xl font-bold text-slate-900">
        {title}
      </h2>
    </div>
    {children}
  </section>
);

export default function ViewInspection() {
  const branding = useBranding();
  const { t } = useT();
  const hubHome = useHubHome();
  const { id } = useParams();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const listUrl = pathname.replace(/\/[^/]+$/, "") || "/admin/inspections";
  const ret = useReturnContext({
    key: "inspections-list",
    label: t("Reports"),
    path: listUrl,
  });
  const caps = getInspectionCapabilities();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [emailOpen, setEmailOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api.get(`/inspections/${id}`);
        if (alive) setData(res.data);
      } catch {
        toast.error(t("Inspection not found"));
        navigate(listUrl);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [id, navigate, listUrl, t]);

  // Auto-print after the page renders if we landed here via ?autoprint=1
  useEffect(() => {
    if (!loading && data) maybeAutoPrint();
  }, [loading, data]);

  const handleDelete = async () => {
    if (!window.confirm(t("Delete this inspection? This cannot be undone."))) return;
    try {
      await api.delete(`/inspections/${id}`);
      toast.success(t("Deleted"));
      navigate(listUrl);
    } catch {
      toast.error(t("Delete failed"));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-500">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> {t("Loading…")}
      </div>
    );
  }
  if (!data) return null;

  const company = getCompanyInfo();
  // Prefer persisted grade (so historic reports never silently re-grade if rules change);
  // fall back to recompute for legacy records that pre-date the grading feature.
  const grade =
    data.score != null
      ? {
          score: data.score,
          status: data.status || (data.score < 74 ? "FAIL" : "PASS"),
          auto_fail_count: data.auto_fail_count || 0,
          yes: data.graded_yes || 0,
          no: data.graded_no || 0,
          total: data.graded_total || 0,
          pass_threshold: 74,
        }
      : computeGrade(data);
  const flagged =
    data.hazards_observed === "Yes" || data.stop_work_issued === "Yes";

  return (
    <div className="min-h-screen bg-slate-50">
      <PrintWatermark />
      <div className="caution-stripe no-print" />
      <header className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10 no-print">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <BackLink to={ret.path} label={ret.label} variant="header" testId="back-link" />
          <MasciLogo variant="mark" size="md" homeLink={hubHome} />
          <div className="flex gap-2">
            <EditProjectDialog
              kind="inspections"
              recordId={data.id}
              current={data}
              onSaved={(rec) => rec && setData(rec)}
            />
            {caps["inspection.delete"] && (
              <Button
                variant="outline"
                size="icon"
                onClick={handleDelete}
                className="h-11 w-11 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:text-red-400"
                data-testid="delete-btn"
                aria-label="Delete inspection"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() => setEmailOpen(true)}
              className="h-11 px-4 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:bg-slate-700 font-bold uppercase tracking-wide text-sm"
              data-testid="email-btn"
            >
              <Mail className="w-4 h-4 mr-1" /> {t("Email")}
            </Button>
            <Button
              onClick={printReport}
              className="h-11 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="print-btn"
            >
              <Printer className="w-4 h-4 mr-1" /> {t("Print / PDF")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 print-page">
        {/* Print header */}
        <div className="flex items-start justify-between border-b-4 border-red-700 pb-4 gap-4">
          <div className="flex-1">
            <MasciLogo variant="mark" size="2xl" className="hidden sm:block max-w-[420px]" onLight homeLink={hubHome} />
            <MasciLogo variant="mark" size="xl" className="sm:hidden" homeLink={hubHome} />
            {/* iter336 · review-side reference continuity */}
            <RefKicker
              recordId={data.inspection_number || data.id}
              testId="view-inspection-ref"
              className="mt-4"
            />
            <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">
              {t("Job Site Safety Inspection Report")}
            </h1>
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 mt-1 flex items-center gap-2 flex-wrap">
              {data.doc_id && (
                <span
                  className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-red-50 border border-red-300 text-red-800 font-bold tabular-nums tracking-wide"
                  data-testid="record-doc-id-badge"
                >
                  <span className="text-[9px] uppercase tracking-[0.22em] text-red-700">{t("Doc ID")}</span>
                  {data.doc_id}
                </span>
              )}
              <span>{t("Report ID")} · {data.id?.slice(0, 8).toUpperCase()}</span>
            </div>
            {data.submit_language === "es" && (
              <div className="mt-2">
                <SubmitLangBadge lang={data.submit_language} />
              </div>
            )}
            <div className="mt-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold flex-wrap" hidden>
              <span>No Guesswork.</span>
              <span className="w-1 h-1 rounded-full bg-red-700" />
              <span>No Missed Steps.</span>
              <span className="w-1 h-1 rounded-full bg-red-700" />
              <span>No Excuses.</span>
            </div>
          </div>
          {flagged && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-2 bg-red-700 text-white rounded-md self-start">
              <AlertTriangle className="w-5 h-5" />
              <span className="font-bold uppercase tracking-wide text-sm">
                {data.stop_work_issued === "Yes" ? t("Stop Work") : t("Hazard Found")}
              </span>
            </div>
          )}
        </div>

        {/* Grade banner */}
        <GradeBanner grade={grade} />

        {/* iter453 · OC-004 lifecycle panel (no-print) */}
        <SiteInspectionLifecyclePanel inspectionId={data.id} />

        <ReportSection number="01" title={t("Project / Inspection Information")}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
            <KV label={t("Project Name")} value={data.project_name} />
            <KV label={t("Project Number")} value={data.project_number} />
            <div className="lg:col-span-2">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                {t("Location")}
              </div>
              <div className="text-base text-slate-900 mt-1 whitespace-pre-wrap">
                {data.location || "—"}
              </div>
              {data.gps_lat != null && data.gps_lng != null && (
                <div
                  className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1 flex items-center gap-1 flex-wrap"
                  data-testid="view-gps-coords"
                >
                  <MapPin className="w-3 h-3 text-red-700" />
                  <span>GPS · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}</span>
                  <a
                    href={`https://www.google.com/maps?q=${data.gps_lat},${data.gps_lng}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-red-700 hover:text-red-800 font-bold no-print"
                    data-testid="view-gps-map-link"
                  >
                    · {t("Open in Maps")}
                  </a>
                </div>
              )}
              {data.gps_lat != null && data.gps_lng != null && (
                <MapThumbnail
                  lat={data.gps_lat}
                  lng={data.gps_lng}
                  className="mt-2"
                />
              )}
            </div>
            <KV label={t("Date")} value={formatDateLong(data.inspection_date)} />
            <KV label={t("Time")} value={data.inspection_time} />
            <KV label={t("Operation")} value={data.operation} />
            <KV label={t("Inspector")} value={data.inspector_name} />
            <KV label={t("Foreman / Supervisor")} value={data.foreman_name} />
            <KV label={t("Crew / Personnel")} value={data.crew_personnel} full />
            <KV label={t("Subcontractors")} value={data.subcontractors} full />
            <KV label={t("Weather Conditions")} value={data.weather_conditions} full />
          </div>
        </ReportSection>

        <ReportSection number="02" title={t("Work Activity Taking Place Onsite")}>
          <p className="text-base text-slate-900 whitespace-pre-wrap">
            {data.work_activity || "—"}
          </p>
        </ReportSection>

        <ReportSection number="03" title={t("PPE Compliance")}>
          {PPE_ITEMS.map((item) => (
            <ReadRow
              key={item.key}
              label={item.label}
              value={data.ppe_compliance?.[item.key]}
            />
          ))}
        </ReportSection>

        {CONDITIONAL_SECTIONS.map((sec, idx) => {
          const num = String(4 + idx).padStart(2, "0");
          const block = data[sec.key] || { applies: "No", items: {}, notes: "" };
          return (
            <ReportSection key={sec.key} number={num} title={sec.title}>
              <ReadRow label={sec.trigger} value={block.applies} />
              {block.applies === "Yes" && (
                <div className="mt-2 pt-2 border-t border-slate-200">
                  {sec.items.map((it) => (
                    <ReadRow
                      key={it.key}
                      label={it.label}
                      value={block.items?.[it.key]}
                      autoFail={it.autoFail}
                    />
                  ))}
                  {block.notes && (
                    <div className="mt-3">
                      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                        {t("Notes")}
                      </div>
                      <p className="text-sm text-slate-900 whitespace-pre-wrap">
                        {block.notes}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </ReportSection>
          );
        })}

        <ReportSection number="11" title={t("General Site Hazards & Housekeeping")}>
          {SITE_HAZARD_ITEMS.map((item) => (
            <ReadRow
              key={item.key}
              label={item.label}
              value={data.site_hazards?.[item.key]}
            />
          ))}
        </ReportSection>

        <ReportSection number="12" title={t("Safety Issues / Corrective Actions")}>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4 mb-4">
            <KV label={t("Hazards Observed")} value={data.hazards_observed} />
            <KV label={t("Stop Work Issued")} value={data.stop_work_issued} />
            <KV label={t("Corrected On Site")} value={data.corrected_on_site} />
          </div>
          <KV label={t("Responsible Party")} value={data.responsible_party} full />
          <div className="mt-3">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
              {t("Description / Corrective Action Notes")}
            </div>
            <p className="text-base text-slate-900 mt-1 whitespace-pre-wrap">
              {data.corrective_action_notes || "—"}
            </p>
          </div>
          {data.photos?.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  {t("Photo Documentation")} ({data.photos.length})
                </div>
                <PhotoZipDownload
                  photos={data.photos}
                  prefix={`${brandSlug()}_Inspection_${(data.id || "").slice(0, 8)}_findings`}
                  testId="inspection-photos-zip"
                />
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4">
                {data.photos.map((p, i) => (
                  <PhotoLightbox
                    key={i}
                    src={p}
                    alt={`Inspection Finding ${i + 1}`}
                    filename={`${brandSlug()}_Inspection_${(data.id || "").slice(0, 8)}_finding${i + 1}.jpg`}
                    className="relative w-full aspect-square rounded-md overflow-hidden border border-slate-200 bg-white"
                    testId={`view-photo-${i}`}
                  >
                    <img
                      src={resolvePhotoSrc(p)}
                      alt={`Finding ${i + 1}`}
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                  </PhotoLightbox>
                ))}
              </div>
            </div>
          )}
        </ReportSection>

        <ReportSection number="13" title={t("Signatures")}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
                {t("Inspector")}
              </div>
              <div className="text-base font-bold text-slate-900 mb-2">
                {data.inspector_name || "—"}
              </div>
              <div className="border border-slate-200 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center">
                {data.inspector_signature ? (
                  <img
                    src={data.inspector_signature}
                    alt="Inspector signature"
                    className="max-h-[120px]"
                    data-testid="view-inspector-sig"
                  />
                ) : (
                  <span className="text-slate-400 text-sm">{t("No signature")}</span>
                )}
              </div>
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
                {t("Foreman / Supervisor")}
              </div>
              <div className="text-base font-bold text-slate-900 mb-2">
                {data.foreman_name || "—"}
              </div>
              <div className="border border-slate-200 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center">
                {data.foreman_signature ? (
                  <img
                    src={data.foreman_signature}
                    alt="Foreman signature"
                    className="max-h-[120px]"
                    data-testid="view-foreman-sig"
                  />
                ) : (
                  <span className="text-slate-400 text-sm">{t("No signature")}</span>
                )}
              </div>
            </div>
          </div>
        </ReportSection>

        <div className="text-center font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 pt-4 pb-8 print-section">
          {t("Generated")} {data.created_at ? new Date(data.created_at).toLocaleString() : ""} · {company.company_name || branding.company_name || "Customer"} {t("Job Site Safety")}
        </div>

        {/* Print-only company info footer */}
        {(company.address || company.phone || company.email || company.website) && (
          <div className="print-only border-t-2 border-black pt-3 mt-2 text-[9pt] leading-snug print-section">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-display font-black text-[11pt] text-black">
                  {company.company_name || branding.company_name || "Customer"}
                </div>
                {company.tagline && (
                  <div className="font-mono text-[8pt] uppercase tracking-[0.2em] text-black">
                    {company.tagline}
                  </div>
                )}
              </div>
              <div className="text-right text-black">
                {company.address && <div>{company.address}</div>}
                {company.city_state_zip && <div>{company.city_state_zip}</div>}
                {(company.phone || company.email) && (
                  <div>
                    {company.phone}
                    {company.phone && company.email ? " · " : ""}
                    {company.email}
                  </div>
                )}
                {company.website && (
                  <div>{company.website}</div>
                )}
              </div>
            </div>
            <div className="text-center mt-2 font-mono text-[8pt] uppercase tracking-[0.2em] text-black border-t border-black pt-2">
              Confidential Safety Inspection Record · Report ID {data.id?.slice(0, 8).toUpperCase()}
            </div>
          </div>
        )}
      </main>
      <EmailReportDialog open={emailOpen} onOpenChange={setEmailOpen} kind="inspection" record={data} />
    </div>
  );
}
