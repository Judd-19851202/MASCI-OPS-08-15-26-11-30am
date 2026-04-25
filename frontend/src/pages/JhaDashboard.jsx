import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, AlertTriangle, Eye, Trash2, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { ShareFormDialog } from "@/components/ShareFormDialog";
import { api } from "@/lib/api";
import { formatDateLong } from "@/lib/utils";
import { toast } from "sonner";

export default function JhaDashboard() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get("/jhas");
      setItems(res.data || []);
    } catch {
      toast.error("Could not load JHAs");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this JHA? This cannot be undone.")) return;
    try {
      await api.delete(`/jhas/${id}`);
      toast.success("JHA deleted");
      setItems((p) => p.filter((i) => i.id !== id));
    } catch {
      toast.error("Delete failed");
    }
  };

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <Link
            to="/"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="hub-link"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Hub
          </Link>
          <MasciLogo variant="mark" size="md" />
          <div className="flex items-center gap-2">
            <ShareFormDialog
              formType="jha"
              path="/jha/submit"
              title="Share JHA Form"
              description="Anyone with this link can fill out a Job Hazard Analysis. No login required."
              testIdPrefix="share-jha"
            />
            <Button
              onClick={() => navigate("/jha/new")}
              className="h-12 px-5 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-4 border-red-900"
              data-testid="new-jha-btn"
            >
              <Plus className="w-5 h-5 mr-1" />
              <span className="hidden sm:inline">New JHA</span>
              <span className="sm:hidden">New</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-8">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
            Job Hazard Analysis
          </span>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-2">
            Pre-Task Hazard Analysis
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
            Walk through every step of the task, identify the hazards, document the
            controls, and get the crew sign-off — before the work starts.
          </p>
        </div>

        <div className="bg-white border-2 border-slate-300 rounded-md overflow-hidden">
          <div className="px-5 py-4 border-b-2 border-slate-200 flex items-center justify-between">
            <h2 className="font-display text-xl font-bold">Recent JHAs</h2>
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
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-md bg-amber-600 mb-5">
                <AlertTriangle className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-display text-2xl font-bold text-slate-900">
                No JHAs on file yet
              </h3>
              <p className="text-slate-600 mt-2 max-w-md mx-auto">
                Document a job hazard analysis before the crew picks up a tool.
              </p>
              <Button
                onClick={() => navigate("/jha/new")}
                className="mt-6 h-12 px-6 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
                data-testid="empty-cta"
              >
                <Plus className="w-5 h-5 mr-2" /> Create First JHA
              </Button>
            </div>
          ) : (
            <ul className="divide-y-2 divide-slate-100">
              {items.map((it) => (
                <li
                  key={it.id}
                  onClick={() => navigate(`/jha/${it.id}`)}
                  className="p-4 sm:p-5 hover:bg-red-50 cursor-pointer transition-colors duration-150 flex flex-col sm:flex-row sm:items-center gap-3"
                  data-testid={`jha-row-${it.id}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-display text-lg font-bold text-slate-900 truncate">
                        {it.job_title || "Untitled JHA"}
                      </span>
                      <span className="inline-flex items-center px-2 py-0.5 bg-amber-100 text-amber-800 text-[10px] font-mono uppercase tracking-wider rounded">
                        {it.step_count || 0} step{it.step_count === 1 ? "" : "s"}
                      </span>
                    </div>
                    <div className="text-sm text-slate-600 mt-1">
                      {it.project_name || "—"} · Crew Lead: {it.crew_lead || "—"}
                    </div>
                    <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500 mt-1">
                      {formatDateLong(it.jha_date)} · {it.signoff_count || 0} sign-off
                      {it.signoff_count === 1 ? "" : "s"}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      to={`/jha/${it.id}`}
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
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );
}
