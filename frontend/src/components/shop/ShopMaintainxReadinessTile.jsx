// ShopMaintainxReadinessTile — read-only Shop-portal tile that
// surfaces defect counts ready / blocked / duplicate-risk / awaiting-RTS
// for MaintainX. NO action buttons, NO edits, NO MaintainX calls
// initiated from the UI; the underlying endpoint is itself read-only.
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Wrench, ShieldAlert, Copy as CopyIcon, CheckCircle2, Clock } from "lucide-react";
import { api } from "@/lib/api";

export default function ShopMaintainxReadinessTile() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const r = await api.get("/integrations/maintainx/defect-coverage", {
          params: { sample_limit: 1, since_days: 60 },
        });
        if (active) setData(r.data);
      } catch {
        if (active) setData(null);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  if (loading || !data) return null;
  const t = data.totals || {};
  const oosOpen = t.out_of_service || 0;

  return (
    <section
      className="bg-white border-2 border-amber-200 rounded-md p-4"
      data-testid="shop-mx-readiness-tile"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Wrench className="w-5 h-5 text-amber-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-900 font-bold">
            MaintainX Readiness Queue · Read-Only
          </span>
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <Cell label="Ready" value={t.ready_for_maintainx} icon={CheckCircle2} tone="ok"
          testId="shop-mx-ready" />
        <Cell label="Blocked" value={t.blocked} icon={ShieldAlert} tone="warn"
          testId="shop-mx-blocked" />
        <Cell label="Duplicate Risk" value={t.duplicate_risk} icon={CopyIcon} tone="info"
          testId="shop-mx-dup" />
        <Cell label="Awaiting RTS" value={oosOpen} icon={Clock} tone="bad"
          testId="shop-mx-awaiting-rts" />
      </div>
      <div className="text-[11px] text-slate-500 mt-2">
        Counts reflect every active equipment defect across DVIR, Pre-Op, Manual OOS,
        and Maintenance Holds. No work orders are created from this view.
      </div>
    </section>
  );
}

function Cell({ label, value, icon: Icon, tone, testId }) {
  const toneMap = {
    ok:   "border-emerald-200 bg-emerald-50 text-emerald-900",
    warn: "border-amber-200 bg-amber-50 text-amber-900",
    info: "border-violet-200 bg-violet-50 text-violet-900",
    bad:  "border-red-200 bg-red-50 text-red-900",
  };
  return (
    <div className={`border rounded-md px-3 py-2 ${toneMap[tone] || "border-slate-200 bg-slate-50"}`} data-testid={testId}>
      <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.16em] font-bold">
        <Icon className="w-3 h-3" />
        {label}
      </div>
      <div className="text-2xl font-display font-black tabular-nums mt-0.5">{value ?? 0}</div>
    </div>
  );
}
