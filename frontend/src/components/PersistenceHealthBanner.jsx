import React, { useEffect, useState } from "react";
import { AlertTriangle, ShieldCheck, Download, Loader2, Mail, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

/**
 * PersistenceHealthBanner — prominent warning when the app is running with
 * an in-container MongoDB (ephemeral — wiped on every Emergent redeploy).
 *
 * Renders NOTHING when Mongo is Atlas or another external service.
 */
export default function PersistenceHealthBanner() {
  const [status, setStatus] = useState(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/admin/persistence-check");
        if (alive) setStatus(r.data);
      } catch {
        /* ignore */
      }
    })();
    return () => { alive = false; };
  }, []);

  const preDeployBackup = async () => {
    if (downloading) return;
    setDownloading(true);
    toast.info("Building backup + emailing to " + (status.backup_email_to || "you") + "…");
    try {
      // Build + email via the run-now endpoint (which also writes the zip to disk)
      const r1 = await api.post("/admin/backups/run-now");
      // And download it right here, right now, so the user has a local copy too
      const r2 = await api.get(
        `/admin/backups/${encodeURIComponent(r1.data.filename)}`,
        { responseType: "blob" },
      );
      const url = URL.createObjectURL(new Blob([r2.data], { type: "application/zip" }));
      const a = document.createElement("a");
      a.href = url; a.download = r1.data.filename;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
      const emailedTo = r1.data.emailed_to;
      if (emailedTo) {
        toast.success(`Backup saved + emailed to ${emailedTo} + downloaded.`);
      } else {
        toast.success("Backup saved + downloaded.");
        toast.warning("Email step skipped — check BACKUP_EMAIL_TO + RESEND_API_KEY.");
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Backup failed");
    } finally {
      setDownloading(false);
    }
  };

  if (!status) return null;

  // Happy path — Atlas / external Mongo, no banner needed
  if (!status.mongo_is_local) {
    return (
      <div
        className="bg-emerald-50 border-l-4 border-emerald-600 text-emerald-900 px-4 py-3 rounded-r-md mb-6"
        data-testid="persistence-health-ok"
      >
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="flex-1 text-sm">
            <div className="font-bold font-display">Persistent database connected</div>
            <div className="text-emerald-800 mt-0.5">
              Mongo host: <code className="font-mono">{status.mongo_host}</code>
              {status.mongo_is_atlas && " (MongoDB Atlas)"}. Redeploys will not wipe your data.
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Danger zone
  return (
    <div
      className="bg-red-50 border-2 border-red-700 rounded-md px-4 py-4 mb-6"
      data-testid="persistence-health-warn"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-6 h-6 text-red-700 shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="font-display font-black text-red-900 text-base sm:text-lg leading-tight">
            ⚠ Your data will be deleted on the next redeploy
          </div>
          <p className="text-sm text-red-900 mt-1.5 leading-relaxed">
            MongoDB is running <strong>inside this container</strong> (<code className="font-mono text-xs">{status.mongo_host}</code>),
            which means every new deploy destroys your database. <strong>Before you redeploy next time,
            always click the button below to grab + email a full backup</strong>, or you will lose
            everything created since the last nightly backup.
          </p>
          <p className="text-sm text-red-900 mt-2 leading-relaxed">
            <strong>Permanent fix:</strong> switch the production app to <strong>MongoDB Atlas</strong> (free tier,
            15-min setup) — see the instructions your developer sent. Once the Atlas connection
            string is in your Emergent production env vars, this banner will turn green and
            redeploys become safe forever.
          </p>

          <div className="mt-4 flex flex-wrap gap-2 items-center">
            <Button
              onClick={preDeployBackup}
              disabled={downloading}
              className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs disabled:bg-slate-400"
              data-testid="pre-deploy-backup-btn"
            >
              {downloading ? (
                <><Loader2 className="w-4 h-4 animate-spin mr-1.5" /> Building + sending…</>
              ) : (
                <><Download className="w-4 h-4 mr-1.5" /> Backup + email + download NOW</>
              )}
            </Button>
            {status.backup_email_to ? (
              <span className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.15em] text-red-900 font-bold">
                <Mail className="w-3 h-3" /> Emails to {status.backup_email_to}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.15em] text-amber-700 font-bold">
                <Mail className="w-3 h-3" /> BACKUP_EMAIL_TO not set
              </span>
            )}
            <a
              href="https://www.mongodb.com/cloud/atlas/register"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.15em] text-red-700 hover:text-red-900 font-bold underline"
              data-testid="atlas-signup-link"
            >
              Sign up for MongoDB Atlas <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          {status.last_backup && (
            <div className="mt-3 text-[11px] font-mono text-red-900 opacity-75">
              Last on-server backup: <strong>{status.last_backup.filename}</strong> ·
              {" "}{new Date(status.last_backup.created_at).toLocaleString()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
