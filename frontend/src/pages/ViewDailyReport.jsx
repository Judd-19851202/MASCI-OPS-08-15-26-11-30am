import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
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
import { EmailReportDialog } from "@/components/EmailReportDialog";
import { EditProjectDialog } from "@/components/EditProjectDialog";
import { SubmitLangBadge } from "@/components/SubmitLangBadge";

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
  <section className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print:break-inside-avoid">
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
  <div className={full ? "sm:col-span-2" : ""}>
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
  const hubHome = useHubHome();
  const { id } = useParams();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  // Parent list URL — strips `/<id>` from the current pathname so PMs
  // viewing /pm/daily/<id> bounce back to /pm/daily, and admins viewing
  // /admin/daily/<id> bounce back to /admin/daily. Avoids the legacy
  // hard-coded "/admin/daily" that wiped the PM token via EnforcePortalScope.
  const listUrl = pathname.replace(/\/[^/]+$/, "") || "/admin/daily";
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
        toast.error("Daily report not found");
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
    if (!window.confirm("Delete this daily report? This cannot be undone."))
      return;
    try {
      await api.delete(`/daily-reports/${id}`);
      toast.success("Deleted");
      navigate(listUrl);
    } catch {
      toast.error("Delete failed");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-500">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
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
            to={listUrl}
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="back-link"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Daily Reports
          </Link>
          <MasciLogo variant="mark" size="md" homeLink={hubHome} />
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
            >
              <Trash2 className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => setEmailOpen(true)}
              className="h-11 px-4 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:text-white hover:bg-slate-700 font-bold uppercase tracking-wide text-sm"
              data-testid="email-btn"
            >
              <Mail className="w-4 h-4 mr-1" /> Email
            </Button>
            <Button
              onClick={printReport}
              className="h-11 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="print-btn"
            >
              <Printer className="w-4 h-4 mr-1" /> Print / PDF
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6">
        <div className="flex items-start justify-between border-b-4 border-red-700 pb-4 gap-4">
          <div className="flex-1">
            <MasciLogo
              variant="lockup"
              size="2xl"
              className="hidden sm:block max-w-[420px]"
              onLight
            homeLink={hubHome} />
            <MasciLogo variant="mark" size="xl" className="sm:hidden" homeLink={hubHome} />
            <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-4">
              Daily Job Report
            </h1>
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 mt-1">
              Report ID · {data.id?.slice(0, 8).toUpperCase()}
              {data.report_number ? ` · #${data.report_number}` : ""}
            </div>
            {data.submit_language === "es" && (
              <div className="mt-2">
                <SubmitLangBadge lang={data.submit_language} />
              </div>
            )}
          </div>
        </div>

        <ReportSection number="01" title="Report Information">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <KV label="Project Name" value={data.project_name} />
            <KV label="Project Number" value={data.project_number} />
            <div className="sm:col-span-2">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                Location
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
            <KV label="Date" value={formatDateLong(data.report_date)} />
            <KV label="Prepared By" value={data.prepared_by} />
            <KV label="Superintendent" value={data.superintendent} />
          </div>
        </ReportSection>

        <ReportSection number="02" title="Weather">
          {data.weather_summary && (
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700 font-bold flex items-center gap-2">
              <CloudSun className="w-4 h-4 text-amber-600" />
              {data.weather_summary}
            </div>
          )}
          {data.weather_snapshots?.length > 0 ? (
            <div className="grid grid-cols-3 gap-3 mt-3">
              {data.weather_snapshots.map((s, i) => (
                <div key={i} className="border-2 border-slate-200 rounded-md p-3 print-row">
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
            <div className="text-slate-500 text-sm">No weather captured.</div>
          )}
        </ReportSection>

        <ReportSection number="03" title="General Information">
          <div className="grid grid-cols-2 gap-4">
            <KV label="Schedule Delays" value={data.schedule_delays} />
            <KV label="Weather Impact" value={data.weather_impact} />
            <KV label="Accidents on Site" value={data.safety_incidents_today} />
            <KV label="Injuries Reported" value={data.injuries_reported} />
            {data.incident_notes && (
              <KV label="Detail" value={data.incident_notes} full />
            )}
            {(data.safety_incidents_today === "Yes" ||
              data.injuries_reported === "Yes") && (
              <div className="sm:col-span-2 mt-2 border-2 border-red-600 bg-red-50 rounded-md p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold mb-2">
                  Safety Escalation
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <KV label="Safety Notified" value={data.safety_notified} />
                  {data.safety_notified === "Yes" && (
                    <>
                      <KV
                        label="Contacted"
                        value={data.safety_contact_person}
                      />
                      <KV
                        label="Time of Contact"
                        value={data.safety_contact_time}
                      />
                      <KV
                        label="Incident Report Filed"
                        value={data.incident_report_filled}
                      />
                      {data.incident_report_filled === "Yes" && (
                        <KV
                          label="Incident Report Time"
                          value={data.incident_report_time}
                        />
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
            {data.general_notes && (
              <KV label="General Notes" value={data.general_notes} full />
            )}
          </div>
        </ReportSection>

        <ReportSection number="04" title={`MASCI Crews (${data.masci_crews?.length || 0})`}>
          <Table
            headers={["Name", "Trade / Role", "Start", "Stop", "Lunch", "Hrs", "Work Performed"]}
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
                    <strong key="tl">Total Hours</strong>,
                    <strong key="th">
                      {(data.masci_crews || [])
                        .reduce((s, r) => s + (parseFloat(r.hours) || 0), 0)
                        .toFixed(2)}
                    </strong>,
                    "",
                  ]]
                : []),
            ]}
            emptyText="No MASCI crews on site."
          />
        </ReportSection>

        <ReportSection number="05" title={`Subcontractors (${data.subcontractors?.length || 0})`}>
          <Table
            headers={["Company", "Trade", "Lead", "#", "Hrs", "Work Performed"]}
            rows={(data.subcontractors || []).map((r) => [
              r.company,
              r.trade,
              r.foreman,
              r.count,
              r.hours,
              r.work_performed,
            ])}
            emptyText="No subcontractors on site."
          />
        </ReportSection>

        <ReportSection number="06" title={`Visitors (${data.visitors?.length || 0})`}>
          <Table
            headers={["Name", "Company", "In", "Out", "Purpose"]}
            rows={(data.visitors || []).map((r) => [
              r.name,
              r.company,
              fmt12h(r.time_in),
              fmt12h(r.time_out),
              r.purpose,
            ])}
            emptyText="No site visitors."
          />
        </ReportSection>

        <ReportSection number="07" title={`Equipment (${data.equipment?.length || 0})`}>
          <Table
            headers={["Description", "Hrs", "Delivered", "Removed", "Notes"]}
            rows={(data.equipment || []).map((r) => [
              r.description,
              r.hours_used,
              fmt12h(r.time_delivered),
              fmt12h(r.time_removed),
              r.notes,
            ])}
            emptyText="No equipment logged."
          />
        </ReportSection>

        <ReportSection number="08" title={`Materials (${data.materials?.length || 0})`}>
          <Table
            headers={["Description", "Qty", "Unit", "Supplier", "Ticket #", "Notes"]}
            rows={(data.materials || []).map((r) => [
              r.description,
              r.quantity,
              r.unit,
              r.supplier,
              r.ticket_number,
              r.notes,
            ])}
            emptyText="No material deliveries."
          />
        </ReportSection>

        <ReportSection number="09" title={`Activity Log (${data.activities?.length || 0})`}>
          <Table
            headers={["Activity", "% Done", "From", "To", "Notes"]}
            rows={(data.activities || []).map((r) => [
              r.activity,
              r.percent_complete != null && r.percent_complete !== ""
                ? `${r.percent_complete}%`
                : "",
              r.station_from,
              r.station_to,
              r.notes,
            ])}
            emptyText="No activities logged."
          />
        </ReportSection>

        {data.photos?.length > 0 && (
          <ReportSection number="10" title={`Photos (${data.photos.length})`}>
            <div className="flex justify-end mb-2 print:hidden">
              <PhotoZipDownload
                photos={data.photos}
                prefix={`MASCI_DR_${(data.id || "").slice(0, 8)}_photos`}
                testId="dr-photos-zip"
              />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {data.photos.map((p, i) => (
                <PhotoLightbox
                  key={i}
                  src={p}
                  alt={`Daily Report Photo ${i + 1}`}
                  filename={`MASCI_DR_${(data.id || "").slice(0, 8)}_photo${i + 1}.jpg`}
                  className="relative w-full aspect-square rounded-md overflow-hidden border-2 border-slate-200 bg-white"
                  testId={`view-photo-${i}`}
                >
                  <img
                    src={p}
                    alt={`Photo ${i + 1}`}
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                </PhotoLightbox>
              ))}
            </div>
          </ReportSection>
        )}

        <ReportSection number="11" title="Sign-Off">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
                Prepared By
              </div>
              <div className="text-base font-bold text-slate-900 mb-2">
                {data.prepared_by || "—"}
              </div>
              <div className="border-2 border-slate-300 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center">
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
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
                Superintendent
              </div>
              <div className="text-base font-bold text-slate-900 mb-2">
                {data.superintendent || "—"}
              </div>
              <div className="border-2 border-slate-300 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center">
                {data.superintendent_signature ? (
                  <img
                    src={data.superintendent_signature}
                    alt="Superintendent signature"
                    className="max-h-[120px]"
                  />
                ) : (
                  <span className="text-slate-400 text-sm">No signature</span>
                )}
              </div>
            </div>
          </div>
        </ReportSection>

        <div className="text-center font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 pt-4 pb-8 print:break-inside-avoid">
          Generated{" "}
          {data.created_at ? new Date(data.created_at).toLocaleString() : ""} ·{" "}
          {company.company_name || "MASCI"} Daily Report
        </div>
        {(company.address ||
          company.phone ||
          company.email) && (
          <div className="print-only border-t-2 border-black pt-3 mt-2 text-[9pt] leading-snug">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-display font-black text-[11pt] text-black">
                  {company.company_name || "MASCI"}
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
