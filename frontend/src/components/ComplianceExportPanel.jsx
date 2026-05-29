import React, { useEffect, useState, useMemo } from "react";
import { Download, FileSpreadsheet, Loader2, Archive } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { isAdmin } from "@/lib/adminAuth";
import { toast } from "sonner";
import { todayLocalIso, toLocalIso } from "@/lib/dateUtils";
import RestoreBackupPanel from "@/components/RestoreBackupPanel";
import StoredBackupsPanel from "@/components/StoredBackupsPanel";

// First day of current month + today (yyyy-mm-dd) — handy default range.
// All helpers use LOCAL date components to avoid the UTC-rollover bug
// where a default date renders as "tomorrow" for east-of-UTC users.
const todayIso = () => todayLocalIso();
const firstOfMonthIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
};
const firstOfPriorMonthIso = () => {
  const d = new Date();
  d.setDate(1);
  d.setMonth(d.getMonth() - 1);
  return toLocalIso(d);
};
const lastOfPriorMonthIso = () => {
  const d = new Date();
  d.setDate(0); // last day of prior month
  return toLocalIso(d);
};

const KINDS = [
  { key: "inspections", label: "Site Inspections" },
  { key: "meetings", label: "Safety Meetings" },
  { key: "jhas", label: "JHPs" },
  { key: "incidents", label: "Incident Reports" },
  { key: "daily-reports", label: "Daily Job Reports" },
  { key: "equipment-inspections", label: "Equipment Pre-Op" },
];

// Fetch a CSV blob via authenticated XHR (we can't use a plain <a download>
// because admin requires the X-Admin-Token header).
async function downloadCsv(kind, start, end, label) {
  try {
    const params = new URLSearchParams({ kind });
    if (start) params.append("start", start);
    if (end) params.append("end", end);
    const res = await api.get(`/exports/csv?${params.toString()}`, {
      responseType: "blob",
    });
    const cd = res.headers["content-disposition"] || "";
    const m = cd.match(/filename="?([^";]+)"?/i);
    const fname = m ? m[1] : `MASCI_${kind}_${todayIso()}.csv`;
    const url = URL.createObjectURL(new Blob([res.data], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = fname;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    const count = res.headers["x-record-count"] || "?";
    toast.success(`Exported ${count} ${label}`);
  } catch (e) {
    console.error(e);
    toast.error("Export failed — check console");
  }
}

export default function ComplianceExportPanel({ hideBackupTools = false } = {}) {
  const [start, setStart] = useState(firstOfMonthIso());
  const [end, setEnd] = useState(todayIso());
  const [counts, setCounts] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloadingAll, setDownloadingAll] = useState(false);
  const [fullBackup, setFullBackup] = useState(false);

  const downloadFullBackup = async () => {
    if (fullBackup) return;
    setFullBackup(true);
    toast.info("Building full backup… this can take 30 sec for large jobs");
    try {
      const res = await api.get("/exports/full-backup", { responseType: "blob" });
      const cd = res.headers["content-disposition"] || "";
      const m = cd.match(/filename="?([^";]+)"?/i);
      const fname = m ? m[1] : `MASCI_full_backup_${todayIso()}.zip`;
      const url = URL.createObjectURL(new Blob([res.data], { type: "application/zip" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = fname;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      const count = res.headers["x-record-count"] || "?";
      const bytes = parseInt(res.headers["x-backup-size-bytes"] || "0", 10);
      const mb = bytes ? (bytes / (1024 * 1024)).toFixed(1) : "?";
      toast.success(`Full backup downloaded — ${count} records · ${mb} MB`);
    } catch (e) {
      console.error(e);
      toast.error("Full backup failed — check console");
    } finally {
      setFullBackup(false);
    }
  };

  const refresh = async (s = start, e = end) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (s) params.append("start", s);
      if (e) params.append("end", e);
      const r = await api.get(`/exports/summary?${params.toString()}`);
      setCounts(r.data);
    } catch {
      setCounts(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const total = counts?.total ?? 0;

  const presets = useMemo(
    () => [
      {
        key: "month-to-date",
        label: "Month to Date",
        start: firstOfMonthIso(),
        end: todayIso(),
      },
      {
        key: "prior-month",
        label: "Prior Month",
        start: firstOfPriorMonthIso(),
        end: lastOfPriorMonthIso(),
      },
      {
        key: "ytd",
        label: "Year to Date",
        start: `${new Date().getFullYear()}-01-01`,
        end: todayIso(),
      },
      { key: "all-time", label: "All Time", start: "", end: "" },
    ],
    []
  );

  const applyPreset = (p) => {
    setStart(p.start);
    setEnd(p.end);
    refresh(p.start, p.end);
  };

  const exportAll = async () => {
    setDownloadingAll(true);
    try {
      for (const k of KINDS) {
        if ((counts?.counts?.[k.key] ?? 0) > 0) {
          // Slight delay between downloads so the browser doesn't block them
          // eslint-disable-next-line no-await-in-loop
          await downloadCsv(k.key, start, end, k.label);
          // eslint-disable-next-line no-await-in-loop
          await new Promise((r) => setTimeout(r, 400));
        }
      }
      toast.success("All exports complete");
    } finally {
      setDownloadingAll(false);
    }
  };

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-5 sm:p-6 mb-8"
      data-testid="compliance-export-panel"
    >
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-display text-lg sm:text-xl font-black tracking-tight text-slate-900">
              Compliance Export
            </h2>
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
              CSV exports for monthly OSHA / DOT review
            </p>
          </div>
        </div>
        <Button
          onClick={exportAll}
          disabled={downloadingAll || total === 0}
          className="h-10 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs disabled:bg-slate-300"
          data-testid="export-all-btn"
        >
          {downloadingAll ? (
            <Loader2 className="w-4 h-4 animate-spin mr-1" />
          ) : (
            <Download className="w-4 h-4 mr-1" />
          )}
          Export All ({total})
        </Button>
      </div>

      {/* Preset chips */}
      <div className="mt-5 flex items-center gap-2 flex-wrap">
        {presets.map((p) => (
          <button
            key={p.key}
            type="button"
            onClick={() => applyPreset(p)}
            className="px-3 py-1.5 rounded font-mono text-[10px] uppercase tracking-[0.15em] font-bold border-2 border-slate-300 bg-white text-slate-700 hover:border-slate-900 hover:text-slate-900 transition-colors"
            data-testid={`preset-${p.key}`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Date inputs */}
      <div className="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4 items-end">
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
            Start date
          </Label>
          <Input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            onBlur={() => refresh()}
            className="mt-1 h-10 border-2 border-slate-300"
            data-testid="export-start-date"
          />
        </div>
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
            End date
          </Label>
          <Input
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            onBlur={() => refresh()}
            className="mt-1 h-10 border-2 border-slate-300"
            data-testid="export-end-date"
          />
        </div>
        <Button
          onClick={() => refresh()}
          variant="outline"
          className="h-10 border-2 border-slate-300 hover:border-slate-900"
          data-testid="export-refresh"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin mr-1" />
          ) : null}
          Refresh counts
        </Button>
      </div>

      {/* Per-kind download grid */}
      <div className="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        {KINDS.map((k) => {
          const n = counts?.counts?.[k.key] ?? 0;
          const disabled = n === 0;
          return (
            <button
              key={k.key}
              type="button"
              disabled={disabled}
              onClick={() => downloadCsv(k.key, start, end, k.label)}
              className={`flex items-center justify-between gap-3 px-4 py-3 rounded border-2 transition-colors text-left ${
                disabled
                  ? "border-slate-200 bg-slate-50 cursor-not-allowed"
                  : "border-slate-300 bg-white hover:border-red-700 hover:bg-red-50"
              }`}
              data-testid={`export-kind-${k.key}`}
            >
              <div className="min-w-0">
                <div
                  className={`font-bold text-sm truncate ${
                    disabled ? "text-slate-400" : "text-slate-900"
                  }`}
                >
                  {k.label}
                </div>
                <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-slate-500 mt-0.5">
                  {n} record{n === 1 ? "" : "s"} in range
                </div>
              </div>
              <Download
                className={`w-4 h-4 shrink-0 ${
                  disabled ? "text-slate-300" : "text-red-700"
                }`}
              />
            </button>
          );
        })}
      </div>

      <p className="mt-4 text-xs text-slate-500 italic">
        CSVs include every field except photos and signatures. Open in Excel,
        Google Sheets, or hand to your OSHA / DOT auditor.
      </p>

      {/* ---------- Full off-site backup (admin-only) ---------- */}
      {!hideBackupTools && isAdmin() && (
        <div className="mt-6 pt-5 border-t-2 border-slate-200">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-3">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-red-700 text-white">
                <Archive className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-display text-base sm:text-lg font-black tracking-tight text-slate-900">
                  Full Off-Site Backup
                </h3>
                <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
                  Single .zip · CSVs + JSON + PDFs + photos
                </p>
              </div>
            </div>
            <Button
              onClick={downloadFullBackup}
              disabled={fullBackup}
              className="h-10 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs disabled:bg-slate-400"
              data-testid="full-backup-btn"
            >
              {fullBackup ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-1" /> Building…
                </>
              ) : (
                <>
                  <Archive className="w-4 h-4 mr-1" /> Download Full Backup
                </>
              )}
            </Button>
          </div>
          <p className="mt-3 text-xs text-slate-600 leading-relaxed">
            One dated .zip covering <strong>everything</strong> on the system: every safety record
            (CSVs + raw JSON + PDFs + photos + signatures) across all 6 modules,
            plus the equipment-unit / JHP-plan / trench-box registries and employees /
            suppliers seed data. Drop the .zip on your office NAS or shared drive after
            download. Restore it anytime from the panel below.
          </p>
        </div>
      )}

      {/* ---------- Stored Backups + Restore (admin-only) ---------- */}
      {!hideBackupTools && isAdmin() && (
        <>
          <StoredBackupsPanel />
          <RestoreBackupPanel />
        </>
      )}
    </section>
  );
}
