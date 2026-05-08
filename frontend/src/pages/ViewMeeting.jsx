import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { ArrowLeft, Printer, Loader2, Trash2, MapPin, Mail } from "lucide-react";
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
import { BilingualConsent } from "@/components/BilingualConsent";
import { SubmitLangBadge } from "@/components/SubmitLangBadge";

const ReportSection = ({ number, title, children }) => (
  <section className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section">
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

const KV = ({ label, value, full = false }) => (
  <div className={full ? "sm:col-span-2" : ""}>
    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
      {label}
    </div>
    <div className="text-base text-slate-900 mt-1 whitespace-pre-wrap">
      {value || "—"}
    </div>
  </div>
);

export default function ViewMeeting() {
  const hubHome = useHubHome();
  const { id } = useParams();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const listUrl = pathname.replace(/\/[^/]+$/, "") || "/admin/meetings";
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [emailOpen, setEmailOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api.get(`/meetings/${id}`);
        if (alive) setData(res.data);
      } catch {
        toast.error("Meeting not found");
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
    if (!window.confirm("Delete this meeting? This cannot be undone.")) return;
    try {
      await api.delete(`/meetings/${id}`);
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
            <ArrowLeft className="w-4 h-4 mr-1" /> Meetings
          </Link>
          <MasciLogo variant="mark" size="md" homeLink={hubHome} />
          <div className="flex gap-2">
            <EditProjectDialog
              kind="meetings"
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
              className="h-11 px-4 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:bg-slate-700 font-bold uppercase tracking-wide text-sm"
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

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 print-page">
        <div className="flex items-start justify-between border-b-4 border-red-700 pb-4 gap-4">
          <div className="flex-1">
            <MasciLogo variant="lockup" size="2xl" className="hidden sm:block max-w-[420px]" onLight homeLink={hubHome} />
            <MasciLogo variant="mark" size="xl" className="sm:hidden" homeLink={hubHome} />
            <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-4">
              Site Safety Meeting Record
            </h1>
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 mt-1 flex items-center gap-2 flex-wrap">
              {data.doc_id && (
                <span
                  className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-red-50 border border-red-300 text-red-800 font-bold tabular-nums tracking-wide"
                  data-testid="record-doc-id-badge"
                >
                  <span className="text-[9px] uppercase tracking-[0.22em] text-red-700">Doc ID</span>
                  {data.doc_id}
                </span>
              )}
              <span>Report ID · {data.id?.slice(0, 8).toUpperCase()}</span>
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
        </div>

        <ReportSection number="01" title="Meeting Information">
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
                  <span>GPS · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}</span>
                  <a
                    href={`https://www.google.com/maps?q=${data.gps_lat},${data.gps_lng}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-red-700 hover:text-red-800 font-bold no-print"
                  >
                    · Open in Maps
                  </a>
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
            <KV label="Date" value={formatDateLong(data.meeting_date)} />
            <KV label="Time" value={data.meeting_time} />
            <KV label="Conducted By" value={data.conducted_by} />
            <KV label="Category" value={data.topic_category} />
          </div>
        </ReportSection>

        <ReportSection number="02" title="Topic & Discussion">
          <div className="space-y-4">
            <KV label="Topic / Subject" value={data.topic} full />
            <KV label="Hazards Reviewed" value={data.hazards_reviewed} full />
            <KV label="Discussion Notes" value={data.discussion_notes} full />
            <KV label="References Cited" value={data.references_cited} full />
            <KV label="Action Items / Follow-Up" value={data.action_items} full />
          </div>
        </ReportSection>

        <ReportSection number="03" title={`Attendees (${data.attendees?.length || 0})`}>
          {data.attendees?.length === 0 ? (
            <div className="text-slate-500 text-sm">No attendees listed.</div>
          ) : (
            <>
              <BilingualConsent variant="meeting" />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
                {(data.attendees || []).map((a, i) => (
                  <div
                    key={i}
                    className="border-2 border-slate-200 rounded-md p-3 print-row"
                  >
                    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                      Attendee {i + 1}
                    </div>
                    <div className="font-bold text-slate-900 mt-1">{a.name || "—"}</div>
                    {a.signature && (
                      <img
                        src={a.signature}
                        alt={`Signature ${i + 1}`}
                        className="max-h-[60px] mt-2 border border-slate-200 rounded"
                      />
                    )}
                    <BilingualConsent variant="meeting" compact />
                  </div>
                ))}
              </div>
            </>
          )}
        </ReportSection>

        {data.photos?.length > 0 && (
          <ReportSection number="04" title={`Photos (${data.photos.length})`}>
            <div className="flex justify-end mb-2 print:hidden">
              <PhotoZipDownload
                photos={data.photos}
                prefix={`MASCI_Meeting_${(data.id || "").slice(0, 8)}_photos`}
                testId="meeting-photos-zip"
              />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {data.photos.map((p, i) => (
                <PhotoLightbox
                  key={i}
                  src={p}
                  alt={`Meeting Photo ${i + 1}`}
                  filename={`MASCI_Meeting_${(data.id || "").slice(0, 8)}_photo${i + 1}.jpg`}
                  className="relative w-full aspect-square rounded-md overflow-hidden border-2 border-slate-200 bg-white"
                  testId={`view-photo-${i}`}
                >
                  <img src={p} alt={`Photo ${i + 1}`} className="absolute inset-0 w-full h-full object-cover" />
                </PhotoLightbox>
              ))}
            </div>
          </ReportSection>
        )}

        <ReportSection number="05" title="Conductor Signature">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
            Conducted By
          </div>
          <div className="text-base font-bold text-slate-900 mb-2">{data.conducted_by || "—"}</div>
          <BilingualConsent variant="meeting" />
          <div className="border-2 border-slate-300 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center max-w-md mt-3">
            {data.conductor_signature ? (
              <img src={data.conductor_signature} alt="Conductor signature" className="max-h-[120px]" />
            ) : (
              <span className="text-slate-400 text-sm">No signature</span>
            )}
          </div>
        </ReportSection>

        <div className="text-center font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 pt-4 pb-8 print-section">
          Generated {data.created_at ? new Date(data.created_at).toLocaleString() : ""} · {company.company_name || "MASCI"} Safety Meeting
        </div>
        {(company.address || company.phone || company.email) && (
          <div className="print-only border-t-2 border-black pt-3 mt-2 text-[9pt] leading-snug print-section">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-display font-black text-[11pt] text-black">{company.company_name || "MASCI"}</div>
                {company.tagline && (
                  <div className="font-mono text-[8pt] uppercase tracking-[0.2em] text-black">{company.tagline}</div>
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
      <EmailReportDialog open={emailOpen} onOpenChange={setEmailOpen} kind="meeting" record={data} />
    </div>
  );
}
