// Field Leadership Records dashboard.
// Used by Admin (full visibility) and PMs (scoped to assigned jobs by the
// backend). Crew leadership w/ leadership token only sees non-supervisor-notes
// records (server enforces).
//
// Filters: form kind, employee, job, supervisor, date range, free-text search.
// Actions: open record view, download PDF, export CSV, soft-delete (admin only).

import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Search, FileDown, FileText, Trash2, ListChecks,
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
import { getLeadershipToken } from "@/lib/leadershipAuth";
import { FIELD_LEADERSHIP_FORMS } from "@/lib/fieldLeadershipSchemas";

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600";

export default function FieldLeadershipRecords() {
  const { t, lang } = useT();
  const navigate = useNavigate();
  const admin = isAdmin();

  useEffect(() => {
    if (!getLeadershipToken() && !admin) {
      navigate("/leadership", { replace: true });
    }
  }, [admin, navigate]);

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

  const fetchRecords = async () => {
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
      const r = await api.get("/field-leadership", { params });
      setItems(r.data?.items || []);
      setCounts(r.data?.counts_by_kind || {});
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not load records"));
    } finally {
      setLoading(false);
    }
  };

  // Initial load + refetch on filter change
  useEffect(() => { fetchRecords(); /* eslint-disable-next-line */ }, [filterKind]);
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
      const r = await api.get(`/field-leadership/${id}/pdf`, { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
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

  return (
    <main className="min-h-screen bg-slate-50 pb-16">
      <header className="bg-slate-900 text-white px-5 sm:px-8 py-5 flex items-center justify-between">
        <Link to="/leadership" className="text-xs font-mono uppercase tracking-[0.2em] text-slate-300 hover:text-white">
          <ArrowLeft className="inline w-3 h-3 mr-1" /> {t("Field Leadership")}
        </Link>
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-400">
          <ListChecks className="inline w-3 h-3 mr-1" /> {t("Records")}
        </span>
      </header>

      <section className="max-w-6xl mx-auto px-5 sm:px-8 pt-6">
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-red-700">{t("Field Leadership")}</div>
        <h1 className="font-display text-2xl sm:text-3xl font-black mt-1">{t("Records & Submissions")}</h1>
        <p className="text-slate-600 mt-1 text-sm">
          {admin ? t("All Field Leadership submissions across every job.") : t("Submissions for jobs assigned to you.")}
        </p>

        {/* COUNTS */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mt-5">
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
        <Card className="mt-6 p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-3">
          <Input placeholder={t("Employee")} value={employee} onChange={(e) => setEmployee(e.target.value)} className={inputCls} data-testid="filter-employee" />
          <Input placeholder={t("Job # or Name")} value={job} onChange={(e) => setJob(e.target.value)} className={inputCls} data-testid="filter-job" />
          <Input placeholder={t("Supervisor")} value={supervisor} onChange={(e) => setSupervisor(e.target.value)} className={inputCls} data-testid="filter-supervisor" />
          <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className={inputCls} data-testid="filter-date-from" />
          <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className={inputCls} data-testid="filter-date-to" />
          <Input placeholder={t("Search…")} value={q} onChange={(e) => setQ(e.target.value)} className={inputCls} data-testid="filter-q" />
          <div className="md:col-span-6 flex gap-2">
            <Button onClick={fetchRecords} className="bg-red-700 hover:bg-red-800 text-white" data-testid="leadership-search-btn">
              <Search className="w-4 h-4 mr-1" />{t("Search")}
            </Button>
            <Button variant="outline" onClick={() => { setEmployee(""); setJob(""); setSupervisor(""); setDateFrom(""); setDateTo(""); setQ(""); fetchRecords(); }}>
              {t("Clear")}
            </Button>
            <div className="flex-1" />
            <Button variant="outline" onClick={exportCsv} data-testid="leadership-export-csv">
              <FileDown className="w-4 h-4 mr-1" />{t("Export CSV")}
            </Button>
          </div>
        </Card>

        {/* LIST */}
        <Card className="mt-4 overflow-hidden">
          <table className="w-full text-sm">
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
              ) : items.map((r) => (
                <tr key={r.id} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`leadership-row-${r.id}`}>
                  <td className="px-3 py-2 font-mono text-xs">{(r.occurred_at || "").replace("T", " ").slice(0, 16)}</td>
                  <td className="px-3 py-2">{kindLabel(r.kind)}</td>
                  <td className="px-3 py-2 font-semibold">{r.employee_name || "—"}</td>
                  <td className="px-3 py-2 text-slate-700">{r.project_number ? `${r.project_number} · ${r.project_name || ""}` : (r.project_name || "—")}</td>
                  <td className="px-3 py-2 text-slate-700">{r.supervisor_name || "—"}</td>
                  <td className="px-3 py-2 text-right">
                    <Button asChild variant="outline" size="sm" className="mr-1" data-testid={`leadership-open-${r.id}`}>
                      <Link to={`/leadership/records/${r.id}`}><FileText className="w-3.5 h-3.5" /></Link>
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
              ))}
            </tbody>
          </table>
        </Card>
      </section>
    </main>
  );
}
