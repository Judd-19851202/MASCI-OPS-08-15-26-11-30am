import React, { useEffect, useState } from "react";
import {
  Clock, Loader2, Play, Download, Trash2, HardDrive, Calendar,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import AdminPasswordConfirm from "@/components/AdminPasswordConfirm";

const fmtBytes = (n) => {
  if (!n) return "0 B";
  const u = ["B", "KB", "MB", "GB"];
  let i = 0; let v = n;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(v < 10 ? 1 : 0)} ${u[i]}`;
};

const fmtDate = (iso) => {
  try { return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }); }
  catch { return iso; }
};

/**
 * StoredBackupsPanel — on-server backup library.
 * Lists `/api/admin/backups`, supports Run-Now, Download, Delete.
 */
export default function StoredBackupsPanel() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loadingFile, setLoadingFile] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);

  const load = async () => {
    try {
      const r = await api.get("/admin/backups");
      setData(r.data);
    } catch (e) {
      toast.error("Failed to load backup list");
    }
  };

  useEffect(() => { load(); }, []);

  const runNow = async () => {
    if (busy) return;
    setBusy(true);
    toast.info("Building backup on server… 5–30 sec");
    try {
      const r = await api.post("/admin/backups/run-now");
      toast.success(
        `Backup saved — ${fmtBytes(r.data.size_bytes)} · ${r.data.records} records`,
      );
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Backup failed");
    } finally {
      setBusy(false);
    }
  };

  const download = async (f) => {
    setLoadingFile(f.filename);
    try {
      const r = await api.get(`/admin/backups/${encodeURIComponent(f.filename)}`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(new Blob([r.data], { type: "application/zip" }));
      const a = document.createElement("a");
      a.href = url; a.download = f.filename;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Download failed");
    } finally {
      setLoadingFile(null);
    }
  };

  const remove = (f) => setPendingDelete(f);

  const confirmRemove = async () => {
    if (!pendingDelete) return;
    try {
      await api.delete(`/admin/backups/${encodeURIComponent(pendingDelete.filename)}`);
      toast.success(`Deleted ${pendingDelete.filename}`);
      setPendingDelete(null);
      await load();
    } catch {
      toast.error("Delete failed");
      throw new Error("delete-failed");
    }
  };

  const sch = data?.schedule;

  return (
    <section
      className="mt-6 pt-5 border-t-2 border-slate-200"
      data-testid="stored-backups-panel"
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white">
            <HardDrive className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-display text-base sm:text-lg font-black tracking-tight text-slate-900">
              Stored Backups on Server
            </h3>
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
              Nightly .zip · Kept on disk · Admin-only
            </p>
          </div>
        </div>
        <Button
          onClick={runNow}
          disabled={busy}
          className="h-10 px-4 bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-xs disabled:bg-slate-400"
          data-testid="backup-run-now-btn"
        >
          {busy ? (
            <><Loader2 className="w-4 h-4 animate-spin mr-1" /> Running…</>
          ) : (
            <><Play className="w-4 h-4 mr-1" /> Run backup now</>
          )}
        </Button>
      </div>

      {/* Schedule strip */}
      {sch && (
        <div
          className="mt-4 bg-slate-50 border border-slate-200 rounded-md px-4 py-3 flex items-center gap-4 flex-wrap text-xs"
          data-testid="backup-schedule"
        >
          <span className="inline-flex items-center gap-1.5 font-mono uppercase tracking-[0.15em] text-slate-600 font-bold">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            {(sch.hours_utc && sch.hours_utc.length > 0
              ? sch.hours_utc.map((h) => String(h).padStart(2, "0") + ":00").join(" · ")
              : String(sch.hour_utc).padStart(2, "0") + ":00")} UTC
          </span>
          <span className="inline-flex items-center gap-1.5 font-mono uppercase tracking-[0.15em] text-slate-600 font-bold">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            Keep {sch.retention_days} days
          </span>
          <span className="font-mono text-[10px] text-slate-400 break-all">{sch.storage_dir}</span>
          <span className={`ml-auto inline-flex items-center gap-1 font-mono uppercase tracking-[0.15em] font-bold ${sch.enabled ? "text-emerald-700" : "text-red-700"}`}>
            <span className={`w-2 h-2 rounded-full ${sch.enabled ? "bg-emerald-500" : "bg-red-500"}`} />
            {sch.enabled ? "Enabled" : "Disabled"}
          </span>
        </div>
      )}

      {/* Backup list */}
      {data === null ? (
        <div className="flex justify-center py-8" data-testid="backups-loading">
          <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
        </div>
      ) : data.backups.length === 0 ? (
        <div
          className="mt-4 bg-white border-2 border-dashed border-slate-300 rounded-md p-6 text-center"
          data-testid="backups-empty"
        >
          <HardDrive className="w-8 h-8 mx-auto text-slate-300" />
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold mt-2">
            No stored backups yet
          </div>
          <p className="text-xs text-slate-600 mt-1">
            The next scheduled backup will appear at{" "}
            {sch?.hours_utc && sch.hours_utc.length > 0
              ? sch.hours_utc.map((h) => String(h).padStart(2, "0") + ":00").join(" or ")
              : String(sch?.hour_utc ?? 2).padStart(2, "0") + ":00"}{" "}
            UTC. Click <strong>Run backup now</strong> to generate one immediately.
          </p>
        </div>
      ) : (
        <div className="mt-4 bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-4 py-2 bg-slate-50 border-b-2 border-slate-100 flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
              {data.count} {data.count === 1 ? "backup" : "backups"} · {fmtBytes(data.total_bytes)} total
            </span>
          </div>
          <ul className="divide-y divide-slate-100" data-testid="backups-list">
            {data.backups.map((f) => (
              <li
                key={f.filename}
                className="px-4 py-3 flex items-center gap-3"
                data-testid={`backup-row-${f.filename}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="font-mono text-sm text-slate-900 font-bold truncate">{f.filename}</div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-500 mt-0.5">
                    {fmtDate(f.created_at)} · {fmtBytes(f.size_bytes)}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => download(f)}
                  disabled={loadingFile === f.filename}
                  className="h-8 text-xs font-bold uppercase tracking-wide border-2"
                  data-testid={`backup-download-${f.filename}`}
                >
                  {loadingFile === f.filename ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <><Download className="w-3 h-3 mr-1" /> Download</>
                  )}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => remove(f)}
                  className="h-8 text-xs font-bold uppercase tracking-wide border-2 border-slate-300 hover:border-red-600 hover:text-red-700"
                  data-testid={`backup-delete-${f.filename}`}
                  title="Delete"
                >
                  <Trash2 className="w-3 h-3" />
                </Button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <AdminPasswordConfirm
        open={!!pendingDelete}
        onOpenChange={(o) => !o && setPendingDelete(null)}
        title={`Delete ${pendingDelete?.filename}?`}
        description={
          `This backup .zip will be permanently removed from the server. ` +
          `It cannot be recovered unless you previously downloaded a copy. ` +
          `Live database records are NOT touched — only this archive is deleted.`
        }
        confirmLabel="Yes, delete backup"
        destructive
        onConfirm={confirmRemove}
        testId="stored-backup-delete-confirm"
      />

      <p className="mt-3 text-[11px] text-slate-500 leading-relaxed">
        Scheduled backups run at{" "}
        {sch?.hours_utc && sch.hours_utc.length > 0
          ? sch.hours_utc.map((h) => String(h).padStart(2, "0") + ":00").join(" and ") +
            " UTC (" +
            (sch.hours_utc.length > 1 ? "two off-site recovery points per day" : "once per day") +
            ")"
          : "once daily at " + String(sch?.hour_utc ?? 2).padStart(2, "0") + ":00 UTC"}
        . Files older than {sch?.retention_days ?? 14} days are auto-deleted. For off-site redundancy, download
        the latest zip to your office NAS or shared drive periodically.
      </p>
    </section>
  );
}
