// Field Leadership Records dashboard.
// Used by Admin (full visibility) and PMs (scoped to assigned jobs by the
// backend). Crew leadership w/ leadership token only sees non-supervisor-notes
// records (server enforces).
//
// Filters: form kind, employee, job, supervisor, date range, free-text search.
// Actions: open record view, download PDF, export CSV, soft-delete (admin only).

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Search, FileDown, FileText, Trash2, ListChecks,
} from "lucide-react";
import { api, API } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { FIELD_LEADERSHIP_FORMS } from "@/lib/fieldLeadershipSchemas";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { HelpTipBlock } from "@/components/HelpTip";
import { PortalShell } from "@/design-system";
import { buildWave3AdminHeaders } from "@/lib/wave3AdminHeaders";
import { sanitizeOperatorProjectName, sanitizeOperatorProjectNumber, sanitizeOperatorReference } from "@/lib/operatorLanguage";

const API_BASE = process.env.REACT_APP_BACKEND_URL.replace(/\/$/, "");
const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600";

export default function FieldLeadershipRecords() {
  const { t, lang } = useT();
  const admin = isAdmin();
  const pm = isPm();
  const adminRoute = typeof window !== "undefined" && window.location.pathname.startsWith("/admin/");
  const portalSwitcherCurrent = admin ? "admin" : pm ? "pm" : undefined;

  // iter96+97 — Back-button destination + label routed by role.
  // BackLink auto-computes them, but this page predates the helper
  // and the labels here are translated via i18n, so we still compute
  // locally and pass `to` + `label` explicitly.
  const backTo = admin ? "/admin" : pm ? "/pm" : "/leadership";
  const backLabel = admin
    ? t("Administration")
    : pm
    ? t("PM Workspace")
    : t("Field Leadership");

  // Auth is enforced by the backend (admin / PM / leadership token all
  // accepted). If the call returns 401, the API interceptor clears the
  // matching token and the route guards on the calling page handle the
  // redirect — we don't pre-empt with a client-side redirect because we
  // can't always tell synchronously which token type the user has yet
  // (the PM session may have just been hydrated from localStorage).

  const [items, setItems] = useState([]);
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [filterKind, setFilterKind] = useState("");
  const [employee, setEmployee] = useState("");
  const [job, setJob] = useState("");
  const [supervisor, setSupervisor] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [q, setQ] = useState("");

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterKind) params.kind = filterKind;
      if (employee) params.employee = employee;
      if (job) params.job = job;
      if (supervisor) params.supervisor = supervisor;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (q) params.q = q;
      if (adminRoute) {
        const query = new URLSearchParams(params).toString();
        const response = await fetch(`${API_BASE}/api/field-leadership${query ? `?${query}` : ""}`, {
          headers: buildWave3AdminHeaders(),
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(body?.detail || t("Could not load records"));
        setItems(body?.items || []);
        setCounts(body?.counts_by_kind || {});
      } else {
        const r = await api.get("/field-leadership", { params });
        setItems(r.data?.items || []);
        setCounts(r.data?.counts_by_kind || {});
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || err?.message || t("Could not load records"));
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo, employee, filterKind, job, q, supervisor, t]);

  // Initial load + refetch on filter change
  useEffect(() => { fetchRecords(); }, [fetchRecords]);
  // Manual refetch after typing — debounced via the search button instead

  const totalCount = useMemo(
    () => Object.values(counts).reduce((a, b) => a + b, 0),
    [counts]
  );

  const kindLabel = (k) => {
    const f = FIELD_LEADERSHIP_FORMS.find((x) => x.kind === k);
    if (!f) return k;
    return f.title[lang] || f.title.en;
  };

  const downloadPdf = async (id) => {
    try {
      const response = adminRoute
        ? await fetch(`${API_BASE}/api/field-leadership/${id}/pdf`, { headers: buildWave3AdminHeaders() })
        : await api.get(`/field-leadership/${id}/pdf`, { responseType: "blob" });
      const blob = adminRoute
        ? await response.blob()
        : new Blob([response.data], { type: "application/pdf" });
      if (adminRoute && !response.ok) throw new Error(t("Could not open PDF"));
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      setTimeout(() => URL.revokeObjectURL(url), 30000);
    } catch (err) {
      toast.error(t("Could not open PDF"));
    }
  };

  const deleteRec = async (id) => {
    if (!window.confirm(t("Permanently archive this record?"))) return;
    try {
      await api.delete(`/field-leadership/${id}`);
      toast.success(t("Archived"));
      fetchRecords();
    } catch {
      toast.error(t("Could not archive"));
    }
  };

  const exportCsv = () => {
    const url = new URL(`${API}/field-leadership/export/csv`);
    if (filterKind) url.searchParams.set("kind", filterKind);
    if (employee) url.searchParams.set("employee", employee);
    // Build a hidden form to send the X-Admin/Leadership token via fetch + blob,
    // because <a href> doesn't include custom headers.
    api.get(url.pathname.replace("/api", "") + url.search, { responseType: "blob" })
      .then((r) => {
        const blobUrl = URL.createObjectURL(new Blob([r.data], { type: "text/csv" }));
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = "field_leadership_records.csv";
        a.click();
        setTimeout(() => URL.revokeObjectURL(blobUrl), 30000);
      })
      .catch(() => toast.error(t("Could not export CSV")));
  };

  const detailHref = (id) => {
    if (adminRoute) return `/admin/leadership/records/${id}`;
    return `/leadership/records/${id}`;
  };

  return (
    <PortalShell
      portalName="MASCI"
      portalRole={admin ? "Admin · Field Leadership" : pm ? "PM · Field Leadership" : "Field Leadership"}
      pageTitle={t("Records & Submissions")}
      subtitle={admin ? t("All Field Leadership submissions across every job.") : t("Submission history and evidence for the jobs assigned to you.")}
      showBack
      backHref={backTo}
      showNotifications={false}
      portalSwitcherCurrent={portalSwitcherCurrent}
      primaryActions={
        <div className="hidden md:flex" data-testid="leadership-records-company-info">
          <CompanyInfoDialog />
        </div>
      }
    >
      <div data-testid="leadership-records-root" className="pb-16 min-w-0">
        <section>
        {/* iter218 · reviewer-side coaching — supers reviewing crew
            filings get coaching on what to look for, how to push back,
            and when to escalate. NOT auditing tone; reading tone. */}
        <div className="mb-5">
          <HelpTipBlock formKey="field-leadership.records" showCounter />
        </div>

        {/* COUNTS */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mt-5" data-testid="leadership-records-count-grid">
          <button
            onClick={() => setFilterKind("")}
            className={`p-3 rounded-md border-2 text-left ${!filterKind ? "border-red-700 bg-red-50" : "border-slate-200 bg-white hover:border-red-400"}`}
            data-testid="leadership-count-all"
          >
            <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-slate-500">{t("Total")}</div>
            <div className="font-display text-2xl font-black">{totalCount}</div>
          </button>
          {FIELD_LEADERSHIP_FORMS.map((f) => (
            <button
              key={f.kind}
              onClick={() => setFilterKind(f.kind)}
              className={`p-3 rounded-md border-2 text-left ${filterKind === f.kind ? "border-red-700 bg-red-50" : "border-slate-200 bg-white hover:border-red-400"}`}
              data-testid={`leadership-count-${f.kind}`}
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-slate-500">
                {f.title[lang] || f.title.en}
              </div>
              <div className="font-display text-xl font-black">{counts[f.kind] || 0}</div>
            </button>
          ))}
        </div>

        {/* FILTERS */}
        <Card className="mt-6 p-4 grid min-w-0 grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-3 wp17-panel" data-testid="leadership-records-filters">
          <Input placeholder={t("Employee")} value={employee} onChange={(e) => setEmployee(e.target.value)} className={inputCls} data-testid="records-filter-employee" />
          <Input placeholder={t("Job # or Name")} value={job} onChange={(e) => setJob(e.target.value)} className={inputCls} data-testid="records-filter-job" />
          <Input placeholder={t("Supervisor")} value={supervisor} onChange={(e) => setSupervisor(e.target.value)} className={inputCls} data-testid="records-filter-supervisor" />
          <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className={inputCls} data-testid="records-filter-date-from" />
          <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className={inputCls} data-testid="records-filter-date-to" />
          <Input placeholder={t("Search…")} value={q} onChange={(e) => setQ(e.target.value)} className={inputCls} data-testid="records-filter-q" />
          <div className="md:col-span-6 flex flex-wrap gap-2">
            <Button onClick={fetchRecords} className="w-full sm:w-auto bg-red-700 hover:bg-red-800 text-white" data-testid="records-search-btn">
              <Search className="w-4 h-4 mr-1" />{t("Search")}
            </Button>
            <Button variant="outline" className="w-full sm:w-auto" onClick={() => { setEmployee(""); setJob(""); setSupervisor(""); setDateFrom(""); setDateTo(""); setQ(""); fetchRecords(); }} data-testid="records-clear-btn">
              {t("Clear")}
            </Button>
            <div className="hidden sm:block sm:flex-1" />
            <Button variant="outline" className="w-full sm:w-auto" onClick={exportCsv} data-testid="records-export-csv">
              <FileDown className="w-4 h-4 mr-1" />{t("Export CSV")}
            </Button>
          </div>
        </Card>

        {/* LIST */}
        <Card className="mt-4 overflow-hidden min-w-0 wp17-data-table" data-testid="leadership-records-table-shell">
          <div className="w-full overflow-x-auto" data-testid="leadership-records-table-scroll">
          <table className="w-full min-w-[42rem] text-sm">
            <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">{t("Date")}</th>
                <th className="text-left px-3 py-2">{t("Form")}</th>
                <th className="text-left px-3 py-2">{t("Employee")}</th>
                <th className="text-left px-3 py-2">{t("Job")}</th>
                <th className="text-left px-3 py-2">{t("Supervisor")}</th>
                <th className="text-right px-3 py-2">{t("Actions")}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="px-3 py-6 text-center text-slate-500">{t("Loading…")}</td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={6} className="px-3 py-6 text-center text-slate-500" data-testid="leadership-empty">{t("No records yet for the current filters.")}</td></tr>
              ) : items.map((r) => {
                const safeEmployee = sanitizeOperatorReference(r.employee_name, t("Crew member"));
                const safeJobNumber = sanitizeOperatorProjectNumber(r.project_number, t("Assigned job"));
                const safeJobName = sanitizeOperatorProjectName(r.project_name, t("Assigned job details"));
                const safeSupervisor = sanitizeOperatorReference(r.supervisor_name, t("Supervisor"));
                return (
                <tr key={r.id} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`leadership-row-${r.id}`}>
                  <td className="px-3 py-2 font-mono text-xs">{(r.occurred_at || "").replace("T", " ").slice(0, 16)}</td>
                  <td className="px-3 py-2">{kindLabel(r.kind)}</td>
                  <td className="px-3 py-2 font-semibold">{safeEmployee || "—"}</td>
                  <td className="px-3 py-2 text-slate-700">{safeJobNumber ? `${safeJobNumber} · ${safeJobName || ""}` : (safeJobName || "—")}</td>
                  <td className="px-3 py-2 text-slate-700">{safeSupervisor || "—"}</td>
                  <td className="px-3 py-2 text-right">
                    <Button asChild variant="outline" size="sm" className="mr-1" data-testid={`leadership-open-${r.id}`}>
                      <Link to={detailHref(r.id)}><FileText className="w-3.5 h-3.5" /></Link>
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => downloadPdf(r.id)} className="mr-1" data-testid={`leadership-pdf-${r.id}`}>
                      <FileDown className="w-3.5 h-3.5" />
                    </Button>
                    {admin && (
                      <Button variant="outline" size="sm" onClick={() => deleteRec(r.id)} className="border-red-300 text-red-700 hover:bg-red-50" data-testid={`leadership-archive-${r.id}`}>
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    )}
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
          </div>
        </Card>
      </section>
      </div>
    </PortalShell>
  );
}
