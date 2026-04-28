import React, { useState } from "react";
import { Wrench, Loader2, CheckCircle2, AlertTriangle } from "lucide-react";
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

/**
 * DataFixesPanel — One-click "Apply Production Data Fixes" with a hard
 * "Are you sure?" gate so nothing fires by accident.
 *
 * Runs two idempotent backend healers via POST /api/admin/data-fixes/run:
 *   1. Splits every equipment_master `make_model` into `make` + `model`
 *   2. Seeds project_members so every owner/admin sees every project
 *
 * Both healers also auto-run on backend boot if equipment data is incomplete,
 * so this is the manual "do it now" button for after a fresh redeploy.
 */
export default function DataFixesPanel() {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [running, setRunning] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  const runFixes = async () => {
    setRunning(true);
    try {
      const res = await api.post("/admin/data-fixes/run");
      setLastResult(res.data);
      const eq = res.data.equipment_master || {};
      const pm = res.data.project_members || {};
      toast.success(
        `Data fixes applied — ${eq.fixed || 0} equipment units fixed, ${pm.created || 0} new project memberships`
      );
      setConfirmOpen(false);
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Failed to run data fixes";
      toast.error(msg);
    } finally {
      setRunning(false);
    }
  };

  const eq = lastResult?.equipment_master;
  const pm = lastResult?.project_members;

  return (
    <section
      className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 mb-8 shadow-sm"
      data-testid="data-fixes-panel"
    >
      <div className="flex items-start gap-3 mb-3">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-amber-500 text-white shrink-0">
          <Wrench className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-700 font-bold">
            Production Data Healers
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            Apply Production Data Fixes
          </h2>
          <p className="text-sm text-slate-600 mt-2">
            Re-runs the two idempotent fixes that populate equipment make/model
            and assign every owner/admin to every project. Safe to run any
            number of times — only updates rows that need updating.
          </p>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-50 border-l-4 border-slate-400 rounded-r px-3 py-2 text-xs">
          <div className="font-mono uppercase tracking-wide text-slate-700 font-bold mb-1">
            Fix #1 — Equipment make/model
          </div>
          <div className="text-slate-600">
            Splits every unit's <code className="text-[11px] bg-white px-1 rounded">make_model</code> into proper{" "}
            <code className="text-[11px] bg-white px-1 rounded">make</code> +{" "}
            <code className="text-[11px] bg-white px-1 rounded">model</code> columns.
          </div>
        </div>
        <div className="bg-slate-50 border-l-4 border-slate-400 rounded-r px-3 py-2 text-xs">
          <div className="font-mono uppercase tracking-wide text-slate-700 font-bold mb-1">
            Fix #2 — Project memberships
          </div>
          <div className="text-slate-600">
            Adds every owner + admin user as a member of every active project so they see all jobs in the Crew Hub.
          </div>
        </div>
      </div>

      <Button
        onClick={() => setConfirmOpen(true)}
        disabled={running}
        className="bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide text-sm px-5 h-11 border-b-2 border-amber-800"
        data-testid="data-fixes-run-btn"
      >
        {running ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Applying…
          </>
        ) : (
          <>
            <Wrench className="w-4 h-4 mr-2" /> Apply Production Data Fixes
          </>
        )}
      </Button>

      {lastResult && (
        <div
          className="mt-4 bg-emerald-50 border-l-4 border-emerald-600 rounded-r px-3 py-2.5 text-sm"
          data-testid="data-fixes-result"
        >
          <div className="flex items-center gap-2 font-bold text-emerald-800">
            <CheckCircle2 className="w-4 h-4" /> Last run:{" "}
            <span className="font-mono text-xs">
              {new Date(lastResult.ran_at).toLocaleString()}
            </span>
          </div>
          <ul className="mt-1.5 text-xs text-emerald-900 space-y-0.5 ml-6 list-disc">
            <li>
              Equipment master: {eq?.fixed ?? 0} units fixed · {eq?.total ?? 0} total ·{" "}
              {eq?.still_missing ?? 0} still missing
            </li>
            <li>
              Project memberships: {pm?.created ?? 0} new rows added ·{" "}
              {pm?.privileged_users ?? 0} privileged users × {pm?.projects ?? 0} projects ={" "}
              {pm?.total_after ?? 0} total memberships
            </li>
          </ul>
        </div>
      )}

      {/* "Are you sure?" gate — nothing fires on cancel */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent data-testid="data-fixes-confirm-dialog">
          <DialogHeader>
            <DialogTitle className="font-display font-black flex items-center gap-2 text-amber-700">
              <AlertTriangle className="w-5 h-5" />
              Apply data fixes now?
            </DialogTitle>
            <DialogDescription>
              This will run two healers against the live database:
              <br />
              <strong>1.</strong> Re-split <code>make_model</code> on every equipment unit.
              <br />
              <strong>2.</strong> Re-seed <code>project_members</code> so every owner / admin
              sees every project.
              <br />
              <br />
              Both are idempotent and safe — but please double-check this is the
              right environment before clicking <strong>Yes</strong>.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setConfirmOpen(false)}
              disabled={running}
              data-testid="data-fixes-cancel-btn"
            >
              No, cancel
            </Button>
            <Button
              onClick={runFixes}
              disabled={running}
              className="bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide"
              data-testid="data-fixes-confirm-btn"
            >
              {running ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Applying…
                </>
              ) : (
                <>Yes, apply fixes</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
