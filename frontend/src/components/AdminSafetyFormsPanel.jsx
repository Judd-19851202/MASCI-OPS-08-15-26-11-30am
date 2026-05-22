import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ShieldCheck,
  Loader2,
  Search,
  Filter,
  ExternalLink,
  Download,
  HardHat,
  GraduationCap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import JobFolderList from "@/components/JobFolderList";
import { api, API } from "@/lib/api";
import { getAdminToken } from "@/lib/adminAuth";
import { fmtMoney } from "@/lib/safetyFormsSchema";
import { formatDateLong } from "@/lib/utils";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";

/**
 * AdminSafetyFormsPanel — admin dashboard tile for the new Safety Forms
 * section. Tabs between "Equipment Issuance" and "Use & Care Training",
 * filters by employee/project/date range, supports global search across
 * employee, project, supervisor/instructor, and lets the admin open the
 * record's view page or download the PDF directly.
 */
export default function AdminSafetyFormsPanel() {
  const [tab, setTab] = useState("issuance"); // "issuance" | "training"
  const [filters, setFilters] = useState({
    q: "",
    employee: "",
    project: "",
    date_from: "",
    date_to: "",
  });
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const apiBase =
    tab === "issuance"
      ? "/safety-forms/equipment-issuances"
      : "/safety-forms/equipment-trainings";

  const load = async () => {
    setLoading(true);
    try {
      const params = {};
      for (const [k, v] of Object.entries(filters)) {
        if (v) params[k] = v;
      }
      const r = await api.get(apiBase, { params });
      setItems(r.data?.items || []);
    } catch (e) {
      toast.error(operationalError(e, "Could not load"));
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const reset = () =>
    setFilters({ q: "", employee: "", project: "", date_from: "", date_to: "" });

  const downloadPdf = async (id, label) => {
    try {
      const headers = { "X-Admin-Token": getAdminToken() };
      const res = await fetch(`${API}${apiBase}/${id}/pdf`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `MASCI_${label}_${id.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error(e?.message || "Download failed");
    }
  };

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-5 sm:p-7 mb-8 shadow-sm"
      data-testid="admin-safety-forms-panel"
    >
      <div className="flex items-start gap-3 mb-4">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-red-700 text-white shrink-0">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
            Safety Department
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            Safety Forms
          </h2>
          <p className="text-sm text-slate-600 mt-2 max-w-3xl">
            Equipment Issuance &amp; Accountability and Use &amp; Care Training records.
            Auto-emailed to <span className="font-mono">safety@mascigc.com</span> on submit.
          </p>
        </div>
        <Link
          to="/safety/forms"
          className="inline-flex items-center gap-1 h-9 px-3 rounded-md bg-red-700 text-white border-2 border-red-900 hover:bg-red-800 text-xs font-bold uppercase tracking-wide"
          data-testid="admin-safety-forms-open"
        >
          <ExternalLink className="w-3.5 h-3.5" /> Open
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        <button
          type="button"
          onClick={() => setTab("issuance")}
          className={`inline-flex items-center gap-2 h-9 px-3 rounded-md font-mono text-xs uppercase tracking-wide font-bold border-2 ${
            tab === "issuance"
              ? "bg-red-700 text-white border-red-900"
              : "bg-white text-slate-700 border-slate-300 hover:border-red-700"
          }`}
          data-testid="admin-sf-tab-issuance"
        >
          <HardHat className="w-3.5 h-3.5" /> Issuance
        </button>
        <button
          type="button"
          onClick={() => setTab("training")}
          className={`inline-flex items-center gap-2 h-9 px-3 rounded-md font-mono text-xs uppercase tracking-wide font-bold border-2 ${
            tab === "training"
              ? "bg-amber-600 text-white border-amber-800"
              : "bg-white text-slate-700 border-slate-300 hover:border-amber-600"
          }`}
          data-testid="admin-sf-tab-training"
        >
          <GraduationCap className="w-3.5 h-3.5" /> Training
        </button>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 mb-3">
        <FilterField label="Search" icon={Search}>
          <Input
            value={filters.q}
            onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
            onKeyDown={(e) => e.key === "Enter" && load()}
            placeholder="Employee, project, supervisor…"
            className="h-9"
            data-testid="admin-sf-q"
          />
        </FilterField>
        <FilterField label="Employee">
          <Input
            value={filters.employee}
            onChange={(e) => setFilters((f) => ({ ...f, employee: e.target.value }))}
            onKeyDown={(e) => e.key === "Enter" && load()}
            className="h-9"
            data-testid="admin-sf-employee"
          />
        </FilterField>
        <FilterField label="Project">
          <Input
            value={filters.project}
            onChange={(e) => setFilters((f) => ({ ...f, project: e.target.value }))}
            onKeyDown={(e) => e.key === "Enter" && load()}
            className="h-9"
            data-testid="admin-sf-project"
          />
        </FilterField>
        <FilterField label="From">
          <Input
            type="date"
            value={filters.date_from}
            onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))}
            className="h-9"
            data-testid="admin-sf-from"
          />
        </FilterField>
        <FilterField label="To">
          <Input
            type="date"
            value={filters.date_to}
            onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))}
            className="h-9"
            data-testid="admin-sf-to"
          />
        </FilterField>
      </div>
      <div className="flex items-center gap-2 mb-4">
        <Button
          onClick={load}
          disabled={loading}
          className="h-9 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold uppercase tracking-wide"
          data-testid="admin-sf-apply"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Filter className="w-3.5 h-3.5 mr-1" />}
          Apply
        </Button>
        <Button
          onClick={() => {
            reset();
            setTimeout(load, 0);
          }}
          variant="outline"
          className="h-9 border-2 border-slate-300 text-xs font-bold uppercase tracking-wide"
          data-testid="admin-sf-reset"
        >
          Reset
        </Button>
        <span className="text-xs text-slate-500 ml-2 font-mono">
          {items.length} {items.length === 1 ? "record" : "records"}
        </span>
      </div>

      {/* Records — grouped by job folder */}
      <div className="border border-slate-200 rounded-md overflow-hidden" data-testid="admin-sf-list">
        {loading && items.length === 0 ? (
          <div className="p-10 text-center text-slate-500">
            <Loader2 className="w-5 h-5 animate-spin inline-block mr-2" />
            Loading…
          </div>
        ) : (
          <JobFolderList
            items={items.map((row) => ({
              ...row,
              _sf_date: tab === "issuance" ? row.issued_date : row.training_date,
            }))}
            dateField="_sf_date"
            testIdPrefix={`admin-sf-folders-${tab}`}
            renderItem={(row) => {
              const date = tab === "issuance" ? row.issued_date : row.training_date;
              return (
                <div
                  className="p-4 sm:p-5 hover:bg-red-50 transition-colors duration-150"
                  data-testid={`admin-sf-row-${row.id}`}
                >
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="inline-flex items-center px-2 py-0.5 bg-red-700 text-white text-[10px] font-mono uppercase tracking-wider rounded font-bold">
                      {formatDateLong(date)}
                    </span>
                    <span className="font-display text-base font-bold text-slate-900 truncate">
                      {row.employee_name}
                    </span>
                    {tab === "issuance" ? (
                      row.status === "returned" ? (
                        <span
                          className="inline-block px-2 py-0.5 rounded font-mono text-[10px] font-bold uppercase tracking-wide bg-emerald-100 text-emerald-800 border border-emerald-300"
                          title={
                            row.return?.chargeback?.total
                              ? `Chargeback: ${fmtMoney(row.return.chargeback.total)}`
                              : "Returned in full"
                          }
                        >
                          Returned
                          {row.return?.chargeback?.total ? (
                            <span className="ml-1 text-red-700 font-bold">
                              · {fmtMoney(row.return.chargeback.total)}
                            </span>
                          ) : null}
                        </span>
                      ) : (
                        <span className="inline-block px-2 py-0.5 rounded font-mono text-[10px] font-bold uppercase tracking-wide bg-amber-100 text-amber-800 border border-amber-300">
                          Out
                        </span>
                      )
                    ) : null}
                    <div className="ml-auto inline-flex items-center gap-1">
                      <Link
                        to={`/safety/forms/${tab === "issuance" ? "equipment-issuance" : "equipment-training"}/${row.id}`}
                        className="inline-flex items-center justify-center w-8 h-8 rounded border-2 border-slate-200 text-slate-700 hover:border-slate-900 hover:text-slate-900"
                        title="Open"
                        data-testid={`admin-sf-open-${row.id}`}
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </Link>
                      <button
                        type="button"
                        onClick={() =>
                          downloadPdf(row.id, tab === "issuance" ? "Issuance" : "Training")
                        }
                        className="inline-flex items-center justify-center w-8 h-8 rounded border-2 border-red-200 text-red-700 hover:border-red-700 hover:bg-red-50"
                        title="Download PDF"
                        data-testid={`admin-sf-pdf-${row.id}`}
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                  <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500 mt-1 flex flex-wrap gap-x-3">
                    {tab === "issuance" ? (
                      <>
                        <span>By: {row.issued_by}</span>
                        <span>{(row.items || []).length} item{(row.items || []).length === 1 ? "" : "s"}</span>
                        <span className="font-bold text-slate-700">{fmtMoney(row.total_value)}</span>
                      </>
                    ) : (
                      <>
                        <span>Instructor: {row.instructor_name}</span>
                        <span>{(row.items || []).length} equipment</span>
                        <span>{(row.topics || []).length} topics</span>
                      </>
                    )}
                  </div>
                </div>
              );
            }}
          />
        )}
      </div>
    </section>
  );
}

function FilterField({ label, icon: Icon, children }) {
  return (
    <div>
      <Label className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-600 font-bold mb-1 inline-flex items-center gap-1">
        {Icon ? <Icon className="w-3 h-3" /> : null}
        {label}
      </Label>
      {children}
    </div>
  );
}
