// AdminRecovery.jsx — Phase D · iter443 · Recovery Dashboard
//
// Single-screen recovery posture view. Polls the read-only snapshot
// endpoint every 30s. NO action buttons (per RECOVERY_DASHBOARD_SPEC.md
// §7 — Admin must navigate to /admin/system for actions).
//
// All data sourced from /api/admin/recovery/snapshot (cached server-side
// for 15s).
import React, { useEffect, useState, useCallback } from "react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { api } from "@/lib/api";
const POLL_MS = 30000;

const PILL_STYLES = {
  GREEN: "bg-emerald-100 text-emerald-800 border-emerald-300",
  AMBER: "bg-amber-100 text-amber-800 border-amber-300",
  RED: "bg-rose-100 text-rose-800 border-rose-300",
};

function fmtAge(minutes) {
  if (minutes == null) return "—";
  if (minutes < 1) return "< 1m";
  if (minutes < 60) return `${Math.round(minutes)} m`;
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return `${h}h ${m}m`;
}

function fmtTs(ts) {
  if (!ts) return "—";
  try {
    return new Date(ts).toISOString().replace("T", " ").slice(0, 19) + "Z";
  } catch {
    return ts;
  }
}

function Card({ title, status, children, testid }) {
  const ring =
    status === "GREEN"
      ? "ring-emerald-200"
      : status === "AMBER"
      ? "ring-amber-200"
      : status === "RED"
      ? "ring-rose-200"
      : "ring-slate-200";
  return (
    <div
      className={`rounded-lg bg-white p-4 ring-1 ${ring} shadow-sm`}
      data-testid={testid}
    >
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
        {title}
      </div>
      {children}
    </div>
  );
}

function Sparkline({ data, width = 600, height = 80 }) {
  if (!data || data.length === 0) {
    return (
      <div className="text-sm text-slate-400">No trend data available yet.</div>
    );
  }
  const xs = data.map((_, i) => i);
  const ys = data.map((d) => d.size_mb || 0);
  const maxY = Math.max(...ys) || 1;
  const minY = Math.min(...ys);
  const pad = 4;
  const sx = (x) =>
    pad + (x * (width - 2 * pad)) / Math.max(1, xs.length - 1);
  const sy = (y) =>
    height - pad - ((y - minY) * (height - 2 * pad)) / Math.max(1, maxY - minY);
  const pts = ys.map((y, i) => `${sx(i)},${sy(y)}`).join(" ");
  const last = data[data.length - 1];
  return (
    <div data-testid="archive-size-trend">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-20"
        preserveAspectRatio="none"
      >
        <polyline
          fill="none"
          stroke="rgb(15 118 110)"
          strokeWidth="2"
          points={pts}
        />
        {ys.map((y, i) => (
          <circle key={i} cx={sx(i)} cy={sy(y)} r="2" fill="rgb(15 118 110)" />
        ))}
      </svg>
      <div className="flex justify-between text-xs text-slate-500 mt-1">
        <span>{fmtTs(data[0]?.ts)}</span>
        <span>min {minY.toFixed(1)} · max {maxY.toFixed(1)} MB</span>
        <span>{fmtTs(last?.ts)}</span>
      </div>
    </div>
  );
}

export default function AdminRecovery() {
  const [snap, setSnap] = useState(null);
  const [backupTrust, setBackupTrust] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [r, trust] = await Promise.all([
        api.get("/admin/recovery/snapshot", { skipSessionStatus: true }),
        api.get("/admin/backup-trust-score", { skipSessionStatus: true }).catch(() => null),
      ]);
      setSnap(r.data);
      setBackupTrust(trust?.data || null);
      setErr(null);
    } catch (e) {
      setErr(String(e?.response?.data?.detail || e?.message || e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [load]);

  return (
    <LegacyAdminModernShell
      title="Recovery Posture"
      subtitle="Read-only recovery dashboard · polls every 30s."
      breadcrumb={[
        { label: "Storage & Recovery", to: "/admin/storage-recovery" },
        { label: "Recovery Posture" },
      ]}
      testidPrefix="admin-recovery"
    >
      <div className="mb-5 rounded-lg border border-slate-200 bg-white p-4">
        <p className="text-sm text-slate-600 leading-relaxed">
          Read-only recovery dashboard. Polls every 30s. For actions
          (trigger backup · run drill · restore from archive), open{" "}
          <a className="underline" href="/admin/operations-control">
            Operations Control
          </a>
          .
        </p>
      </div>
      {loading && (
        <div className="text-sm text-slate-500" data-testid="recovery-loading">
          Loading recovery posture…
        </div>
      )}
      {err && (
        <div
          className="rounded-md bg-rose-50 border border-rose-200 text-rose-700 p-3 text-sm"
          data-testid="recovery-error"
        >
          Failed to load snapshot: {err}
        </div>
      )}
      {snap && (
        <div className="space-y-4">
          {/* Hero pill */}
          <div
            className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-base font-semibold ${
              PILL_STYLES[snap.pill] || PILL_STYLES.AMBER
            }`}
            data-testid="recovery-pill"
          >
            <span>Recovery Posture:</span>
            <span>{snap.pill}</span>
            <span className="ml-2 text-xs font-normal opacity-70">
              ({fmtTs(snap.computed_at)})
            </span>
          </div>

          {/* Top row: last backup · last drill · backup age */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Card
              title="Last backup"
              status={snap.last_backup?.ok ? "GREEN" : "RED"}
              testid="card-last-backup"
            >
              {snap.last_backup ? (
                <div className="text-sm space-y-1">
                  <div className="font-mono text-xs break-all">
                    {snap.last_backup.filename}
                  </div>
                  <div>
                    <span className="font-semibold">{snap.last_backup.size_mb}</span> MB ·{" "}
                    <span className="font-semibold">
                      {snap.last_backup.records.toLocaleString()}
                    </span>{" "}
                    records · ok={String(snap.last_backup.ok)}
                  </div>
                  <div className="text-xs text-slate-500">
                    inlined_photos = {snap.last_backup.inlined_photos} · {fmtTs(snap.last_backup.ts)}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-slate-400">No backups yet.</div>
              )}
            </Card>

            <Card title="Last restore drill" status={snap.last_drill?.outcome === "ok" ? "GREEN" : "AMBER"} testid="card-last-drill">
              {snap.last_drill ? (
                <div className="text-sm space-y-1">
                  <div className="text-xs font-mono uppercase tracking-wide text-slate-500">
                    Representative namespace restore
                  </div>
                  <div className="font-semibold">
                    outcome: {snap.last_drill.outcome}
                  </div>
                  <div>
                    {(snap.last_drill.records || 0).toLocaleString()} records ·{" "}
                    {snap.last_drill.photos || 0} photos
                  </div>
                  <div className="text-xs text-slate-500">
                    {snap.last_drill.duration_min ? `${snap.last_drill.duration_min}m · ` : ""}
                    {fmtTs(snap.last_drill.ts)}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-slate-400">
                  No representative namespace restore drill on file.
                </div>
              )}
            </Card>

            <Card title="Backup age" status={
              snap.backup_age_minutes == null
                ? "RED"
                : snap.backup_age_minutes > 2 * snap.backup_age_target_minutes
                ? "RED"
                : snap.backup_age_minutes > snap.backup_age_target_minutes
                ? "AMBER"
                : "GREEN"
            } testid="card-backup-age">
              <div className="text-2xl font-bold">
                {fmtAge(snap.backup_age_minutes)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                target ≤ {fmtAge(snap.backup_age_target_minutes)}
              </div>
            </Card>

            <Card
              title="Backup Trust Score"
              status={(backupTrust?.score_band || "amber").toUpperCase()}
              testid="card-backup-trust-score"
            >
              <div className="space-y-1 text-sm" data-testid="backup-trust-score-panel">
                <div className="text-3xl font-bold text-slate-900">{backupTrust?.trust_score ?? "—"}</div>
                <div className="font-semibold text-slate-700">{backupTrust?.score_band_label || "Missing evidence"}</div>
                <div className="text-xs text-slate-500">{backupTrust?.score_reason || "Backup trust evidence not yet loaded."}</div>
                <div className="text-xs text-slate-500">
                  Production activation disabled: {String(backupTrust?.production_activation_disabled ?? true)}
                </div>
              </div>
            </Card>
          </div>

          {/* Row 2: RPO/RTO · archive count · bucket usage */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Card title="RPO / RTO" status={
              snap.rpo.status === "GREEN" && snap.rto.status === "GREEN" ? "GREEN" : "AMBER"
            } testid="card-rpo-rto">
              <div className="space-y-1 text-sm">
                <div>
                  RPO target: <span className="font-semibold">{snap.rpo.target_min}m</span> · actual:{" "}
                  <span className="font-semibold">{snap.rpo.actual_min == null ? "—" : `${snap.rpo.actual_min}m`}</span>{" "}
                  <span className="text-xs">({snap.rpo.status})</span>
                </div>
                <div>
                  RTO target: <span className="font-semibold">{snap.rto.target_min}m</span> · last drill:{" "}
                  <span className="font-semibold">
                    {snap.rto.last_drill_min == null ? "—" : `${snap.rto.last_drill_min}m`}
                  </span>{" "}
                  <span className="text-xs">({snap.rto.status})</span>
                </div>
              </div>
            </Card>

            <Card title="Archive count" status="GREEN" testid="card-archive-count">
              <div className="text-sm space-y-1">
                <div>
                  Total in R2: <span className="font-semibold">{snap.archive_count.r2_total}</span>
                </div>
                <div>
                  Last 7 d: <span className="font-semibold">{snap.archive_count.last_7d}</span> · Last 30 d:{" "}
                  <span className="font-semibold">{snap.archive_count.last_30d}</span>
                </div>
              </div>
            </Card>

            <Card title="Bucket usage" status={snap.bucket_usage.status} testid="card-bucket-usage">
              <div className="text-sm space-y-1">
                <div>
                  <span className="font-semibold">{snap.bucket_usage.gb}</span> GB
                </div>
                <div className="text-xs text-slate-500">
                  WARN ≥ {snap.bucket_usage.warn_gb} GB · ALERT ≥ {snap.bucket_usage.alert_gb} GB
                </div>
                <div className="text-xs text-slate-500">
                  Lifecycle: 90 d on backups/auto-90d/*
                </div>
              </div>
            </Card>
          </div>

          {/* Trend */}
          <Card title="Archive size trend (last 30)" status="GREEN" testid="card-trend">
            <Sparkline data={snap.archive_size_trend} />
          </Card>

          {/* Failures + warnings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Card
              title="Failures (last 7 days)"
              status={snap.failures_7d.length === 0 ? "GREEN" : "AMBER"}
              testid="card-failures"
            >
              {snap.failures_7d.length === 0 ? (
                <div className="text-sm text-slate-400">No failures in the last 7 days.</div>
              ) : (
                <div className="space-y-1 max-h-40 overflow-auto">
                  {snap.failures_7d.map((f, i) => (
                    <div key={i} className="text-xs">
                      <span className="font-mono text-slate-500">{fmtTs(f.ts)}</span>{" "}
                      <span className="font-semibold">{f.mode}</span> — {f.error}
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card
              title="Warnings (active)"
              status={snap.warnings.length === 0 ? "GREEN" : "AMBER"}
              testid="card-warnings"
            >
              {snap.warnings.length === 0 ? (
                <div className="text-sm text-slate-400">No active warnings.</div>
              ) : (
                <ul className="space-y-1">
                  {snap.warnings.map((w, i) => (
                    <li key={i} className="text-sm">
                      <span className="font-semibold">[{w.severity}]</span>{" "}
                      {w.message}{" "}
                      <span className="text-xs text-slate-400">({w.kind})</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>

          {/* Footer · scheduler line */}
          <div className="text-xs text-slate-500 border-t pt-2" data-testid="recovery-footer">
            Scheduler: alive=<span className="font-semibold">{String(snap.scheduler.alive)}</span> ·
            last lock = {fmtTs(snap.scheduler.last_lock_ts)} · pod={" "}
            <span className="font-mono">{snap.scheduler.owner_pod || "—"}</span> ·
            BACKUP_R2_HOURLY={String(snap.hourly_cadence_enabled)} ·
            cached={String(snap.cached)} ·
            overlap_blocked={String(snap.scheduler?.backup_runtime?.overlap?.overlap_blocked || false)}
          </div>
        </div>
      )}
    </LegacyAdminModernShell>
  );
}
