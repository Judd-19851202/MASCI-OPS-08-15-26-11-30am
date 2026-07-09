/**
 * OA-1 · OperationsActionDetail.jsx
 * Full ownership + status workflow + notes + photos + history.
 */
import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft, Home, Loader2, AlertTriangle, RefreshCw, Save, Send, MessageSquare,
} from "lucide-react";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { usePageTitle } from "@/lib/usePageTitle";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import CoachingPanel from "@/components/oa/CoachingPanel";
import StatusBadge from "@/components/oa/StatusBadge";
import OwnerPicker from "@/components/oa/OwnerPicker";
import PhotoUploader from "@/components/oa/PhotoUploader";
import HistoryFeed from "@/components/oa/HistoryFeed";
import {
  oaApi, CATEGORIES, CATEGORY_LABEL, PRIORITIES, PRIORITY_LABEL,
  STATUSES, STATUS_LABEL, PRIORITY_TONE,
} from "@/lib/oa";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

export default function OperationsActionDetail() {
  const { id } = useParams();
  usePageTitle("Operations Action · MASCI");
  const { t } = useT();
  const nav = useNavigate();
  const [oa, setOa] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({});
  const [saving, setSaving] = useState(false);
  const [noteText, setNoteText] = useState("");
  const [showAssign, setShowAssign] = useState(false);
  const [newOwner, setNewOwner] = useState(null);

  const load = async () => {
    setLoading(true); setErr("");
    try {
      const r = await oaApi.read(id);
      setOa(r.data);
      setDraft({
        title: r.data.title, category: r.data.category, priority: r.data.priority,
        job_number: r.data.job_number || "", location: r.data.location || "",
        description: r.data.description || "", due_date: r.data.due_date || "",
      });
    } catch (e) {
      setErr(e?.response?.data?.detail || "Could not load Operations Action.");
    } finally {
      setLoading(false);
    }
  };

   
  useEffect(() => { load(); }, [id]);

  const saveEdits = async () => {
    setSaving(true);
    try {
      const r = await oaApi.patch(id, draft);
      setOa(r.data);
      setEditing(false);
      toast.success(t("Update"));
    } catch (e) {
      toast.error(e?.response?.data?.detail || t("Could not save. Please try again."));
    } finally {
      setSaving(false);
    }
  };

  const doAssign = async () => {
    if (!newOwner) return;
    setSaving(true);
    try {
      const r = await oaApi.assign(id, newOwner);
      setOa(r.data);
      setNewOwner(null);
      setShowAssign(false);
      toast.success(t("Assign"));
    } catch (e) {
      toast.error(e?.response?.data?.detail || t("Could not save. Please try again."));
    } finally {
      setSaving(false);
    }
  };

  const setStatus = async (status) => {
    setSaving(true);
    try {
      const r = await oaApi.changeStatus(id, status);
      setOa(r.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || t("Could not save. Please try again."));
    } finally {
      setSaving(false);
    }
  };

  const addNote = async () => {
    const body = noteText.trim();
    if (!body) { toast.error(t("Note cannot be empty.")); return; }
    setSaving(true);
    try {
      await oaApi.addNote(id, body);
      setNoteText("");
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || t("Could not save. Please try again."));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen blueprint-bg flex items-center justify-center" data-testid="oa-detail-loading">
        <div className="text-slate-500"><Loader2 className="w-5 h-5 inline animate-spin mr-2" />{t("Loading…") || "Loading…"}</div>
      </div>
    );
  }
  if (err || !oa) {
    return (
      <div className="min-h-screen blueprint-bg flex items-center justify-center px-4" data-testid="oa-detail-error">
        <div className="bg-rose-50 border-2 border-rose-200 rounded-md p-4 text-sm text-rose-800 max-w-md">
          <AlertTriangle className="w-4 h-4 inline -mt-0.5 mr-1" /> {err || "Not found."}
        </div>
      </div>
    );
  }

  const isClosed = oa.status === "closed";

  return (
    <div className="min-h-screen blueprint-bg pb-16" data-testid="oa-detail-root">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-indigo-500">
        <div className="max-w-5xl mx-auto px-4 sm:px-8 py-3 flex items-center gap-3">
          <Link to="/" className="text-white hover:text-indigo-200 text-xs sm:text-sm font-bold" data-testid="oa-det-nav-home"><Home className="w-4 h-4 inline sm:mr-1" /><span className="hidden sm:inline">Home</span></Link>
          <button onClick={() => nav("/operations-actions")} className="text-white hover:text-indigo-200 text-xs sm:text-sm font-bold" data-testid="oa-det-nav-back"><ArrowLeft className="w-4 h-4 inline sm:mr-1" /><span className="hidden sm:inline">Back</span></button>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <div className="flex-1" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-8 py-6 space-y-5">
        {/* Header strip */}
        <section className="bg-white border border-slate-200 border-l-4 border-l-indigo-500 rounded-md p-4">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-indigo-700 font-bold" data-testid="oa-det-oa-number">{oa.oa_number}</span>
                <StatusBadge status={oa.status} />
                <span className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${PRIORITY_TONE[oa.priority] || ""}`} data-testid="oa-det-priority">{t(PRIORITY_LABEL[oa.priority] || oa.priority)}</span>
                <span className="text-[10px] font-mono text-slate-500">{t(CATEGORY_LABEL[oa.category] || oa.category)}</span>
              </div>
              <h1 className="font-display text-xl sm:text-2xl font-black tracking-tight mt-1" data-testid="oa-det-title">{oa.title}</h1>
              <div className="text-xs text-slate-600 mt-1">
                {oa.job_number ? <><span className="font-mono">{oa.job_number}</span> · </> : null}
                {oa.location || ""}
              </div>
            </div>
            <button onClick={load} className="text-[10px] font-mono uppercase tracking-wider text-slate-500 hover:text-slate-800 inline-flex items-center gap-1" data-testid="oa-det-refresh"><RefreshCw className="w-3 h-3" />Refresh</button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 text-xs">
            <KV label={t("Created By")} value={oa.created_by?.name} testid="oa-det-created-by" />
            <KV label={t("Created")} value={formatPlatformTime(oa.created_at)} testid="oa-det-created-at" />
            <KV label={t("Current Owner")} value={oa.current_owner?.name || "—"} testid="oa-det-owner" />
            <KV label={t("Last Updated")} value={formatPlatformTime(oa.last_updated_at)} testid="oa-det-updated-at" />
          </div>
        </section>

        {/* Mandatory coaching */}
        <CoachingPanel compact />

        {/* Status actions */}
        {!isClosed ? (
          <section className="bg-white border border-slate-200 rounded-md p-3" data-testid="oa-det-status-actions">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">{t("History")} — {t("Update")}</div>
            <div className="flex flex-wrap gap-2">
              {STATUSES.filter((s) => s !== "open" && s !== oa.status).map((s) => (
                <button
                  key={s}
                  type="button"
                  disabled={saving || (s === "assigned" && !oa.current_owner)}
                  onClick={() => setStatus(s)}
                  data-testid={`oa-action-set-status-${s}`}
                  className="px-2.5 py-1.5 text-xs font-bold uppercase tracking-wide rounded border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50"
                >
                  {t(STATUS_LABEL[s])}
                </button>
              ))}
              <button
                type="button"
                disabled={saving}
                onClick={() => setShowAssign((v) => !v)}
                data-testid="oa-action-assign-toggle"
                className="px-2.5 py-1.5 text-xs font-bold uppercase tracking-wide rounded border border-indigo-300 bg-indigo-50 hover:bg-indigo-100 text-indigo-900"
              >
                {oa.current_owner ? t("Reassign") : t("Assign")}
              </button>
            </div>
            {showAssign ? (
              <div className="mt-3 flex items-end gap-2 flex-wrap" data-testid="oa-assign-row">
                <div className="flex-1 min-w-[200px]">
                  <OwnerPicker value={newOwner} onChange={setNewOwner} autoFocus />
                </div>
                <button
                  type="button"
                  disabled={!newOwner || saving}
                  onClick={doAssign}
                  data-testid="oa-action-assign-confirm"
                  className="inline-flex items-center gap-2 px-3 py-2 rounded bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold uppercase tracking-wide disabled:opacity-50"
                >
                  <Send className="w-4 h-4" /> {t("Assign")}
                </button>
              </div>
            ) : null}
          </section>
        ) : null}

        {/* Edit core fields */}
        <section className="bg-white border border-slate-200 rounded-md p-3" data-testid="oa-det-edit-section">
          <div className="flex items-center justify-between mb-2">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Description")}</div>
            {!isClosed ? (
              <button
                type="button"
                onClick={() => setEditing((v) => !v)}
                className="text-[10px] font-mono uppercase tracking-wider text-indigo-700 hover:text-indigo-900"
                data-testid="oa-det-edit-toggle"
              >
                {editing ? t("Cancel") : t("Update")}
              </button>
            ) : null}
          </div>
          {!editing ? (
            <div className="text-sm text-slate-700 whitespace-pre-wrap" data-testid="oa-det-description-view">
              {oa.description || <span className="text-slate-400 italic">—</span>}
            </div>
          ) : (
            <div className="space-y-3" data-testid="oa-det-edit-form">
              <input type="text" value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded text-base font-bold" data-testid="oa-edit-title" />
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <select value={draft.category} onChange={(e) => setDraft({ ...draft, category: e.target.value })} className="px-2 py-2 border border-slate-300 rounded text-sm" data-testid="oa-edit-category">
                  {CATEGORIES.map((c) => (<option key={c} value={c}>{t(CATEGORY_LABEL[c])}</option>))}
                </select>
                <select value={draft.priority} onChange={(e) => setDraft({ ...draft, priority: e.target.value })} className="px-2 py-2 border border-slate-300 rounded text-sm" data-testid="oa-edit-priority">
                  {PRIORITIES.map((p) => (<option key={p} value={p}>{t(PRIORITY_LABEL[p])}</option>))}
                </select>
                <input type="date" value={draft.due_date || ""} onChange={(e) => setDraft({ ...draft, due_date: e.target.value })} className="px-2 py-2 border border-slate-300 rounded text-sm" data-testid="oa-edit-due" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <input type="text" placeholder={t("Job Number")} value={draft.job_number} onChange={(e) => setDraft({ ...draft, job_number: e.target.value })} className="px-2 py-2 border border-slate-300 rounded text-sm font-mono" data-testid="oa-edit-job" />
                <input type="text" placeholder={t("Location")} value={draft.location} onChange={(e) => setDraft({ ...draft, location: e.target.value })} className="px-2 py-2 border border-slate-300 rounded text-sm" data-testid="oa-edit-location" />
              </div>
              <textarea value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })} rows={3} className="w-full px-3 py-2 border border-slate-300 rounded text-sm" data-testid="oa-edit-description" />
              <div className="text-right">
                <button type="button" disabled={saving} onClick={saveEdits} data-testid="oa-edit-save" className="inline-flex items-center gap-1.5 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-sm font-bold uppercase tracking-wide disabled:opacity-50">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} {t("Save")}
                </button>
              </div>
            </div>
          )}
        </section>

        {/* Photos */}
        <section className="bg-white border border-slate-200 rounded-md p-3" data-testid="oa-det-photos-section">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">{t("Photos")}</div>
          <PhotoUploader oaId={id} photos={oa.photos} onChange={(photos) => setOa({ ...oa, photos })} />
        </section>

        {/* Notes */}
        <section className="bg-white border border-slate-200 rounded-md p-3" data-testid="oa-det-notes-section">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">{t("Notes")}</div>
          <div className="space-y-2">
            {(oa.notes || []).slice().reverse().map((n) => (
              <div key={n.id} data-testid={`oa-note-${n.id}`} className="border border-slate-200 rounded p-2 text-xs">
                <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500 mb-1">
                  <MessageSquare className="w-3 h-3" /> {n.author?.name || "—"} · {formatPlatformTime(n.created_at)}
                </div>
                <div className="text-slate-800 whitespace-pre-wrap">{n.body_en}</div>
              </div>
            ))}
            {!(oa.notes && oa.notes.length) ? <div className="text-xs text-slate-500 italic" data-testid="oa-notes-empty">{t("No actions yet.")}</div> : null}
          </div>
          {!isClosed ? (
            <div className="mt-3 flex items-end gap-2">
              <textarea value={noteText} onChange={(e) => setNoteText(e.target.value)} rows={2} placeholder={t("Add a note")} className="flex-1 px-3 py-2 border border-slate-300 rounded text-sm" data-testid="oa-note-input" />
              <button type="button" disabled={saving || !noteText.trim()} onClick={addNote} data-testid="oa-note-submit" className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded text-sm font-bold uppercase tracking-wide disabled:opacity-50">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} {t("Add note")}
              </button>
            </div>
          ) : null}
        </section>

        {/* History */}
        <section className="bg-white border border-slate-200 rounded-md p-3" data-testid="oa-det-history-section">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">{t("History")}</div>
          <HistoryFeed entries={oa.history} />
        </section>
      </main>
    </div>
  );
}

function KV({ label, value, testid }) {
  return (
    <div data-testid={testid}>
      <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className="text-slate-900 truncate">{value || <span className="text-slate-400 italic">—</span>}</div>
    </div>
  );
}
