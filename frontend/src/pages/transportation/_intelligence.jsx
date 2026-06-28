/**
 * TRACK 16.12 · Transportation Operations Intelligence — UI center.
 *
 * Native MASCI styling. Reuses PortalShell wrapper from
 * TransportationApp + shared chips / cards. Three tabs:
 *   - Executive (dashboard)
 *   - Recommendations
 *   - Predictions
 *
 * Strictly read-only. Never writes intelligence.
 */
import React, { useCallback, useEffect, useState } from "react";
import { NavLink, Routes, Route } from "react-router-dom";
import {
  Activity, ListChecks, TrendingUp, RefreshCw, ShieldCheck, Star,
  AlertTriangle, Users, Building2, Truck as TruckIcon,
} from "lucide-react";
import { api } from "@/lib/api";
import { adminHeaders, PageHeader, EmptyState } from "./_shared";

const SUB_TABS = [
  { to: "", label: "Executive", end: true, testid: "tx-intel-tab-exec",
    icon: Activity },
  { to: "recommendations", label: "Recommendations",
    testid: "tx-intel-tab-recs", icon: Star },
  { to: "predictions", label: "Predictions",
    testid: "tx-intel-tab-pred", icon: TrendingUp },
];

const BAND_PALETTE = {
  excellent: "bg-emerald-100 text-emerald-800 border-emerald-300",
  strong: "bg-emerald-50 text-emerald-800 border-emerald-200",
  fair: "bg-amber-100 text-amber-800 border-amber-300",
  watch: "bg-amber-200 text-amber-900 border-amber-400",
  critical: "bg-rose-100 text-rose-800 border-rose-300",
};

function BandChip({ band, testid }) {
  if (!band) return null;
  const cls = BAND_PALETTE[band.grade] || "bg-slate-100 text-slate-700 border-slate-300";
  return (
    <span data-testid={testid} className={`px-2 py-0.5 rounded-full border text-[11px] font-medium ${cls}`}>
      {Math.round(band.score)} · {band.grade}
    </span>
  );
}

export function IntelligenceCenter() {
  return (
    <div data-testid="tx-intel-center" className="space-y-4">
      <PageHeader
        title="Operations Intelligence"
        subtitle="One engine · explainable scoring · deterministic forecasts"
        right={<ShieldCheck className="h-5 w-5 text-emerald-700" />}
      />
      <div className="flex items-center gap-1 border-b border-slate-200">
        {SUB_TABS.map((t) => (
          <NavLink
            key={t.to || "exec"}
            to={`/admin/transportation/intelligence/${t.to}`}
            end={t.end}
            className={({ isActive }) =>
              `inline-flex items-center gap-1 px-3 py-2 text-sm border-b-2 ${
                isActive
                  ? "border-blue-600 text-blue-700 font-medium"
                  : "border-transparent text-slate-600 hover:text-slate-900"}`}
            data-testid={t.testid}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </NavLink>
        ))}
      </div>
      <Routes>
        <Route index element={<ExecutiveDashboard />} />
        <Route path="recommendations" element={<RecommendationsPanel />} />
        <Route path="predictions" element={<PredictionsPanel />} />
      </Routes>
    </div>
  );
}


// ───────────────────────────── Executive ─────────────────────────────
function ExecutiveDashboard() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/transportation/intelligence/dashboard",
        { headers: adminHeaders() });
      setData(r.data);
      setErr(null);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (loading && !data) return <div data-testid="tx-intel-exec-loading" className="text-sm text-slate-500">Loading…</div>;
  if (err) return <div data-testid="tx-intel-exec-error" className="text-sm text-rose-700">{err}</div>;
  if (!data) return <EmptyState title="No intelligence yet" testid="tx-intel-exec-empty" />;

  return (
    <div data-testid="tx-intel-exec" className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <HealthTile label="Transportation" band={data.transportation_health} testid="tx-intel-health-transportation" />
        <HealthTile label="Driver" band={data.driver_health} testid="tx-intel-health-driver" />
        <HealthTile label="Carrier" band={data.carrier_health} testid="tx-intel-health-carrier" />
        <HealthTile label="Truck" band={data.truck_health} testid="tx-intel-health-truck" />
        <HealthTile label="Dispatch readiness" band={data.dispatch_readiness} testid="tx-intel-dispatch-readiness" />
      </div>

      <section className="border border-slate-200 rounded-md bg-white p-4">
        <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <Users className="h-4 w-4 text-slate-500" /> Capacity
        </h3>
        <div className="grid grid-cols-3 gap-3 text-sm">
          <CapacityTile label="Drivers" data={data.capacity?.drivers} icon={Users} testid="tx-intel-capacity-drivers" />
          <CapacityTile label="Trucks" data={data.capacity?.trucks} icon={TruckIcon} testid="tx-intel-capacity-trucks" />
          <CapacityTile label="Carriers" data={data.capacity?.carriers} icon={Building2} testid="tx-intel-capacity-carriers" />
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <PerformerList title="Top performers" testid="tx-intel-top" data={data.top_performers} />
        <PerformerList title="Attention required" testid="tx-intel-attention" data={data.attention_required} negative />
      </div>

      <section className="border border-slate-200 rounded-md bg-white p-4" data-testid="tx-intel-trends">
        <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-slate-500" /> Trends
        </h3>
        <div className="grid grid-cols-3 gap-3 text-xs">
          {["30d", "90d", "365d"].map((k) => (
            <div key={k} className="border border-slate-200 rounded p-3" data-testid={`tx-intel-trend-${k}`}>
              <div className="font-mono uppercase tracking-wider text-[10px] text-slate-500">{k}</div>
              {Object.entries(data.trends?.[k] || {}).map(([kind, v]) => (
                <div key={kind} className="mt-1 flex items-center justify-between">
                  <span className="text-slate-600">{kind.replace("_intelligence_refresh", "")}</span>
                  <span className="font-medium text-slate-900">
                    {v.avg_score ?? "—"} · n={v.samples}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>

      <div className="text-[10px] uppercase tracking-wide text-slate-400 flex items-center gap-3">
        <span>Schema {data.schema_version}</span>
        <span>· Generated {(data.generated_at || "").slice(0, 19).replace("T", " ")}</span>
        <button onClick={load} className="ml-auto inline-flex items-center gap-1 text-blue-600 hover:underline" data-testid="tx-intel-exec-refresh">
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>
    </div>
  );
}

function HealthTile({ label, band, testid }) {
  return (
    <div className="border border-slate-200 rounded-md bg-white p-3" data-testid={testid}>
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="mt-1 flex items-center justify-between">
        <div className="text-2xl font-semibold text-slate-900">{band ? Math.round(band.score) : "—"}</div>
        <BandChip band={band} testid={`${testid}-chip`} />
      </div>
    </div>
  );
}

function CapacityTile({ label, data, icon: Icon, testid }) {
  if (!data) return null;
  return (
    <div className="border border-slate-200 rounded-md p-3" data-testid={testid}>
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
        <Icon className="h-4 w-4 text-slate-400" />
      </div>
      <div className="mt-1 text-xl font-semibold text-slate-900">{data.total ?? 0}</div>
      {typeof data.pct_eligible === "number" && (
        <div className="text-[11px] text-slate-500 mt-1">
          {data.eligible ?? 0} eligible · {data.pct_eligible}%
        </div>
      )}
    </div>
  );
}

function PerformerList({ title, data, negative, testid }) {
  return (
    <section className="border border-slate-200 rounded-md bg-white p-4" data-testid={testid}>
      <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
        {negative
          ? <AlertTriangle className="h-4 w-4 text-amber-600" />
          : <Star className="h-4 w-4 text-emerald-600" />}
        {title}
      </h3>
      {["drivers", "carriers", "trucks"].map((cat) => (
        <div key={cat} className="mb-2 last:mb-0">
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">{cat}</div>
          <ul className="space-y-1">
            {(data?.[cat] || []).slice(0, 5).map((row) => (
              <li key={row.id} className="text-xs flex items-center justify-between border-b border-slate-100 py-1"
                  data-testid={`${testid}-${cat}-${row.id}`}>
                <span className="text-slate-800 truncate">{row.name}</span>
                <span className="font-mono text-[11px] text-slate-600">{Math.round(row.score)}</span>
              </li>
            ))}
            {(!data?.[cat] || data[cat].length === 0) && (
              <li className="text-[11px] text-slate-400">No data</li>
            )}
          </ul>
        </div>
      ))}
    </section>
  );
}


// ─────────────────────────── Recommendations ───────────────────────────
function RecommendationsPanel() {
  const [scope, setScope] = useState("triple");
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get(
        `/admin/transportation/intelligence/recommendations?scope=${scope}&limit=10`,
        { headers: adminHeaders() });
      setData(r.data);
      setErr(null);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [scope]);
  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid="tx-intel-recs" className="space-y-4">
      <div className="flex items-center gap-2 text-sm">
        {["triple", "driver", "carrier", "truck"].map((s) => (
          <button
            key={s}
            onClick={() => setScope(s)}
            className={`px-2 py-1 rounded text-xs border ${
              scope === s
                ? "border-blue-600 text-blue-700 bg-blue-50"
                : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}
            data-testid={`tx-intel-recs-scope-${s}`}
          >
            {s}
          </button>
        ))}
      </div>
      {err && <div className="text-sm text-rose-700">{err}</div>}
      {loading && !data && <div className="text-sm text-slate-500">Loading…</div>}

      {scope === "triple" && data && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          <RecommendationCard kind="Driver" item={data.driver} testid="tx-intel-rec-driver" />
          <RecommendationCard kind="Truck" item={data.truck} testid="tx-intel-rec-truck" />
          <RecommendationCard kind="Carrier" item={data.carrier} testid="tx-intel-rec-carrier" />
        </div>
      )}

      {scope !== "triple" && data && (
        <div className="space-y-2">
          {(data.items || []).map((it, i) => (
            <RecommendationCard
              key={it.driver_id || it.truck_id || it.carrier_id || i}
              kind={scope}
              item={it}
              testid={`tx-intel-rec-${scope}-${i}`}
            />
          ))}
          {(!data.items || data.items.length === 0) && (
            <div className="text-xs text-slate-500">No recommendations available.</div>
          )}
        </div>
      )}
    </div>
  );
}

function RecommendationCard({ kind, item, testid }) {
  if (!item) return (
    <div className="border border-slate-200 rounded-md p-3 bg-white text-xs text-slate-500" data-testid={`${testid}-empty`}>
      No {kind.toLowerCase()} candidate available.
    </div>
  );
  const name = item.display_name || item.legal_name || item.truck_number || item.driver_id || item.carrier_id || item.truck_id;
  return (
    <div className="border border-slate-200 rounded-md p-4 bg-white" data-testid={testid}>
      <div className="flex items-center justify-between mb-2">
        <div className="text-[10px] uppercase tracking-wider text-slate-500">{kind}</div>
        <BandChip band={item.overall} testid={`${testid}-chip`} />
      </div>
      <div className="font-semibold text-slate-900 mb-2">{name}</div>
      {item.why?.length > 0 && (
        <div className="text-[11px] text-slate-700">
          <div className="font-medium text-emerald-700 mb-0.5">Why</div>
          <ul className="space-y-0.5">
            {item.why.map((w, i) => (
              <li key={i} data-testid={`${testid}-why-${i}`}>• {w}</li>
            ))}
          </ul>
        </div>
      )}
      {item.watch?.length > 0 && (
        <div className="text-[11px] text-slate-600 mt-2">
          <div className="font-medium text-amber-700 mb-0.5">Watch</div>
          <ul className="space-y-0.5">
            {item.watch.map((w, i) => (
              <li key={i} data-testid={`${testid}-watch-${i}`}>• {w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}


// ─────────────────────────── Predictions ───────────────────────────
function PredictionsPanel() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const load = useCallback(async () => {
    try {
      const r = await api.get(
        "/admin/transportation/intelligence/predictions",
        { headers: adminHeaders() });
      setData(r.data);
      setErr(null);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (err) return <div className="text-sm text-rose-700">{err}</div>;
  if (!data) return <div className="text-sm text-slate-500">Loading…</div>;

  return (
    <div data-testid="tx-intel-pred" className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {["overdue", "due_this_week", "due_30_days", "due_90_days", "beyond_horizon"].map((b) => (
          <div key={b} className="border border-slate-200 rounded-md bg-white p-3"
               data-testid={`tx-intel-pred-bucket-${b}`}>
            <div className="text-[10px] uppercase tracking-wider text-slate-500">
              {b.replace(/_/g, " ")}
            </div>
            <div className="mt-1 text-2xl font-semibold text-slate-900">
              {data.by_bucket?.[b] ?? 0}
            </div>
          </div>
        ))}
      </div>

      <ForecastList title="Documentation expirations" items={data.documentation_expirations} testid="tx-intel-pred-docs" />
      <ForecastList title="Inspection expirations" items={data.inspection_expirations} testid="tx-intel-pred-insp" />
      <ForecastList title="Orientation renewals" items={data.orientation_renewals} testid="tx-intel-pred-orient" />

      <section className="border border-slate-200 rounded-md bg-white p-4" data-testid="tx-intel-pred-carrier-risk">
        <h3 className="font-semibold text-slate-800 mb-3">Carrier risk</h3>
        <ul className="space-y-1 text-xs">
          {(data.carrier_risk || []).map((r) => (
            <li key={r.subject_id} className="flex items-center justify-between border-b border-slate-100 py-1"
                data-testid={`tx-intel-pred-carrier-risk-${r.subject_id}`}>
              <span>{r.carrier_legal_name}</span>
              <span className={`text-[11px] px-2 py-0.5 rounded-full border ${
                r.risk === "high" ? "border-rose-300 text-rose-800 bg-rose-50" :
                r.risk === "elevated" ? "border-amber-300 text-amber-800 bg-amber-50" :
                r.risk === "watch" ? "border-amber-200 text-amber-700 bg-amber-50" :
                "border-emerald-300 text-emerald-800 bg-emerald-50"}`}>
                {r.risk} · {r.open_actions} actions
              </span>
            </li>
          ))}
          {(!data.carrier_risk || data.carrier_risk.length === 0) && (
            <li className="text-[11px] text-slate-400">No carriers tracked.</li>
          )}
        </ul>
      </section>

      <div className="text-[10px] uppercase tracking-wide text-slate-400">
        Schema {data.schema_version} · Generated {(data.generated_at || "").slice(0, 19).replace("T", " ")}
      </div>
    </div>
  );
}

function ForecastList({ title, items, testid }) {
  if (!items || items.length === 0) {
    return (
      <section className="border border-slate-200 rounded-md bg-white p-4" data-testid={testid}>
        <h3 className="font-semibold text-slate-800 mb-2">{title}</h3>
        <div className="text-xs text-slate-500">Nothing in the horizon.</div>
      </section>
    );
  }
  return (
    <section className="border border-slate-200 rounded-md bg-white p-4" data-testid={testid}>
      <h3 className="font-semibold text-slate-800 mb-2">{title} ({items.length})</h3>
      <ul className="space-y-1 text-xs max-h-72 overflow-y-auto">
        {items.slice(0, 60).map((it) => (
          <li key={it.subject_id}
              data-testid={`${testid}-${it.subject_id}`}
              className="flex items-center justify-between border-b border-slate-100 py-1">
            <span>{it.record_label}</span>
            <span className="font-mono text-[11px] text-slate-600">
              {it.bucket.replace(/_/g, " ")} · {it.due_in_days}d
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
