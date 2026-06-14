// HrDailyReports — iter332 · HR Portal read-only Daily Reports Review.
//
// HR needs visibility into daily reports to verify labor, subcontractor
// attendance, vendor presence, and payroll context — WITHOUT PM scope,
// no edit, no delete, no submit, no email, no approval. This page
// surfaces the new `/api/hr/daily-reports` namespace (X-HR-Token gated)
// with the 6 required filters: date range · project · employee ·
// subcontractor · vendor · report number.
//
// The detail view at `/hr/daily-reports/:id` re-uses the read-only
// renderer below; no edit controls are rendered.
import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ClipboardList, Search, Loader2, ChevronRight, Filter, ArrowLeft,
  Calendar, MapPin, CloudSun, Users, Truck, Building2, FileText,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { PortalShell } from "@/design-system";
import HrSideNavV2 from "@/components/hr/sidebar/HrSideNavV2";
import { RefKicker } from "@/components/RefKicker";
import { getHrToken } from "@/lib/hrAuth";
import { useT } from "@/lib/i18n";
import { paletteFor } from "@/lib/portalPalette";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const HR_PAL = paletteFor("hr");
const auth = () => ({ headers: { "X-HR-Token": getHrToken() } });

export default function HrDailyReports() {
  const { t } = useT();
  const nav = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters — 6 per operator mandate.
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [project, setProject] = useState("");
  const [employee, setEmployee] = useState("");
  const [subcontractor, setSubcontractor] = useState("");
  const [vendor, setVendor] = useState("");
  const [reportNumber, setReportNumber] = useState("");

  const fetchList = async () => {
    setLoading(true);
    try {
      const params = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (project) params.project = project;
      if (employee) params.employee = employee;
      if (subcontractor) params.subcontractor = subcontractor;
      if (vendor) params.vendor = vendor;
      if (reportNumber) params.report_number = reportNumber;
      const r = await axios.get(`${API}/hr/daily-reports`, { ...auth(), params });
      setItems(Array.isArray(r.data?.items) ? r.data.items : []);
    } catch (e) {
      toast.error(operationalError(
        e,
        t("Daily Reports temporarily unavailable. Try again in a moment."),
        t("Your HR session expired. Please sign in again.")
      ));
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchList(); /* eslint-disable-next-line */ }, []);

  const onApply = (e) => { e?.preventDefault?.(); fetchList(); };
  const onClear = () => {
    setDateFrom(""); setDateTo(""); setProject(""); setEmployee("");
    setSubcontractor(""); setVendor(""); setReportNumber("");
    setTimeout(fetchList, 0);
  };

  const totals = useMemo(() => ({
    count: items.length,
    crews: items.reduce((s, r) => s + (r.crew_count || 0), 0),
    subs: items.reduce((s, r) => s + (r.sub_count || 0), 0),
    visitors: items.reduce((s, r) => s + (r.visitor_count || 0), 0),
  }), [items]);

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="HR Portal · Daily Reports"
      pageTitle={t("Daily Reports Review")}
      subtitle={t("Read-only visibility into daily reports — labor crews, subcontractors, vendors, weather, location, and photo counts. No edit, no delete, no email, no approval.")}
      sideNav={<HrSideNavV2 />}
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-6 py-6 space-y-5" data-testid="hr-daily-reports-page">
        {/* KPI strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
          <Kpi label={t("Reports")} value={totals.count} stripe="border-l-purple-700" testId="hr-dr-kpi-reports" />
          <Kpi label={t("Crews")} value={totals.crews} stripe="border-l-emerald-600" testId="hr-dr-kpi-crews" />
          <Kpi label={t("Subs")} value={totals.subs} stripe="border-l-amber-600" testId="hr-dr-kpi-subs" />
          <Kpi label={t("Visitors")} value={totals.visitors} stripe="border-l-cyan-600" testId="hr-dr-kpi-visitors" />
        </div>

        {/* Filters · 6 required */}
        <form onSubmit={onApply} className="bg-white border border-slate-200 rounded-md p-4" data-testid="hr-dr-filters">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <FilterField label={t("Date from")} testId="hr-dr-date-from">
              <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="h-9" />
            </FilterField>
            <FilterField label={t("Date to")} testId="hr-dr-date-to">
              <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="h-9" />
            </FilterField>
            <FilterField label={t("Project")} testId="hr-dr-project">
              <Input value={project} onChange={(e) => setProject(e.target.value)} placeholder={t("Project name or number")} className="h-9" />
            </FilterField>
            <FilterField label={t("Report number")} testId="hr-dr-report-number">
              <Input value={reportNumber} onChange={(e) => setReportNumber(e.target.value)} placeholder="DR-…" className="h-9 font-mono" />
            </FilterField>
            <FilterField label={t("Employee")} testId="hr-dr-employee">
              <Input value={employee} onChange={(e) => setEmployee(e.target.value)} placeholder={t("Crew member name")} className="h-9" />
            </FilterField>
            <FilterField label={t("Subcontractor")} testId="hr-dr-subcontractor">
              <Input value={subcontractor} onChange={(e) => setSubcontractor(e.target.value)} placeholder={t("Sub company name")} className="h-9" />
            </FilterField>
            <FilterField label={t("Vendor / Visitor")} testId="hr-dr-vendor">
              <Input value={vendor} onChange={(e) => setVendor(e.target.value)} placeholder={t("Vendor name")} className="h-9" />
            </FilterField>
            <div className="flex items-end gap-2">
              <Button type="submit" className="h-9 bg-purple-700 hover:bg-purple-800 text-white font-bold uppercase tracking-wide text-xs" data-testid="hr-dr-apply">
                <Search className="w-3.5 h-3.5 mr-1" /> {t("Apply")}
              </Button>
              <Button type="button" variant="outline" onClick={onClear} className="h-9 text-xs uppercase tracking-wide" data-testid="hr-dr-clear">
                {t("Clear")}
              </Button>
            </div>
          </div>
        </form>

        {/* Table */}
        <div className="bg-white border border-slate-200 rounded-md overflow-x-auto" data-testid="hr-dr-list">
          {loading ? (
            <div className="text-center py-12 text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            </div>
          ) : items.length === 0 ? (
            <div className="p-10 text-center text-slate-500" data-testid="hr-dr-empty">
              <Filter className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="italic">{t("No daily reports match these filters. Try a wider date range or clear all filters to see everything on file.")}</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em] text-[10px]">
                <tr>
                  <th className="text-left px-3 py-2">{t("Date")}</th>
                  <th className="text-left px-3 py-2">{t("Report #")}</th>
                  <th className="text-left px-3 py-2">{t("Project")}</th>
                  <th className="text-left px-3 py-2">{t("Prepared by")}</th>
                  <th className="text-center px-3 py-2">{t("Crews")}</th>
                  <th className="text-center px-3 py-2">{t("Subs")}</th>
                  <th className="text-center px-3 py-2">{t("Visitors")}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((r, idx) => (
                  <tr key={r.id || idx} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`hr-dr-row-${idx}`}>
                    <td className="px-3 py-2 font-mono text-xs text-slate-600 whitespace-nowrap">{r.report_date || "—"}</td>
                    <td className="px-3 py-2 font-mono text-xs text-slate-700">{r.report_number || "—"}</td>
                    <td className="px-3 py-2 truncate max-w-[16rem]">
                      <div className="font-bold">{r.project_name || "—"}</div>
                      {r.project_number && <div className="text-xs text-slate-500 font-mono">{r.project_number}</div>}
                    </td>
                    <td className="px-3 py-2 text-slate-600 truncate max-w-[10rem]">{r.prepared_by || "—"}</td>
                    <td className="px-3 py-2 text-center font-mono font-bold">{r.crew_count || 0}</td>
                    <td className="px-3 py-2 text-center font-mono">{r.sub_count || 0}</td>
                    <td className="px-3 py-2 text-center font-mono">{r.visitor_count || 0}</td>
                    <td className="px-3 py-2 text-right">
                      <Link
                        to={`/hr/daily-reports/${r.id}`}
                        className="text-purple-700 hover:underline font-bold inline-flex items-center"
                        data-testid={`hr-dr-open-${idx}`}
                      >
                        {t("Open")} <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <p className="text-xs text-slate-500 font-mono">{items.length} {t("of")} {totals.count} {t("records shown")}</p>
      </div>
    </PortalShell>
  );
}

function Kpi({ label, value, stripe, testId }) {
  return (
    <div className={`bg-white border border-slate-200 border-l-4 ${stripe} rounded-md p-4`} data-testid={testId}>
      <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">{label}</div>
      <div className="font-display text-3xl font-black text-slate-900 mt-1">{value}</div>
    </div>
  );
}

function FilterField({ label, testId, children }) {
  return (
    <div data-testid={testId}>
      <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{label}</Label>
      <div className="mt-1">{children}</div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Detail view — read-only renderer mounted at /hr/daily-reports/:id.
// Renders narrative, crews, subs, vendors, weather, location, photos
// WITHOUT any edit/delete/email control.
export function HrDailyReportDetail() {
  const { t } = useT();
  const nav = useNavigate();
  const { id } = useParams();
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const r = await axios.get(`${API}/hr/daily-reports/${id}`, auth());
        setDoc(r.data);
      } catch (e) {
        toast.error(operationalError(
          e,
          t("That report is temporarily unavailable. Try again in a moment."),
          t("Your HR session expired. Please sign in again.")
        ));
      } finally {
        setLoading(false);
      }
    })();
  }, [id, t]);

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="HR Portal · Daily Report"
      pageTitle={t("Daily Report")}
      subtitle={t("Read-only HR view. To edit or send this report, the PM must use the PM Portal.")}
      sideNav={<HrSideNavV2 />}
      showBack
      backHref="/hr/daily-reports"
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-6 py-6 space-y-5" data-testid="hr-dr-detail-page">
        {loading ? (
          <div className="text-center py-12 text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
          </div>
        ) : !doc ? (
          <div className="bg-white border border-slate-200 rounded-md p-6 text-slate-500 italic">
            {t("Report not found.")}
          </div>
        ) : (
          <>
            <header className="bg-white border border-slate-200 border-l-4 border-l-purple-700 rounded-md p-5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`font-mono text-xs uppercase tracking-[0.22em] ${HR_PAL.hubKicker} font-bold`}>
                  {t("Daily Report")} · {t("Read-only")}
                </span>
                {doc.report_number && (
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700">
                    {doc.report_number}
                  </span>
                )}
              </div>
              {/* iter336 · review-side reference continuity */}
              <RefKicker
                recordId={doc.report_number || doc.id}
                testId="hr-dr-detail-ref"
                className="mt-1"
              />
              <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight mt-0.5">
                {doc.project_name || "—"}
              </h1>
              <div className="text-sm text-slate-600 mt-1 flex items-center gap-3 flex-wrap">
                <span className="inline-flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {doc.report_date || "—"}</span>
                {doc.project_number && <span className="font-mono text-xs">#{doc.project_number}</span>}
                {doc.location && <span className="inline-flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {doc.location}</span>}
                {doc.prepared_by && <span>· {t("Prepared by")} {doc.prepared_by}</span>}
              </div>
            </header>

            {doc.weather_summary && (
              <Section icon={CloudSun} title={t("Weather")}>
                <p className="text-sm text-slate-700">{doc.weather_summary}</p>
              </Section>
            )}

            {Array.isArray(doc.masci_crews) && doc.masci_crews.length > 0 && (
              <Section icon={Users} title={t("MASCI Crews")} count={doc.masci_crews.length}>
                <ul className="space-y-3">
                  {doc.masci_crews.map((crew, idx) => (
                    <li key={idx} className="border border-slate-200 rounded-md p-3 bg-slate-50">
                      <div className="font-bold text-sm">{crew.foreman || crew.lead || t("Crew")} {idx + 1}</div>
                      {Array.isArray(crew.members) && crew.members.length > 0 && (
                        <ul className="mt-1 grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4 text-sm">
                          {crew.members.map((m, mi) => (
                            <li key={mi} className="text-slate-700">
                              {m.name || "—"}{m.hours ? ` · ${m.hours}h` : ""}
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {Array.isArray(doc.subcontractors) && doc.subcontractors.length > 0 && (
              <Section icon={Building2} title={t("Subcontractors")} count={doc.subcontractors.length}>
                <ul className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4 text-sm">
                  {doc.subcontractors.map((s, idx) => (
                    <li key={idx} className="border border-slate-200 rounded-md p-2 bg-white">
                      <div className="font-bold">{s.name || "—"}</div>
                      {s.crew_size && <div className="text-xs text-slate-600">{t("Crew size")}: {s.crew_size}</div>}
                      {s.work_performed && <div className="text-xs text-slate-600">{s.work_performed}</div>}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {Array.isArray(doc.visitors) && doc.visitors.length > 0 && (
              <Section icon={Truck} title={t("Visitors / Vendors")} count={doc.visitors.length}>
                <ul className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4 text-sm">
                  {doc.visitors.map((v, idx) => (
                    <li key={idx} className="border border-slate-200 rounded-md p-2 bg-white">
                      <div className="font-bold">{v.name || "—"}</div>
                      {v.company && <div className="text-xs text-slate-600">{v.company}</div>}
                      {v.purpose && <div className="text-xs text-slate-600 italic">{v.purpose}</div>}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {doc.narrative && (
              <Section icon={FileText} title={t("Narrative")}>
                <p className="whitespace-pre-wrap text-sm text-slate-700">{doc.narrative}</p>
              </Section>
            )}

            {Array.isArray(doc.photos) && doc.photos.length > 0 && (
              <Section title={t("Photos")} count={doc.photos.length}>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
                  {doc.photos.map((p, idx) => (
                    <a key={idx} href={p.url || p} target="_blank" rel="noreferrer">
                      <img src={p.url || p} alt={`photo-${idx}`} loading="lazy" decoding="async" className="w-full h-32 object-cover rounded border border-slate-200" />
                    </a>
                  ))}
                </div>
              </Section>
            )}

            <p className="text-xs text-slate-500 italic" data-testid="hr-dr-readonly-notice">
              {t("This is a read-only HR view. To edit or send this report, the PM must use the PM Portal.")}
            </p>
          </>
        )}
      </div>
    </PortalShell>
  );
}

function Section({ icon: Icon, title, count, children }) {
  return (
    <section className="bg-white border border-slate-200 rounded-md p-4" data-testid={`hr-dr-section-${title}`}>
      <div className="flex items-center gap-2 mb-2">
        {Icon && <Icon className="w-4 h-4 text-purple-700" />}
        <h2 className="font-mono text-xs uppercase tracking-[0.22em] text-slate-700 font-bold">{title}</h2>
        {typeof count === "number" && (
          <span className="font-mono text-[10px] text-slate-500">({count})</span>
        )}
      </div>
      {children}
    </section>
  );
}
