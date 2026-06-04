// DispatchEquipmentMaintenanceIndicator — small calm indicator placed
// on the Dispatch Hub. Shows the count of OOS-equipment maintenance
// issues currently awaiting attention. Read-only. No MaintainX calls
// originated from the UI.
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";

export default function DispatchEquipmentMaintenanceIndicator() {
  const [count, setCount] = useState(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const r = await api.get("/integrations/maintainx/defect-coverage", {
          params: { sample_limit: 1, since_days: 60 },
        });
        if (active) setCount(r.data?.totals?.out_of_service ?? 0);
      } catch {
        if (active) setCount(null);
      }
    })();
    return () => { active = false; };
  }, []);

  if (count === null || count === 0) return null;

  return (
    <div
      className="bg-white border border-amber-300 rounded-md px-3 py-2 flex items-center justify-between gap-3"
      data-testid="dispatch-mx-indicator"
    >
      <div className="flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-700" />
        <span className="text-sm text-slate-800">
          <strong>Equipment Maintenance Issues Requiring Attention:</strong>{" "}
          <span className="font-display font-black text-lg tabular-nums" data-testid="dispatch-mx-count">
            {count}
          </span>
        </span>
      </div>
      <Link
        to="/dispatch/board"
        className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate-700 hover:text-slate-900 underline"
        data-testid="dispatch-mx-link"
      >
        View Equipment Status
      </Link>
    </div>
  );
}
