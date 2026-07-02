// Track 19.22 · Phase 4 · Historical Records — Bulk Batches list
// Route: /hr/historical-records/batches
// HR sees all batches. Safety sees Safety lane batches. Asset Admin
// sees Asset lane batches. Create a new batch from here.
import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  ArrowLeft, ChevronRight, FolderOpen, Plus, RefreshCw,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import {
  createBatch, fetchVocabulary, listBatches,
} from "@/lib/employeeRecordsApi";

const LANE_LABEL = {
  hr: "HR", safety: "Safety", asset: "Asset", corporate_import: "Corporate Import",
};

function _fmt(x) {
  if (!x) return "—";
  try { return new Date(x).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }); }
  catch { return x; }
}

export default function HistoricalRecordsBatches() {
  const { t } = useT();
  const navigate = useNavigate();
  const [vocab, setVocab] = useState(null);
  const [batches, setBatches] = useState([]);
  const [busy, setBusy] = useState(false);
  const [newLane, setNewLane] = useState("");
  const [newLabel, setNewLabel] = useState("");
  const [newSrcName, setNewSrcName] = useState("");
  const [newSrcType, setNewSrcType] = useState("");
  const [newSrcLoc, setNewSrcLoc] = useState("");

  useEffect(() => {
    fetchVocabulary()
      .then((v) => {
        setVocab(v);
        if (v?.allowed_lanes_for_actor?.length) {
          setNewLane((cur) => cur || v.allowed_lanes_for_actor[0]);
        }
      })
      .catch((e) => toast.error(String(e.message || e)));
  }, []);

  const load = useCallback(async () => {
    setBusy(true);
    try {
      const r = await listBatches();
      setBatches(r.batches || []);
    } catch (e) { toast.error(String(e.message || e)); }
    finally { setBusy(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onCreate = async () => {
    if (!newLane) { toast.error(t("Pick a lane.")); return; }
    setBusy(true);
    try {
      const r = await createBatch({
        ownership_lane: newLane,
        label: newLabel,
        source_name: newSrcName,
        source_type: newSrcType,
        source_location: newSrcLoc,
      });
      toast.success(t("Batch created."));
      setNewLabel("");
      setNewSrcName("");
      setNewSrcType("");
      setNewSrcLoc("");
      navigate(`/hr/historical-records/batches/${r.batch.id}`);
    } catch (e) { toast.error(String(e.message || e)); }
    finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-slate-50" data-testid="historical-records-batches">
      <div className="max-w-5xl mx-auto p-4 sm:p-6 space-y-4">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
          data-testid="batches-back"
        >
          <ArrowLeft className="w-4 h-4" /> {t("Back")}
        </button>

        <header className="rounded-xl border-2 border-slate-300 bg-white p-4 sm:p-5"
                data-testid="batches-header">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("Historical Records")} · {t("Bulk Intake Batches")}
          </div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
            {t("Batches")}
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            {t("Upload many files at once. Then classify + assign employees + approve in bulk. Manual review only — no OCR, no AI classification.")}
          </p>
        </header>

        {/* New batch form */}
        <div className="rounded-xl border-2 border-slate-300 bg-white p-4 space-y-3"
             data-testid="batches-new">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("New Intake Session")}
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Lane")}
              </label>
              <select
                value={newLane}
                onChange={(e) => setNewLane(e.target.value)}
                className="mt-1 rounded-md border-2 border-slate-300 bg-white px-2 py-1.5 text-sm font-mono"
                data-testid="batches-new-lane"
              >
                {(vocab?.allowed_lanes_for_actor || []).map((l) => (
                  <option key={l} value={l}>{LANE_LABEL[l] || l}</option>
                ))}
              </select>
            </div>
            <div className="flex-1 min-w-[220px]">
              <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Session label")}
              </label>
              <input
                type="text"
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                placeholder={t("e.g. 2024 Personnel Files")}
                className="mt-1 w-full rounded-md border-2 border-slate-300 bg-white px-3 py-1.5 text-sm"
                data-testid="batches-new-label"
              />
            </div>
          </div>
          {/* Track 19.25 · Session provenance — inherited by every file. */}
          <div className="grid gap-3 sm:grid-cols-3" data-testid="batches-new-session-provenance">
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Source name")}
              </label>
              <input
                type="text"
                value={newSrcName}
                onChange={(e) => setNewSrcName(e.target.value)}
                placeholder={t("2019 HR file cabinet")}
                className="mt-1 w-full rounded-md border-2 border-slate-300 bg-white px-3 py-1.5 text-sm"
                data-testid="batches-new-source-name"
              />
            </div>
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Source type")}
              </label>
              <select
                value={newSrcType}
                onChange={(e) => setNewSrcType(e.target.value)}
                className="mt-1 w-full rounded-md border-2 border-slate-300 bg-white px-3 py-1.5 text-sm font-mono"
                data-testid="batches-new-source-type"
              >
                <option value="">{t("(pick)")}</option>
                <option value="cabinet">{t("Cabinet")}</option>
                <option value="binder">{t("Binder")}</option>
                <option value="box">{t("Box")}</option>
                <option value="folder">{t("Folder")}</option>
                <option value="digital">{t("Digital archive")}</option>
                <option value="other">{t("Other")}</option>
              </select>
            </div>
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Location")}
              </label>
              <input
                type="text"
                value={newSrcLoc}
                onChange={(e) => setNewSrcLoc(e.target.value)}
                placeholder={t("University High School · trailer")}
                className="mt-1 w-full rounded-md border-2 border-slate-300 bg-white px-3 py-1.5 text-sm"
                data-testid="batches-new-source-location"
              />
            </div>
          </div>
          <div>
            <button
              type="button"
              onClick={onCreate}
              disabled={busy || !newLane}
              className="inline-flex items-center gap-2 rounded-md bg-purple-700 text-white px-4 py-2 text-sm font-semibold hover:bg-purple-800 disabled:opacity-50"
              data-testid="batches-create"
            >
              <Plus className="w-3.5 h-3.5" /> {t("Create batch")}
            </button>
            <span className="ml-3 text-[11px] text-slate-500">
              {t("Provenance is inherited by every file in this batch.")}
            </span>
          </div>
        </div>

        {/* List */}
        <div className="rounded-xl border-2 border-slate-300 bg-white overflow-hidden"
             data-testid="batches-list">
          <div className="p-3 flex items-center justify-between border-b border-slate-200">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
              {t("Recent batches")} · {batches.length}
            </div>
            <button
              type="button"
              onClick={load}
              disabled={busy}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
              data-testid="batches-refresh"
            >
              <RefreshCw className={`w-3 h-3 ${busy ? "animate-spin" : ""}`} /> {t("Refresh")}
            </button>
          </div>
          {batches.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-sm" data-testid="batches-empty">
              {t("No batches yet.")}
            </div>
          ) : (
            <ul className="divide-y divide-slate-200">
              {batches.map((b) => (
                <li key={b.id}>
                  <button
                    type="button"
                    onClick={() => navigate(`/hr/historical-records/batches/${b.id}`)}
                    className="w-full text-left p-3 hover:bg-slate-50 flex items-start gap-3"
                    data-testid={`batches-item-${b.id}`}
                  >
                    <FolderOpen className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-sm text-slate-900">
                          {b.label || `Batch ${b.id.slice(0, 8)}`}
                        </span>
                        <span className="text-[10px] font-mono uppercase tracking-widest rounded bg-slate-100 border border-slate-200 px-1.5 py-0.5 text-slate-700">
                          {LANE_LABEL[b.ownership_lane] || b.ownership_lane}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500">
                          #{b.id.slice(0, 8)}
                        </span>
                      </div>
                      <div className="mt-0.5 text-xs text-slate-600 flex flex-wrap gap-x-3">
                        <span>{t("Files")}: {b.file_count ?? 0}</span>
                        <span>{t("Records")}: {b.record_count ?? 0}</span>
                        <span>{t("By")}: {b.created_by || "—"}</span>
                        <span>{_fmt(b.created_at)}</span>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-400 shrink-0 mt-1" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
