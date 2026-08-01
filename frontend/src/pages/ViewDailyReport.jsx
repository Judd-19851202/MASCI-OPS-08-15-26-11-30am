import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { brandSlug } from "@/lib/brandFilename";
import { useBranding } from "@/lib/BrandingProvider";
import {
  Printer,
  Loader2,
  Trash2,
  MapPin,
  CloudSun,
  Mail,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { RefKicker } from "@/components/RefKicker";
import { MasciLogo } from "@/components/MasciLogo";
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
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { resolvePhotoSrc } from "@/lib/photoSrc";
import { EmailReportDialog } from "@/components/EmailReportDialog";
import { EditProjectDialog } from "@/components/EditProjectDialog";
import { SubmitLangBadge } from "@/components/SubmitLangBadge";
import MaterialMovementTile from "@/components/MaterialMovementTile";
import { useT } from "@/lib/i18n";
import { DetailPageHero } from "@/components/detail/DetailPageHero";
import { DataTable } from "@/design-system/DataTable";
import EmptyState from "@/components/EmptyState";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

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
  <section className="wp17-panel rounded-[1.5rem] p-5 sm:p-7 print:break-inside-avoid shadow-[0_16px_40px_rgba(15,23,42,0.05)]">
    <div className="flex items-baseline gap-3 mb-4 pb-3 border-b border-slate-200/80">
      <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-red-700 font-bold">
        Section {number}
      </span>
      <h2 className="font-display text-xl sm:text-2xl font-black tracking-tight text-slate-900">
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

function formatSummarySource(source, t) {
  switch (String(source || "").toLowerCase()) {
    case "manual":
      return t("Manual summary approved");
    case "fallback":
      return t("Generated fallback summary approved");
    case "edited":
      return t("Edited AI summary approved");
    case "ai":
      return t("AI summary approved");
    default:
      return t("Approved summary");
  }
}

const Table = ({ headers, rows, emptyText }) => {
  const columns = headers.map((header, idx) => ({
    key: `c${idx}`,
    header,
    wrap: true,
    render: (row) => row[`c${idx}`] ?? "—",
  }));

  const normalizedRows = (rows || []).map((row, idx) => {
    const entry = { __id: idx };
    headers.forEach((_, cellIdx) => {
      entry[`c${cellIdx}`] = row[cellIdx] || "—";
    });
    return entry;
  });

  return (
    <DataTable
      columns={columns}
      rows={normalizedRows}
      rowKey={(row) => row.__id}
      density="compact"
      empty={<EmptyState title={emptyText} message="" icon={CloudSun} data-testid="daily-report-table-empty" />}
      emptyText={emptyText}
      tableMinWidth="720px"
      data-testid="daily-report-data-table"
    />
  );
};

function formatAttachmentSize(bytes) {
  const size = Number(bytes || 0);
  if (!size) return "—";
  if (size >= 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  if (size >= 1024) return `${Math.round(size / 1024)} KB`;
  return `${size} B`;
}

function attachmentKindLabel(rawKind, rawCategory) {
  const key = String(rawKind || rawCategory || "other").trim().toLowerCase();
  const labels = {
    pdf: "PDF",
    spreadsheet: "Spreadsheet",
    text: "Text",
    document: "Document",
    other: "Other",
  };
  return labels[key] || String(rawCategory || rawKind || "Other");
}

export default function ViewDailyReport() {
  const branding = useBranding();
  const { t } = useT();
  const hubHome = useHubHome();
  const { id } = useParams();
  const navigate = useNavigate();
  const { pathname, state: navState } = useLocation();
  const isAdminRoute = pathname.startsWith("/admin/");
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
  const explicitReturnTo = typeof navState?.returnTo === "string" && navState.returnTo.trim()
    ? navState.returnTo
    : "";
  const backHref = cameFromPmPhotos
    ? (navState.returnTo || "/pm/command-center")
    : (explicitReturnTo || (isHrReadOnly ? "/hr/daily-reports" : listUrl));
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
    const loadingContent = (
      <div className="min-h-screen flex items-center justify-center text-slate-500">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> {t("Loading…")}
      </div>
    );
    return isAdminRoute ? (
      <AdminRouteShell
        pageTitle="Daily Report"
        subtitle="Admin review for field activity, labor, production, weather, and attachments."
        portalRole="Admin · Daily Reports"
        crumbs={[{ label: "Field Operations" }, { label: "Daily Reports" }]}
        showShellHeader={false}
        showBreadcrumbs={false}
        testId="admin-view-daily-report-shell"
      >
        {loadingContent}
      </AdminRouteShell>
    ) : loadingContent;
  }
  if (!data) return null;

  const company = getCompanyInfo();
  const acceptedSummary = (data.ai_accepted_summary || data.daily_operational_summary || "").trim();
  const acceptedSummaryMeta = data.ai_accepted_summary_meta || {};
  const photoObservations = Array.isArray(data.ai_photo_observations)
    ? data.ai_photo_observations
    : Array.isArray(data.photo_observations)
      ? data.photo_observations
      : [];
  const notificationState = String(data.notification_state || "").toLowerCase();
  const deliveryMode = String(data.notification_delivery_mode || "");
  const notificationMessage = notificationState === "captured_preview"
    ? t("Preview capture recorded. No live email was sent.")
    : notificationState === "provider_accepted"
      ? t("Provider accepted the notification for delivery.")
      : notificationState === "configuration_blocked"
        ? t("Notification delivery is configuration-blocked and requires follow-up.")
        : notificationState === "retryable_failure"
          ? t("Notification delivery failed and is retryable.")
          : notificationState === "permanent_failure"
            ? t("Notification delivery failed and requires operator correction.")
            : t("Notification state pending or not yet recorded.");

  const content = (
    <div className="min-h-screen bg-slate-50">
      <PrintWatermark />
      <div className="caution-stripe no-print" />
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
              {t("Project Management")}
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
        <DetailPageHero
          backHref={backHref}
          backLabel={backLabel}
          kicker={isHrReadOnly ? t("Human Resources · Daily Report Review") : t("Field Operations · Daily Report Review")}
          title={t("Daily Job Report")}
          description={t("Review field activity, delivery status, and attachments before printing, emailing, or moving the report downstream.")}
          actions={isHrReadOnly ? null : (
            <>
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
                data-testid="delete-btn"
                aria-label="Delete daily report"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                onClick={() => setEmailOpen(true)}
                size="sm"
                data-testid="email-btn"
              >
                <Mail className="w-4 h-4 mr-1" /> {t("Email")}
              </Button>
              <Button
                onClick={printReport}
                size="sm"
                data-testid="print-btn"
              >
                <Printer className="w-4 h-4 mr-1" /> {t("Print / PDF")}
              </Button>
            </>
          )}
          chips={
            <>
              <RefKicker recordId={data.report_number || data.id} testId="view-daily-ref" />
              {data.doc_id ? (
                <span className="wp17-status-badge wp17-tone--red" data-testid="record-doc-id-badge">
                  <span className="text-[9px] uppercase tracking-[0.22em] text-red-700">{t("Doc ID")}</span>
                  {data.doc_id}
                </span>
              ) : null}
              <span className="wp17-status-badge wp17-tone--slate">
                {t("Report ID")} · {data.id?.slice(0, 8).toUpperCase()}
                {data.report_number ? ` · #${data.report_number}` : ""}
              </span>
              {data.submit_language === "es" ? <SubmitLangBadge lang={data.submit_language} /> : null}
            </>
          }
          toolbar={isHrReadOnly ? (
            <div className="wp17-status-badge wp17-tone--slate" data-testid="hr-readonly-badge">
              {t("Read-only · HR")}
            </div>
          ) : null}
          testId="view-daily-hero"
        />
        <div className="hidden print:flex items-start justify-between border-b-4 border-red-700 pb-4 gap-4">
          <div className="flex-1">
            <MasciLogo
              variant="mark"
              size="2xl"
              className="hidden sm:block max-w-[420px]"
              onLight
            homeLink={hubHome} />
            <MasciLogo variant="mark" size="xl" className="sm:hidden" homeLink={hubHome} />
            {/* iter336 · review-side reference continuity */}
            <RefKicker recordId={data.report_number || data.id} testId="view-daily-ref-print" className="mt-4" />
            <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">
              {t("Daily Job Report")}
            </h1>
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 mt-1 flex items-center gap-2 flex-wrap">
              {data.doc_id && (
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-red-50 border border-red-300 text-red-800 font-bold tabular-nums tracking-wide">
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
        {!isHrReadOnly && <DailyReportLifecyclePanel reportId={data.id} />}

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
                  {data.location_source || "GPS"} · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}
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
          <div
            className="mt-4 rounded-xl border border-slate-200 bg-white/90 p-4"
            data-testid="daily-report-notification-status"
          >
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
              {t("Notification Delivery")}
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span
                className="rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-900"
                data-testid="daily-report-notification-state-badge"
              >
                {notificationState || t("pending")}
              </span>
              <span
                className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-900"
                data-testid="daily-report-delivery-mode-badge"
              >
                {deliveryMode || t("unknown")}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-700" data-testid="daily-report-notification-status-text">
              {notificationMessage}
            </p>
            {data.notification_failure_reason && (
              <p className="mt-2 text-xs text-slate-500" data-testid="daily-report-notification-reason">
                {data.notification_failure_reason}
              </p>
            )}
          </div>
        </ReportSection>

        <ReportSection number="02" title={t("Weather")}>
          {data.weather_summary && (
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700 font-bold flex items-center gap-2">
              <CloudSun className="w-4 h-4 text-amber-600" />
              {data.weather_summary}
            </div>
          )}
          {(data.weather_snapshot_meta?.provider || data.weather_snapshot_meta?.source || data.weather_snapshot_meta?.timezone) && (
            <div className="mt-2 text-xs text-slate-600" data-testid="view-dr-weather-meta">
              {data.weather_snapshot_meta?.provider || data.weather_snapshot_meta?.source || "—"}
              {data.weather_snapshot_meta?.timezone ? ` · ${data.weather_snapshot_meta.timezone}` : ""}
              {data.weather_snapshot_meta?.observation_timestamp ? ` · ${data.weather_snapshot_meta.observation_timestamp}` : ""}
            </div>
          )}
          {data.weather_snapshots?.length > 0 ? (
            <div className="grid grid-cols-3 gap-3 mt-3">
              {data.weather_snapshots.map((s, i) => (
                <div key={i} className="wp17-result-tile print-row">
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
              <div className="lg:col-span-2 mt-2 rounded-[1.1rem] border border-red-300 bg-red-50 p-4">
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

        {acceptedSummary && (
          <ReportSection number="03b" title={t("Operational Summary") }>
            <div className="wp17-result-tile" data-testid="view-dr-operational-summary">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2">
                {formatSummarySource(acceptedSummaryMeta.source, t)}
              </div>
              <div className="whitespace-pre-wrap text-sm leading-6 text-slate-900">
                {acceptedSummary}
              </div>
              {acceptedSummaryMeta.accepted_at && (
                <div className="mt-3 text-xs text-slate-500" data-testid="view-dr-operational-summary-meta">
                  {t("Accepted")}: {formatPlatformTime(acceptedSummaryMeta.accepted_at)}
                </div>
              )}
            </div>
          </ReportSection>
        )}

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
            {photoObservations.length > 0 && (
              <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4" data-testid="view-dr-photo-observations">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2">
                  {t("Grounded Photo Observations")}
                </div>
                <div className="space-y-3">
                  {photoObservations.slice(0, 8).map((item, idx) => (
                    <div key={`${item.photo_ref || item.photo_id || idx}`} className="text-sm text-slate-800" data-testid={`view-dr-photo-observation-${idx}`}>
                      {item.summary && <div className="font-medium text-slate-900">{item.summary}</div>}
                      {Array.isArray(item.observations) && item.observations.length > 0 && (
                        <ul className="mt-1 list-disc pl-5 text-slate-700">
                          {item.observations.slice(0, 4).map((obs, obsIdx) => (
                            <li key={obsIdx}>{obs}</li>
                          ))}
                        </ul>
                      )}
                      {item.ticket_text && (
                        <div className="mt-1 text-xs text-slate-600">{item.ticket_text}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </ReportSection>
        )}

        {data.attachments?.length > 0 && (
          <ReportSection number="10A" title={`${t("Attachments & document evidence")} (${data.attachments.length})`}>
            <div data-testid="dr-view-attachments">
              <Table
                headers={[t("Kind"), t("Filename"), t("Size"), t("Uploaded")]}
                rows={(data.attachments || []).map((attachment) => [
                  attachmentKindLabel(attachment?.kind, attachment?.category),
                  attachment?.filename || t("Attachment"),
                  formatAttachmentSize(attachment?.file_size),
                  attachment?.uploaded_at ? formatPlatformTime(attachment.uploaded_at) : "—",
                ])}
                emptyText={t("No attachments uploaded.")}
              />
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
          {data.created_at ? formatPlatformTime(data.created_at) : ""} ·{" "}
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

  return isAdminRoute ? (
    <AdminRouteShell
      pageTitle="Daily Report"
      subtitle="Admin review for field activity, labor, production, weather, and attachments."
      portalRole="Admin · Daily Reports"
      crumbs={[
        { label: "Field Operations" },
        { label: "Daily Reports" },
        { label: data.project_name || data.id?.slice(0, 8)?.toUpperCase() || "Report" },
      ]}
      showShellHeader={false}
      showBreadcrumbs={false}
      contentClassName="px-0 py-0"
      testId="admin-view-daily-report-shell"
    >
      {content}
    </AdminRouteShell>
  ) : content;
}
