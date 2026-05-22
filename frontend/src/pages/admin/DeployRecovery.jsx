// DeployRecovery.jsx — Iter130. Read-only deployment recovery playbook
// + R2/backup chain probe. Admin-only. NO destructive actions.
import React, { useEffect, useState } from "react";
import {
  Rocket, ShieldCheck, AlertTriangle, CheckCircle2, RefreshCcw, Loader2,
  Cloud, HardDrive, Clock, ArrowRight,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";

const STATUS_CLS = {
  green:  "bg-emerald-50 border-emerald-300 text-emerald-900",
  yellow: "bg-amber-50 border-amber-300 text-amber-900",
  red:    "bg-red-50 border-red-300 text-red-900",
};

export default function DeployRecovery() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try { setData((await api.get("/admin/deploy-recovery")).data); }
    catch (e) { toast.error(operationalError(e, "Failed to load recovery state")); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  return (
    <AdminShell title="Deployment Recovery" section="system">
      <div className="max-w-5xl mx-auto" data-testid="admin-deploy-recovery-page">
        <div className="bg-white border border-slate-200 rounded-md p-5 mb-4 flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-900 text-white shrink-0">
            <Rocket className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
              Pre / Post-Deploy Playbook · iter130
            </span>
            <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
              Deployment Recovery
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              Read-only operational checklist + the current backup chain state. No destructive actions on this page.
            </p>
          </div>
          <Button onClick={load} variant="outline" size="sm" disabled={loading} data-testid="recovery-refresh">
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
          </Button>
        </div>

        {/* Current state probe */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div className="bg-white border border-slate-200 rounded-md p-4">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 font-bold mb-1">Current build</div>
            <div className="font-display text-lg font-black break-words">{data?.current?.version || "—"}</div>
            <div className="text-xs text-slate-500 font-mono">{data?.current?.built_at || ""}</div>
          </div>
          <div className={`border-2 rounded-md p-4 ${STATUS_CLS[data?.r2?.status || "yellow"]}`} data-testid="recovery-r2-card">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold mb-1 flex items-center gap-1">
              <Cloud className="w-3.5 h-3.5" /> R2 cloud archive
            </div>
            <div className="font-display text-lg font-black">{(data?.r2?.status || "—").toUpperCase()}</div>
            <div className="text-xs">{data?.r2?.detail || ""}</div>
          </div>
          <div className="bg-white border border-slate-200 rounded-md p-4">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 font-bold mb-1 flex items-center gap-1">
              <HardDrive className="w-3.5 h-3.5" /> Recent backups
            </div>
            <div className="font-display text-3xl font-black">{(data?.recent_backups || []).length}</div>
            <div className="text-xs text-slate-500">Successful runs on record</div>
          </div>
        </div>

        {/* Backup chain */}
        <div className="bg-white border border-slate-200 rounded-md p-4 mb-4">
          <h2 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" /> Latest successful backups
          </h2>
          {(data?.recent_backups || []).length === 0 ? (
            <p className="text-sm text-slate-500 italic">No backup runs recorded yet — confirm the hourly R2 snapshot cron is armed before deploy.</p>
          ) : (
            <ul className="text-xs divide-y divide-slate-100" data-testid="recovery-backup-list">
              {data.recent_backups.map((b, i) => (
                <li key={i} className="py-2 flex items-center gap-3">
                  <span className="font-mono text-slate-500 whitespace-nowrap">{(b.started_at || "").slice(0, 19).replace("T", " ")}</span>
                  <span className="font-bold">{b.kind}</span>
                  <span className="text-slate-500">→ {b.destination}</span>
                  <span className="ml-auto font-mono text-slate-500">{(b.size_bytes / 1024 / 1024).toFixed(1)} MB</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Known-good build history */}
        {(data?.known_good_history || []).length > 0 && (
          <div className="bg-white border border-slate-200 rounded-md p-4 mb-4">
            <h2 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">Known-good build history</h2>
            <ul className="text-xs divide-y divide-slate-100" data-testid="recovery-good-history">
              {data.known_good_history.map((h, i) => (
                <li key={i} className="py-2 flex items-center gap-3">
                  <span className="font-mono text-slate-500">{(h.deployed_at || "").slice(0, 19).replace("T", " ")}</span>
                  <span className="font-bold">{h.version}</span>
                  <span className="text-slate-500">{h.note || ""}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Rollback playbook */}
        <div className="bg-white border border-slate-200 rounded-md p-5">
          <h2 className="font-display text-xl font-black flex items-center gap-2 mb-3">
            <ShieldCheck className="w-5 h-5 text-red-700" /> Rollback playbook
          </h2>

          <Playbook icon={AlertTriangle} title="If a deploy looks bad (errors spiking, users blocked)" color="red">
            <ol className="ml-5 list-decimal space-y-1">
              <li>Open <Link to="/admin/system-health" className="font-bold underline text-red-700" data-testid="recovery-health-link">System Health</Link> in a new tab. Confirm the red signals (MongoDB · R2 · auth failures · failed syncs).</li>
              <li>Tell the deploy operator <strong>"halt and roll back"</strong> and screenshot the System Health panel.</li>
              <li>The hosting platform has one-click revert to the previous deploy. Use it. Production traffic re-routes within ~60 s.</li>
              <li>While reverting, freeze NEW logins via Admin → System &amp; Backups → temporarily set <code>RATE_LIMITING=hard</code> or block at the edge.</li>
            </ol>
          </Playbook>

          <Playbook icon={Cloud} title="Database / data corruption suspected" color="amber">
            <ol className="ml-5 list-decimal space-y-1">
              <li>Stop further writes — set the deploy back to the previous build first.</li>
              <li>Go to <Link to="/admin/system" className="font-bold underline text-amber-700">Admin → System &amp; Backups</Link> → "Restore from R2 archive". Pick the most recent hourly snapshot taken BEFORE the corruption window.</li>
              <li>Restore reads the R2 snapshot into a quarantine collection set first. Verify counts, then promote.</li>
              <li>Cross-reference the <Link to="/admin/audit-log" className="font-bold underline text-amber-700" data-testid="recovery-audit-link">Audit Log</Link> for the actor/source-module behind the offending writes.</li>
            </ol>
          </Playbook>

          <Playbook icon={CheckCircle2} title="Pre-deploy verification checklist" color="emerald">
            <ol className="ml-5 list-decimal space-y-1">
              <li>System Health overall = GREEN.</li>
              <li>At least one R2 backup in the last 1 h.</li>
              <li>No active auth-failure spikes.</li>
              <li>All required env vars set on the deploy target (<code>AUTO_EMAIL_REPORTS</code>, <code>RATE_LIMITING</code>, <code>CORS_ORIGINS</code>, <code>ADMIN_HMAC_SECRET</code>, R2 + Resend keys, fresh <code>ADMIN_SESSION_EPOCH</code>).</li>
              <li>Smoke test the 6 portal logins with the super-admin account.</li>
              <li>Snapshot the build version above so it can be referenced in the rollback target.</li>
            </ol>
          </Playbook>

          <Playbook icon={Rocket} title="Post-deploy smoke (60-second loop)" color="slate">
            <ol className="ml-5 list-decimal space-y-1">
              <li>Hit <code>GET /api/health</code> → expect 200.</li>
              <li>Hit <code>POST /api/auth/multi-login</code> with the super-admin account → expect all 6 portal tokens.</li>
              <li>Open <Link to="/admin/dispatch" className="font-bold underline">Dispatch Portal</Link> → confirm Utilization renders.</li>
              <li>Open this page → confirm overall System Health is green.</li>
              <li>If all green for 60 s straight, announce "deploy stable" to the team.</li>
            </ol>
          </Playbook>

          <div className="mt-4 pt-3 border-t border-slate-200 text-xs text-slate-500 font-mono flex items-center gap-2">
            <span>This page is READ-ONLY.</span>
            <ArrowRight className="w-3 h-3" />
            <span>Destructive actions live at <Link to="/admin/system" className="underline">/admin/system</Link>.</span>
          </div>
        </div>
      </div>
    </AdminShell>
  );
}

function Playbook({ icon: Icon, title, color, children }) {
  const colors = {
    red:     "border-red-300 bg-red-50 text-red-900",
    amber:   "border-amber-300 bg-amber-50 text-amber-900",
    emerald: "border-emerald-300 bg-emerald-50 text-emerald-900",
    slate:   "border-slate-300 bg-slate-50 text-slate-900",
  };
  return (
    <div className={`border-2 rounded-md p-4 mb-3 ${colors[color] || colors.slate}`}>
      <div className="flex items-center gap-2 mb-2 font-display font-black">
        <Icon className="w-4 h-4" />
        {title}
      </div>
      <div className="text-sm leading-relaxed">{children}</div>
    </div>
  );
}
