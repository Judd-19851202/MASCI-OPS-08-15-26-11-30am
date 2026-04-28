import React, { useRef, useState } from "react";
import { Download, Upload, Loader2, Archive, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { toast } from "sonner";

/**
 * BackupHeroPanel — the ONLY thing most admins need to touch.
 *
 * Two giant buttons:
 *   🟥 BACKUP EVERYTHING  (download + email .zip)
 *   🟩 RESTORE FROM FILE  (upload .zip)
 *
 * Everything else — the compliance CSV exports, the stored-backups library,
 * the merge-vs-replace mode toggles — stays in the panels BELOW this hero
 * for advanced use. This panel is the "press this, you're safe" button.
 */
export default function BackupHeroPanel() {
  const [busyBackup, setBusyBackup] = useState(false);
  const [busyRestore, setBusyRestore] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingFile, setPendingFile] = useState(null);
  const fileRef = useRef(null);

  const backupNow = async () => {
    if (busyBackup) return;
    setBusyBackup(true);
    toast.info("Building your complete backup… ~30 seconds");
    try {
      // Fire the run-now (which also emails) + pull the zip in one shot
      const run = await api.post("/admin/backups/run-now");
      const dl = await api.get(
        `/admin/backups/${encodeURIComponent(run.data.filename)}`,
        { responseType: "blob" },
      );
      const url = URL.createObjectURL(new Blob([dl.data], { type: "application/zip" }));
      const a = document.createElement("a");
      a.href = url; a.download = run.data.filename;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
      const mb = (run.data.size_bytes / 1024 / 1024).toFixed(1);
      if (run.data.emailed_to) {
        toast.success(
          `✓ Backed up ${run.data.records} records · ${mb} MB · emailed to ${run.data.emailed_to} · downloaded`,
        );
      } else {
        toast.success(`✓ Backed up ${run.data.records} records · ${mb} MB · downloaded`);
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Backup failed — please try again");
      console.error(e);
    } finally {
      setBusyBackup(false);
    }
  };

  const onPickFile = (e) => {
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
    setPendingFile(f);
    setConfirmOpen(true);
    e.target.value = "";
  };

  const runRestore = async () => {
    if (!pendingFile) return;
    setConfirmOpen(false);
    setBusyRestore(true);
    toast.info("Restoring backup… ~30 seconds");
    const fd = new FormData();
    fd.append("file", pendingFile);
    fd.append("merge", "true");  // Always safe mode from the hero button
    try {
      const r = await api.post("/exports/restore", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success(
        `✓ Restored ${r.data.total_processed} records across ${Object.keys(r.data.collections || {}).length} collections`,
      );
    } catch (e) {
      const detail = e?.response?.data?.detail || "Restore failed";
      toast.error(typeof detail === "string" ? detail : "Restore failed — see console");
      console.error(e);
    } finally {
      setBusyRestore(false);
      setPendingFile(null);
    }
  };

  return (
    <section
      className="bg-white border-4 border-slate-900 rounded-md p-5 sm:p-6 mb-8 shadow-lg"
      data-testid="backup-hero-panel"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 rounded-md bg-slate-900 text-white flex items-center justify-center">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <h2 className="font-display text-xl sm:text-2xl font-black tracking-tight text-slate-900 leading-tight">
            Backup &amp; Restore Everything
          </h2>
          <p className="text-sm text-slate-600">
            Two buttons. Your whole MASCI Safety Hub — every form, every photo, every Crew Hub message.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* BACKUP button */}
        <button
          onClick={backupNow}
          disabled={busyBackup}
          className="group bg-red-700 hover:bg-red-800 active:bg-red-900 disabled:bg-slate-400 text-white rounded-md p-6 text-left transition-colors border-b-4 border-red-900 disabled:border-slate-500"
          data-testid="hero-backup-btn"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-md bg-white/15 flex items-center justify-center">
              {busyBackup ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <Download className="w-6 h-6" />
              )}
            </div>
            <div className="flex-1">
              <div className="font-display text-lg sm:text-xl font-black tracking-tight uppercase">
                {busyBackup ? "Building backup…" : "Backup Everything"}
              </div>
              <div className="text-xs font-mono uppercase tracking-[0.2em] text-red-200 mt-0.5">
                Step 1 · Do this before any redeploy
              </div>
            </div>
          </div>
          <p className="text-sm text-red-50 leading-relaxed">
            Downloads a single <code className="bg-white/20 px-1 rounded font-mono text-xs">.zip</code> containing
            every safety record, photo, signature, PDF, Crew Hub message, to-do, schedule, and doc.
            Also emails a copy to your inbox.
          </p>
        </button>

        {/* RESTORE button */}
        <button
          onClick={() => fileRef.current?.click()}
          disabled={busyRestore}
          className="group bg-emerald-700 hover:bg-emerald-800 active:bg-emerald-900 disabled:bg-slate-400 text-white rounded-md p-6 text-left transition-colors border-b-4 border-emerald-900 disabled:border-slate-500"
          data-testid="hero-restore-btn"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-md bg-white/15 flex items-center justify-center">
              {busyRestore ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <Upload className="w-6 h-6" />
              )}
            </div>
            <div className="flex-1">
              <div className="font-display text-lg sm:text-xl font-black tracking-tight uppercase">
                {busyRestore ? "Restoring…" : "Restore From File"}
              </div>
              <div className="text-xs font-mono uppercase tracking-[0.2em] text-emerald-200 mt-0.5">
                Step 2 · Use after a redeploy to get data back
              </div>
            </div>
          </div>
          <p className="text-sm text-emerald-50 leading-relaxed">
            Pick a MASCI backup <code className="bg-white/20 px-1 rounded font-mono text-xs">.zip</code> from your computer.
            Every record inside is merged into the live system. Safe — existing data isn't wiped.
          </p>
        </button>

        <input
          ref={fileRef}
          type="file"
          accept=".zip,application/zip"
          onChange={onPickFile}
          className="hidden"
          data-testid="hero-restore-file-input"
        />
      </div>

      <div className="mt-4 bg-slate-50 border-l-4 border-slate-400 rounded-r px-3 py-2 text-xs text-slate-700 leading-relaxed">
        <strong>The .zip is a normal file</strong> — you can open it in Windows Explorer or Mac Finder
        with no password, no special tool. Each safety record is inside as both a raw <code>.json</code> and a
        printable <code>.pdf</code>. Photos and signatures are embedded in the JSON. Safe to archive forever.
      </div>

      {/* Restore confirmation */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent data-testid="hero-restore-confirm-dialog">
          <DialogHeader>
            <DialogTitle className="font-display font-black flex items-center gap-2 text-emerald-700">
              <Upload className="w-5 h-5" />
              Restore from <span className="font-mono text-base">{pendingFile?.name}</span>?
            </DialogTitle>
            <DialogDescription>
              Every record inside this .zip will be merged into the live system — existing rows are
              overwritten with the backup's copy, new rows are added. Anything in the DB that isn't in
              the backup is left alone. This is safe to run.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => { setConfirmOpen(false); setPendingFile(null); }}>
              Cancel
            </Button>
            <Button
              onClick={runRestore}
              className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold uppercase tracking-wide"
              data-testid="hero-restore-confirm-btn"
            >
              Yes, restore it
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
