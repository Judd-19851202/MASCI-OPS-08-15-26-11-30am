// PreDeploySnapshotPanel — iter85
//
// Goal: turn "remember to back up before redeploy" from discipline into
// muscle memory. Renders at the top of /admin/system and gives admins
// a single visible answer to: "Am I safe to redeploy RIGHT NOW?"
//
// Color logic (last complete archive age from the active runtime state):
//   🟢 GREEN  · <  1 hour old → fresh archive evidence exists
//   🟡 YELLOW · 1-12 h old    → archive is aging
//   🔴 RED    · > 12 h old    → archive is stale for redeploy confidence

import React, { useEffect, useState, useCallback } from "react";
import {
  ShieldCheck, ShieldAlert, Loader2, Rocket, CheckCircle2, AlertOctagon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";

function fmtAge(ts) {
  if (!ts) return null;
  try {
    const ms = Date.now() - new Date(ts).getTime();
    const mins = Math.max(0, Math.round(ms / 60000));
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins} min ago`;
    const hrs = mins / 60;
    if (hrs < 24) return `${hrs.toFixed(hrs < 10 ? 1 : 0)} hr ago`;
    return `${(hrs / 24).toFixed(1)} day ago`;
  } catch { return null; }
}

function ageHrs(ts) {
  if (!ts) return Infinity;
  try { return (Date.now() - new Date(ts).getTime()) / 36e5; } catch { return Infinity; }
}

export default function PreDeploySnapshotPanel() {
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const r = await api.get("/admin/backups-complete-r2-state");
      setState(r.data);
    } catch {
      setState({ configured: false });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  // Auto-refresh every 30 s while open so the freshness clock stays live
  useEffect(() => {
    const id = setInterval(refresh, 30000);
    return () => clearInterval(id);
  }, [refresh]);

  const snapshotNow = async () => {
    if (building) return;
    setBuilding(true);
    toast.info("Building complete archive → R2… ~30–60 sec");
    try {
      const r = await api.post("/admin/backups/run-complete-now");
      if (r.data?.accepted) {
        // Poll state for in-progress completion
        let attempts = 0;
        const poll = setInterval(async () => {
          attempts++;
          await refresh();
          const cur = (await api.get("/admin/backups-complete-r2-state")).data;
          if (!cur?.in_progress || attempts > 30) {
            clearInterval(poll);
            setBuilding(false);
            if (cur?.last?.outcome === "ok") {
      toast.success(`Backup complete — ${cur.last.filename}`);
            } else if (cur?.last?.outcome && cur.last.outcome !== "in-progress") {
      toast.error(`Backup failed — ${cur.last.outcome}`);
            }
          }
        }, 3000);
      } else {
        setBuilding(false);
      }
    } catch (e) {
      setBuilding(false);
      toast.error(operationalError(e, "Backup failed"));
    }
  };

  if (loading) {
    return (
      <div className="bg-white border border-slate-200 rounded-md p-4 flex items-center gap-2 text-sm text-slate-500" data-testid="predeploy-loading">
        <Loader2 className="w-4 h-4 animate-spin" /> Checking backup freshness…
      </div>
    );
  }

  // R2 not configured — hide entirely
  if (state?.configured === false) {
    return null;
  }

  const lastTs = state?.nightly_last?.ts || state?.last?.ts;
  const hrs = ageHrs(lastTs);
  const inProgress = state?.in_progress;
  const hourly = state?.hourly_activation || {};

  // Pick zone
  let zone;
  if (inProgress || building) {
    zone = {
      key: "building",
      bg: "bg-blue-50",
      border: "border-blue-400",
      text: "text-blue-900",
      accent: "text-blue-700",
      icon: Loader2,
      iconSpin: true,
      label: "BACKUP RUN IN PROGRESS",
      msg: "A fresh complete archive is being written to R2 right now.",
    };
  } else if (hrs < 1) {
    zone = {
      key: "green",
      bg: "bg-emerald-50",
      border: "border-emerald-500",
      text: "text-emerald-900",
      accent: "text-emerald-700",
      icon: CheckCircle2,
      label: "FRESH ARCHIVE EVIDENCE",
      msg: "A fresh complete archive landed in R2 less than an hour ago. Preview archive evidence is current.",
    };
  } else if (hrs < 12) {
    zone = {
      key: "yellow",
      bg: "bg-amber-50",
      border: "border-amber-500",
      text: "text-amber-900",
      accent: "text-amber-700",
      icon: ShieldAlert,
      label: "ARCHIVE IS AGING",
      msg: "Last complete archive is more than an hour old. Capture a fresh preview snapshot before any redeploy decision.",
    };
  } else {
    zone = {
      key: "red",
      bg: "bg-red-50",
      border: "border-red-600",
      text: "text-red-900",
      accent: "text-red-700",
      icon: AlertOctagon,
      label: "ARCHIVE IS STALE",
      msg: "No fresh complete archive in the last 12 hours. Run a new preview snapshot before any redeploy decision.",
    };
  }

  const Icon = zone.icon;

  return (
    <section
      className={`border-l-8 ${zone.border} ${zone.bg} rounded-md p-5 shadow-sm`}
      data-testid="pre-deploy-snapshot-panel"
    >
      <div className="flex items-start gap-3 flex-wrap">
        <div className={`inline-flex items-center justify-center w-12 h-12 rounded-md bg-white border-2 ${zone.border}`}>
          <Icon className={`w-6 h-6 ${zone.accent} ${zone.iconSpin ? "animate-spin" : ""}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className={`font-mono text-[10px] uppercase tracking-[0.25em] font-bold ${zone.accent}`}>
            Pre-Deploy Backup Check
          </div>
          <h3 className={`font-display text-lg sm:text-xl font-black tracking-tight ${zone.text} leading-tight mt-0.5`}>
            {zone.label}
          </h3>
          <p className={`text-sm mt-1.5 ${zone.text} leading-relaxed`}>
            {zone.msg}
          </p>
          <div className={`text-[11px] font-mono uppercase tracking-[0.15em] mt-2 ${zone.accent}`}>
            Last complete archive: {lastTs ? <strong>{fmtAge(lastTs)}</strong> : <em>never</em>}
            {state?.last?.filename && <> · <span className="font-bold normal-case">{state.last.filename}</span></>}
          </div>
        </div>
        <Button
          onClick={snapshotNow}
          disabled={building || inProgress}
          className={`h-11 px-4 font-bold uppercase tracking-wide text-xs disabled:bg-slate-400 ${
            zone.key === "green"
              ? "bg-slate-900 hover:bg-slate-800 text-white"
              : zone.key === "yellow"
              ? "bg-amber-600 hover:bg-amber-700 text-white"
              : zone.key === "red"
              ? "bg-red-700 hover:bg-red-800 text-white"
              : "bg-blue-600 hover:bg-blue-700 text-white"
          }`}
          data-testid="pre-deploy-snapshot-btn"
        >
          {building || inProgress ? (
            <><Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> Building…</>
          ) : (
            <><Rocket className="w-4 h-4 mr-1.5" /> Run Backup Now</>
          )}
        </Button>
      </div>
      <div className={`mt-3 text-[10px] font-mono uppercase tracking-[0.2em] ${zone.accent} flex items-center gap-2 flex-wrap`}>
        <ShieldCheck className="w-3 h-3" />
        <span>
          Hourly complete archive {hourly.activation_status || "DISABLED BY CONFIGURATION"} ·
          Nightly complete archive {String(state?.r2_full_hour_utc ?? 3).padStart(2, "0")}:00 platform time
        </span>
      </div>
    </section>
  );
}
