import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { brandSlug } from "@/lib/brandFilename";
import { useBranding } from "@/lib/BrandingProvider";
import {
  ArrowLeft,
  Printer,
  Loader2,
  Trash2,
  MapPin,
  CloudSun,
  Mail,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { RefKicker } from "@/components/RefKicker";
import { useHubHome } from "@/components/HubBackLink";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { formatDateLong } from "@/lib/utils";
import { getCompanyInfo } from "@/lib/companyInfo";
import { formatCoords } from "@/lib/geolocation";
import { MapThumbnail } from "@/components/MapThumbnail";
import { printReport, maybeAutoPrint } from "@/lib/printReport";
import { PrintWatermark } from "@/components/PrintWatermark";
import { PhotoLightbox } from "@/components/PhotoLightbox";
import { PhotoZipDownload } from "@/components/PhotoZipDownload";
import { DailyReportLifecyclePanel } from "@/components/DailyReportLifecyclePanel";
import { resolvePhotoSrc } from "@/lib/photoSrc";
import { EmailReportDialog } from "@/components/EmailReportDialog";
import { EditProjectDialog } from "@/components/EditProjectDialog";
import { SubmitLangBadge } from "@/components/SubmitLangBadge";
import MaterialMovementTile from "@/components/MaterialMovementTile";
import { useT } from "@/lib/i18n";

// 24-hour HH:MM → 12-hour h:MM AM/PM (returns the original string if
// it can't be parsed so we never silently drop user-typed data).
function fmt12h(s) {
  if (!s) return "";
  const m = String(s).match(/^(\d{1,2}):(\d{2})/);
  if (!m) return s;
  const h = Number(m[1]);
  const mm = m[2];
  if (Number.isNaN(h) || h < 0 || h > 23) return s;
  const ampm = h >= 12 ? "PM" : "AM";
  const h12 = h % 12 === 0 ? 12 : h % 12;
  return `${h12}:${mm} ${ampm}`;
}

// "7:00 AM → 5:30 PM · 10.5 h gross − 0.5 h lunch = 10.00 h net"
function grossNetLine(start, stop, lunchMin) {
  if (!start || !stop) return "";
  const a = String(start).match(/^(\d{1,2}):(\d{2})/);
  const b = String(stop).match(/^(\d{1,2}):(\d{2})/);
  if (!a || !b) return "";
  const sh = Number(a[1]), sm = Number(a[2]);
  const eh = Number(b[1]), em = Number(b[2]);
  if ([sh, sm, eh, em].some((n) => Number.isNaN(n))) return "";
  let grossMin = (eh * 60 + em) - (sh * 60 + sm);
  if (grossMin < 0) grossMin += 24 * 60;
  const lunch = Number(lunchMin) || 0;
  const netMin = Math.max(0, grossMin - lunch);
  const hr = (m) => (m % 60 === 0 ? (m / 60).toFixed(1) : (m / 60).toFixed(2));
  return `${fmt12h(start)} \u2192 ${fmt12h(stop)} \u00b7 ${hr(grossMin)} h gross \u2212 ${hr(lunch)} h lunch = ${hr(netMin)} h net`;
}

const ReportSection = ({ number, title, children }) => (
  <section className="bg-white border border-slate-200 rounded-md p-5 sm:p-7 print:break-inside-avoid">
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

const KV = ({ label, value, full }) => (
  <div className={full ? "lg:col-span-2" : ""}>
    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
      {label}
    </div>
    <div className="text-base text-slate-900 mt-1 whitespace-pre-wrap">
      {value || "—"}
    </div>
  </div>
);

const Table = ({ headers, rows, emptyText }) => {
  if (!rows?.length) {
    return <div className="text-slate-500 text-sm">{emptyText}</div>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-2 border-slate-200 rounded">
        <thead>
          <tr className="bg-slate-100">
            {headers.map((h) => (
              <th
                key={h}
                className="text-left px-2 py-1.5 font-mono text-[10px] uppercase tracking-[0.15em] text-slate-700 border-b-2 border-slate-300"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-slate-100">
              {r.map((cell, j) => (
                <td
                  key={j}
                  className="px-2 py-1.5 align-top whitespace-pre-wrap"
                >
                  {cell || "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default function ViewDailyReport() {
  const branding = useBranding();
  const { t } = useT();
  const hubHome = useHubHome();
  const { id } = useParams();
  const navigate = useNavigate();
  const { pathname, state: navState } = useLocation();
  // Parent list URL — strips `/<id>` from the current pathname so PMs
  // viewing /pm/daily/<id> bounce back to /pm/daily, and admins viewing
  // /admin/daily/<id> bounce back to /admin/daily. Avoids the legacy
  // hard-coded "/admin/daily" that wiped the PM token via EnforcePortalScope.
  const listUrl = pathname.replace(/\/[^/]+$/, "") || "/admin/daily";
  // Track 15.12A · Photo Workflow Recovery — when the user arrived here
  // by clicking a photo tile on the PM Command Center, honor the
  // `{from: "pm-photos"}` location.state so the back button takes them
  // back to the dashboard photo panel instead of dumping them in the
  // Daily Reports list.
  const cameFromPmPhotos = navState && navState.from === "pm-photos";
  // Track 15.13C — HR portal mounts this same view via /hr/daily-reports/:id
  // for read-only access. Backend already rejects HR's X-HR-Token on
  // every mutating endpoint; UI hides the mutation controls so the
  // page looks read-only as well as behaves read-only.
  const isHrReadOnly = pathname.startsWith("/hr/");
  const backHref = cameFromPmPhotos
    ? (navState.returnTo || "/pm/command-center")
    : (isHrReadOnly ? "/hr/daily-reports" : listUrl);
  const backLabel = cameFromPmPhotos
    ? t("Photos")
    : (isHrReadOnly ? t("Daily Reports") : t("Daily Reports"));
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [emailOpen, setEmailOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api.get(`/daily-reports/${id}`);
        if (alive) setData(res.data);
      } catch {
        toast.error("Daily report not found.");
        navigate(listUrl);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [id, navigate, listUrl]);

  // Auto-print after the page renders if we landed here via ?autoprint=1
  useEffect(() => {
    if (!loading && data) maybeAutoPrint();
  }, [loading, data]);

  const handleDelete = async () => {
    if (!window.confirm(t("Delete this daily report? This cannot be undone.")))
      return;
    try {
      await api.delete(`/daily-reports/${id}`);
      toast.success(t("Deleted"));
      navigate(listUrl);
    } catch {
      toast.error(t("Could not delete. Try again."));
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

  return (
    <div className="min-h-screen bg-slate-50">
      <PrintWatermark />
      <div className="caution-stripe no-print" />
      <header className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10 no-print">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link
            to={backHref}
            className="inline-flex items-center min-h-[44px] -ml-2 px-2 text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="back-link"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {backLabel}
          </Link>
          <MasciLogo variant="mark" size="md" homeLink={hubHome} />
          {isHrReadOnly ? (
            /* Track 15.13C · HR read-only — surface the read-only badge
               in the same slot where Edit / Delete / Email / Print
               render for PM/Admin. HR sees the EXACT real Daily Report
               body below; just no mutation surface. */
            <div
              className="text-[10px] font-mono uppercase tracking-[0.22em] font-bold px-2 py-1 rounded border border-slate-500 text-slate-200"
              data-testid="hr-readonly-badge"
            >
              {t("Read-only · HR")}
            </div>
          ) : (
            <div className="flex gap-2">
              <EditProjectDialog
                kind="daily-reports"
                recordId={data.id}
                current={data}
                onSaved={(rec) => rec && setData(rec)}
              />
              <Button
                variant="outline"
                size="icon"
                onClick={handleDelete}
                className="h-11 w-11 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:text-red-400"
                data-testid="delete-btn"
                aria-label="Delete daily report"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                onClick={() => setEmailOpen(true)}
                className="h-11 px-4 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:text-white hover:bg-slate-700 font-bold uppercase tracking-wide text-sm"
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
          )}
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6">
        {/* Track 15.12A · breadcrumb only when arriving from the PM
            Command Center photo lightbox, so the user can see the
            navigation source they came from. */}
        {cameFromPmPhotos && (
          <nav
            aria-label="Breadcrumb"
            data-testid="view-daily-breadcrumb"
            className="no-print -mt-2 text-[11px] font-mono uppercase tracking-[0.18em] text-slate-500"
          >
            <Link to="/pm/command-center" className="hover:text-red-700 hover:underline font-bold">
              {t("PM Portal")}
            </Link>
            <span className="mx-1 text-slate-400">/</span>
            <Link to="/pm/command-center" className="hover:text-red-700 hover:underline font-bold">
              {t("Command Center")}
            </Link>
            <span className="mx-1 text-slate-400">/</span>
            <Link to="/pm/command-center" className="hover:text-red-700 hover:underline font-bold">
              {t("Photos")}
            </Link>
            <span className="mx-1 text-slate-400">/</span>
            <span className="text-slate-700 font-bold">{t("Daily Report")}</span>
          </nav>
        )}
        <div className="flex items-start justify-between border-b-4 border-red-700 pb-4 gap-4">
          <div className="flex-1">
            <MasciLogo
              variant="mark"
              size="2xl"
              className="hidden sm:block max-w-[420px]"
              onLight
            homeLink={hubHome} />
            <MasciLogo variant="mark" size="xl" className="sm:hidden" homeLink={hubHome} />
            {/* iter336 · review-side reference continuity */}
            <RefKicker
              recordId={data.report_number || data.id}
              testId="view-daily-ref"
              className="mt-4"
            />
            <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">
              {t("Daily Job Report")}
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
              {data.report_number ? <span>· #{data.report_number}</span> : null}
            </div>
            {data.submit_language === "es" && (
              <div className="mt-2">
                <SubmitLangBadge lang={data.submit_language} />
              </div>
            )}
          </div>
        </div>

        {/* OMEGA · Phase 1A · iter452 · OC-002 Daily Report Office Review.
            Operator directive: OPEN → PENDING_REVIEW → REVIEWED → CLOSED
            with kickback PENDING_REVIEW → OPEN and audited REOPEN. */}
        <DailyReportLifecyclePanel reportId={data.id} />

        <ReportSection number="01" title={t("Report Information")}>
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
              {data.gps_lat != null && (
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1 flex items-center gap-1 flex-wrap">
                  <MapPin className="w-3 h-3 text-red-700" />
                  GPS · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}
                </div>
              )}
              {data.gps_lat != null && (
                <MapThumbnail
                  lat={data.gps_lat}
                  lng={data.gps_lng}
                  className="mt-2"
                />
              )}
            </div>
            <KV label={t("Date")} value={formatDateLong(data.report_date)} />
            <KV label={t("Prepared By")} value={data.prepared_by} />
            <KV label={t("Superintendent")} value={data.superintendent} />
          </div>
        </ReportSection>

        <ReportSection number="02" title={t("Weather")}>
          {data.weather_summary && (
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700 font-bold flex items-center gap-2">
              <CloudSun className="w-4 h-4 text-amber-600" />
              {data.weather_summary}
            </div>
          )}
          {data.weather_snapshots?.length > 0 ? (
            <div className="grid grid-cols-3 gap-3 mt-3">
              {data.weather_snapshots.map((s, i) => (
                <div key={i} className="border border-slate-200 rounded-md p-3 print-row">
                  <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-red-700 font-bold">
                    {s.time}
                  </div>
                  <div className="font-display font-bold text-2xl text-slate-900 mt-1">
                    {s.temp_f != null ? `${s.temp_f}°F` : "—"}
                  </div>
                  <div className="text-sm text-slate-700">{s.condition || "—"}</div>
                  <div className="text-xs text-slate-500 mt-1">
                    {s.precip_in ?? 0}″ · {s.humidity_pct ?? "—"}% ·{" "}
                    {s.wind_mph ?? "—"} mph
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-slate-500 text-sm">{t("No weather captured.")}</div>
          )}
        </ReportSection>

        <ReportSection number="03" title={t("General Information")}>
          <div className="grid grid-cols-2 gap-4">
            <KV label={t("Schedule Delays")} value={data.schedule_delays} />
            <KV label={t("Weather Impact")} value={data.weather_impact} />
            <KV label={t("Accidents on Site")} value={data.safety_incidents_today} />
            <KV label={t("Injuries Reported")} value={data.injuries_reported} />
            {data.incident_notes && (
              <KV label={t("Detail")} value={data.incident_notes} full />
            )}
            {(data.safety_incidents_today === "Yes" ||
              data.injuries_reported === "Yes") && (
              <div className="lg:col-span-2 mt-2 border-2 border-red-600 bg-red-50 rounded-md p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold mb-2">
                  {t("Safety Escalation")}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
                  <KV label={t("Safety Notified")} value={data.safety_notified} />
                  {data.safety_notified === "Yes" && (
                    <>
                      <KV
                        label={t("Contacted")}
                        value={data.safety_contact_person}
                      />
                      <KV
                        label={t("Time of Contact")}
                        value={data.safety_contact_time}
                      />
                      <KV
                        label={t("Incident Report Filed")}
                        value={data.incident_report_filled}
                      />
                      {data.incident_report_filled === "Yes" && (
                        <KV
                          label={t("Incident Report Time")}
                          value={data.incident_report_time}
                        />
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
            {data.general_notes && (
              <KV label={t("General Notes")} value={data.general_notes} full />
            )}
          </div>
        </ReportSection>

        <ReportSection number="04" title={`${t("Crews")} (${data.masci_crews?.length || 0})`}>
          <Table
            headers={[t("Name"), t("Trade / Role"), t("Start"), t("Stop"), t("Lunch"), t("Hrs"), t("Work Performed")]}
            rows={[
              ...(data.masci_crews || []).map((r, i) => {
                // Build a small inline gross/net math line shown
                // beneath the work-performed cell so a PM reviewing
                // the report can sanity-check the hours calculation
                // without a calculator.
                const summary = grossNetLine(r.start_time, r.stop_time, r.lunch_minutes);
                return [
                  r.name,
                  r.trade,
                  fmt12h(r.start_time),
                  fmt12h(r.stop_time),
                  r.lunch_minutes !== undefined && r.lunch_minutes !== "" ? `${r.lunch_minutes} min` : "",
                  r.hours,
                  summary ? (
                    <div key={`wp-${i}`}>
                      <div>{r.work_performed}</div>
                      <div className="mt-1 font-mono text-[10px] tracking-[0.02em] text-slate-500">
                        {summary}
                      </div>
                    </div>
                  ) : (
                    r.work_performed
                  ),
                ];
              }),
              ...((data.masci_crews || []).length > 0
                ? [[
                    "",
                    "",
                    "",
                    "",
                    <strong key="tl">{t("Total Hours")}</strong>,
                    <strong key="th">
                      {(data.masci_crews || [])
                        .reduce((s, r) => s + (parseFloat(r.hours) || 0), 0)
                        .toFixed(2)}
                    </strong>,
                    "",
                  ]]
                : []),
            ]}
            emptyText={t("No crews on site.")}
          />
        </ReportSection>

        <ReportSection number="05" title={`${t("Subcontractors")} (${data.subcontractors?.length || 0})`}>
          <Table
            headers={[t("Company"), t("Trade"), t("Lead"), t("#"), t("Hrs"), t("Work Performed")]}
            rows={(data.subcontractors || []).map((r) => [
              r.company,
              r.trade,
              r.foreman,
              r.count,
              r.hours,
              r.work_performed,
            ])}
            emptyText={t("No subcontractors on site.")}
          />
          {(data.subcontractors || []).some((s) => (s.photos?.length || 0) > 0 || s.attachment_note) && (
            <div className="mt-4 space-y-4" data-testid="dr-sub-attachments">
              {(data.subcontractors || []).map((s, idx) => {
                const photos = s.photos || [];
                if (photos.length === 0 && !s.attachment_note) return null;
                return (
                  <div
                    key={idx}
                    className="border border-slate-200 rounded-md p-3 bg-slate-50"
                    data-testid={`dr-sub-attachment-${idx}`}
                  >
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">
                      {s.company || `${t("Subcontractor")} #${idx + 1}`}
                      {s.trade ? ` · ${s.trade}` : ""}
                    </div>
                    {s.attachment_note && (
                      <div
                        className="text-sm text-slate-800 mb-2 italic"
                        data-testid={`dr-sub-attachment-note-${idx}`}
                      >
                        {s.attachment_note}
                      </div>
                    )}
                    {photos.length > 0 && (
                      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
                        {photos.map((p, i) => (
                          <PhotoLightbox
                            key={i}
                            src={p}
                            alt={`${s.company || "Subcontractor"} photo ${i + 1}`}
                            filename={`${brandSlug()}_DR_sub_${(s.company || "sub").replace(/[^a-z0-9]+/gi, "_")}_${i + 1}.jpg`}
                            className="aspect-square rounded-md overflow-hidden border-2 border-slate-200"
                            testId={`dr-sub-photo-${idx}-${i}`}
                          >
                            <img
                              src={resolvePhotoSrc(p)}
                              alt={`${s.company || "Subcontractor"} photo ${i + 1}`}
                              className="w-full h-full object-cover"
                            />
                          </PhotoLightbox>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </ReportSection>

        <ReportSection number="06" title={`${t("Visitors")} (${data.visitors?.length || 0})`}>
          <Table
            headers={[t("Name"), t("Company"), t("In"), t("Out"), t("Purpose")]}
            rows={(data.visitors || []).map((r) => [
              r.name,
              r.company,
              fmt12h(r.time_in),
              fmt12h(r.time_out),
              r.purpose,
            ])}
            emptyText={t("No site visitors.")}
          />
        </ReportSection>

        <ReportSection number="07" title={`${t("Equipment")} (${data.equipment?.length || 0})`}>
          <Table
            headers={[t("Description"), t("Hrs"), t("Delivered"), t("Removed"), t("Notes")]}
            rows={(data.equipment || []).map((r) => [
              r.description,
              r.hours_used,
              fmt12h(r.time_delivered),
              fmt12h(r.time_removed),
              r.notes,
            ])}
            emptyText={t("No equipment logged.")}
          />
        </ReportSection>

        <ReportSection number="08" title={`${t("Materials")} (${data.materials?.length || 0})`}>
          <Table
            headers={[t("Description"), t("Qty"), t("Unit"), t("Supplier"), t("Ticket #"), t("Notes")]}
            rows={(data.materials || []).map((r) => [
              r.description,
              r.quantity,
              r.unit,
              r.supplier,
              r.ticket_number,
              r.notes,
            ])}
            emptyText={t("No material deliveries.")}
          />
        </ReportSection>

        <ReportSection number="09" title={`${t("Activity Log")} (${data.activities?.length || 0})`}>
          <Table
            headers={[t("Activity"), t("% Done"), t("From"), t("To"), t("Notes")]}
            rows={(data.activities || []).map((r) => [
              r.activity,
              r.percent_complete != null && r.percent_complete !== ""
                ? `${r.percent_complete}%`
                : "",
              r.station_from,
              r.station_to,
              r.notes,
            ])}
            emptyText={t("No activities logged.")}
          />
        </ReportSection>

        {/* R1 · DR-FIX-1 · Production V.2 (Wave-1B). Stored on the
            record but previously invisible to consumers. NO schema
            change · NO workflow change · pure surface.
            Doctrine: /app/memory/DR_AUDIT_001_FULL_CONSTITUTIONAL_AUDIT.md */}
        {(data.production?.length || 0) > 0 && (
          <div data-testid="dr-view-production">
          <ReportSection number="09b" title={`${t("Production Quantities")} (${data.production.length})`}>
            <Table
              headers={[t("Description"), t("Quantity"), t("Unit"), t("From"), t("To"), t("Notes")]}
              rows={(data.production || []).map((r) => [
                r.description,
                r.quantity != null && r.quantity !== "" ? String(r.quantity) : "",
                r.unit === "OTHER" && r.custom_unit_label
                  ? `OTHER · ${r.custom_unit_label}`
                  : (r.unit || ""),
                r.station_from || "",
                r.station_to || "",
                r.notes || "",
              ])}
              emptyText={t("No production rows.")}
            />
          </ReportSection>
          </div>
        )}

        {/* R2 · DR-FIX-1 · Constraints V.2 (Wave-1B). Stored on the
            record but previously invisible to consumers. Surfaces the
            server-derived RFI / Schedule advisory flags. */}
        {(data.constraints?.length || 0) > 0 && (
          <div data-testid="dr-view-constraints">
          <ReportSection number="09c" title={`${t("Delays / Extra Work")} (${data.constraints.length})`}>
            <Table
              headers={[t("Type"), t("Hours Impact"), t("Advisory"), t("Notes")]}
              rows={(data.constraints || []).map((r) => {
                const flags = [];
                if (r.may_require_rfi) flags.push("RFI");
                if (r.may_affect_schedule) flags.push(t("Schedule"));
                return [
                  r.constraint_type || "",
                  r.hours_impact != null && r.hours_impact !== "" ? `${r.hours_impact} h` : "",
                  flags.join(" · "),
                  r.notes || "",
                ];
              })}
              emptyText={t("No constraints recorded.")}
            />
          </ReportSection>
          </div>
        )}

        {/* E-1 · MM-001B · Material Movement visibility tile.
            Read-only · derived from dispatch_assignments + DR rows.
            Doctrine: MM_001A_A_EXTERNAL_MATERIAL_MOVEMENT_GAP_AUDIT.md */}
        {data.project_number && data.report_date && (
          <div data-testid="dr-view-material-movement">
            <MaterialMovementTile
              projectNumber={data.project_number}
              reportDate={data.report_date}
            />
          </div>
        )}

        {data.photos?.length > 0 && (
          <ReportSection number="10" title={`${t("Photos")} (${data.photos.length})`}>
            <div className="flex justify-end mb-2 print:hidden">
              <PhotoZipDownload
                photos={data.photos}
                prefix={`${brandSlug()}_DR_${(data.id || "").slice(0, 8)}_photos`}
                testId="dr-photos-zip"
              />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4">
              {data.photos.map((p, i) => (
                <PhotoLightbox
                  key={i}
                  src={p}
                  alt={`Daily Report Photo ${i + 1}`}
                  filename={`${brandSlug()}_DR_${(data.id || "").slice(0, 8)}_photo${i + 1}.jpg`}
                  className="relative w-full aspect-square rounded-md overflow-hidden border border-slate-200 bg-white"
                  testId={`view-photo-${i}`}
                >
                  <img
                    src={resolvePhotoSrc(p)}
                    alt={`Photo ${i + 1}`}
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                </PhotoLightbox>
              ))}
            </div>
          </ReportSection>
        )}

        <ReportSection number="11" title="Sign-Off">
          {/* DR-FIX-3 · R13 · Single accountable signer.
              Superintendent block removed; Superintendent name remains
              as informational context in Section 01. */}
          <div className="max-w-md" data-testid="dr-view-signoff">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
              Prepared By
            </div>
            <div className="text-base font-bold text-slate-900 mb-2">
              {data.prepared_by || "—"}
            </div>
            <div className="border border-slate-200 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center">
              {data.prepared_by_signature ? (
                <img
                  src={data.prepared_by_signature}
                  alt="Prepared By signature"
                  className="max-h-[120px]"
                />
              ) : (
                <span className="text-slate-400 text-sm">No signature</span>
              )}
            </div>
          </div>
        </ReportSection>

        <div className="text-center font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 pt-4 pb-8 print:break-inside-avoid">
          Generated{" "}
          {data.created_at ? new Date(data.created_at).toLocaleString() : ""} ·{" "}
          {company.company_name || branding.company_name || "Customer"} Daily Report
        </div>
        {(company.address ||
          company.phone ||
          company.email) && (
          <div className="print-only border-t-2 border-black pt-3 mt-2 text-[9pt] leading-snug">
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
              </div>
            </div>
          </div>
        )}
      </main>
      <EmailReportDialog
        open={emailOpen}
        onOpenChange={setEmailOpen}
        kind="daily-report"
        record={data}
      />
    </div>
  );
}
