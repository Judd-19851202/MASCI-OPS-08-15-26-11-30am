// AdminSignatureMigrationPanel — admin tool to migrate base64 signatures
// out of MongoDB and into Cloudflare R2. Iter75.
//
// The R2 storage is already wired (photos shipped via iter64). This
// panel runs the same upload-and-rewrite flow over every signature
// field in every collection that stores forms with signatures. The
// rendered look stays identical (frontend uses resolvePhotoSrc;
// backend PDF renderers resolve photo:// refs at print time).

import React, { useEffect, useState } from "react";
import {
  Signature, Loader2, ShieldCheck, CloudUpload, AlertOctagon,
  RefreshCcw, Eye, Rocket,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import { toast } from "sonner";

function fmtKb(n) {
  if (!n) return "0";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}

export default function AdminSignatureMigrationPanel() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [lastRun, setLastRun] = useState(null);

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/signatures/status");
      setStatus(r.data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const runMigration = async (dryRun) => {
    if (!dryRun && !window.confirm(
      "This will move every remaining base64 signature out of the database " +
      "and into Cloudflare R2. Records will reference the new location going " +
      "forward. PDFs and View pages will continue to render the signatures " +
      "exactly as before. Continue?"
    )) return;
    setBusy(true);
    setLastRun(null);
    try {
      const r = await api.post(
        `/admin/signatures/migrate?dry_run=${dryRun}&limit=2000`,
      );
      setLastRun({ ...r.data, dry_run: dryRun });
      toast.success(
        dryRun
          ? `Dry run complete — ${r.data.migrated} signatures would be migrated`
          : `Migrated ${r.data.migrated} signatures (${r.data.failed} failed)`,
      );
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Migration failed");
    } finally {
      setBusy(false);
    }
  };

  const grand = status?.grand_total || {};
  const rows = status?.rows || [];
  const r2Ok = status?.r2_configured;

  return (
    <div
      className="border border-slate-200 rounded-md p-5 bg-white"
      data-testid="admin-signature-migration-panel"
    >
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-900 text-white shrink-0">
            <Signature className="w-6 h-6" />
          </div>
          <div>
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700 font-bold">
              Storage Optimization
            </span>
            <h3 className="font-display text-xl sm:text-2xl font-black mt-1 leading-none">
              Signature → Cloudflare R2 Migration
            </h3>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
              Moves remaining base64 signature blobs out of the database and into the same R2 bucket that already stores every job photo. The visible result is identical — pages and PDFs render the signature exactly as before — but database rows shrink, backups become readable, and the IT server-dump becomes useful.
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={refresh} disabled={loading} className="h-9" data-testid="sig-mig-refresh">
          {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <RefreshCcw className="w-4 h-4 mr-1" />}
          Refresh
        </Button>
      </div>

      {/* R2 health */}
      {status && (
        <div
          className={`mb-4 p-3 rounded border-2 ${r2Ok ? "border-emerald-300 bg-emerald-50" : "border-amber-300 bg-amber-50"}`}
          data-testid="sig-mig-r2-health"
        >
          <div className="flex items-center gap-2 text-sm font-bold">
            {r2Ok ? <ShieldCheck className="w-4 h-4 text-emerald-700" /> : <AlertOctagon className="w-4 h-4 text-amber-700" />}
            <span className={r2Ok ? "text-emerald-800" : "text-amber-800"}>
              {r2Ok ? "Cloudflare R2 connected and ready" : "Cloudflare R2 not configured — migration unavailable"}
            </span>
          </div>
        </div>
      )}

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <StatBox label="Records w/ signatures" value={grand.docs_with_sig} />
        <StatBox label="In Cloud (R2)" value={grand.cloud} accent="emerald" />
        <StatBox label="Still in DB" value={grand.base64} accent={grand.base64 > 0 ? "amber" : "slate"} />
        <StatBox label="DB bytes recoverable" value={fmtKb(grand.bytes)} accent={grand.bytes > 0 ? "amber" : "slate"} />
      </div>

      {/* Per-collection table */}
      <div className="overflow-x-auto mb-5">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
            <tr>
              <th className="text-left px-3 py-2">Collection</th>
              <th className="text-right px-3 py-2">Total</th>
              <th className="text-right px-3 py-2">w/ Signature</th>
              <th className="text-right px-3 py-2">Cloud</th>
              <th className="text-right px-3 py-2">Base64</th>
              <th className="text-right px-3 py-2">DB Bytes</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="text-center py-6 text-slate-500"><Loader2 className="w-5 h-5 mx-auto animate-spin" /></td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-6 text-slate-500">
                No signatures detected — every record is already either signature-less or migrated.
              </td></tr>
            ) : rows.map((r) => (
              <tr key={r.collection} className="border-t border-slate-100">
                <td className="px-3 py-2 font-mono text-xs">{r.collection}</td>
                <td className="px-3 py-2 text-right">{r.total_records}</td>
                <td className="px-3 py-2 text-right">{r.records_with_signature}</td>
                <td className="px-3 py-2 text-right text-emerald-700">{r.cloud}</td>
                <td className={`px-3 py-2 text-right ${r.base64 > 0 ? "text-amber-700 font-bold" : ""}`}>{r.base64}</td>
                <td className="px-3 py-2 text-right font-mono text-xs">{fmtKb(r.bytes_in_db)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2 items-center">
        <Button
          variant="outline"
          onClick={() => runMigration(true)}
          disabled={busy || !r2Ok || grand.base64 === 0}
          data-testid="sig-mig-dryrun"
        >
          {busy ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Eye className="w-4 h-4 mr-1" />}
          Dry Run
        </Button>
        <Button
          onClick={() => runMigration(false)}
          disabled={busy || !r2Ok || grand.base64 === 0}
          className="bg-slate-900 hover:bg-slate-800 text-white"
          data-testid="sig-mig-commit"
        >
          {busy ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Rocket className="w-4 h-4 mr-1" />}
          Migrate Now
        </Button>
        {grand.base64 === 0 && grand.cloud > 0 && (
          <span className="inline-flex items-center gap-1 text-xs font-bold uppercase tracking-wider text-emerald-700 ml-2">
            <CloudUpload className="w-3.5 h-3.5" /> All signatures live in R2 — nothing left to migrate.
          </span>
        )}
      </div>

      {/* Last run result */}
      {lastRun && (
        <div
          className={`mt-4 p-3 rounded border-2 ${lastRun.failed > 0 ? "border-amber-300 bg-amber-50" : "border-emerald-300 bg-emerald-50"}`}
          data-testid="sig-mig-result"
        >
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
            Last {lastRun.dry_run ? "dry run" : "migration"} result
          </div>
          <div className="mt-1 text-sm">
            <strong>{lastRun.migrated}</strong> signatures{" "}
            {lastRun.dry_run ? "would be " : ""}migrated ·{" "}
            <strong className={lastRun.failed > 0 ? "text-amber-700" : ""}>{lastRun.failed}</strong> failed ·{" "}
            <strong>{fmtKb(lastRun.bytes_recovered)}</strong> recovered
          </div>
          {(lastRun.collections || []).length > 0 && (
            <div className="mt-2 text-xs font-mono text-slate-600">
              {lastRun.collections.map((c) =>
                `${c.collection}: ${c.signatures_migrated} (${fmtKb(c.bytes_recovered)})`
              ).join(" · ")}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatBox({ label, value, accent }) {
  const cls = {
    amber: "border-amber-400 bg-amber-50",
    emerald: "border-emerald-300 bg-emerald-50",
    slate: "border-slate-200 bg-slate-50",
  }[accent || "slate"];
  return (
    <Card className={`border-2 ${cls} p-3`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
        {label}
      </div>
      <div className="font-display text-2xl font-black mt-1">{value ?? 0}</div>
    </Card>
  );
}
