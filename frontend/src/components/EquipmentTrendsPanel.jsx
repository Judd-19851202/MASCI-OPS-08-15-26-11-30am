import { useEffect, useState } from "react";
import { TrendingUp, AlertOctagon, AlertTriangle, RefreshCw, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

/**
 * Three-up leaderboard: Equipment / Operators / Jobsites with the most
 * Out-of-Service + Needs-Attention fails in the configurable window
 * (default 90 days). Embedded near the top of /admin/equipment.
 */
const EquipmentTrendsPanel = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(90);
  const [tab, setTab] = useState("equipment");

  const load = async (windowDays = days) => {
    setLoading(true);
    try {
      const r = await api.get(`/admin/equipment-inspections/trends?days=${windowDays}`);
      setData(r.data);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const tabs = [
    { key: "equipment", label: "Equipment", count: data?.equipment?.length || 0 },
    { key: "operators", label: "Operators", count: data?.operators?.length || 0 },
    { key: "jobsites",  label: "Jobsites",  count: data?.jobsites?.length  || 0 },
  ];

  return (
    <div
      className="bg-white border-2 border-slate-200 rounded-md overflow-hidden mb-6"
      data-testid="equipment-trends-panel"
    >
      <div className="bg-slate-900 text-white px-4 py-3 flex items-center gap-3 flex-wrap">
        <TrendingUp className="w-5 h-5 text-amber-400" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-400 font-bold flex-1">
          Pre-Op Trends
        </span>
        <select
          value={days}
          onChange={(e) => {
            const v = Number(e.target.value);
            setDays(v);
            load(v);
          }}
          className="bg-slate-800 text-white border border-slate-700 rounded px-2 py-1 text-xs font-mono"
          data-testid="trends-window-select"
        >
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={180}>Last 180 days</option>
          <option value={365}>Last 12 months</option>
        </select>
        <Button
          onClick={() => load(days)}
          variant="ghost"
          size="sm"
          className="text-slate-300 hover:text-white hover:bg-slate-800 h-8 px-2"
          data-testid="trends-refresh-btn"
          title="Refresh"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {/* KPI strip */}
      {data && (
        <div className="grid grid-cols-3 border-b border-slate-200">
          <Stat
            label="Inspections"
            value={data.totals.inspections}
            icon={null}
            color="text-slate-900"
          />
          <Stat
            label="Out of Service fails"
            value={data.totals.out_of_service_fails}
            icon={<AlertOctagon className="w-3 h-3" />}
            color="text-red-700"
          />
          <Stat
            label="Needs Attention fails"
            value={data.totals.needs_attention_fails}
            icon={<AlertTriangle className="w-3 h-3" />}
            color="text-amber-700"
          />
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={`flex-1 px-3 py-2.5 text-xs font-mono uppercase tracking-[0.18em] font-bold border-b-2 transition-colors ${
              tab === t.key
                ? "text-red-700 border-red-700 bg-red-50"
                : "text-slate-500 border-transparent hover:bg-slate-50"
            }`}
            data-testid={`trends-tab-${t.key}`}
          >
            {t.label}{" "}
            <span className="ml-1 opacity-70 normal-case font-normal tracking-normal">
              ({t.count})
            </span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="p-8 flex items-center justify-center text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading trends…
        </div>
      ) : !data ? (
        <div className="p-6 text-sm text-slate-500 text-center">
          Could not load trends.
        </div>
      ) : (
        <Table data={data[tab] || []} kind={tab} />
      )}
    </div>
  );
};

const Stat = ({ label, value, icon, color }) => (
  <div className="px-4 py-3 text-center border-r last:border-r-0 border-slate-200">
    <div className={`font-display text-2xl font-black flex items-center justify-center gap-1 ${color}`}>
      {icon}
      {value}
    </div>
    <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500 mt-0.5">
      {label}
    </div>
  </div>
);

const Table = ({ data, kind }) => {
  if (!data.length) {
    return (
      <div className="p-6 text-sm text-slate-500 text-center">
        No fails in this window for {kind}.
      </div>
    );
  }
  const cols = {
    equipment: [
      { label: "Unit", get: (r) => `${r.equipment_type || "?"} · ${r.equipment_unit || "?"}` },
      { label: "Inspections", get: (r) => r.inspections },
    ],
    operators: [
      { label: "Operator", get: (r) => r.operator_name },
      { label: "Inspections", get: (r) => r.inspections },
    ],
    jobsites: [
      { label: "Job #", get: (r) => r.project_number || r.project_name || "—" },
      { label: "Inspections", get: (r) => r.inspections },
    ],
  }[kind];

  return (
    <div className="overflow-x-auto" data-testid={`trends-table-${kind}`}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b-2 border-slate-200 bg-slate-50">
            {cols.map((c, i) => (
              <th key={i} className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
                {c.label}
              </th>
            ))}
            <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">
              OOS Fails
            </th>
            <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-amber-700 font-bold">
              Needs Attn
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
              {cols.map((c, j) => (
                <td key={j} className="px-3 py-2 text-slate-800">
                  {j === 0 ? <span className="font-bold">{c.get(row)}</span> : c.get(row)}
                </td>
              ))}
              <td className="px-3 py-2 text-right font-mono font-bold text-red-700">
                {row.oos_fails}
              </td>
              <td className="px-3 py-2 text-right font-mono font-bold text-amber-700">
                {row.attn_fails}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default EquipmentTrendsPanel;
