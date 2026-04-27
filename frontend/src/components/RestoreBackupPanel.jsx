import React, { useRef, useState } from "react";
import { Upload, Loader2, ShieldAlert, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { toast } from "sonner";

/**
 * RestoreBackupPanel — pair to the "Download Full Backup" button.
 * Uploads a MASCI full-backup .zip to POST /api/exports/restore.
 *
 * MERGE: upsert rows by id — new rows added, existing rows overwritten,
 * untouched collections untouched. Safe default.
 *
 * REPLACE: wipe each collection found in the ZIP, then reinsert. Destructive.
 * Guarded by a confirmation dialog + typing "REPLACE" to confirm.
 */
export default function RestoreBackupPanel() {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [mode, setMode] = useState("merge"); // 'merge' | 'replace'
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [pendingFile, setPendingFile] = useState(null);
  const fileRef = useRef(null);

  const onPick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".zip")) {
      toast.error("Please pick a .zip backup file");
      e.target.value = "";
      return;
    }
    if (f.size > 500 * 1024 * 1024) {
      toast.error("File exceeds 500 MB limit");
      e.target.value = "";
      return;
    }
    if (mode === "replace") {
      setPendingFile(f);
      setConfirmText("");
      setConfirmOpen(true);
      e.target.value = "";
    } else {
      runRestore(f, true);
      e.target.value = "";
    }
  };

  const runRestore = async (file, merge) => {
    setBusy(true);
    setResult(null);
    toast.info(
      merge
        ? "Restoring backup (merge — existing rows updated, new rows added)…"
        : "Restoring backup (REPLACE — collections wiped first)…",
    );
    const fd = new FormData();
    fd.append("file", file);
    fd.append("merge", merge ? "true" : "false");
    try {
      const r = await api.post("/exports/restore", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(r.data);
      toast.success(
        `Restore complete — ${r.data.total_processed} records across ${Object.keys(r.data.collections || {}).length} collections`,
      );
    } catch (e) {
      const detail = e?.response?.data?.detail || "Restore failed";
      toast.error(typeof detail === "string" ? detail : "Restore failed — see console");
      console.error(e);
    } finally {
      setBusy(false);
      setPendingFile(null);
    }
  };

  const confirmReplace = () => {
    if (confirmText !== "REPLACE" || !pendingFile) return;
    setConfirmOpen(false);
    runRestore(pendingFile, false);
  };

  return (
    <section
      className="mt-6 pt-5 border-t-2 border-slate-200"
      data-testid="restore-backup-panel"
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-600 text-white">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-display text-base sm:text-lg font-black tracking-tight text-slate-900">
              Restore from Backup
            </h3>
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
              Upload a MASCI .zip · rebuilds the entire system
            </p>
          </div>
        </div>
      </div>

      {/* Mode toggle */}
      <div className="mt-4 flex items-center gap-2 flex-wrap">
        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
          Mode:
        </Label>
        <div className="inline-flex rounded-md border-2 border-slate-200 overflow-hidden" data-testid="restore-mode-toggle">
          <button
            type="button"
            onClick={() => setMode("merge")}
            className={`px-3 py-1.5 text-xs font-bold uppercase tracking-wide ${
              mode === "merge" ? "bg-emerald-600 text-white" : "bg-white text-slate-700 hover:bg-slate-50"
            }`}
            data-testid="restore-mode-merge"
          >
            Merge (safe)
          </button>
          <button
            type="button"
            onClick={() => setMode("replace")}
            className={`px-3 py-1.5 text-xs font-bold uppercase tracking-wide ${
              mode === "replace" ? "bg-red-700 text-white" : "bg-white text-slate-700 hover:bg-slate-50"
            }`}
            data-testid="restore-mode-replace"
          >
            Replace (wipe + restore)
          </button>
        </div>
      </div>

      {/* File input */}
      <div className="mt-4 flex items-center gap-3 flex-wrap">
        <input
          ref={fileRef}
          type="file"
          accept=".zip,application/zip"
          onChange={onPick}
          className="hidden"
          data-testid="restore-file-input"
        />
        <Button
          onClick={() => fileRef.current?.click()}
          disabled={busy}
          className={`h-10 px-4 font-bold uppercase tracking-wide text-xs disabled:bg-slate-400 ${
            mode === "replace"
              ? "bg-red-700 hover:bg-red-800 text-white"
              : "bg-emerald-600 hover:bg-emerald-700 text-white"
          }`}
          data-testid="restore-choose-file-btn"
        >
          {busy ? (
            <><Loader2 className="w-4 h-4 animate-spin mr-1" /> Restoring…</>
          ) : (
            <><Upload className="w-4 h-4 mr-1" /> Pick backup .zip</>
          )}
        </Button>
        <span className="text-xs text-slate-500">
          ≤ 500 MB · must be a backup produced by "Download Full Backup"
        </span>
      </div>

      {/* Helper text per mode */}
      <div
        className={`mt-3 border-l-4 rounded-r-md px-3 py-2 text-xs leading-relaxed ${
          mode === "replace"
            ? "bg-red-50 border-red-600 text-red-900"
            : "bg-emerald-50 border-emerald-600 text-emerald-900"
        }`}
        data-testid="restore-mode-explainer"
      >
        {mode === "merge" ? (
          <>
            <strong>Merge mode</strong> — every record in the .zip is <em>upserted</em> by id:
            existing rows are overwritten with the backup's copy, new rows are inserted,
            and anything not in the backup is left untouched. Safe to run repeatedly.
          </>
        ) : (
          <>
            <strong>Replace mode</strong> — every collection found in the .zip is <strong>wiped first</strong>,
            then repopulated from the backup. Any records added since the backup will be lost.
            Requires typing <strong>REPLACE</strong> to confirm.
          </>
        )}
      </div>

      {/* Results summary */}
      {result && (
        <div
          className="mt-4 bg-white border-2 border-emerald-300 rounded-md p-4"
          data-testid="restore-result"
        >
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-700" />
            <div className="font-display font-black text-emerald-900 text-sm">
              Restore complete — {result.total_processed} records
            </div>
            <span className="ml-auto text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500 font-bold">
              {result.mode} · backup v{result.backup_version}
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-1 text-xs font-mono">
            {Object.entries(result.collections || {}).sort().map(([coll, s]) => (
              <div key={coll} className="flex items-baseline gap-2 py-0.5">
                <span className="text-slate-700 font-bold truncate">{coll}</span>
                <span className="text-slate-400">·</span>
                <span className="text-slate-600">
                  {s.processed}{s.deleted ? ` (wiped ${s.deleted})` : ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* REPLACE confirmation */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent data-testid="restore-confirm-dialog">
          <DialogHeader>
            <DialogTitle className="font-display font-black flex items-center gap-2 text-red-700">
              <ShieldAlert className="w-5 h-5" />
              Confirm REPLACE restore
            </DialogTitle>
            <DialogDescription>
              This will <strong>wipe every collection</strong> present in the .zip before reinserting
              the backup's rows. Anything created since the backup was generated will be
              permanently lost. Type <strong>REPLACE</strong> below to proceed.
            </DialogDescription>
          </DialogHeader>
          <input
            autoFocus
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="Type REPLACE to confirm"
            className="w-full h-11 px-3 border-2 border-slate-300 focus:border-red-700 focus:outline-none rounded font-mono text-sm"
            data-testid="restore-confirm-input"
          />
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>Cancel</Button>
            <Button
              onClick={confirmReplace}
              disabled={confirmText !== "REPLACE"}
              className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide disabled:bg-slate-400"
              data-testid="restore-confirm-btn"
            >
              Replace & restore
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
