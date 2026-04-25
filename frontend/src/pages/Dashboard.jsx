import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, FileText, AlertTriangle, ShieldCheck, Eye, Trash2, Loader2, ClipboardCheck, ShieldX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { ShareFormDialog } from "@/components/ShareFormDialog";
import { GradePill } from "@/components/Grade";
import { api } from "@/lib/api";
import { formatDateLong } from "@/lib/utils";
import { toast } from "sonner";

const StatPill = ({ icon: Icon, value, label, tone = "slate" }) => {
  const tones = {
    slate: "bg-slate-900 text-white",
    yellow: "bg-yellow-400 text-slate-900",
    red: "bg-red-600 text-white",
    green: "bg-green-700 text-white",
  };
  return (
    <div className={`${tones[tone]} px-5 py-4 rounded-md flex items-center gap-3`}>
      <Icon className="w-7 h-7 shrink-0" />
      <div>
        <div className="font-display text-3xl font-black leading-none">{value}</div>
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] mt-1 opacity-90">
          {label}
        </div>
      </div>
    </div>
  );
};

export default function Dashboard() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get("/inspections");
      setItems(res.data || []);
    } catch (e) {
      toast.error("Could not load inspections");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this inspection? This cannot be undone.")) return;
    try {
      await api.delete(`/inspections/${id}`);
      toast.success("Inspection deleted");
      setItems((prev) => prev.filter((i) => i.id !== id));
    } catch {
      toast.error("Delete failed");
    }
  };

  const stats = {
    total: items.length,
    pass: items.filter((i) => i.status === "PASS").length,
    fail: items.filter((i) => i.status === "FAIL").length,
    avgScore:
      items.length === 0
        ? 0
        : Math.round(
            items.reduce((s, i) => s + (i.score || 0), 0) / items.length
          ),
  };

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="2xl" className="hidden sm:block" />
          <MasciLogo variant="mark" size="lg" className="sm:hidden" />
          <div className="flex items-center gap-2">
            <ShareFormDialog />
            <CompanyInfoDialog />
            <Button
              onClick={() => navigate("/inspect/new")}
              className="h-12 sm:h-14 px-5 sm:px-7 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm sm:text-base border-b-4 border-red-900"
              data-testid="new-inspection-btn"
            >
              <Plus className="w-5 h-5 mr-1 sm:mr-2" />
              <span className="hidden sm:inline">New Inspection</span>
              <span className="sm:hidden">New</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-10 sm:mb-14">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-slate-500">
            Job Site Safety Program
          </span>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 mt-2">
            Inspection Reports
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
            Document compliance, capture findings, and produce print-ready reports
            from any device — phone, tablet, or desktop.
          </p>
          <div className="mt-4 flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.25em]">
            <span className="text-red-700 font-bold">No Shortcuts</span>
            <span className="w-1 h-1 rounded-full bg-red-700" />
            <span className="text-red-700 font-bold">No Exceptions</span>
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-10">
          <StatPill icon={FileText} value={stats.total} label="Total Reports" tone="slate" />
          <StatPill icon={ShieldCheck} value={stats.pass} label="Passing" tone="green" />
          <StatPill icon={ShieldX} value={stats.fail} label="Failing" tone="red" />
          <StatPill icon={AlertTriangle} value={`${stats.avgScore}%`} label="Avg Score" tone="yellow" />
        </div>

        <div className="bg-white border-2 border-slate-300 rounded-md overflow-hidden">
          <div className="px-5 py-4 border-b-2 border-slate-200 flex items-center justify-between">
            <h2 className="font-display text-xl font-bold">Recent Inspections</h2>
            {!loading && (
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
                {items.length} on file
              </span>
            )}
          </div>

          {loading ? (
            <div className="p-12 flex items-center justify-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading...
            </div>
          ) : items.length === 0 ? (
            <div className="p-10 sm:p-16 text-center" data-testid="empty-state">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-md bg-red-700 mb-5">
                <ClipboardCheck className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-display text-2xl font-bold text-slate-900">
                No inspections yet
              </h3>
              <p className="text-slate-600 mt-2 max-w-md mx-auto">
                Send the inspection link to your foremen and supervisors. Submitted
                reports show up here automatically.
              </p>
              <Button
                onClick={() => navigate("/inspect/new")}
                className="mt-6 h-12 px-6 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
                data-testid="empty-state-cta"
              >
                <Plus className="w-5 h-5 mr-2" /> Start First Inspection
              </Button>
            </div>
          ) : (
            <ul className="divide-y-2 divide-slate-100">
              {items.map((it) => {
                const flagged = it.hazards_observed === "Yes" || it.stop_work_issued === "Yes";
                const grade = it.score != null
                  ? {
                      score: it.score,
                      status: it.status || (it.score < 74 ? "FAIL" : "PASS"),
                      auto_fail_count: it.auto_fail_count || 0,
                      yes: it.graded_yes || 0,
                      no: it.graded_no || 0,
                      total: it.graded_total || 0,
                    }
                  : null;
                return (
                  <li
                    key={it.id}
                    onClick={() => navigate(`/inspect/${it.id}`)}
                    className="p-4 sm:p-5 hover:bg-red-50 cursor-pointer transition-colors duration-150 flex flex-col sm:flex-row sm:items-center gap-3"
                    data-testid={`inspection-row-${it.id}`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-display text-lg font-bold text-slate-900 truncate">
                          {it.project_name || "Untitled Project"}
                        </span>
                        <GradePill grade={grade} testId={`grade-${it.id}`} />
                        {flagged && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-600 text-white text-[10px] font-mono uppercase tracking-wider rounded">
                            <AlertTriangle className="w-3 h-3" />
                            {it.stop_work_issued === "Yes" ? "Stop Work" : "Hazard"}
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-slate-600 mt-1">
                        {it.location || "—"} · Inspector: {it.inspector_name || "—"}
                      </div>
                      <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500 mt-1">
                        {formatDateLong(it.inspection_date)} · {it.photo_count} photo
                        {it.photo_count === 1 ? "" : "s"}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Link
                        to={`/inspect/${it.id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center justify-center h-10 px-4 rounded-md bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm uppercase tracking-wide"
                        data-testid={`view-${it.id}`}
                      >
                        <Eye className="w-4 h-4 mr-1" /> View
                      </Link>
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-10 w-10 border-2 border-slate-300 hover:border-red-500 hover:text-red-600"
                        onClick={(e) => handleDelete(it.id, e)}
                        data-testid={`delete-${it.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
        MASCI · Job Site Safety Inspection
      </footer>
    </div>
  );
}
