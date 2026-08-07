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
import React, { useCallback, useEffect, useMemo, useState } from "react";
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
import { resolvePhotoSrc } from "@/lib/photoSrc";
import { useT } from "@/lib/i18n";
import { paletteFor } from "@/lib/portalPalette";
import { operationalError } from "@/lib/errors";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { toast } from "sonner";
import axios from "axios";
import { sanitizeOperatorProjectName, sanitizeOperatorProjectNumber, sanitizeOperatorReference } from "@/lib/operatorLanguage";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const HR_PAL = paletteFor("hr");
const auth = () => ({ headers: buildScopedPortalAuthHeaders(["hr"]) });

export default function HrDailyReports() {
  const { t } = useT();
  const nav = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters — Track 15.9A · 10 operational filters per HR mandate.
  // Stored as a single object so resetting all filters at once is a
  // single setState call (lint-clean and idiomatic).
  const EMPTY_FILTERS = {
    dateFrom: "", dateTo: "", project: "", pm: "",
    superintendent: "", foreman: "", employee: "",
    subcontractor: "", vendor: "", reportNumber: "",
  };
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const setF = (k) => (e) =>
    setFilters((prev) => ({ ...prev, [k]: e.target.value }));

  const fetchList = useCallback(async (overrides, retryCount = 0) => {
    setLoading(true);
    try {
      const s = { ...filters, ...(overrides || {}) };
      const params = {};
      if (s.dateFrom) params.date_from = s.dateFrom;
      if (s.dateTo) params.date_to = s.dateTo;
      if (s.project) params.project = s.project;
      if (s.pm) params.pm = s.pm;
      if (s.superintendent) params.superintendent = s.superintendent;
      if (s.foreman) params.foreman = s.foreman;
      if (s.employee) params.employee = s.employee;
      if (s.subcontractor) params.subcontractor = s.subcontractor;
      if (s.vendor) params.vendor = s.vendor;
      if (s.reportNumber) params.report_number = s.reportNumber;
      const r = await axios.get(`${API}/hr/daily-reports`, { ...auth(), params });
      setItems(Array.isArray(r.data?.items) ? r.data.items : []);
    } catch (e) {
      const status = e?.response?.status;
      // TRACK 15.13H — Preserve previously-loaded list on transient
      // failures (5xx, 502/503/504/520, network blips) so the user
      // doesn't see "0 reports" flash whenever the origin briefly
      // hiccups. Only reset the list on a real auth boundary (401)
      // or a real "no results" 2xx. 403/404/422 also keep the list:
      // those are per-call client errors, not platform outages.
      const isTransient = !e?.response || (typeof status === "number" && status >= 500);
      const isAuth = status === 401;
      if (isAuth) {
        setItems([]);
        toast.error(t("Your HR session expired. Please sign in again."));
        return;
      }
      // TRACK 15.13I — Auto-retry on transient/network/5xx failures so
      // the page self-recovers from a pod restart (the common
      // production cause). Up to 2 silent retries spaced 4s + 8s
      // apart. Only after the third attempt fails do we surface the
      // "temporarily unavailable" toast — and we still preserve the
      // previously-loaded items so the user keeps whatever they had.
      if (isTransient && retryCount < 2) {
        const delayMs = 4000 * (retryCount + 1);  // 4s, then 8s
        setTimeout(() => {
          fetchList(overrides, retryCount + 1);
        }, delayMs);
        // Don't toast yet — give the retry a chance first.
        return;
      }
      // 403/404/422 → operator-detail message (not session expired).
      // After exhausted retries on 5xx → calm fallback.
      toast.error(operationalError(
        e,
        t("Daily Reports temporarily unavailable. Try again in a moment."),
        t("Your HR session expired. Please sign in again.")
      ));
    } finally {
      setLoading(false);
    }
  }, [filters, t]);

  useEffect(() => { fetchList(); }, [fetchList]);  

  const onApply = (e) => { e?.preventDefault?.(); fetchList(); };
  const onClear = () => {
    setFilters(EMPTY_FILTERS);
    fetchList(EMPTY_FILTERS);
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
      pageTitle={t("Daily Reports")}
      subtitle={t("Read-only access to field daily reports.")}
      sideNav={<HrSideNavV2 />}
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-6 py-6 space-y-5" data-testid="hr-daily-reports-page">
        {/* TRACK 15.13K — KPI strip removed per user directive.
            HR needs ONE thing: read-only access to Daily Reports.
            No counts, no totals, no dashboard metrics. The list itself
            is the source of truth. */}

        {/* Filters · 6 required */}
        <form onSubmit={onApply} className="bg-white border border-slate-200 rounded-md p-4" data-testid="hr-dr-filters">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <FilterField label={t("Date from")} testId="hr-dr-date-from">
              <Input type="date" value={filters.dateFrom} onChange={setF("dateFrom")} className="h-9" />
            </FilterField>
            <FilterField label={t("Date to")} testId="hr-dr-date-to">
              <Input type="date" value={filters.dateTo} onChange={setF("dateTo")} className="h-9" />
            </FilterField>
            <FilterField label={t("Project")} testId="hr-dr-project">
              <Input value={filters.project} onChange={setF("project")} placeholder={t("Project name or number")} className="h-9" />
            </FilterField>
            <FilterField label={t("PM")} testId="hr-dr-pm">
              <Input value={filters.pm} onChange={setF("pm")} placeholder={t("Project manager name or email")} className="h-9" />
            </FilterField>
            <FilterField label={t("Superintendent")} testId="hr-dr-superintendent">
              <Input value={filters.superintendent} onChange={setF("superintendent")} placeholder={t("Superintendent name")} className="h-9" />
            </FilterField>
            <FilterField label={t("Foreman")} testId="hr-dr-foreman">
              <Input value={filters.foreman} onChange={setF("foreman")} placeholder={t("Foreman name")} className="h-9" />
            </FilterField>
            <FilterField label={t("Report number")} testId="hr-dr-report-number">
              <Input value={filters.reportNumber} onChange={setF("reportNumber")} placeholder="DR-…" className="h-9 font-mono" />
            </FilterField>
            <FilterField label={t("Employee")} testId="hr-dr-employee">
              <Input value={filters.employee} onChange={setF("employee")} placeholder={t("Crew member name")} className="h-9" />
            </FilterField>
            <FilterField label={t("Subcontractor")} testId="hr-dr-subcontractor">
              <Input value={filters.subcontractor} onChange={setF("subcontractor")} placeholder={t("Sub company name")} className="h-9" />
            </FilterField>
            <FilterField label={t("Vendor / Visitor")} testId="hr-dr-vendor">
              <Input value={filters.vendor} onChange={setF("vendor")} placeholder={t("Vendor name")} className="h-9" />
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
                  <th className="text-left px-3 py-2">{t("PM")}</th>
                  <th className="text-left px-3 py-2">{t("Superintendent")}</th>
                  <th className="text-left px-3 py-2">{t("Prepared by")}</th>
                  <th className="text-center px-3 py-2">{t("Crews")}</th>
                  <th className="text-center px-3 py-2">{t("Subs")}</th>
                  <th className="text-center px-3 py-2">{t("Visitors")}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((r, idx) => (
                  (() => {
                    const safeProjectName = sanitizeOperatorProjectName(r.project_name, "Project details");
                    const safeProjectNumber = sanitizeOperatorProjectNumber(r.project_number, "Project support");
                    const safePmName = sanitizeOperatorReference(r.pm_name, "Project manager");
                    const safeSuperintendent = sanitizeOperatorReference(r.superintendent, "Superintendent");
                    const safePreparedBy = sanitizeOperatorReference(r.prepared_by, "Field record");
                    return (
                  <tr key={r.id || idx} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`hr-dr-row-${idx}`}>
                    <td className="px-3 py-2 font-mono text-xs text-slate-600 whitespace-nowrap">{r.report_date || "—"}</td>
                    <td className="px-3 py-2 font-mono text-xs text-slate-700">{r.report_number || "—"}</td>
                    <td className="px-3 py-2 truncate max-w-[16rem]">
                      <div className="font-bold">{safeProjectName || "—"}</div>
                      {r.project_number && <div className="text-xs text-slate-500 font-mono">{safeProjectNumber}</div>}
                    </td>
                    <td className="px-3 py-2 text-slate-700 truncate max-w-[11rem]" data-testid={`hr-dr-row-${idx}-pm`}>
                      {safePmName ? (
                        <>
                          <div className="font-bold text-xs">{safePmName}</div>
                          {r.pm_email && <div className="text-[10px] text-slate-500 font-mono truncate">{r.pm_email}</div>}
                        </>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-slate-700 truncate max-w-[10rem]" data-testid={`hr-dr-row-${idx}-superintendent`}>
                      {safeSuperintendent || <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-2 text-slate-600 truncate max-w-[10rem]">{safePreparedBy || "—"}</td>
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
                    );
                  })()
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
              {/* Track 15.9A · PM + Superintendent identity row so HR can
                  identify project ownership without inspecting raw fields. */}
              {(doc.pm_name || doc.pm_email || doc.superintendent) && (
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-xs" data-testid="hr-dr-detail-pm-strip">
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">{t("Project Manager")}</div>
                    <div className="mt-0.5 text-slate-800">
                      {doc.pm_name || <span className="text-slate-400">—</span>}
                      {doc.pm_email && (
                        <span className="text-slate-500 font-mono text-[11px] ml-2">{doc.pm_email}</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">{t("Superintendent")}</div>
                    <div className="mt-0.5 text-slate-800">
                      {doc.superintendent || <span className="text-slate-400">—</span>}
                    </div>
                  </div>
                </div>
              )}
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
                  {doc.photos.map((p, idx) => {
                    // TRACK 15.13B FAILURE #3 · resolvePhotoSrc bypass.
                    // The iter64 R2 migration stores photos as
                    // `photo://masci-hub/photos/...` references. The
                    // browser cannot resolve `photo://` directly — it
                    // errors out and renders the `alt` text instead,
                    // which is why production HR was showing literal
                    // strings "photo-0 / photo-1 / photo-2 / photo-3"
                    // for every report attachment. Pipe every photo
                    // ref through the canonical `resolvePhotoSrc`
                    // resolver (the same helper PM / Inspection /
                    // Meeting / Equipment / Incident views all use)
                    // so the browser fetches bytes via the
                    // /api/photo-bytes resolver instead.
                    const ref = typeof p === "string" ? p : (p?.url || p?.ref || "");
                    const src = resolvePhotoSrc(ref);
                    return (
                      <a key={idx} href={src} target="_blank" rel="noreferrer" data-testid={`hr-dr-photo-${idx}`}>
                        <img
                          src={src}
                          alt={`Photo ${idx + 1}`}
                          loading="lazy"
                          decoding="async"
                          className="w-full h-32 object-cover rounded border border-slate-200"
                        />
                      </a>
                    );
                  })}
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
