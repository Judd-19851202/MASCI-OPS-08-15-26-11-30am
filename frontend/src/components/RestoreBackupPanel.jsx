import React, { useEffect, useRef, useState } from "react";
import { Upload, Loader2, ShieldAlert, CheckCircle2, Cloud, CloudDownload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { toast } from "sonner";
import AdminPasswordConfirm from "@/components/AdminPasswordConfirm";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";
import { useT } from "@/lib/i18n";

/**
 * RestoreBackupPanel — pair to the "Download Full Backup" button.
 * Two sources:
 *   1. SOURCE = "file"  → uploads a MASCI full-backup .zip from disk
 *   2. SOURCE = "r2"    → picks a cloud archive from the R2 library,
 *                         streams it down via its presigned URL, then
 *                         re-uploads the same blob to /exports/restore.
 *                         No new backend endpoint needed.
 *
 * Two modes:
 *   MERGE   — upsert rows by id (safe default)
 *   REPLACE — wipe collections in the .zip first, then reinsert. Destructive.
 */
export default function RestoreBackupPanel() {
  const { t } = useT();
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [mode, setMode] = useState("merge"); // 'merge' | 'replace'
  const [source, setSource] = useState("file"); // 'file' | 'r2'
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [backupAck, setBackupAck] = useState(false);
  const [pendingFile, setPendingFile] = useState(null);
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [archives, setArchives] = useState(null);
  const [pickedKey, setPickedKey] = useState("");
  const [fetchingR2, setFetchingR2] = useState(false);
  const fileRef = useRef(null);

  // Lazy-load R2 archives when admin switches to that source
  useEffect(() => {
    if (source !== "r2" || archives !== null) return;
    (async () => {
      try {
        const r = await api.get("/admin/backups-list-r2", { params: { limit: 50 } });
        setArchives(r.data);
      } catch (e) {
        if (e?.response?.status === 400) {
          setArchives({ configured: false, count: 0, backups: [] });
        } else {
          toast.error("Could not load cloud archives. Try again.");
          setArchives({ configured: true, count: 0, backups: [] });
        }
      }
    })();
  }, [source, archives]);

  const onPick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".zip")) {
      toast.error("Choose a .zip backup file.");
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
    fd.append("dry_run", "false");
    if (!merge) {
      fd.append("confirm", "RESTORE_REPLACE_ALL_COLLECTIONS");
      fd.append("backup_ack", backupAck ? "true" : "false");
    }
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
    if (confirmText !== "REPLACE" || !pendingFile || !backupAck) return;
    setConfirmOpen(false);
    // Second gate — admin must re-type the password before any
    // collection is wiped. The pending file is already vetted.
    setPasswordOpen(true);
  };

  const passwordConfirmReplace = async () => {
    if (!pendingFile) return;
    await runRestore(pendingFile, false);
  };

  // R2 source: download the presigned URL to a Blob, wrap it as a File,
  // then funnel through the same flow as a local file pick. This reuses
  // every guard (size, mode toggle, password gate) without a new
  // backend endpoint.
  const restoreFromR2 = async () => {
    if (!pickedKey || fetchingR2) return;
    const picked = (archives?.backups || []).find((b) => b.key === pickedKey);
    if (!picked?.download_url) {
      toast.error("Archive has no presigned URL — refresh and try again");
      return;
    }
    setFetchingR2(true);
    toast.info(`Fetching ${picked.filename} from R2…`);
    try {
      const res = await fetch(picked.download_url);
      if (!res.ok) throw new Error(`R2 fetch returned HTTP ${res.status}`);
      const blob = await res.blob();
      const file = new File([blob], picked.filename, { type: "application/zip" });
      if (file.size > 500 * 1024 * 1024) {
        toast.error("Archive exceeds 500 MB — restore via direct R2 stream not yet supported");
        return;
      }
      if (mode === "replace") {
        setPendingFile(file);
        setConfirmText("");
        setConfirmOpen(true);
      } else {
        await runRestore(file, true);
      }
    } catch (e) {
      toast.error(e?.message || "R2 fetch failed");
      console.error(e);
    } finally {
      setFetchingR2(false);
    }
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
              {t("Restore from Backup")}
            </h3>
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
              {t("Upload a MASCI .zip · rebuilds the entire system")}
            </p>
          </div>
        </div>
      </div>

      {/* Source toggle */}
      <div className="mt-4 flex items-center gap-2 flex-wrap">
        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
          {t("Source:")}
        </Label>
        <div className="inline-flex rounded-md border border-slate-200 overflow-hidden" data-testid="restore-source-toggle">
          <button
            type="button"
            onClick={() => setSource("file")}
            className={`px-3 py-1.5 text-xs font-bold uppercase tracking-wide ${
              source === "file" ? "bg-slate-900 text-white" : "bg-white text-slate-700 hover:bg-slate-50"
            }`}
            data-testid="restore-source-file"
          >
            <Upload className="w-3 h-3 inline mr-1" /> {t("Upload .zip")}
          </button>
          <button
            type="button"
            onClick={() => setSource("r2")}
            className={`px-3 py-1.5 text-xs font-bold uppercase tracking-wide ${
              source === "r2" ? "bg-orange-600 text-white" : "bg-white text-slate-700 hover:bg-slate-50"
            }`}
            data-testid="restore-source-r2"
          >
            <Cloud className="w-3 h-3 inline mr-1" /> {t("From R2 archive")}
          </button>
        </div>
      </div>

      {/* Mode toggle */}
      <div className="mt-3 flex items-center gap-2 flex-wrap">
        <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
          {t("Mode:")}
        </Label>
        <div className="inline-flex rounded-md border border-slate-200 overflow-hidden" data-testid="restore-mode-toggle">
          <button
            type="button"
            onClick={() => setMode("merge")}
            className={`px-3 py-1.5 text-xs font-bold uppercase tracking-wide ${
              mode === "merge" ? "bg-emerald-600 text-white" : "bg-white text-slate-700 hover:bg-slate-50"
            }`}
            data-testid="restore-mode-merge"
          >
            {t("Merge (safe)")}
          </button>
          <button
            type="button"
            onClick={() => setMode("replace")}
            className={`px-3 py-1.5 text-xs font-bold uppercase tracking-wide ${
              mode === "replace" ? "bg-red-700 text-white" : "bg-white text-slate-700 hover:bg-slate-50"
            }`}
            data-testid="restore-mode-replace"
          >
            {t("Replace (wipe + restore)")}
          </button>
        </div>
      </div>

      {/* File input (source=file) */}
      {source === "file" && (
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
              <><Upload className="w-4 h-4 mr-1" /> {t("Pick backup .zip")}</>
            )}
          </Button>
          <span className="text-xs text-slate-500">
            {t("≤ 500 MB · must be a backup produced by “Download Full Backup”")}
          </span>
        </div>
      )}

      {/* R2 picker (source=r2) */}
      {source === "r2" && (
        <div className="mt-4" data-testid="restore-r2-picker">
          {archives === null && (
            <div className="flex items-center gap-2 text-xs text-slate-500 py-3">
              <Loader2 className="w-4 h-4 animate-spin" /> {t("Loading R2 archives…")}
            </div>
          )}
          {archives && archives.configured === false && (
            <div className="bg-amber-50 border-2 border-amber-300 rounded-md p-3 text-xs text-amber-900">
              {t("R2 not configured on this deploy. Cloud archive restore is unavailable.")}
            </div>
          )}
          {archives && archives.configured !== false && (archives.backups || []).length === 0 && (
            <div className="bg-slate-50 border-2 border-dashed border-slate-300 rounded-md p-3 text-xs text-slate-600">
              No archives in R2 yet. Trigger one from the Cloud Archives panel above first.
            </div>
          )}
          {archives && (archives.backups || []).length > 0 && (
            <div className="flex items-center gap-3 flex-wrap">
              <select
                value={pickedKey}
                onChange={(e) => setPickedKey(e.target.value)}
                className="h-10 px-3 border-2 border-slate-300 rounded font-mono text-xs bg-white max-w-full"
                data-testid="restore-r2-select"
              >
                <option value="">— Pick a cloud archive —</option>
                {archives.backups.map((b) => (
                  <option key={b.key} value={b.key}>
                    {`${b.filename} · ${formatPlatformDate(b.last_modified)}`}
                  </option>
                ))}
              </select>
              <Button
                onClick={restoreFromR2}
                disabled={!pickedKey || fetchingR2 || busy}
                className={`h-10 px-4 font-bold uppercase tracking-wide text-xs disabled:bg-slate-400 ${
                  mode === "replace"
                    ? "bg-red-700 hover:bg-red-800 text-white"
                    : "bg-orange-600 hover:bg-orange-700 text-white"
                }`}
                data-testid="restore-r2-go-btn"
              >
                {fetchingR2 ? (
                  <><Loader2 className="w-4 h-4 animate-spin mr-1" /> Fetching…</>
                ) : busy ? (
                  <><Loader2 className="w-4 h-4 animate-spin mr-1" /> Restoring…</>
                ) : (
                  <><CloudDownload className="w-4 h-4 mr-1" /> Restore from R2</>
                )}
              </Button>
              <span className="text-xs text-slate-500">
                Streams the archive from Cloudflare → applies via the same restore pipeline
              </span>
            </div>
          )}
        </div>
      )}

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
            existing rows are overwritten with the backup&apos;s copy, new rows are inserted,
            and anything not in the backup is left untouched. Safe to run repeatedly.
          </>
        ) : (
          <>
            <strong>Replace mode</strong> — every collection found in the .zip is <strong>wiped first</strong>,
            then repopulated from the backup. Any records added since the backup will be lost.
            Requires typing <strong>REPLACE</strong> and acknowledging backup safety to confirm.
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
              the backup&apos;s rows. Anything created since the backup was generated will be
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
          <label className="flex items-center gap-2 text-sm text-red-900" data-testid="restore-backup-ack-label">
            <input
              type="checkbox"
              checked={backupAck}
              onChange={(e) => setBackupAck(e.target.checked)}
              data-testid="restore-backup-ack-checkbox"
            />
            I acknowledge backup and recovery expectations before replace mode.
          </label>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>Cancel</Button>
            <Button
              onClick={confirmReplace}
              disabled={confirmText !== "REPLACE" || !backupAck}
              className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide disabled:bg-slate-400"
              data-testid="restore-confirm-btn"
            >
              Replace & restore
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* SECOND GATE — admin password required before wipe */}
      <AdminPasswordConfirm
        open={passwordOpen}
        onOpenChange={(o) => {
          setPasswordOpen(o);
          if (!o) setPendingFile(null);
        }}
        title="Confirm REPLACE — wipe collections?"
        description={
          `Every collection inside ${pendingFile?.name || "this backup"} will be ` +
          `WIPED first, then repopulated from the .zip. Records added since the ` +
          `backup was generated will be permanently lost. Re-enter the admin ` +
          `password to authorize this destructive restore.`
        }
        confirmLabel="Wipe & restore"
        destructive
        onConfirm={passwordConfirmReplace}
        testId="restore-password-confirm"
      />
    </section>
  );
}
