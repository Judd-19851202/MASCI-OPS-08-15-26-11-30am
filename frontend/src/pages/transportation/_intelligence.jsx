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
import { isAdmin } from "@/lib/adminAuth";
import {
  Activity, ListChecks, TrendingUp, RefreshCw, ShieldCheck, Star,
  AlertTriangle, Users, Building2, Truck as TruckIcon, GraduationCap,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  adminHeaders,
  PageHeader,
  EmptyState,
  txGet,
  txFetchJson,
  isTxRestricted,
  txCatch,
  useTxPathPrefix,
} from "./_shared";
import { TxOpsRestrictedData } from "@/components/transportation/TxOpsRestricted";

const SUB_TABS = [
  { to: "", label: "Executive", end: true, testid: "tx-intel-tab-exec",
    icon: Activity },
  { to: "recommendations", label: "Recommendations",
    testid: "tx-intel-tab-recs", icon: Star },
  { to: "predictions", label: "Predictions",
    testid: "tx-intel-tab-pred", icon: TrendingUp },
  { to: "learning", label: "Learning Loop",
    testid: "tx-intel-tab-learning", icon: GraduationCap },
  { to: "cleanup", label: "Cleanup Companion",
    testid: "tx-intel-tab-cleanup", icon: ListChecks },
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
  const prefix = useTxPathPrefix();
  const admin = isAdmin();
  const subTabs = admin
    ? SUB_TABS
    : SUB_TABS.filter((tab) => tab.to === "cleanup");

  return (
    <div data-testid="tx-intel-center" className="space-y-4">
      <PageHeader
        title="Operations Intelligence"
        subtitle="Transportation outlook, best next moves, and follow-up work"
        right={<ShieldCheck className="h-5 w-5 text-emerald-700" />}
      />
      <div className="flex items-center gap-1 border-b border-slate-200">
        {subTabs.map((t) => (
          <NavLink
            key={t.to || "exec"}
            to={t.to ? `${prefix}/intelligence/${t.to}` : `${prefix}/intelligence`}
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
        <Route path="learning" element={<LearningLoopPanel />} />
        <Route path="cleanup" element={<CleanupCompanionPanel />} />
      </Routes>
    </div>
  );
}


// ───────────────────────────── Executive ─────────────────────────────
function ExecutiveDashboard() {
  const [data, setData] = useState(null);
  const [restricted, setRestricted] = useState(false);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet("/admin/transportation/intelligence/dashboard");
      if (isTxRestricted(r)) { setRestricted(true); setErr(null); return; }
      setData(r.data);
      setErr(null);
    } catch (e) {
      const safe = txCatch(e);
      if (safe == null) { setRestricted(true); return; }
      setErr(safe);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    const kickoff = setTimeout(() => { load(); }, 1200);
    return () => clearTimeout(kickoff);
  }, [load]);

  if (loading && !data) return <div data-testid="tx-intel-exec-loading" className="text-sm text-slate-500">Loading…</div>;
  if (restricted) return <TxOpsRestrictedData testid="tx-intel-exec-restricted" />;
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
        <span>Prepared {(data.generated_at || "").slice(0, 19).replace("T", " ")}</span>
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
              <li className="text-[11px] text-slate-400">No {cat} scored yet</li>
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
  const [restricted, setRestricted] = useState(false);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet(
        "/admin/transportation/intelligence/recommendations",
        { scope, limit: 10 }
      );
      if (isTxRestricted(r)) { setRestricted(true); setErr(null); return; }
      setData(r.data);
      setErr(null);
    } catch (e) {
      const safe = txCatch(e);
      if (safe == null) { setRestricted(true); return; }
      setErr(safe);
    } finally {
      setLoading(false);
    }
  }, [scope]);
  useEffect(() => { load(); }, [load]);

  if (restricted) return <TxOpsRestrictedData testid="tx-intel-recs-restricted" />;

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
            {{ triple: "Best overall", driver: "Driver", carrier: "Carrier", truck: "Truck" }[s] || s}
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
  const [restricted, setRestricted] = useState(false);
  const [err, setErr] = useState(null);
  const load = useCallback(async () => {
    try {
      const r = await txGet("/admin/transportation/intelligence/predictions");
      if (isTxRestricted(r)) { setRestricted(true); setErr(null); return; }
      setData(r.data);
      setErr(null);
    } catch (e) {
      const safe = txCatch(e);
      if (safe == null) { setRestricted(true); return; }
      setErr(safe);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (restricted) return <TxOpsRestrictedData testid="tx-intel-pred-restricted" />;
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
        Prepared {(data.generated_at || "").slice(0, 19).replace("T", " ")}
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


// ────────────────────────── Learning Loop ──────────────────────────
// TRACK 16.14 · Team-level operational learning. NO individual
// scorekeeping. NO emails. Read-only insight surface.
function LearningLoopPanel() {
  const [data, setData] = useState(null);
  const [restricted, setRestricted] = useState(false);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet(
        "/admin/transportation/intelligence/dispatch-learning",
        { days }
      );
      if (isTxRestricted(r)) { setRestricted(true); setErr(null); return; }
      setData(r.data); setErr(null);
    } catch (e) {
      const safe = txCatch(e);
      if (safe == null) { setRestricted(true); return; }
      setErr(safe);
    } finally {
      setLoading(false);
    }
  }, [days]);
  useEffect(() => { load(); }, [load]);

  if (loading && !data) return <div data-testid="tx-intel-learning-loading" className="text-sm text-slate-500">Loading…</div>;
  if (restricted) return <TxOpsRestrictedData testid="tx-intel-learning-restricted" />;
  if (err) return <div data-testid="tx-intel-learning-error" className="text-sm text-rose-700">{err}</div>;
  if (!data) return <EmptyState title="No dispatcher learning data yet" testid="tx-intel-learning-empty" />;

  const s = data.summary || {};
  const empty = !s.recommendations_generated;

  return (
    <div data-testid="tx-intel-learning" className="space-y-4">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-slate-500">Window:</span>
        {[7, 30, 90].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => setDays(n)}
            className={`px-2 py-1 rounded text-xs border ${
              days === n
                ? "border-blue-600 text-blue-700 bg-blue-50"
                : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}
            data-testid={`tx-intel-learning-days-${n}`}
          >
            {n} days
          </button>
        ))}
        <button onClick={load} className="ml-auto inline-flex items-center gap-1 text-blue-600 hover:underline text-xs" data-testid="tx-intel-learning-refresh">
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>

      <div className="text-[10px] uppercase tracking-wide text-slate-400 -mt-1" data-testid="tx-intel-learning-disclaimer">
        Team-level learning only · no individual scorekeeping
      </div>

      {empty && (
        <div className="rounded border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600" data-testid="tx-intel-learning-empty-state">
          No dispatcher recommendation interactions captured yet in this window. Once dispatchers use the Decision Surface, insights will appear here.
        </div>
      )}

      <section className="grid grid-cols-2 lg:grid-cols-6 gap-3" data-testid="tx-intel-learning-summary">
        <SummaryCard label="Generated" value={s.recommendations_generated ?? 0} testid="tx-intel-learning-generated" />
        <SummaryCard label="Viewed" value={s.recommendations_viewed ?? 0} testid="tx-intel-learning-viewed" />
        <SummaryCard label="Recommended selected" value={s.recommended_selected ?? 0} accent="emerald" testid="tx-intel-learning-selected" />
        <SummaryCard label="Eligible alternative" value={s.eligible_alternative_selected ?? 0} accent="amber" testid="tx-intel-learning-alt" />
        <SummaryCard label="Ignored" value={s.ignored ?? 0} testid="tx-intel-learning-ignored" />
        <SummaryCard label="Unavailable" value={s.recommendation_unavailable ?? 0} accent="rose" testid="tx-intel-learning-unavailable" />
      </section>

      <section className="border border-slate-200 rounded-md bg-white p-4" data-testid="tx-intel-learning-adoption">
        <h3 className="font-semibold text-slate-800 mb-2">Adoption Trend</h3>
        {(data.adoption?.points || []).length === 0 ? (
          <div className="text-xs text-slate-500">No data points in this window.</div>
        ) : (
          <ul className="space-y-1 text-xs max-h-60 overflow-y-auto">
            {data.adoption.points.map((p) => (
              <li key={p.date} className="flex items-center justify-between border-b border-slate-100 py-1"
                  data-testid={`tx-intel-learning-adoption-${p.date}`}>
                <span className="text-slate-700">{p.date}</span>
                <span className="font-mono text-[11px] text-slate-600">
                  {p.generated} gen · {p.selected} sel · {p.non_recommended_selected} alt · {p.ignored} ign · {p.adoption_pct == null ? "—" : `${p.adoption_pct}%`}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <PatternList
        title="Common alternative-selection patterns"
        emptyLabel="No alternative-selection notes captured."
        items={(data.alternative_reasons?.patterns || []).map((p) => ({
          label: p.label, count: p.count, suffix: `${p.share_pct ?? 0}% of alt-selections`,
        }))}
        testid="tx-intel-learning-alt-reasons"
      />

      <PatternList
        title="Watch item patterns"
        emptyLabel="No watch items captured yet."
        items={(data.watch_items?.patterns || []).map((p) => ({
          label: p.label, count: p.count,
        }))}
        testid="tx-intel-learning-watch"
      />

      <PatternList
        title="Excluded option patterns"
        emptyLabel="No excluded entries yet."
        items={(data.excluded_patterns?.patterns || []).map((p) => ({
          label: p.label, count: p.count,
        }))}
        footer={data.excluded_patterns?.total_excluded_entities
          ? `${data.excluded_patterns.total_excluded_entities} excluded entities`
          : null}
        testid="tx-intel-learning-excluded"
      />

      <section className="border border-slate-200 rounded-md bg-white p-4" data-testid="tx-intel-learning-tuning">
        <h3 className="font-semibold text-slate-800 mb-2">Engine Tuning Signals</h3>
        {(data.tuning_signals?.signals || []).length === 0 ? (
          <div className="text-xs text-slate-500">No tuning signals — system is operating within expected ranges.</div>
        ) : (
          <ul className="space-y-2 text-xs">
            {data.tuning_signals.signals.map((sig) => (
              <li key={sig.code}
                  className="rounded border border-slate-200 px-3 py-2"
                  data-testid={`tx-intel-learning-tuning-${sig.code}`}>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase tracking-wider text-slate-500">{sig.kind}</span>
                  <span className="font-mono text-[10px] text-slate-500">count {sig.count}{sig.share_pct != null ? ` · ${sig.share_pct}%` : ""}</span>
                </div>
                <div className="text-slate-900 font-medium mt-0.5">{sig.label}</div>
                <div className="text-slate-600 mt-0.5">{sig.detail}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="text-[10px] uppercase tracking-wide text-slate-400">
        Prepared {(data.generated_at || "").slice(0, 19).replace("T", " ")} · Window {data.range?.days} days
      </div>
      {(data.notes || []).length > 0 && (
        <ul className="text-[10px] text-slate-500 list-disc pl-4" data-testid="tx-intel-learning-notes">
          {data.notes.map((n, i) => (<li key={i}>{n}</li>))}
        </ul>
      )}
    </div>
  );
}

function SummaryCard({ label, value, accent, testid }) {
  const palette = {
    emerald: "border-emerald-300 bg-emerald-50 text-emerald-900",
    amber: "border-amber-300 bg-amber-50 text-amber-900",
    rose: "border-rose-300 bg-rose-50 text-rose-900",
  }[accent] || "border-slate-200 bg-white text-slate-900";
  return (
    <div className={`rounded-md border px-3 py-2 ${palette}`} data-testid={testid}>
      <div className="text-[10px] uppercase tracking-wider opacity-80">{label}</div>
      <div className="text-xl font-semibold mt-0.5">{value}</div>
    </div>
  );
}

function PatternList({ title, items, emptyLabel, footer, testid }) {
  return (
    <section className="border border-slate-200 rounded-md bg-white p-4" data-testid={testid}>
      <h3 className="font-semibold text-slate-800 mb-2">{title}</h3>
      {(!items || items.length === 0) ? (
        <div className="text-xs text-slate-500">{emptyLabel}</div>
      ) : (
        <ul className="space-y-1 text-xs">
          {items.map((it, i) => (
            <li key={i} className="flex items-center justify-between border-b border-slate-100 py-1"
                data-testid={`${testid}-item-${i}`}>
              <span className="text-slate-800">{it.label}</span>
              <span className="font-mono text-[11px] text-slate-600">
                {it.count}{it.suffix ? ` · ${it.suffix}` : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
      {footer && (
        <div className="text-[10px] uppercase tracking-wide text-slate-400 mt-2">{footer}</div>
      )}
    </section>
  );
}



// ────────────────────── Cleanup Companion (Track 16.15) ──────────────────────
function CleanupCompanionPanel() {
  const [loading, setLoading] = useState(true);
  const [signals, setSignals] = useState(null);
  const [restricted, setRestricted] = useState(false);
  const [err, setErr] = useState(null);
  const [openSignal, setOpenSignal] = useState(null);
  const [detail, setDetail] = useState(null);
  const [busy, setBusy] = useState(false);
  const [materialized, setMaterialized] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txFetchJson(
        "/admin/transportation/intelligence/cleanup-signals",
        { days: 30 }
      );
      if (isTxRestricted(r)) {
        setRestricted(true); setSignals(null); setErr(null); return;
      }
      setRestricted(false); setSignals(r.data); setErr(null);
    } catch (e) {
      const safe = txCatch(e);
      if (safe == null) { setRestricted(true); setSignals(null); return; }
      setErr(safe);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    const kickoff = setTimeout(() => { load(); }, 1200);
    return () => {
      clearTimeout(kickoff);
    };
  }, [load]);

  const openDetail = async (key) => {
    setOpenSignal(key); setDetail(null); setMaterialized(null);
    try {
      const r = await txFetchJson(
        `/admin/transportation/intelligence/cleanup-signals/${key}`,
        { days: 30 }
      );
      if (isTxRestricted(r)) {
        setDetail({ ok: false, restricted: true });
        return;
      }
      setDetail(r.data);
    } catch (e) {
      const safe = txCatch(e);
      setDetail({ ok: false, error: safe || "Detail unavailable." });
    }
  };

  const materialize = async () => {
    if (!openSignal) return;
    setBusy(true);
    try {
      const r = await api.post(
        `/admin/transportation/intelligence/cleanup-signals/${openSignal}/materialize-actions?days=30`,
        null, { headers: adminHeaders() });
      setMaterialized(r.data);
      // refresh detail so the existing_action_item_id annotations update.
      await openDetail(openSignal);
    } catch (e) {
      alert(txCatch(e) || "Permission denied.");
    } finally {
      setBusy(false);
    }
  };

  if (restricted) return <TxOpsRestrictedData testid="tx-intel-cleanup-restricted" />;
  if (err) return <div data-testid="tx-intel-cleanup-error" className="text-sm text-rose-700">{err}</div>;
  if (loading) return <div data-testid="tx-intel-cleanup-loading" className="text-sm text-slate-500">Loading…</div>;
  if (!signals) return <div data-testid="tx-intel-cleanup-empty" className="text-sm text-slate-500">No cleanup signals available.</div>;

  const list = signals.signals || [];
  const top = list[0];

  return (
    <div data-testid="tx-intel-cleanup" className="space-y-4">
      <div className="text-[10px] uppercase tracking-wide text-slate-400" data-testid="tx-intel-cleanup-disclaimer">
        Action lists built from current records · {signals.note}
      </div>

      {list.length === 0 ? (
        <div data-testid="tx-intel-cleanup-empty" className="rounded border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
          No cleanup signals detected. Transportation data is currently in a healthy state.
        </div>
      ) : (
        <>
          {/* Top Cleanup Signal Card */}
          {top && (
            <section
              className="rounded-lg border border-amber-300 bg-amber-50 p-4"
              data-testid="tx-intel-cleanup-top-card"
            >
              <div className="flex items-center justify-between mb-2">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-amber-800 font-semibold">
                    Top cleanup opportunity
                  </div>
                  <div className="text-lg font-semibold text-amber-900 mt-0.5" data-testid="tx-intel-cleanup-top-title">
                    {top.title}
                  </div>
                </div>
                <span className="text-[11px] px-2 py-0.5 rounded-full border border-amber-400 bg-amber-100 text-amber-900">
                  {top.affected_count} affected
                </span>
              </div>
              <div className="text-xs text-amber-900">{top.description}</div>
              <div className="text-xs text-amber-900 mt-1">
                <span className="font-medium">Recommended action: </span>{top.recommended_action}
              </div>
              <div className="mt-3 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => openDetail(top.signal_key)}
                  data-testid="tx-intel-cleanup-top-view"
                  className="rounded bg-amber-700 hover:bg-amber-800 text-white px-3 py-1.5 text-xs font-medium"
                >
                  View affected records
                </button>
              </div>
            </section>
          )}

          {/* Signal list */}
          <ul className="grid grid-cols-1 lg:grid-cols-2 gap-3" data-testid="tx-intel-cleanup-list">
            {list.map((s) => (
              <li
                key={s.signal_key}
                className="rounded border border-slate-200 bg-white p-3"
                data-testid={`tx-intel-cleanup-signal-${s.signal_key}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="text-sm font-semibold text-slate-900">{s.title}</div>
                  <span className={`text-[11px] px-2 py-0.5 rounded-full border ${
                    s.severity === "action_required"
                      ? "border-rose-300 bg-rose-50 text-rose-800"
                      : "border-amber-300 bg-amber-50 text-amber-800"}`}>
                    {s.severity.replace("_", " ")}
                  </span>
                </div>
                <div className="text-xs text-slate-600">{s.description}</div>
                <div className="text-[11px] text-slate-500 mt-1">
                  {s.affected_count} affected · source: {s.source}
                </div>
                <button
                  type="button"
                  onClick={() => openDetail(s.signal_key)}
                  data-testid={`tx-intel-cleanup-open-${s.signal_key}`}
                  className="mt-2 text-xs text-blue-600 hover:underline"
                >
                  View affected records →
                </button>
              </li>
            ))}
          </ul>
        </>
      )}

      {openSignal && (
        <AffectedDrawer
          signal={openSignal}
          detail={detail}
          busy={busy}
          materialized={materialized}
          onClose={() => { setOpenSignal(null); setDetail(null); setMaterialized(null); }}
          onMaterialize={materialize}
        />
      )}

      <div className="text-[10px] uppercase tracking-wide text-slate-400">
        Prepared {(signals.generated_at || "").slice(0, 19).replace("T", " ")}
      </div>
    </div>
  );
}

function AffectedDrawer({ signal, detail, busy, materialized, onClose, onMaterialize }) {
  return (
    <>
      <div className="fixed inset-0 bg-slate-950/50 z-[60]" onClick={onClose}
           data-testid="tx-intel-cleanup-drawer-scrim" />
      <aside
        data-testid="tx-intel-cleanup-affected-drawer"
        className="fixed inset-y-0 right-0 w-full sm:w-[600px] bg-white shadow-2xl z-[70] overflow-y-auto"
      >
        <header className="sticky top-0 bg-white border-b border-slate-200 px-5 py-4 flex items-start justify-between">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-700 font-bold">Cleanup detail</div>
            <div className="text-lg font-black text-slate-900 mt-1" data-testid="tx-intel-cleanup-detail-title">
              {detail?.signal?.title || signal}
            </div>
            {detail?.signal?.recommended_action && (
              <div className="text-xs text-slate-600 mt-0.5">{detail.signal.recommended_action}</div>
            )}
          </div>
          <button type="button" onClick={onClose}
                  data-testid="tx-intel-cleanup-detail-close"
                  className="inline-flex items-center justify-center h-10 w-10 -mr-2 text-slate-500 hover:text-slate-900">
            ×
          </button>
        </header>
        <section className="px-5 py-4 space-y-3 text-xs">
          {!detail && <div className="text-slate-500">Loading affected records…</div>}
          {detail && detail.ok === false && (
            <div className="text-rose-700">Couldn&apos;t load detail.</div>
          )}
          {detail?.ok && (
            <>
              <div className="flex items-center justify-between">
                <div className="text-slate-700">
                  <strong>{detail.affected?.length || 0}</strong> affected entities
                </div>
                <button
                  type="button"
                  onClick={onMaterialize}
                  disabled={busy || !detail.affected?.length}
                  data-testid="tx-intel-cleanup-materialize-btn"
                  className="rounded bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                >
                  {busy ? "Creating…" : "Create cleanup actions"}
                </button>
              </div>
              {materialized && (
                <div className="rounded border border-emerald-300 bg-emerald-50 px-3 py-2 text-emerald-900"
                     data-testid="tx-intel-cleanup-materialized-result">
                  Created {materialized.created} action{materialized.created === 1 ? "" : "s"} ·
                  reused {materialized.existing_action_count} existing ·
                  skipped {materialized.skipped_duplicates} duplicate{materialized.skipped_duplicates === 1 ? "" : "s"}
                </div>
              )}
              <ul className="space-y-2">
                {(detail.affected || []).map((it, i) => (
                  <li key={it.entity_id || i}
                      data-testid={`tx-intel-cleanup-affected-${i}`}
                      className="border border-slate-200 rounded px-3 py-2">
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-slate-900">{it.display_name}</div>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                        it.severity === "action_required"
                          ? "border-rose-300 bg-rose-50 text-rose-800"
                          : "border-amber-300 bg-amber-50 text-amber-800"}`}>
                        {it.severity.replace("_", " ")}
                      </span>
                    </div>
                    <div className="text-slate-600 mt-0.5">{it.reason}</div>
                    <div className="flex items-center justify-between mt-1 text-[11px] text-slate-500">
                      <span>
                        {it.due_date ? `Due: ${it.due_date.slice(0, 10)}` : "No due date"}
                        {it.existing_action_item_id && ` · action ${it.action_status}`}
                      </span>
                      {it.direct_link && (
                        <a href={it.direct_link} className="text-blue-600 hover:underline"
                           data-testid={`tx-intel-cleanup-link-${i}`}>
                          Open record →
                        </a>
                      )}
                    </div>
                  </li>
                ))}
                {(!detail.affected || detail.affected.length === 0) && (
                  <li className="text-slate-500">No affected records.</li>
                )}
              </ul>
            </>
          )}
        </section>
      </aside>
    </>
  );
}

