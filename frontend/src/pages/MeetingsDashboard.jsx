import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Plus,
  Users,
  Eye,
  Trash2,
  Loader2,
  ArrowLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { ShareFormDialog } from "@/components/ShareFormDialog";
import { api } from "@/lib/api";
import { formatDateLong } from "@/lib/utils";
import { toast } from "sonner";

export default function MeetingsDashboard() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get("/meetings");
      setItems(res.data || []);
    } catch {
      toast.error("Could not load meetings");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this meeting? This cannot be undone.")) return;
    try {
      await api.delete(`/meetings/${id}`);
      toast.success("Meeting deleted");
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
            to="/admin"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="hub-link"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Admin
          </Link>
          <MasciLogo variant="mark" size="md" />
          <div className="flex items-center gap-2">
            <ShareFormDialog
              formType="meeting"
              path="/meetings/submit"
              title="Share Meeting Form"
              description="Anyone with this link can log a Site Safety Meeting. No login required."
              testIdPrefix="share-meeting"
            />
            <Button
              onClick={() => navigate("/meetings/new")}
              className="h-12 px-5 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-4 border-red-900"
              data-testid="new-meeting-btn"
            >
              <Plus className="w-5 h-5 mr-1" />
              <span className="hidden sm:inline">New Meeting</span>
              <span className="sm:hidden">New</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-8">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
            Site Safety Meetings
          </span>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-2">
            Toolbox Talks &amp; Huddles
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
            Document every safety meeting with topic, attendance, and signatures.
          </p>
        </div>

        <div className="bg-white border-2 border-slate-300 rounded-md overflow-hidden">
          <div className="px-5 py-4 border-b-2 border-slate-200 flex items-center justify-between">
            <h2 className="font-display text-xl font-bold">Recent Meetings</h2>
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
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-md bg-slate-800 mb-5">
                <Users className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-display text-2xl font-bold text-slate-900">
                No meetings logged yet
              </h3>
              <p className="text-slate-600 mt-2 max-w-md mx-auto">
                Run a toolbox talk and document who attended.
              </p>
              <Button
                onClick={() => navigate("/meetings/new")}
                className="mt-6 h-12 px-6 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
                data-testid="empty-cta"
              >
                <Plus className="w-5 h-5 mr-2" /> Log First Meeting
              </Button>
            </div>
          ) : (
            <ul className="divide-y-2 divide-slate-100">
              {items.map((it) => (
                <li
                  key={it.id}
                  onClick={() => navigate(`/meetings/${it.id}`)}
                  className="p-4 sm:p-5 hover:bg-red-50 cursor-pointer transition-colors duration-150 flex flex-col sm:flex-row sm:items-center gap-3"
                  data-testid={`meeting-row-${it.id}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-display text-lg font-bold text-slate-900 truncate">
                        {it.topic || "Untitled Meeting"}
                      </span>
                      {it.topic_category && (
                        <span className="inline-flex items-center px-2 py-0.5 bg-slate-200 text-slate-700 text-[10px] font-mono uppercase tracking-wider rounded">
                          {it.topic_category}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-slate-600 mt-1">
                      {it.project_name || "—"} · Conducted by: {it.conducted_by || "—"}
                    </div>
                    <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500 mt-1">
                      {formatDateLong(it.meeting_date)} · {it.attendee_count || 0} attendee
                      {it.attendee_count === 1 ? "" : "s"}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      to={`/admin/meetings/${it.id}`}
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
