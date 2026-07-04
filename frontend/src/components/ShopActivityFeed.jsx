import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, RefreshCw, Hammer, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

/**
 * Last N shop sign-offs, newest first. Two purposes:
 *   1. Workflow log so the shop can see what's been touched lately.
 *   2. Credibility log for owners + insurance auditors — proof that
 *      every flagged FAIL was reviewed and resolved by name + date.
 *
 * Backed by GET /api/shop/activity?limit=20.
 */
const ShopActivityFeed = ({ baseHref = "/shop/equipment", limit = 20, testIdPrefix = "shop-activity" }) => {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get(`/shop/activity?limit=${limit}`);
      setItems(r.data?.items || []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);  

  const fmt = (iso) => {
    if (!iso) return "—";
    try {
      const d = new Date(iso);
      return d.toLocaleString();
    } catch {
      return iso;
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid={`${testIdPrefix}-panel`}>
      <div className="bg-slate-900 text-white px-4 py-3 flex items-center gap-3">
        <Hammer className="w-5 h-5 text-emerald-400" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-emerald-400 font-bold flex-1">
          {t("Shop Activity Feed")}
        </span>
        <Button
          onClick={load}
          variant="ghost"
          size="sm"
          className="text-slate-300 hover:text-white hover:bg-slate-800 h-8 px-2"
          data-testid={`${testIdPrefix}-refresh`}
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
          {t("No sign-offs recorded yet. Once the shop closes out a FAIL it will appear here.")}
        </div>
      ) : (
        <ul className="divide-y divide-slate-100" data-testid={`${testIdPrefix}-list`}>
          {items.map((s, i) => (
            <li key={`${s.inspection_id}-${s.section}-${s.item}-${i}`} className="px-4 py-3 hover:bg-emerald-50">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-slate-900">{s.signed_by || "—"}</span>
                    <span className="text-slate-500">·</span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-emerald-600 text-white text-[10px] font-mono uppercase tracking-wider font-bold">
                      {s.action_taken || t("Signed off")}
                    </span>
                  </div>
                  <div className="text-sm text-slate-700 mt-0.5">
                    <span className="font-semibold">{s.equipment_type} · {s.equipment_unit}</span>
                    <span className="text-slate-400"> — </span>
                    {s.item}
                  </div>
                  {s.notes && (
                    <div className="text-xs italic text-slate-500 mt-0.5">&quot;{s.notes}&quot;</div>
                  )}
                  <div className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mt-1">
                    {fmt(s.signed_at)} {s.project_number ? `· #${s.project_number}` : ""}
                  </div>
                </div>
                <Link
                  to={`${baseHref}/${s.inspection_id}`}
                  className="inline-flex items-center gap-1 text-emerald-700 hover:text-emerald-900 text-xs font-bold uppercase tracking-wide"
                  data-testid={`${testIdPrefix}-link-${i}`}
                >
                  {t("Open")} <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ShopActivityFeed;
