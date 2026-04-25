import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Printer, Loader2, AlertTriangle, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { api } from "@/lib/api";
import { toast } from "sonner";
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

const ReadRow = ({ label, value }) => (
  <div className="flex items-start justify-between gap-4 py-2 border-b border-slate-100 last:border-b-0 print-row">
    <span className="text-sm text-slate-700 leading-snug">{label}</span>
    <StatusBadge value={value} />
  </div>
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

const ReportSection = ({ number, title, children }) => (
  <section
    className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section"
    data-testid={`view-section-${number}`}
  >
    <div className="flex items-baseline gap-3 mb-4 pb-2 border-b-2 border-slate-200">
      <span className="font-mono text-xs uppercase tracking-[0.2em] text-yellow-600">
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
        navigate("/");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [id, navigate]);

  const handleDelete = async () => {
    if (!window.confirm("Delete this inspection? This cannot be undone.")) return;
    try {
      await api.delete(`/inspections/${id}`);
      toast.success("Deleted");
      navigate("/");
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

  const flagged =
    data.hazards_observed === "Yes" || data.stop_work_issued === "Yes";

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe no-print" />
      <header className="bg-white border-b-2 border-slate-300 sticky top-0 z-10 no-print">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link
            to="/"
            className="inline-flex items-center text-slate-700 hover:text-slate-900 text-sm font-bold uppercase tracking-wide"
            data-testid="back-link"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Reports
          </Link>
          <MasciLogo size="sm" />
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={handleDelete}
              className="h-11 w-11 border-2 border-slate-300 hover:border-red-500 hover:text-red-600"
              data-testid="delete-btn"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
            <Button
              onClick={() => window.print()}
              className="h-11 px-4 bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-bold uppercase tracking-wide text-sm"
              data-testid="print-btn"
            >
              <Printer className="w-4 h-4 mr-1" /> Print / PDF
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 print-page">
        {/* Print header */}
        <div className="flex items-start justify-between border-b-4 border-slate-900 pb-4">
          <div>
            <MasciLogo size="lg" />
            <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-3">
              Job Site Safety Inspection Report
            </h1>
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 mt-1">
              Report ID · {data.id?.slice(0, 8).toUpperCase()}
            </div>
          </div>
          {flagged && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-2 bg-red-600 text-white rounded-md">
              <AlertTriangle className="w-5 h-5" />
              <span className="font-bold uppercase tracking-wide text-sm">
                {data.stop_work_issued === "Yes" ? "Stop Work" : "Hazard Found"}
              </span>
            </div>
          )}
        </div>

        <ReportSection number="01" title="Project / Inspection Information">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <KV label="Project Name" value={data.project_name} />
            <KV label="Project Number" value={data.project_number} />
            <KV label="Location" value={data.location} full />
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
                {data.photos.map((p, i) => (
                  <img
                    key={i}
                    src={p}
                    alt={`Finding ${i + 1}`}
                    className="w-full aspect-square object-cover rounded-md border-2 border-slate-200"
                    data-testid={`view-photo-${i}`}
                  />
                ))}
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

        <div className="text-center font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 pt-4 pb-8">
          Generated {data.created_at ? new Date(data.created_at).toLocaleString() : ""} · MASCI Job Site Safety
        </div>
      </main>
    </div>
  );
}
