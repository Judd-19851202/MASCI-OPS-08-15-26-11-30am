import React, { useEffect, useState } from "react";
import {
  Cloud,
  CloudOff,
  CloudDownload,
  Loader2,
  Play,
  Calendar,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const fmtBytes = (n) => {
  if (!n) return "0 B";
  const u = ["B", "KB", "MB", "GB"];
  let i = 0; let v = n;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(v < 10 ? 1 : 0)} ${u[i]}`;
};

const fmtDate = (iso) => {
  try {
    return formatPlatformTime(iso);
  } catch { return iso; }
};

/**
 * CloudArchivesPanel — Cloudflare R2 cloud backup library.
 *
 * Lists `/api/admin/backups-list-r2` (complete archives in R2 with
 * inlined photos), supports a one-click manual rebuild via
 * `POST /api/admin/backups/run-complete-now`, and renders click-to-download
 * presigned URLs (valid 7 days each).
 *
 * Mirrors StoredBackupsPanel's visual language so the two libraries
 * (on-server slim + cloud complete) read as a pair.
 */
export default function CloudArchivesPanel() {
  const [data, setData] = useState(null);
  const [state, setState] = useState(null);
  const [busy, setBusy] = useState(false);

  const loadList = async () => {
    try {
      const r = await api.get("/admin/backups-list-r2", { params: { limit: 50 } });
      setData(r.data);
    } catch (e) {
      // 400 means R2 isn't configured; render the disabled view instead of toasting.
      if (e?.response?.status === 400) {
        setData({ configured: false, count: 0, backups: [] });
      } else {
        toast.error("Could not load cloud archives. Try again.");
      }
    }
  };

  const loadState = async () => {
    try {
      const r = await api.get("/admin/backups-complete-r2-state");
      setState(r.data);
    } catch { /* non-fatal */ }
  };

  useEffect(() => {
    loadList();
    loadState();
  }, []);

  // Poll while a manual build is in-flight so the UI updates without
  // a manual refresh.
  useEffect(() => {
    if (!state?.in_progress) return undefined;
    const id = setInterval(async () => {
      await loadState();
      await loadList();
    }, 4000);
    return () => clearInterval(id);
  }, [state?.in_progress]);

  const runNow = async () => {
    if (busy) return;
    setBusy(true);
    toast.info("Building complete archive → R2… ~30–60 sec");
    try {
      const r = await api.post("/admin/backups/run-complete-now");
      if (r.data.accepted) {
        await loadState();
      }
    } catch (e) {
      toast.error(operationalError(e, "Build failed"));
    } finally {
      setBusy(false);
    }
  };

  // R2 is not configured on this deploy → render an explanatory empty
  // state instead of an error.
  const r2Disabled = data && data.configured === false;
  const nightlyDate = state?.nightly_last_date;
  const nightlyLast = state?.nightly_last;
  const inFlight = state?.in_progress;
  const r2Hour = state?.r2_full_hour_utc ?? 3;
  const last = state?.last;

  return (
    <section
      className="mt-6 pt-5 border-t-2 border-slate-200"
      data-testid="cloud-archives-panel"
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-orange-600 text-white">
            {r2Disabled ? <CloudOff className="w-5 h-5" /> : <Cloud className="w-5 h-5" />}
          </div>
          <div>
            <h3 className="font-display text-base sm:text-lg font-black tracking-tight text-slate-900">
              Cloud Archives · Cloudflare R2
            </h3>
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
              Nightly complete archive · Mongo + every photo · Self-contained
            </p>
          </div>
        </div>
        {!r2Disabled && (
          <Button
            onClick={runNow}
            disabled={busy || inFlight}
            className="h-10 px-4 bg-orange-600 hover:bg-orange-700 text-white font-bold uppercase tracking-wide text-xs disabled:bg-slate-400"
            data-testid="cloud-archive-run-now-btn"
          >
            {(busy || inFlight) ? (
              <><Loader2 className="w-4 h-4 animate-spin mr-1" /> Building…</>
            ) : (
              <><Play className="w-4 h-4 mr-1" /> Build complete archive now</>
            )}
          </Button>
        )}
      </div>

      {/* Disabled state — R2 not configured */}
      {r2Disabled && (
        <div
          className="mt-4 bg-amber-50 border-2 border-amber-300 rounded-md p-4"
          data-testid="cloud-archives-disabled"
        >
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-amber-900 font-bold">
            R2 not configured
          </div>
          <p className="text-xs text-amber-900 mt-1 leading-relaxed">
            Cloud archives are off because Cloudflare R2 credentials aren&apos;t
            set in the deployment environment. Add{" "}
            <code className="bg-white px-1 rounded">S3_ENDPOINT_URL</code>,{" "}
            <code className="bg-white px-1 rounded">S3_BUCKET</code>,{" "}
            <code className="bg-white px-1 rounded">S3_ACCESS_KEY</code>,{" "}
            <code className="bg-white px-1 rounded">S3_SECRET_KEY</code>{" "}
            and redeploy.
          </p>
        </div>
      )}

      {/* Schedule + last run strip */}
      {!r2Disabled && (
        <div
          className="mt-4 bg-orange-50 border-2 border-orange-200 rounded-md px-4 py-3 flex items-center gap-4 flex-wrap text-xs"
          data-testid="cloud-archives-schedule"
        >
          <span className="inline-flex items-center gap-1.5 font-mono uppercase tracking-[0.15em] text-orange-900 font-bold">
            <Calendar className="w-3.5 h-3.5 text-orange-500" />
            Nightly {String(r2Hour).padStart(2, "0")}:00 UTC
          </span>
          {nightlyDate ? (
            <span className="inline-flex items-center gap-1.5 font-mono uppercase tracking-[0.15em] text-emerald-700 font-bold">
              <ShieldCheck className="w-3.5 h-3.5" />
              Last nightly: {nightlyDate}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 font-mono uppercase tracking-[0.15em] text-slate-500">
              Last nightly: never (waiting for first run)
            </span>
          )}
          <button
            type="button"
            onClick={() => { loadList(); loadState(); }}
            className="ml-auto inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.15em] text-slate-500 hover:text-slate-900 font-bold"
            data-testid="cloud-archives-refresh-btn"
          >
            <RefreshCw className="w-3 h-3" />
            Refresh
          </button>
        </div>
      )}

      {/* In-flight build banner */}
      {!r2Disabled && inFlight && (
        <div
          className="mt-3 bg-blue-50 border-2 border-blue-200 rounded-md px-4 py-2.5 text-xs flex items-center gap-2"
          data-testid="cloud-archive-in-flight"
        >
          <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-700" />
          <span className="text-blue-900 font-medium">
            Building complete archive… typically 30–90 sec on production.
          </span>
        </div>
      )}

      {/* Last manual run result */}
      {!r2Disabled && last && last.outcome && last.outcome !== "in-progress" && (
        <div
          className={`mt-3 border-2 rounded-md px-4 py-2.5 text-xs flex items-center gap-2 ${
            last.outcome === "ok"
              ? "bg-emerald-50 border-emerald-200 text-emerald-900"
              : "bg-red-50 border-red-200 text-red-900"
          }`}
          data-testid="cloud-archive-last-result"
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span className="font-medium">
            Last manual build:{" "}
            {last.outcome === "ok"
              ? `OK · ${last.filename} (${fmtBytes(last.size_bytes)})`
              : last.outcome}
          </span>
        </div>
      )}

      {/* R2 archive list */}
      {!r2Disabled && data === null && (
        <div className="flex justify-center py-8" data-testid="cloud-archives-loading">
          <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
        </div>
      )}

      {!r2Disabled && data && (data.backups || []).length === 0 && (
        <div
          className="mt-4 bg-white border-2 border-dashed border-slate-300 rounded-md p-6 text-center"
          data-testid="cloud-archives-empty"
        >
          <Cloud className="w-8 h-8 mx-auto text-slate-300" />
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold mt-2">
            No archives in R2 yet
          </div>
          <p className="text-xs text-slate-600 mt-1">
            The next nightly build at {String(r2Hour).padStart(2, "0")}:00 UTC
            will land here. Click <strong>Build complete archive now</strong>{" "}
            to generate one immediately.
          </p>
        </div>
      )}

      {!r2Disabled && data && (data.backups || []).length > 0 && (
        <div className="mt-4 bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-4 py-2 bg-slate-50 border-b-2 border-slate-100 flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
              {data.count} {data.count === 1 ? "archive" : "archives"} in R2
            </span>
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-400">
              Links valid 7 days
            </span>
          </div>
          <ul className="divide-y divide-slate-100" data-testid="cloud-archives-list">
            {data.backups.map((f) => (
              <li
                key={f.key}
                className="px-4 py-3 flex items-center gap-3"
                data-testid={`cloud-archive-row-${f.filename}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="font-mono text-sm text-slate-900 font-bold truncate">
                    {f.filename}
                  </div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-500 mt-0.5">
                    {fmtDate(f.last_modified)} · {fmtBytes(f.size_bytes)} · r2:/{f.key}
                  </div>
                </div>
                <a
                  href={f.download_url || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="h-8 px-3 inline-flex items-center gap-1 text-xs font-bold uppercase tracking-wide border-2 border-orange-600 text-orange-700 hover:bg-orange-50 rounded-md"
                  data-testid={`cloud-archive-download-${f.filename}`}
                >
                  <CloudDownload className="w-3 h-3" />
                  Download
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="mt-3 text-[11px] text-slate-500 leading-relaxed">
        Complete archives include every record AND every photo (fetched
        from R2 and inlined), so the zip is fully self-contained — restore
        the entire platform from this one file even if Cloudflare R2
        becomes unreachable. Nightly build runs at{" "}
        {String(r2Hour).padStart(2, "0")}:00 UTC. Set{" "}
        <code className="bg-slate-100 px-1 rounded">BACKUP_R2_FULL_HOUR_UTC</code>{" "}
        in the deploy env to change the hour. Download links above are
        Cloudflare R2 presigned URLs — valid 7 days, no admin token needed
        to share with IT.
      </p>
    </section>
  );
}
