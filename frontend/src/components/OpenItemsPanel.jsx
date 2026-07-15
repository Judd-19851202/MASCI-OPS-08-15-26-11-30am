import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, AlertOctagon, AlertTriangle, RefreshCw, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { formatDateLong } from "@/lib/utils";

/**
 * Lists every still-open FAIL line (no shop sign-off yet) across every
 * equipment inspection. Lets the shop drill straight into the inspection
 * to record a sign-off.
 *
 * Backed by GET /api/admin/equipment-inspections/open-items.
 */
const OpenItemsPanel = ({ baseHref = "/admin/equipment", testIdPrefix = "open-items" }) => {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [severity, setSeverity] = useState("all"); // all | oos | attn

  const load = useCallback(async (sev = severity) => {
    setLoading(true);
    try {
      const r = await api.get(`/admin/equipment-inspections/open-items?severity=${sev}`);
      setItems(r.data?.items || []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [severity]);

  useEffect(() => {
    load(severity);
  }, [load, severity]);

  const onChangeSeverity = (s) => {
    setSeverity(s);
    load(s);
  };

  // Track 21.1 tech-debt: hoist SevPill out of parent in a future refactor (Track 21.y).
  // Kept in place here to preserve tightly-coupled testIdPrefix + t() closure with no runtime change.
  // eslint-disable-next-line react/no-unstable-nested-components
  const SevPill = ({ sev }) => {
    if (sev === "oos") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-black tracking-[0.1em] bg-red-700 text-white" data-testid={`${testIdPrefix}-sev-oos`}>
          <AlertOctagon className="w-3 h-3" /> {t("OUT OF SERVICE")}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-black tracking-[0.1em] bg-amber-500 text-white" data-testid={`${testIdPrefix}-sev-attn`}>
        <AlertTriangle className="w-3 h-3" /> {t("NEEDS ATTENTION")}
      </span>
    );
  };

  return (
    <div className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid={`${testIdPrefix}-panel`}>
      <div className="bg-slate-900 text-white px-4 py-3 flex items-center gap-3 flex-wrap">
        <Wrench className="w-5 h-5 text-amber-400" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-400 font-bold flex-1">
          {t("Open Shop Items")}
        </span>
        <select
          value={severity}
          onChange={(e) => onChangeSeverity(e.target.value)}
          className="bg-slate-800 text-white border border-slate-700 rounded px-2 py-1 text-xs font-mono"
          data-testid={`${testIdPrefix}-severity-select`}
        >
          <option value="all">{t("All severities")}</option>
          <option value="oos">{t("Out of Service only")}</option>
          <option value="attn">{t("Needs Attention only")}</option>
        </select>
        <Button
          onClick={() => load(severity)}
          variant="ghost"
          size="sm"
          className="text-slate-300 hover:text-white hover:bg-slate-800 h-8 px-2"
          data-testid={`${testIdPrefix}-refresh-btn`}
          title={t("Refresh")}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {loading ? (
        <div className="p-8 flex items-center justify-center text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> {t("Loading…")}
        </div>
      ) : items.length === 0 ? (
        <div className="p-8 text-center text-slate-500" data-testid={`${testIdPrefix}-empty`}>
          <span className="font-display text-xl font-bold text-emerald-700">{t("All clear.")}</span>
          <p className="text-sm mt-1">{t("Every Pre-Op fail has been signed off by the shop.")}</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid={`${testIdPrefix}-table`}>
            <thead>
              <tr className="border-b-2 border-slate-200 bg-slate-50">
                <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Severity")}</th>
                <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Unit")}</th>
                <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Failed item")}</th>
                <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Operator")}</th>
                <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Date")}</th>
                <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Action")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it, i) => (
                <tr key={`${it.inspection_id}-${it.key}-${i}`} className="border-b border-slate-100 hover:bg-amber-50">
                  <td className="px-3 py-2"><SevPill sev={it.severity} /></td>
                  <td className="px-3 py-2 font-bold text-slate-900">{it.equipment_type} · {it.equipment_unit}</td>
                  <td className="px-3 py-2 text-slate-800">
                    <div>{it.item}</div>
                    {it.operator_note && (
                      <div className="text-xs italic text-slate-500 mt-0.5">↳ {it.operator_note}</div>
                    )}
                  </td>
                  <td className="px-3 py-2 text-slate-700">{it.operator_name || "—"}</td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-500">
                    {it.inspection_date ? formatDateLong(it.inspection_date) : "—"}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Link
                      to={`${baseHref}/${it.inspection_id}`}
                      className="inline-flex items-center justify-center h-8 px-3 rounded bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs uppercase tracking-wide"
                      data-testid={`${testIdPrefix}-open-${it.inspection_id}`}
                    >
                      {t("Sign Off")}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default OpenItemsPanel;
