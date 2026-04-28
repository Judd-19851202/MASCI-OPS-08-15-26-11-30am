import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  Loader2,
  KeyRound,
  RefreshCcw,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
 * CrewRecoveryPanel — emergency recovery for the office when nobody can log
 * into the Crew Hub. Authenticated by the LEGACY admin password (X-Admin-Token)
 * — NOT by a Crew Hub JWT — so it works even when every crew owner is locked
 * out.
 *
 * Two operations:
 *   1. Reset any Crew Hub user's password back to a known value.
 *   2. Force-reseed equipment / employees / suppliers from the JSON files
 *      (clears + re-runs the seeds). Use ONLY if those lists are empty.
 */
export default function CrewRecoveryPanel() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resetEmail, setResetEmail] = useState("");
  const [resetPassword, setResetPassword] = useState("");
  const [resetSubmitting, setResetSubmitting] = useState(false);
  const [reseedConfirmOpen, setReseedConfirmOpen] = useState(false);
  const [reseedRunning, setReseedRunning] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/crew-recovery/status");
      setStatus(r.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to load status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const onReset = async (e) => {
    e.preventDefault();
    if (!resetEmail || !resetPassword) {
      toast.error("Email + new password required");
      return;
    }
    if (resetPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    setResetSubmitting(true);
    try {
      await api.post("/admin/crew-recovery/reset-password", {
        email: resetEmail.trim().toLowerCase(),
        new_password: resetPassword,
      });
      toast.success(`Password reset for ${resetEmail}. They must change it on next login.`);
      setResetEmail("");
      setResetPassword("");
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Reset failed");
    } finally {
      setResetSubmitting(false);
    }
  };

  const runReseed = async () => {
    setReseedRunning(true);
    try {
      const r = await api.post("/admin/crew-recovery/force-reseed");
      const s = r.data.summary || {};
      toast.success(
        `Re-seeded: equipment ${s.equipment_master?.after_seed ?? 0}, employees ${s.employees?.after_seed ?? 0}, suppliers ${s.suppliers?.after_seed ?? 0}`
      );
      setReseedConfirmOpen(false);
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Force-reseed failed");
    } finally {
      setReseedRunning(false);
    }
  };

  const counts = status?.counts || {};
  const users = status?.crew_users || [];

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
            Emergency Recovery — Use only if locked out
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            Crew Hub Recovery
          </h2>
          <p className="text-sm text-slate-600 mt-2">
            Reset any Crew Hub user's password from this admin console (works
            even when nobody can log in), and re-seed equipment / employees /
            suppliers if those lists are empty after a redeploy.
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

      {/* ===== System counts ===== */}
      <div className="bg-slate-50 border-2 border-slate-200 rounded p-3 mb-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-700 font-bold mb-2">
          System status
        </div>
        {loading ? (
          <div className="text-slate-500 text-sm flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading…
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            {Object.entries(counts).map(([k, v]) => (
              <div
                key={k}
                className={`px-2 py-1.5 rounded border ${
                  v === 0 && ["equipment_master", "employees", "suppliers"].includes(k)
                    ? "border-red-400 bg-red-50 text-red-800"
                    : v < 0
                    ? "border-slate-300 bg-slate-100 text-slate-500"
                    : "border-slate-200 bg-white text-slate-700"
                }`}
              >
                <div className="text-[9px] uppercase tracking-wide opacity-75">{k}</div>
                <div className="font-bold text-base">{v < 0 ? "?" : v.toLocaleString()}</div>
              </div>
            ))}
          </div>
        )}
        {emptyAlert && (
          <div className="mt-3 text-xs bg-red-50 border-l-4 border-red-600 px-3 py-2 text-red-800">
            <strong>Equipment / employees / suppliers list is empty.</strong>{" "}
            Use the orange "Force re-seed" button below to repopulate from the
            JSON seed files.
          </div>
        )}
      </div>

      {/* ===== Reset crew user password ===== */}
      <div className="border-2 border-slate-200 rounded p-3 mb-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-700 font-bold mb-2 flex items-center gap-1.5">
          <KeyRound className="w-3.5 h-3.5" /> Reset Crew Hub password
        </div>
        <form onSubmit={onReset} className="grid sm:grid-cols-[1fr_1fr_auto] gap-2">
          <div>
            <Input
              list="crew-emails"
              placeholder="email@mascigc.com"
              value={resetEmail}
              onChange={(e) => setResetEmail(e.target.value)}
              className="h-10 text-sm"
              data-testid="crew-recovery-email-input"
              autoComplete="off"
            />
            <datalist id="crew-emails">
              {users.map((u) => (
                <option key={u.id} value={u.email}>
                  {u.email} — {u.role}
                </option>
              ))}
            </datalist>
          </div>
          <Input
            type="text"
            placeholder="New password (min 8 chars)"
            value={resetPassword}
            onChange={(e) => setResetPassword(e.target.value)}
            className="h-10 text-sm font-mono"
            data-testid="crew-recovery-password-input"
            autoComplete="off"
          />
          <Button
            type="submit"
            disabled={resetSubmitting}
            className="bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-xs h-10 px-4"
            data-testid="crew-recovery-reset-btn"
          >
            {resetSubmitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <KeyRound className="w-3.5 h-3.5 mr-1" /> Reset
              </>
            )}
          </Button>
        </form>
        <p className="text-[11px] text-slate-500 mt-2">
          The user must change this password on their next login. Type
          something simple like <code className="bg-slate-100 px-1 rounded">Welcome2MASCI!</code>{" "}
          and tell them what it is.
        </p>
        {users.length > 0 && (
          <div className="mt-3 text-xs">
            <div className="font-mono text-[9px] uppercase tracking-wide text-slate-500 mb-1">
              Crew users on file
            </div>
            <ul className="grid sm:grid-cols-2 gap-1">
              {users.map((u) => (
                <li
                  key={u.id}
                  className="flex items-center justify-between bg-slate-50 border border-slate-200 px-2 py-1 rounded font-mono"
                >
                  <span className="truncate">
                    <button
                      type="button"
                      onClick={() => setResetEmail(u.email)}
                      className="text-red-700 hover:underline"
                    >
                      {u.email}
                    </button>{" "}
                    <span className="text-[10px] text-slate-500">{u.role}</span>
                  </span>
                  <span className="text-[10px] text-slate-400">
                    {u.is_active ? "active" : "disabled"}
                    {u.must_change_password ? " · must-change" : ""}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* ===== Force re-seed ===== */}
      <div className="border-2 border-orange-300 bg-orange-50 rounded p-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-orange-800 font-bold mb-2">
          Force re-seed equipment / employees / suppliers
        </div>
        <p className="text-xs text-slate-700 mb-2.5">
          Wipes the equipment_master / equipment_units / employees / suppliers
          collections and re-loads them from the JSON seed files. Use only when
          those lists are empty after a redeploy. Safety records, projects, and
          user accounts are <strong>NOT</strong> touched.
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
              onClick={runReseed}
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
                  <CheckCircle2 className="w-4 h-4 mr-2" /> Yes, re-seed now
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
