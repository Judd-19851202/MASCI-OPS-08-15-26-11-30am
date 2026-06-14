// iter353d · FL Accountability Mini-Widget.
// Compact read-only employee accountability lookup used inside FL
// portal surfaces (Driver Readiness row drawer + FL Dashboard
// employee lookup card). Renders the
// /api/field-leadership/portal/employee/:id/snapshot payload as a
// dispatch-grade readiness card with one-click drill into the full
// iter353c accountability timeline.
import React, { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import {
  ShieldCheck, AlertTriangle, Activity, Truck, FileCheck2,
  CircleSlash, ArrowRight, X, Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { getFlToken } from "@/lib/flAuth";
import { operationalError } from "@/lib/errors";
import { useT } from "@/lib/i18n";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function ReadinessBadge({ ready }) {
  const { t } = useT();
  return ready ? (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-600 text-white text-[10px] font-mono uppercase tracking-wider rounded">
      <ShieldCheck className="w-3 h-3" /> {t("Dispatchable")}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-rose-600 text-white text-[10px] font-mono uppercase tracking-wider rounded">
      <CircleSlash className="w-3 h-3" /> {t("Not dispatchable")}
    </span>
  );
}

function MetricRow({ icon: Icon, label, value, tint = "slate" }) {
  const tints = {
    slate: "text-slate-700",
    amber: "text-amber-700 font-bold",
    rose: "text-rose-700 font-bold",
  };
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-slate-100 last:border-0">
      <div className="flex items-center gap-2 text-xs text-slate-600">
        <Icon className="w-3.5 h-3.5" /> {label}
      </div>
      <div className={`font-mono text-sm ${tints[tint]}`}>{value}</div>
    </div>
  );
}

/**
 * FL Mini-Widget.
 * Props:
 *   - employeeId: required
 *   - onClose: optional (renders an X button if provided)
 *   - compact: bool — when true, suppresses the heading + footer link
 */
export default function FlAccountabilityWidget({ employeeId, onClose, compact = false }) {
  const { t } = useT();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true); setErr("");
      try {
        const r = await axios.get(
          `${API}/field-leadership/portal/employee/${employeeId}/snapshot`,
          { headers: { "X-FL-Token": getFlToken() || "" } },
        );
        if (alive) setData(r.data);
      } catch (e) {
        if (alive) setErr(operationalError(e, t("Could not load employee snapshot.")));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [employeeId, t]);

  if (loading) {
    return (
      <div className="bg-white border-2 border-red-200 rounded-md p-4 flex items-center gap-2 text-sm text-slate-600" data-testid="fl-widget-loading">
        <Loader2 className="w-4 h-4 animate-spin" /> {t("Loading employee snapshot…")}
      </div>
    );
  }
  if (err) {
    return (
      <div className="bg-rose-50 border border-rose-300 rounded-md p-3 text-sm text-rose-900" data-testid="fl-widget-error">
        {err}
      </div>
    );
  }
  if (!data) return null;

  const emp = data.employee || {};
  const r = data.readiness || {};

  return (
    <div className="bg-white border-2 border-red-700 rounded-md overflow-hidden" data-testid="fl-widget">
      <div className="bg-slate-900 px-4 py-2.5 flex items-center justify-between border-b-4 border-red-700">
        <div className="min-w-0">
          {!compact && (
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-400 font-bold">
              {t("Field Leadership · Accountability Lookup")}
            </div>
          )}
          <div className="text-white font-display font-black text-lg leading-tight truncate" data-testid="fl-widget-name">
            {emp.name}
          </div>
          <div className="text-xs text-slate-300 mt-0.5">
            {emp.trade || "—"}{emp.employee_id ? <span className="ml-2 font-mono text-[10px]">#{emp.employee_id}</span> : null}
          </div>
        </div>
        {onClose ? (
          <Button variant="ghost" size="icon" onClick={onClose} className="text-white hover:bg-white/10" data-testid="fl-widget-close" aria-label="Close" title="Close">
            <X className="w-4 h-4" />
          </Button>
        ) : null}
      </div>

      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between" data-testid="fl-widget-readiness">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">
            {t("Operational readiness")}
          </div>
          <ReadinessBadge ready={!!r.available_now} />
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded p-2">
          <MetricRow icon={Truck} label={t("CDL")} value={emp.cdl_expiration_date || "—"} />
          <MetricRow icon={FileCheck2} label={t("Medical card")} value={emp.medical_card_expiration_date || "—"} />
          <MetricRow icon={ShieldCheck} label={t("Approved driver")} value={emp.approved_company_driver ? t("Yes") : t("No")} />
          <MetricRow icon={Activity} label={t("Driver status")} value={emp.driver_status || "—"} />
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded p-2">
          <MetricRow icon={Activity} label={t("Training records")} value={r.training_record_count || 0} />
          <MetricRow icon={ShieldCheck} label={t("PPE records")} value={r.ppe_record_count || 0} />
          <MetricRow
            icon={AlertTriangle}
            label={t("Expiring ≤30d")}
            value={r.expiring_within_30d || 0}
            tint={r.expiring_within_30d ? "amber" : "slate"}
          />
          <MetricRow
            icon={CircleSlash}
            label={t("Expired")}
            value={r.expired_count || 0}
            tint={r.expired_count ? "rose" : "slate"}
          />
          <MetricRow
            icon={AlertTriangle}
            label={t("Incidents (1y)")}
            value={r.incident_count_last_365d || 0}
            tint={r.incident_count_last_365d ? "amber" : "slate"}
          />
        </div>

        {(data.expired?.length || 0) > 0 ? (
          <div className="bg-rose-50 border-l-4 border-rose-500 px-2 py-1.5 text-xs text-rose-900" data-testid="fl-widget-expired-strip">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold">{t("Expired")}</div>
            <ul className="mt-0.5 space-y-0.5">
              {data.expired.slice(0, 3).map((e, i) => (
                <li key={i}><strong>{e.title}</strong> · <span className="font-mono">{e.expiration_date}</span></li>
              ))}
            </ul>
          </div>
        ) : null}

        {!compact ? (
          <Link
            to={`/hr/employees/${employeeId}/accountability`}
            className="flex items-center justify-between bg-red-50 hover:bg-red-100 border border-red-300 rounded px-3 py-2 text-xs font-mono uppercase tracking-wider text-red-900 mt-2"
            data-testid="fl-widget-open-timeline"
          >
            {t("Open full accountability timeline")}
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        ) : null}
      </div>
    </div>
  );
}
