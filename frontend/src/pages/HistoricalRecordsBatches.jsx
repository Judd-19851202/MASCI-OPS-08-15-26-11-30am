// Track 19.22 · Phase 4 · Historical Records — Bulk Batches list
// Route: /hr/historical-records/batches
// HR sees all batches. Safety sees Safety lane batches. Asset Admin
// sees Asset lane batches. Create a new batch from here.
import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  ChevronRight, FolderOpen, FolderPlus, Plus, RefreshCw,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import {
  createBatch, fetchVocabulary, listBatches,
} from "@/lib/employeeRecordsApi";
import HrPageShell from "@/components/HrPageShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const LANE_LABEL = {
  hr: "HR", safety: "Safety", asset: "Asset", corporate_import: "Corporate Import",
};

function _fmt(x) {
  if (!x) return "—";
  try { return formatPlatformTime(x); }
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
    <HrPageShell title="Record Intake Sessions" kicker="HR · Historical record intake">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6" data-testid="historical-records-batches">
        <Card data-testid="batches-header">
          <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-2">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Historical records")} · {t("Record intake sessions")}
              </div>
              <CardTitle>{t("Bring archived people files into one clean review flow")}</CardTitle>
              <CardDescription className="max-w-3xl">
                {t("Start one intake session, gather related files, sort them to the right employee record, and approve them together with clear source details.")}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={load} disabled={busy} data-testid="batches-refresh">
                <RefreshCw className={`h-4 w-4 ${busy ? "animate-spin" : ""}`} /> {t("Refresh")}
              </Button>
              <Button type="button" variant="secondary" onClick={() => navigate("/hr/historical-records/queue")} data-testid="batches-open-queue">
                <FolderOpen className="h-4 w-4" /> {t("Open review queue")}
              </Button>
            </div>
          </CardHeader>
        </Card>

        <div className="grid gap-6 xl:grid-cols-[1.15fr,0.85fr]">
          <Card data-testid="batches-list">
            <CardHeader>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Open intake sessions")} · {batches.length}
              </div>
              <CardTitle>{t("Recent sessions")}</CardTitle>
              <CardDescription>
                {t("Open a session to upload files, assign employees, and move records into the review queue.")}
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              {batches.length === 0 ? (
                <div className="rounded-[1.5rem] border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center text-sm text-slate-500" data-testid="batches-empty">
                  {t("No intake sessions yet. Start one to gather files for review.")}
                </div>
              ) : (
                <ul className="space-y-3">
                  {batches.map((b) => (
                    <li key={b.id}>
                      <button
                        type="button"
                        onClick={() => navigate(`/hr/historical-records/batches/${b.id}`)}
                        className="wp17-focus-ring flex w-full items-start gap-4 rounded-[1.5rem] border border-[color:var(--border-hairline)] bg-white/90 p-4 text-left shadow-sm transition-[border-color,transform,box-shadow] duration-[140ms] hover:-translate-y-0.5 hover:border-[color:var(--border-bold)] hover:shadow-[var(--shadow-panel)]"
                        data-testid={`batches-item-${b.id}`}
                      >
                        <div className="flex h-11 w-11 items-center justify-center rounded-[1.1rem] bg-[color:var(--surface-muted)] text-[color:var(--brand-strong)]">
                          <FolderOpen className="h-5 w-5" />
                        </div>
                        <div className="min-w-0 flex-1 space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-sm font-semibold text-slate-900">
                              {b.label || `Batch ${b.id.slice(0, 8)}`}
                            </span>
                            <span className="rounded-full border border-slate-200 bg-slate-100 px-2 py-0.5 text-[10px] font-mono uppercase tracking-widest text-slate-700">
                              {LANE_LABEL[b.ownership_lane] || b.ownership_lane}
                            </span>
                            <span className="text-[10px] font-mono text-slate-500">#{b.id.slice(0, 8)}</span>
                          </div>
                          <div className="grid gap-2 text-xs text-slate-600 sm:grid-cols-2 xl:grid-cols-4">
                            <span>{t("Files")}: {b.file_count ?? 0}</span>
                            <span>{t("Records")}: {b.record_count ?? 0}</span>
                            <span>{t("Started by")}: {b.created_by || "—"}</span>
                            <span>{_fmt(b.created_at)}</span>
                          </div>
                        </div>
                        <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-slate-400" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card data-testid="batches-new">
            <CardHeader>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("New intake session")}
              </div>
              <CardTitle>{t("Set up one file intake run")}</CardTitle>
              <CardDescription>
                {t("Capture where the files came from so everyone reviewing this session is working from the same record trail.")}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-0">
              <div className="grid gap-4 sm:grid-cols-[11rem,1fr]">
                <div>
                  <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Lane")}</label>
                  <select
                    value={newLane}
                    onChange={(e) => setNewLane(e.target.value)}
                    className="wp17-focus-ring mt-1 flex h-[3rem] w-full rounded-[1rem] border border-[color:var(--border-bold)] bg-white px-3.5 text-sm text-[color:var(--ink-strong)]"
                    data-testid="batches-new-lane"
                  >
                    {(vocab?.allowed_lanes_for_actor || []).map((l) => (
                      <option key={l} value={l}>{LANE_LABEL[l] || l}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Session name")}</label>
                  <Input
                    type="text"
                    value={newLabel}
                    onChange={(e) => setNewLabel(e.target.value)}
                    placeholder={t("e.g. 2024 Personnel Files")}
                    className="mt-1"
                    data-testid="batches-new-label"
                  />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3" data-testid="batches-new-session-provenance">
                <div>
                  <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Source name")}</label>
                  <Input
                    type="text"
                    value={newSrcName}
                    onChange={(e) => setNewSrcName(e.target.value)}
                    placeholder={t("2019 HR file cabinet")}
                    className="mt-1"
                    data-testid="batches-new-source-name"
                  />
                </div>
                <div>
                  <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Source type")}</label>
                  <select
                    value={newSrcType}
                    onChange={(e) => setNewSrcType(e.target.value)}
                    className="wp17-focus-ring mt-1 flex h-[3rem] w-full rounded-[1rem] border border-[color:var(--border-bold)] bg-white px-3.5 text-sm text-[color:var(--ink-strong)]"
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
                  <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Location")}</label>
                  <Input
                    type="text"
                    value={newSrcLoc}
                    onChange={(e) => setNewSrcLoc(e.target.value)}
                    placeholder={t("University High School · trailer")}
                    className="mt-1"
                    data-testid="batches-new-source-location"
                  />
                </div>
              </div>

              <div className="rounded-[1.4rem] border border-dashed border-[color:var(--border-hairline)] bg-[color:var(--surface-muted)] px-4 py-3 text-sm text-slate-600">
                {t("These source details stay with every file in the session so reviewers know what cabinet, binder, folder, or archive the record came from.")}
              </div>

              <Button type="button" onClick={onCreate} disabled={busy || !newLane} data-testid="batches-create">
                <FolderPlus className="h-4 w-4" /> {t("Create session")}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </HrPageShell>
  );
}
