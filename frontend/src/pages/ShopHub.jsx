import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Wrench, Eye, AlertOctagon, Loader2, LogOut, Truck, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import EquipmentTrendsPanel from "@/components/EquipmentTrendsPanel";
import OpenItemsPanel from "@/components/OpenItemsPanel";
import ShopActivityFeed from "@/components/ShopActivityFeed";
import PartsCatalog from "@/components/PartsCatalog";
import EquipmentMasterPanel from "@/components/EquipmentMasterPanel";
import IntegrationHealthCard from "@/components/IntegrationHealthCard";
import IntegrationEventsCard from "@/components/IntegrationEventsCard";
import { LangToggle } from "@/components/LangToggle";
import PortalSwitcher from "@/components/PortalSwitcher";
import { api } from "@/lib/api";
import { formatDateLong } from "@/lib/utils";
import { clearShopToken, getShopToken } from "@/lib/shopAuth";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearPmToken } from "@/lib/pmAuth";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

/**
 * Shop / mechanic console — a focused subset of the admin equipment
 * dashboard: trends, open items needing sign-off, recent inspections,
 * and the master equipment list. Intentionally has NO access to
 * incidents / dailies / meetings / inspections / settings.
 */
export default function ShopHub() {
  const { t } = useT();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [equipmentMaster, setEquipmentMaster] = useState({ items: [], grouped: {}, count: 0 });
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("open"); // open | activity | trends | recent | equipment | parts
  const [me, setMe] = useState(null); // per-shop-user identity, null for legacy/admin

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/shop/me");
        if (!alive) return;
        // /shop/me returns {ok, user} for per-user OR {ok, is_legacy: true}
        // for admin/shared. We only show the change-pw button when there's
        // a real shop user behind the token — admins use /admin reset flow.
        if (r.data?.user?.id) setMe(r.data.user);
      } catch {
        // Endpoint failure is non-fatal — just hide the button.
      }
    })();
    return () => { alive = false; };
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const [insp, eq] = await Promise.all([
        api.get("/equipment-inspections"),
        api.get("/equipment-master"),
      ]);
      setItems(insp.data || []);
      setEquipmentMaster(eq.data || { items: [], grouped: {}, count: 0 });
    } catch {
      toast.error(t("Could not load shop data"));
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, []); // eslint-disable-line

  const failCount = items.filter((i) => (i.fail_count || 0) > 0).length;
  const totalSigned = items.reduce((acc, i) => acc + (i.signoff_count ?? (i.shop_signoffs || []).length), 0);

  const onLogout = () => {
    // Wipe every tier on sign-out so a shared trailer phone can't leak
    // an identity to the next user.
    clearShopToken();
    clearAdminToken();
    clearPmToken();
    navigate("/");
  };

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-amber-500">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <Link to="/" className="inline-flex items-center text-white hover:text-amber-300 text-sm font-bold uppercase tracking-wide" data-testid="shop-back-hub">
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <div className="flex items-center gap-2">
            <PortalSwitcher current="shop" />
            <LangToggle />
            {me && (
              <Button
                onClick={() => navigate("/shop/change-password")}
                variant="outline"
                className="h-10 px-3 border-2 border-amber-400 text-amber-400 hover:bg-amber-500 hover:text-white bg-transparent font-bold uppercase tracking-wide text-xs hidden sm:inline-flex"
                title={`Signed in as ${me.email}`}
                data-testid="shop-change-pw-link"
              >
                <KeyRound className="w-4 h-4 mr-1" /> {t("Change password")}
              </Button>
            )}
            <Button
              onClick={onLogout}
              variant="outline"
              className="h-10 px-3 border-2 border-amber-400 text-amber-400 hover:bg-amber-500 hover:text-white bg-transparent font-bold uppercase tracking-wide text-xs"
              data-testid="shop-logout-btn"
            >
              <LogOut className="w-4 h-4 mr-1" /> {t("Sign out")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12 space-y-6">
        <div>
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-amber-700 font-bold">
            {t("Shop Console")}
          </span>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-2">
            {t("Pre-Op & Equipment")}
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
            {t("Every Pre-Op inspection. Sign off on Out-of-Service and Needs-Attention items so jobs can keep moving.")}
          </p>
        </div>

        {/* KPI strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3" data-testid="shop-kpi-strip">
          <Kpi label={t("Inspections on file")} value={items.length} />
          <Kpi label={t("Units flagged FAIL")} value={failCount} valueClass="text-red-700" />
          <Kpi label={t("Shop sign-offs")} value={totalSigned} valueClass="text-emerald-700" />
          <Kpi label={t("Equipment in fleet")} value={equipmentMaster.count} />
        </div>

        {/* Tabs */}
        <div className="flex border-b-2 border-slate-200">
          {[
            { key: "open", label: t("Open Items") },
            { key: "activity", label: t("Activity Feed") },
            { key: "trends", label: t("Trends") },
            { key: "recent", label: t("Recent Inspections") },
            { key: "equipment", label: t("Equipment List") },
            { key: "parts", label: t("Parts Catalog") },
            { key: "integrations", label: t("Integrations") },
          ].map((s) => (
            <button
              key={s.key}
              type="button"
              onClick={() => setTab(s.key)}
              className={`px-4 py-3 text-xs font-mono uppercase tracking-[0.18em] font-bold border-b-4 -mb-0.5 transition-colors ${
                tab === s.key
                  ? "text-amber-700 border-amber-600 bg-amber-50"
                  : "text-slate-500 border-transparent hover:bg-slate-50"
              }`}
              data-testid={`shop-tab-${s.key}`}
            >
              {s.label}
            </button>
          ))}
        </div>

        {tab === "open" && (
          <OpenItemsPanel baseHref="/shop/equipment" testIdPrefix="shop-open" />
        )}
        {tab === "activity" && <ShopActivityFeed baseHref="/shop/equipment" testIdPrefix="shop-activity" />}
        {tab === "trends" && <EquipmentTrendsPanel />}
        {tab === "recent" && (
          <div className="bg-white border-2 border-slate-200 rounded-md overflow-hidden">
            <div className="px-4 py-3 bg-slate-900 text-white flex items-center gap-2">
              <Wrench className="w-5 h-5 text-amber-400" />
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-400 font-bold">
                {t("Recent Pre-Op Inspections")}
              </span>
            </div>
            {loading ? (
              <div className="p-12 flex items-center justify-center text-slate-500">
                <Loader2 className="w-6 h-6 animate-spin mr-2" /> {t("Loading…")}
              </div>
            ) : items.length === 0 ? (
              <div className="p-10 text-center text-slate-500" data-testid="shop-recent-empty">
                {t("No equipment inspections yet.")}
              </div>
            ) : (
              <ul className="divide-y-2 divide-slate-100" data-testid="shop-recent-list">
                {items.slice(0, 50).map((it) => {
                  const fail = (it.fail_count || 0) > 0;
                  const signed = it.signoff_count ?? (it.shop_signoffs || []).length;
                  const cleared = it.cleared || (fail && signed >= (it.fail_count || 0));
                  return (
                    <li
                      key={it.id}
                      onClick={() => navigate(`/shop/equipment/${it.id}`)}
                      className={`p-4 sm:p-5 hover:bg-amber-50 cursor-pointer transition-colors flex flex-col sm:flex-row sm:items-center gap-3 ${fail && !cleared ? "border-l-4 border-red-700" : cleared ? "border-l-4 border-emerald-600" : ""}`}
                      data-testid={`shop-equipment-row-${it.id}`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-display text-lg font-bold text-slate-900 truncate">
                            {it.equipment_type} · {it.equipment_unit}
                          </span>
                          {fail && !cleared && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-700 text-white text-[10px] font-mono uppercase tracking-wider rounded">
                              <AlertOctagon className="w-3 h-3" /> {it.fail_count} {t("FAIL")}
                            </span>
                          )}
                          {cleared && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-600 text-white text-[10px] font-mono uppercase tracking-wider rounded" data-testid={`shop-cleared-${it.id}`}>
                              ✓ {t("CLEARED TO OPERATE")}
                            </span>
                          )}
                          {signed > 0 && !cleared && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-600 text-white text-[10px] font-mono uppercase tracking-wider rounded">
                              ✓ {signed} {t("signed")}
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-slate-600 mt-1">
                          {it.project_name || "—"} {it.project_number ? `· #${it.project_number}` : ""} · {t("Operator")}: {it.operator_name || "—"}
                        </div>
                        <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500 mt-1">
                          {formatDateLong(it.inspection_date)} · {it.location || "—"}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Link
                          to={`/shop/equipment/${it.id}`}
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center justify-center h-10 px-4 rounded-md bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm uppercase tracking-wide"
                          data-testid={`shop-view-${it.id}`}
                        >
                          <Eye className="w-4 h-4 mr-1" /> {t("View")}
                        </Link>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}
        {tab === "equipment" && <EquipmentMasterPanel />}
        {tab === "parts" && <PartsCatalog />}
        {tab === "integrations" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" data-testid="shop-integrations-tab">
            <IntegrationHealthCard
              tokenHeader={{ "X-Shop-Token": getShopToken() || "" }}
              accent="orange"
              showAdminLink={false}
            />
            <IntegrationEventsCard
              provider="maintainx"
              tokenHeader={{ "X-Shop-Token": getShopToken() || "" }}
              accent="orange"
              limit={8}
            />
          </div>
        )}
      </main>
    </div>
  );
}

const Kpi = ({ label, value, valueClass = "text-slate-900" }) => (
  <div className="bg-white border-2 border-slate-200 rounded-md px-4 py-3">
    <div className={`font-display text-3xl font-black ${valueClass}`}>{value}</div>
    <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500 mt-1">{label}</div>
  </div>
);

const EquipmentListPanel = ({ master, loading }) => {
  const { t } = useT();
  const [filter, setFilter] = useState("");
  const [cat, setCat] = useState("all");
  const cats = Object.keys(master.grouped || {}).sort();

  const filtered = (master.items || []).filter((it) => {
    if (cat !== "all" && it.category !== cat) return false;
    if (!filter) return true;
    const s = filter.toLowerCase();
    return (
      (it.unit_number || "").toLowerCase().includes(s) ||
      (it.make || "").toLowerCase().includes(s) ||
      (it.model || "").toLowerCase().includes(s) ||
      (it.category || "").toLowerCase().includes(s)
    );
  });

  return (
    <div className="bg-white border-2 border-slate-200 rounded-md overflow-hidden" data-testid="shop-equipment-list">
      <div className="px-4 py-3 bg-slate-900 text-white flex items-center gap-2 flex-wrap">
        <Truck className="w-5 h-5 text-amber-400" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-400 font-bold flex-1">
          {t("MASCI Fleet")} · {master.count} {t("units")}
        </span>
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder={t("Search unit, make, model…")}
          className="bg-slate-800 text-white placeholder:text-slate-500 border border-slate-700 rounded px-2 py-1 text-xs"
          data-testid="shop-equipment-search"
        />
        <select
          value={cat}
          onChange={(e) => setCat(e.target.value)}
          className="bg-slate-800 text-white border border-slate-700 rounded px-2 py-1 text-xs font-mono"
          data-testid="shop-equipment-cat"
        >
          <option value="all">{t("All categories")}</option>
          {cats.map((c) => (
            <option key={c} value={c}>{c} ({master.grouped[c]?.length || 0})</option>
          ))}
        </select>
      </div>
      {loading ? (
        <div className="p-12 flex items-center justify-center text-slate-500">
          <Loader2 className="w-6 h-6 animate-spin mr-2" /> {t("Loading…")}
        </div>
      ) : (
        <div className="overflow-x-auto max-h-[500px]">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-slate-50">
              <tr className="border-b-2 border-slate-200">
                <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Unit #")}</th>
                <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Make")}</th>
                <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Model")}</th>
                <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Category")}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u, i) => (
                <tr key={`${u.unit_number}-${i}`} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-bold font-mono text-slate-900">{u.unit_number}</td>
                  <td className="px-3 py-2 text-slate-800">{u.make || "—"}</td>
                  <td className="px-3 py-2 text-slate-700">{u.model || "—"}</td>
                  <td className="px-3 py-2 text-slate-500 text-xs">{u.category || "—"}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center text-slate-500 py-8">{t("No matching equipment.")}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
