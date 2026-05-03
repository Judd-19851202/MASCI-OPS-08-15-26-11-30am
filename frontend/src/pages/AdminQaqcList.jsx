import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ClipboardCheck, Download, Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { api } from "@/lib/api";
import { getAdminToken } from "@/lib/adminAuth";

const KIND_LABEL = {
  concrete_form: "Concrete Form",
  rebar: "Rebar",
  subcontractor_work: "Subcontractor",
};

/**
 * AdminQaqcList — admin-only list view of every QA/QC inspection,
 * with filter-by-kind, free-text search, and CSV export.
 */
export default function AdminQaqcList() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [kindFilter, setKindFilter] = useState("");
  const [q, setQ] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    api.get("/qaqc-inspections").then((r) => setRows(r.data))
      .catch((e) => setErr(e?.response?.data?.detail || "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      if (kindFilter && r.inspection_kind !== kindFilter) return false;
      if (q) {
        const blob = `${r.project_name} ${r.project_number} ${r.location} ${r.inspector_name} ${r.subcontractor_name}`.toLowerCase();
        if (!blob.includes(q.toLowerCase())) return false;
      }
      return true;
    });
  }, [rows, kindFilter, q]);

  async function onExport() {
    setExporting(true);
    try {
      const res = await api.get("/admin/qaqc-inspections/export.csv", {
        responseType: "blob",
        headers: { "X-Admin-Token": getAdminToken() || "" },
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "masci-qaqc-inspections.csv";
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="min-h-screen blueprint-bg">
      <header className="bg-slate-900 border-b-4 border-emerald-600">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="lg" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8">
        <Link to="/admin" className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-emerald-700 font-bold mb-4">
          <ArrowLeft className="w-3.5 h-3.5" /> Admin
        </Link>

        <div className="flex items-start gap-3 mb-5">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-emerald-600 text-white shrink-0">
            <ClipboardCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-emerald-700 font-bold">Admin · QA/QC</span>
            <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900">
              All QA / QC Inspections
            </h1>
          </div>
        </div>

        <div className="bg-white border-2 border-slate-300 rounded-md p-4 mb-4 flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px]">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold block mb-1">Search</label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Project, inspector, sub…" className="pl-9 h-10 border-2 border-slate-300" data-testid="qaqc-search" />
            </div>
          </div>
          <div>
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold block mb-1">Kind</label>
            <select value={kindFilter} onChange={(e) => setKindFilter(e.target.value)}
              className="h-10 border-2 border-slate-300 rounded px-3 text-sm bg-white" data-testid="qaqc-kind-filter">
              <option value="">All kinds</option>
              <option value="concrete_form">Concrete Form</option>
              <option value="rebar">Rebar</option>
              <option value="subcontractor_work">Subcontractor</option>
            </select>
          </div>
          <Button onClick={onExport} variant="outline" disabled={exporting || !rows.length} data-testid="qaqc-export-csv">
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            <span className="ml-1">Export CSV</span>
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-10 text-slate-500"><Loader2 className="w-5 h-5 animate-spin inline-block mr-2" />Loading…</div>
        ) : err ? (
          <div className="bg-red-50 border-2 border-red-300 rounded p-4 text-red-900">{err}</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-10 text-slate-500 italic">No QA/QC inspections yet.</div>
        ) : (
          <div className="bg-white border-2 border-slate-300 rounded-md overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b-2 border-slate-200">
                <tr className="text-left">
                  <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Date</th>
                  <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Kind</th>
                  <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Project</th>
                  <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Location</th>
                  <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Inspector</th>
                  <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 text-right">Pass / Fail / N/A</th>
                  <th className="px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 text-right">Photos</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.id} className="border-b border-slate-100 hover:bg-emerald-50/40" data-testid={`qaqc-row-${r.id}`}>
                    <td className="px-3 py-2 text-slate-900">
                      <Link to={`/qaqc/${r.id}`} className="hover:text-emerald-700 font-medium">
                        {r.inspection_date}
                      </Link>
                    </td>
                    <td className="px-3 py-2 text-slate-600">{KIND_LABEL[r.inspection_kind] || r.inspection_kind}</td>
                    <td className="px-3 py-2 text-slate-900 font-medium">
                      {r.project_name}
                      {r.project_number && <span className="text-slate-400 text-xs ml-1">· {r.project_number}</span>}
                    </td>
                    <td className="px-3 py-2 text-slate-600">{r.location}</td>
                    <td className="px-3 py-2 text-slate-600">{r.inspector_name}</td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      <span className="text-emerald-700">{r.pass_count}</span> / <span className="text-red-700 font-bold">{r.fail_count}</span> / <span className="text-slate-500">{r.na_count}</span>
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-slate-600">{r.photo_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
