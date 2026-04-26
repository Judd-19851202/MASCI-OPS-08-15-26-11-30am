import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Printer, Loader2, AlertTriangle, Trash2, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { getCompanyInfo } from "@/lib/companyInfo";
import { computeGrade } from "@/lib/grading";
import { GradeBanner } from "@/components/Grade";
import { formatCoords } from "@/lib/geolocation";
import { MapThumbnail } from "@/components/MapThumbnail";
import { printReport, maybeAutoPrint } from "@/lib/printReport";
import {
  PPE_ITEMS,
  SITE_HAZARD_ITEMS,
  CONDITIONAL_SECTIONS,
} from "@/lib/inspectionSchema";
import { formatDateLong } from "@/lib/utils";

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
  <div className={full ? "sm:col-span-2" : ""}>
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
    className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section"
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
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api.get(`/inspections/${id}`);
        if (alive) setData(res.data);
      } catch {
        toast.error("Inspection not found");
        navigate("/admin/inspections");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [id, navigate]);

  // Auto-print after the page renders if we landed here via ?autoprint=1
  useEffect(() => {
    if (!loading && data) maybeAutoPrint();
  }, [loading, data]);

  const handleDelete = async () => {
    if (!window.confirm("Delete this inspection? This cannot be undone.")) return;
    try {
      await api.delete(`/inspections/${id}`);
      toast.success("Deleted");
      navigate("/admin/inspections");
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
      <div className="caution-stripe no-print" />
      <header className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10 no-print">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link
            to="/admin/inspections"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="back-link"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Reports
          </Link>
          <MasciLogo variant="mark" size="md" />
          <div className="flex gap-2">
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
        {/* Print header */}
        <div className="flex items-start justify-between border-b-4 border-red-700 pb-4 gap-4">
          <div className="flex-1">
            <MasciLogo variant="lockup" size="2xl" className="hidden sm:block max-w-[420px]" onLight />
            <MasciLogo variant="mark" size="xl" className="sm:hidden" />
            <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-4">
              Job Site Safety Inspection Report
            </h1>
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 mt-1">
              Report ID · {data.id?.slice(0, 8).toUpperCase()}
            </div>
            <div className="mt-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
              <span>No Shortcuts</span>
              <span className="w-1 h-1 rounded-full bg-red-700" />
              <span>No Exceptions</span>
            </div>
          </div>
          {flagged && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-2 bg-red-700 text-white rounded-md self-start">
              <AlertTriangle className="w-5 h-5" />
              <span className="font-bold uppercase tracking-wide text-sm">
                {data.stop_work_issued === "Yes" ? "Stop Work" : "Hazard Found"}
              </span>
            </div>
          )}
        </div>

        {/* Grade banner */}
        <GradeBanner grade={grade} />

        <ReportSection number="01" title="Project / Inspection Information">
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
                    · Open in Maps
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
            <KV label="Date" value={formatDateLong(data.inspection_date)} />
            <KV label="Time" value={data.inspection_time} />
            <KV label="Operation" value={data.operation} />
            <KV label="Inspector" value={data.inspector_name} />
            <KV label="Foreman / Supervisor" value={data.foreman_name} />
            <KV label="Crew / MASCI Personnel" value={data.crew_personnel} full />
            <KV label="Subcontractors" value={data.subcontractors} full />
            <KV label="Weather Conditions" value={data.weather_conditions} full />
          </div>
        </ReportSection>

        <ReportSection number="02" title="Work Activity Taking Place Onsite">
          <p className="text-base text-slate-900 whitespace-pre-wrap">
            {data.work_activity || "—"}
          </p>
        </ReportSection>

        <ReportSection number="03" title="PPE Compliance">
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
                        Notes
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

        <ReportSection number="11" title="General Site Hazards & Housekeeping">
          {SITE_HAZARD_ITEMS.map((item) => (
            <ReadRow
              key={item.key}
              label={item.label}
              value={data.site_hazards?.[item.key]}
            />
          ))}
        </ReportSection>

        <ReportSection number="12" title="Safety Issues / Corrective Actions">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
            <KV label="Hazards Observed" value={data.hazards_observed} />
            <KV label="Stop Work Issued" value={data.stop_work_issued} />
            <KV label="Corrected On Site" value={data.corrected_on_site} />
          </div>
          <KV label="Responsible Party" value={data.responsible_party} full />
          <div className="mt-3">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
              Description / Corrective Action Notes
            </div>
            <p className="text-base text-slate-900 mt-1 whitespace-pre-wrap">
              {data.corrective_action_notes || "—"}
            </p>
          </div>
          {data.photos?.length > 0 && (
            <div className="mt-4">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2">
                Photo Documentation ({data.photos.length})
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {data.photos.map((p, i) => {
                  const stamp = `${(company.company_name || "MASCI").toUpperCase()} · ${
                    (data.id || "").slice(0, 8).toUpperCase()
                  } · ${formatDateLong(data.inspection_date)}`;
                  return (
                    <div
                      key={i}
                      className="relative w-full aspect-square rounded-md overflow-hidden border-2 border-slate-200 bg-white"
                      data-testid={`view-photo-${i}`}
                    >
                      <img
                        src={p}
                        alt={`Finding ${i + 1}`}
                        className="absolute inset-0 w-full h-full object-cover"
                      />
                      {/* Diagonal MASCI watermark — visible on screen and print */}
                      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                        <span
                          className="font-display font-black text-white/30 select-none"
                          style={{
                            transform: "rotate(-30deg)",
                            fontSize: "clamp(14px, 6vw, 28px)",
                            letterSpacing: "0.2em",
                            textShadow: "0 1px 2px rgba(0,0,0,0.4)",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {(company.company_name || "MASCI").toUpperCase()}
                        </span>
                      </div>
                      {/* Bottom traceability strip */}
                      <div className="absolute bottom-0 left-0 right-0 bg-black/65 text-white px-1.5 py-1 font-mono text-[8px] uppercase tracking-wider truncate">
                        {stamp}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </ReportSection>

        <ReportSection number="13" title="Signatures">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
                Inspector
              </div>
              <div className="text-base font-bold text-slate-900 mb-2">
                {data.inspector_name || "—"}
              </div>
              <div className="border-2 border-slate-300 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center">
                {data.inspector_signature ? (
                  <img
                    src={data.inspector_signature}
                    alt="Inspector signature"
                    className="max-h-[120px]"
                    data-testid="view-inspector-sig"
                  />
                ) : (
                  <span className="text-slate-400 text-sm">No signature</span>
                )}
              </div>
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
                Foreman / Supervisor
              </div>
              <div className="text-base font-bold text-slate-900 mb-2">
                {data.foreman_name || "—"}
              </div>
              <div className="border-2 border-slate-300 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center">
                {data.foreman_signature ? (
                  <img
                    src={data.foreman_signature}
                    alt="Foreman signature"
                    className="max-h-[120px]"
                    data-testid="view-foreman-sig"
                  />
                ) : (
                  <span className="text-slate-400 text-sm">No signature</span>
                )}
              </div>
            </div>
          </div>
        </ReportSection>

        <div className="text-center font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 pt-4 pb-8 print-section">
          Generated {data.created_at ? new Date(data.created_at).toLocaleString() : ""} · {company.company_name || "MASCI"} Job Site Safety
        </div>

        {/* Print-only company info footer */}
        {(company.address || company.phone || company.email || company.website) && (
          <div className="print-only border-t-2 border-black pt-3 mt-2 text-[9pt] leading-snug print-section">
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
    </div>
  );
}
