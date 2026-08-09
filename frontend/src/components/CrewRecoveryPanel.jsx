import React, { useEffect, useMemo, useState } from "react";
import {
  ShieldAlert,
  Loader2,
  RefreshCcw,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";
import AdminPasswordConfirm from "@/components/AdminPasswordConfirm";
import { formatPlatformTime } from "@/lib/platformTime";

const FALLBACK_COUNT_AUDIT = {
  users: {
    label: "Legacy crew users",
    truth_classification: "legacy_deprecated",
    classification_label: "Legacy / deprecated",
    operator_truth_rule: "Legacy authentication-only data. Do not treat as active workforce truth.",
    canonical_surface: "/admin/identity-security",
  },
  projects: {
    label: "Retired crew projects",
    truth_classification: "legacy_deprecated",
    classification_label: "Legacy / deprecated",
    operator_truth_rule: "Retired Crew Hub residue. Zero does not indicate live project health.",
    canonical_surface: "/admin/jobs",
  },
  project_members: {
    label: "Retired crew project memberships",
    truth_classification: "legacy_deprecated",
    classification_label: "Legacy / deprecated",
    operator_truth_rule: "Retired Crew Hub memberships. Do not use as staffing truth.",
    canonical_surface: "/admin/project-staffing",
  },
  equipment_master: {
    label: "Equipment master records",
    truth_classification: "canonical_live",
    classification_label: "Canonical / live",
    operator_truth_rule: "Raw count is live master-data volume only. Operational truth lives on the governed equipment surfaces.",
    canonical_surface: "/admin/equipment",
  },
  equipment_units: {
    label: "Equipment units",
    truth_classification: "canonical_live",
    classification_label: "Canonical / live",
    operator_truth_rule: "Raw count is technical volume only. Unit readiness requires the governed equipment views.",
    canonical_surface: "/admin/equipment",
  },
  equipment_inspections: {
    label: "Equipment inspections",
    truth_classification: "canonical_live",
    classification_label: "Canonical / live",
    operator_truth_rule: "Raw count can include historical or governed-hidden rows. Review governed equipment inspection surfaces for business truth.",
    canonical_surface: "/admin/equipment",
  },
  inspections: {
    label: "Safety inspections",
    truth_classification: "canonical_live",
    classification_label: "Canonical / live",
    operator_truth_rule: "Raw count is a collection diagnostic only. Operator truth belongs to governed safety inspection surfaces.",
    canonical_surface: "/admin/incidents",
  },
  meetings: {
    label: "Safety meetings",
    truth_classification: "canonical_live",
    classification_label: "Canonical / live",
    operator_truth_rule: "Raw count is technical volume only. Use governed safety meeting records for operational truth.",
    canonical_surface: "/admin/incidents",
  },
  jhas: {
    label: "JHAs",
    truth_classification: "canonical_live",
    classification_label: "Canonical / live",
    operator_truth_rule: "Raw count can include certification or audit rows. Governed JHA surfaces own business truth.",
    canonical_surface: "/admin/incidents",
  },
  incidents: {
    label: "Incidents",
    truth_classification: "canonical_live",
    classification_label: "Canonical / live",
    operator_truth_rule: "Raw count is not incident severity truth. Use the governed incident command surfaces.",
    canonical_surface: "/admin/incidents",
  },
  daily_reports: {
    label: "Daily reports",
    truth_classification: "canonical_live",
    classification_label: "Canonical / live",
    operator_truth_rule: "Raw count is technical volume only. Governed reporting surfaces apply visibility and contamination rules.",
    canonical_surface: "/admin/daily-reports",
  },
  docs: {
    label: "Retired crew documents",
    truth_classification: "legacy_deprecated",
    classification_label: "Legacy / deprecated",
    operator_truth_rule: "Legacy Crew Hub documents. Do not interpret zero as a live content outage.",
    canonical_surface: "/admin/legacy-imports",
  },
  employees: {
    label: "Employee master records",
    truth_classification: "canonical_live",
    classification_label: "Canonical / live",
    operator_truth_rule: "Raw count is master-data volume only. Workforce truth requires governed people and compliance surfaces.",
    canonical_surface: "/admin/people",
  },
  suppliers: {
    label: "Supplier master records",
    truth_classification: "canonical_live",
    classification_label: "Canonical / live",
    operator_truth_rule: "Raw count is technical volume only. Vendor readiness must be reviewed on governed supplier surfaces.",
    canonical_surface: "/admin/equipment",
  },
  notifications: {
    label: "Notification events",
    truth_classification: "telemetry",
    classification_label: "Telemetry",
    operator_truth_rule: "High volume does not equal operator backlog. This is system-event telemetry, not business work-in-progress.",
    canonical_surface: "/admin/communications",
  },
  activity_log: {
    label: "Legacy crew activity log",
    truth_classification: "legacy_deprecated",
    classification_label: "Legacy / deprecated",
    operator_truth_rule: "Retired Crew Hub audit residue only.",
    canonical_surface: "/admin/audit-log",
  },
};

const CLASS_BADGE = {
  canonical_live: "bg-emerald-100 text-emerald-800 ring-emerald-200",
  governed_derived: "bg-sky-100 text-sky-800 ring-sky-200",
  legacy_deprecated: "bg-slate-100 text-slate-700 ring-slate-200",
  telemetry: "bg-violet-100 text-violet-800 ring-violet-200",
  unavailable: "bg-rose-100 text-rose-800 ring-rose-200",
};

const STATE_BADGE = {
  available: "bg-slate-100 text-slate-700 ring-slate-200",
  genuine_zero: "bg-amber-100 text-amber-900 ring-amber-200",
  unavailable: "bg-rose-100 text-rose-800 ring-rose-200",
  legacy_zero: "bg-slate-100 text-slate-700 ring-slate-200",
};

/**
 * SystemRecoveryPanel — admin recovery for the office.
 * Authenticated by the LEGACY admin password (X-Admin-Token).
 *
 * One remaining operation (the password-reset section was removed when the
 * Crew Hub was retired in favor of Basecamp on 2026-04-28):
 *   - Force-reseed equipment / employees / suppliers from the JSON files
 *     (clears + re-runs the seeds). Use ONLY if those lists are empty.
 *
 * Also shows a live system-status grid of every collection count so the
 * office can see at a glance what's populated and what isn't.
 */
export default function CrewRecoveryPanel() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reseedConfirmOpen, setReseedConfirmOpen] = useState(false);
  const [reseedPasswordOpen, setReseedPasswordOpen] = useState(false);
  const [reseedRunning, setReseedRunning] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/crew-recovery/status");
      setStatus(r.data);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load status"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const runReseed = async () => {
    setReseedRunning(true);
    try {
      const r = await api.post("/admin/crew-recovery/force-reseed");
      const s = r.data.summary || {};
      toast.success(
        `Re-seeded: equipment ${s.equipment_master?.after_seed ?? 0}, employees ${s.employees?.after_seed ?? 0}, suppliers ${s.suppliers?.after_seed ?? 0}`
      );
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Force-reseed failed");
      throw err;
    } finally {
      setReseedRunning(false);
    }
  };

  const proceedToPassword = () => {
    setReseedConfirmOpen(false);
    setReseedPasswordOpen(true);
  };

  const counts = status?.counts || {};
  const diagnosticsRows = useMemo(() => {
    const auditRows = Array.isArray(status?.count_audit) && status.count_audit.length > 0
      ? status.count_audit
      : Object.entries(counts).map(([collection, count]) => ({
          collection,
          count,
          count_state: count < 0 ? "unavailable" : count === 0 && FALLBACK_COUNT_AUDIT[collection]?.truth_classification === "legacy_deprecated" ? "legacy_zero" : count === 0 ? "genuine_zero" : "available",
          ...FALLBACK_COUNT_AUDIT[collection],
        }));
    return auditRows;
  }, [counts, status?.count_audit]);

  // Highlight rows that look "empty" so the office sees at a glance what's missing
  const emptyAlert = ["equipment_master", "employees", "suppliers"].some(
    (k) => (counts[k] ?? 0) === 0
  );

  return (
    <section
      className="bg-white border-2 border-amber-400 rounded-md p-5 sm:p-7 mb-8 shadow-sm"
      data-testid="crew-recovery-panel"
    >
      <div className="flex items-start gap-3 mb-4">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-amber-600 text-white shrink-0">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-700 font-bold">
            Exceptional recovery controls
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            System Recovery
          </h2>
          <p className="text-sm text-slate-600 mt-2">
            Reserved for destructive reconstruction when governed Storage & Recovery,
            Diagnostics, and Maintenance evidence already prove that routine recovery is not enough.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={refresh}
          disabled={loading}
          className="h-9 text-xs font-mono uppercase tracking-wide"
          data-testid="crew-recovery-refresh"
        >
          {loading ? (
            <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
          ) : (
            <RefreshCcw className="w-3.5 h-3.5 mr-1" />
          )}
          Refresh
        </Button>
      </div>

      <div className="grid gap-3 mb-5 lg:grid-cols-3" data-testid="crew-recovery-canonical-links">
        <Link
          to="/admin/storage-recovery"
          className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700 hover:bg-slate-100 transition-colors"
          data-testid="crew-recovery-link-storage"
        >
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">Canonical recovery evidence</div>
          <div className="mt-1 font-semibold text-slate-900">Storage & Recovery</div>
          <div className="mt-1 text-xs">Backups, manifests, retention, restore drills, and integrity jobs.</div>
        </Link>
        <Link
          to="/admin/diagnostics"
          className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700 hover:bg-slate-100 transition-colors"
          data-testid="crew-recovery-link-diagnostics"
        >
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">Canonical technical probes</div>
          <div className="mt-1 font-semibold text-slate-900">Diagnostics</div>
          <div className="mt-1 text-xs">Runtime health, workers, deploy readiness, and governed system checks.</div>
        </Link>
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-900" data-testid="crew-recovery-exception-note">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em]">Exception-only rule</div>
          <div className="mt-1 font-semibold">Do not use raw counts here as business truth.</div>
          <div className="mt-1 text-xs leading-relaxed">This panel is for technical diagnosis and guarded reconstruction only. Operational truth still belongs to the governed domain surfaces above.</div>
        </div>
      </div>

      {/* ===== System counts ===== */}
      <div className="bg-slate-50 border-2 border-slate-200 rounded p-3 mb-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-700 font-bold mb-2">
          Technical collection diagnostics
        </div>
        <p className="mb-3 text-xs text-slate-600">
          Each figure below is a raw collection count. It shows database presence only — not governed business truth,
          not filtered operator truth, and not release readiness by itself.
        </p>
        {loading ? (
          <div className="text-slate-500 text-sm flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading…
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-3 text-xs">
            {diagnosticsRows.map((row) => {
              const classTone = CLASS_BADGE[row.truth_classification] || CLASS_BADGE.unavailable;
              const stateTone = STATE_BADGE[row.count_state] || STATE_BADGE.available;
              const countValue = typeof row.count === "number" && row.count >= 0 ? row.count.toLocaleString() : "?";
              return (
              <div
                key={row.collection}
                className="rounded border border-slate-200 bg-white p-3"
                data-testid={`crew-recovery-count-${row.collection}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-[9px] uppercase tracking-wide text-slate-500">{row.collection}</div>
                    <div className="font-semibold text-slate-900">{row.label || row.collection}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-black text-xl leading-none text-slate-900" data-testid={`crew-recovery-count-${row.collection}-value`}>{countValue}</div>
                    <div className="mt-1 flex flex-wrap justify-end gap-1">
                      <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-mono font-semibold uppercase tracking-widest ring-1 ${classTone}`}>
                        {row.classification_label || "Classified"}
                      </span>
                      <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-mono font-semibold uppercase tracking-widest ring-1 ${stateTone}`}>
                        {(row.count_state || "available").replace(/_/g, " ")}
                      </span>
                    </div>
                  </div>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-600" data-testid={`crew-recovery-count-${row.collection}-rule`}>
                  {row.operator_truth_rule || "Technical diagnostic only."}
                </p>
                <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
                  <span>Canonical surface: <span className="font-mono text-slate-700">{row.canonical_surface || "—"}</span></span>
                  <span>Last refresh: <span className="font-mono text-slate-700">{formatPlatformTime(status?.refreshed_at)}</span></span>
                </div>
              </div>
            )})}
          </div>
        )}
        {emptyAlert && (
          <div className="mt-3 text-xs bg-red-50 border-l-4 border-red-600 px-3 py-2 text-red-800" data-testid="crew-recovery-empty-master-warning">
            <strong>One or more seed-managed master collections are empty.</strong>{" "}
            Confirm that governed Storage & Recovery evidence and Diagnostics both support a reconstruction path before using the destructive action below.
          </div>
        )}
      </div>

      {/* ===== Force re-seed ===== */}
      <div className="border-2 border-orange-300 bg-orange-50 rounded p-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-orange-800 font-bold mb-2">
          Destructive reconstruction
        </div>
        <p className="text-xs text-slate-700 mb-2.5">
          Wipes the seed-managed equipment / employee / supplier masters and rebuilds them from the JSON seed files.
          Use only after consequence review, explicit confirmation, and traceable evidence that governed recovery paths cannot restore the problem safely.
        </p>
        <Button
          onClick={() => setReseedConfirmOpen(true)}
          disabled={reseedRunning}
          className="bg-orange-600 hover:bg-orange-700 text-white font-bold uppercase tracking-wide text-xs h-10 px-4 border-b-2 border-orange-800"
          data-testid="crew-recovery-reseed-btn"
        >
          {reseedRunning ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Re-seeding…
            </>
          ) : (
            <>
              <RefreshCcw className="w-3.5 h-3.5 mr-1.5" /> Force re-seed
            </>
          )}
        </Button>
        <div className="mt-3 rounded-md border border-orange-200 bg-white px-3 py-2 text-xs text-slate-700" data-testid="crew-recovery-destructive-disclosure">
          Scope: <strong>equipment_master</strong>, <strong>equipment_units</strong>, <strong>employees</strong>, and <strong>suppliers</strong> only. Safety records, projects, audit history, and user accounts are not rebuilt by this action.
        </div>
      </div>

      {/* Confirm dialog for force-reseed */}
      <Dialog open={reseedConfirmOpen} onOpenChange={setReseedConfirmOpen}>
        <DialogContent data-testid="crew-recovery-reseed-confirm-dialog">
          <DialogHeader>
            <DialogTitle className="font-display font-black flex items-center gap-2 text-orange-700">
              <AlertTriangle className="w-5 h-5" />
              Force re-seed equipment / employees / suppliers?
            </DialogTitle>
            <DialogDescription>
              This will <strong>delete</strong> every row in:
              <br />
              • <code>equipment_master</code> ({counts.equipment_master ?? 0} rows)
              <br />
              • <code>equipment_units</code> ({counts.equipment_units ?? 0} rows)
              <br />
              • <code>employees</code> ({counts.employees ?? 0} rows)
              <br />
              • <code>suppliers</code> ({counts.suppliers ?? 0} rows)
              <br />
              <br />
              …and re-create them from the JSON seed files (
              <code>/app/backend/data/*.json</code>). Safety records, projects,
              and user accounts are NOT touched.
              <br />
              <br />
              <strong>Only do this if those lists are currently empty</strong>{" "}
              and you want to restore the standard fleet/employee/supplier seed.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setReseedConfirmOpen(false)}
              disabled={reseedRunning}
              data-testid="crew-recovery-reseed-cancel-btn"
            >
              No, cancel
            </Button>
            <Button
              onClick={proceedToPassword}
              disabled={reseedRunning}
              className="bg-orange-600 hover:bg-orange-700 text-white font-bold uppercase tracking-wide"
              data-testid="crew-recovery-reseed-confirm-btn"
            >
              {reseedRunning ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Re-seeding…
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 mr-2" /> Continue
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* SECOND GATE — admin password required before wipe */}
      <AdminPasswordConfirm
        open={reseedPasswordOpen}
        onOpenChange={setReseedPasswordOpen}
        title="Force re-seed — wipe & reload?"
        description={
          `This will delete every row in equipment_master (${counts.equipment_master ?? 0}), ` +
          `equipment_units (${counts.equipment_units ?? 0}), ` +
          `employees (${counts.employees ?? 0}), and suppliers (${counts.suppliers ?? 0}), ` +
          `then re-create them from the JSON seed files. Re-enter the admin password ` +
          `to authorize this destructive action.`
        }
        confirmLabel="Wipe & re-seed"
        destructive
        onConfirm={runReseed}
        testId="crew-recovery-password-confirm"
      />
    </section>
  );
}
