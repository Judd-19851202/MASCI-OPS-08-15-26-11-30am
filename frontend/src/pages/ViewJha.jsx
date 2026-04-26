import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Printer, Loader2, Trash2, MapPin, CheckSquare, AlertTriangle, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { formatDateLong } from "@/lib/utils";
import { getCompanyInfo } from "@/lib/companyInfo";
import { formatCoords } from "@/lib/geolocation";
import { PPE_OPTIONS, PERMIT_OPTIONS } from "@/lib/jhaSchema";
import { BilingualConsent } from "@/components/BilingualConsent";

const ReportSection = ({ number, title, children }) => (
  <section className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section">
    <div className="flex items-baseline gap-3 mb-4 pb-2 border-b-2 border-slate-200">
      <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700">Section {number}</span>
      <h2 className="font-display text-xl sm:text-2xl font-bold text-slate-900">{title}</h2>
    </div>
    {children}
  </section>
);

const KV = ({ label, value, full = false }) => (
  <div className={full ? "sm:col-span-2" : ""}>
    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{label}</div>
    <div className="text-base text-slate-900 mt-1 whitespace-pre-wrap">{value || "—"}</div>
  </div>
);

export default function ViewJha() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api.get(`/jhas/${id}`);
        if (alive) setData(res.data);
      } catch {
        toast.error("JHA not found");
        navigate("/jha");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [id, navigate]);

  const handleDelete = async () => {
    if (!window.confirm("Delete this JHA? This cannot be undone.")) return;
    try {
      await api.delete(`/jhas/${id}`);
      toast.success("Deleted");
      navigate("/jha");
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
  const checkedPpe = PPE_OPTIONS.filter((o) => data.ppe_required?.[o.key]);
  const checkedPermits = PERMIT_OPTIONS.filter((o) => data.permits_required?.[o.key]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe no-print" />
      <header className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10 no-print">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link to="/jha" className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide" data-testid="back-link">
            <ArrowLeft className="w-4 h-4 mr-1" /> JHAs
          </Link>
          <MasciLogo variant="mark" size="md" />
          <div className="flex gap-2">
            <Button variant="outline" size="icon" onClick={handleDelete} className="h-11 w-11 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:text-red-400" data-testid="delete-btn">
              <Trash2 className="w-4 h-4" />
            </Button>
            <Button onClick={() => window.print()} className="h-11 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900" data-testid="print-btn">
              <Printer className="w-4 h-4 mr-1" /> Print / PDF
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 print-page">
        <div className="flex items-start justify-between border-b-4 border-red-700 pb-4 gap-4">
          <div className="flex-1">
            <MasciLogo variant="lockup" size="2xl" className="hidden sm:block max-w-[420px]" />
            <MasciLogo variant="mark" size="xl" className="sm:hidden" />
            <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-4">
              Job Hazard Analysis
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
        </div>

        <ReportSection number="01" title="Job / Task Information">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <KV label="Project Name" value={data.project_name} />
            <KV label="Project Number" value={data.project_number} />
            <div className="sm:col-span-2">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Location</div>
              <div className="text-base text-slate-900 mt-1 whitespace-pre-wrap">{data.location || "—"}</div>
              {data.gps_lat != null && (
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1 flex items-center gap-1 flex-wrap">
                  <MapPin className="w-3 h-3 text-red-700" />
                  <span>GPS · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}</span>
                  <a href={`https://www.google.com/maps?q=${data.gps_lat},${data.gps_lng}`} target="_blank" rel="noopener noreferrer" className="text-red-700 hover:text-red-800 font-bold no-print">· Open in Maps</a>
                </div>
              )}
            </div>
            <KV label="Date" value={formatDateLong(data.jha_date)} />
            <KV label="Crew Lead / Foreman" value={data.crew_lead} />
            <KV label="Job / Task Title" value={data.job_title} full />
            <KV label="Job Description" value={data.job_description} full />
            <KV label="Crew Members" value={data.crew_members} full />
          </div>
        </ReportSection>

        <ReportSection number="02" title="Required PPE & Permits">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2">PPE</div>
              {checkedPpe.length === 0 ? (
                <div className="text-slate-500 text-sm">None specified</div>
              ) : (
                <ul className="space-y-1">
                  {checkedPpe.map((o) => (
                    <li key={o.key} className="flex items-center gap-2 text-sm text-slate-800">
                      <CheckSquare className="w-4 h-4 text-green-700" /> {o.label}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2">Permits</div>
              {checkedPermits.length === 0 ? (
                <div className="text-slate-500 text-sm">None required</div>
              ) : (
                <ul className="space-y-1">
                  {checkedPermits.map((o) => (
                    <li key={o.key} className="flex items-center gap-2 text-sm text-slate-800">
                      <CheckSquare className="w-4 h-4 text-amber-600" /> {o.label}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
          {data.tools_equipment && (
            <div className="mt-4 pt-4 border-t border-slate-200">
              <KV label="Tools & Equipment" value={data.tools_equipment} full />
            </div>
          )}
        </ReportSection>

        <ReportSection number="03" title="Hazard Analysis">
          <div className="space-y-3">
            {(data.task_steps || []).filter((s) => s.step?.trim() || s.hazards?.trim() || s.controls?.trim()).map((s, i) => (
              <div key={i} className="border-2 border-slate-200 rounded-md p-4 print-row">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold mb-2">Step {i + 1}</div>
                <div className="font-bold text-slate-900 mb-2">{s.step || "—"}</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-red-700 font-bold flex items-center gap-1 mb-1">
                      <AlertTriangle className="w-3 h-3" /> Potential Hazards
                    </div>
                    <div className="text-slate-800 whitespace-pre-wrap">{s.hazards || "—"}</div>
                  </div>
                  <div>
                    <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-green-700 font-bold flex items-center gap-1 mb-1">
                      <ShieldCheck className="w-3 h-3" /> Controls / Safe Practices
                    </div>
                    <div className="text-slate-800 whitespace-pre-wrap">{s.controls || "—"}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ReportSection>

        <ReportSection number="04" title="Emergency & Stop Work">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <KV label="Stop Work Authority" value={data.stop_work_acknowledged} />
            <div />
            <KV label="Nearest Hospital / ER" value={data.nearest_hospital} />
            <KV label="Emergency Contact #" value={data.emergency_contact} />
          </div>
        </ReportSection>

        <ReportSection number="05" title={`Crew Sign-Off (${data.crew_signoffs?.length || 0})`}>
          {(!data.crew_signoffs || data.crew_signoffs.length === 0) ? (
            <div className="text-slate-500 text-sm">No crew sign-offs recorded.</div>
          ) : (
            <>
              <BilingualConsent variant="jha" />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
                {data.crew_signoffs.map((c, i) => (
                  <div key={i} className="border-2 border-slate-200 rounded-md p-3 print-row">
                    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Crew Member {i + 1}</div>
                    <div className="font-bold text-slate-900 mt-1">{c.name || "—"}</div>
                    {c.signature && (
                      <img src={c.signature} alt={`Sig ${i + 1}`} className="max-h-[60px] mt-2 border border-slate-200 rounded" />
                    )}
                    <BilingualConsent variant="jha" compact />
                  </div>
                ))}
              </div>
            </>
          )}
        </ReportSection>

        {data.photos?.length > 0 && (
          <ReportSection number="06" title={`Photos (${data.photos.length})`}>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {data.photos.map((p, i) => {
                const stamp = `${(company.company_name || "MASCI").toUpperCase()} · ${(data.id || "").slice(0, 8).toUpperCase()} · ${formatDateLong(data.jha_date)}`;
                return (
                  <div key={i} className="relative w-full aspect-square rounded-md overflow-hidden border-2 border-slate-200 bg-white">
                    <img src={p} alt={`Photo ${i + 1}`} className="absolute inset-0 w-full h-full object-cover" />
                    <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                      <span className="font-display font-black text-white/30 select-none" style={{ transform: "rotate(-30deg)", fontSize: "clamp(14px, 6vw, 28px)", letterSpacing: "0.2em", textShadow: "0 1px 2px rgba(0,0,0,0.4)", whiteSpace: "nowrap" }}>
                        {(company.company_name || "MASCI").toUpperCase()}
                      </span>
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 bg-black/65 text-white px-1.5 py-1 font-mono text-[8px] uppercase tracking-wider truncate">{stamp}</div>
                  </div>
                );
              })}
            </div>
          </ReportSection>
        )}

        <ReportSection number="07" title="Foreman Approval">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">Foreman / Crew Lead</div>
          <div className="text-base font-bold text-slate-900 mb-2">{data.crew_lead || "—"}</div>
          <BilingualConsent variant="jha" />
          <div className="border-2 border-slate-300 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center max-w-md mt-3">
            {data.foreman_signature ? (
              <img src={data.foreman_signature} alt="Foreman signature" className="max-h-[120px]" />
            ) : (
              <span className="text-slate-400 text-sm">No signature</span>
            )}
          </div>
        </ReportSection>

        <div className="text-center font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 pt-4 pb-8 print-section">
          Generated {data.created_at ? new Date(data.created_at).toLocaleString() : ""} · {company.company_name || "MASCI"} JHA
        </div>
        {(company.address || company.phone || company.email || company.license_number) && (
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
                {(company.phone || company.email) && <div>{company.phone}{company.phone && company.email ? " · " : ""}{company.email}</div>}
                {company.license_number && <div>License #{company.license_number}</div>}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
