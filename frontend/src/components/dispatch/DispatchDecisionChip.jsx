/**
 * TRACK 16.13 · Dispatch Decision Surface chip + Why drawer.
 *
 * Read-only · explainable · never blocks the assignment flow.
 *
 * Mounts inside the existing AssignmentDrawer header. One chip; one
 * Why drawer; one ranked alternatives list; one excluded section.
 * Delegates to the existing Track 16.12 intelligence engine via
 * /api/dispatch/transportation/recommendation.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { formatPlatformTime } from "@/lib/platformTime";
import { Sparkles, Info, AlertTriangle, X, ListChecks, ShieldOff } from "lucide-react";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { sanitizeOperatorCopy } from "@/lib/operatorLanguage";

const API = `${process.env.REACT_APP_BACKEND_URL || ""}/api`;

function authHeaders() {
  return {
    "Content-Type": "application/json",
    ...buildScopedPortalAuthHeaders(["admin", "dispatch"]),
  };
}

const GRADE_PALETTE = {
  excellent: "bg-emerald-100 text-emerald-800 border-emerald-300",
  strong: "bg-emerald-50 text-emerald-800 border-emerald-200",
  fair: "bg-amber-100 text-amber-800 border-amber-300",
  watch: "bg-amber-200 text-amber-900 border-amber-400",
  critical: "bg-rose-100 text-rose-800 border-rose-300",
};

function GradeChip({ score, grade }) {
  const cls = GRADE_PALETTE[grade] || "bg-slate-100 text-slate-700 border-slate-300";
  return (
    <span className={`px-2 py-0.5 rounded-full border text-[11px] font-medium ${cls}`}
          data-testid="dispatch-decision-grade-chip">
      {Math.round(Number(score) || 0)} · {grade || "—"}
    </span>
  );
}

export default function DispatchDecisionChip({
  carrierId, currentDriverId, currentTruckId,
  onSelectRecommendation,
}) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const buildUrl = useCallback(() => {
    const params = new URLSearchParams();
    if (carrierId) params.set("carrier_id", carrierId);
    params.set("limit", "5");
    return `${API}/dispatch/transportation/recommendation?${params.toString()}`;
  }, [carrierId]);

  // Debounced load — recompute only when carrier context changes.
  useEffect(() => {
    let cancelled = false;
    const handle = setTimeout(async () => {
      setLoading(true);
      try {
        const r = await fetch(buildUrl(), { headers: authHeaders() });
        const body = await r.json();
        if (!cancelled) { setData(body); setErr(null); }
      } catch (e) {
        if (!cancelled) setErr(e.message || "load failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 300);
    return () => { cancelled = true; clearTimeout(handle); };
  }, [buildUrl]);

  const auditEvent = useCallback(async (event, extra = {}) => {
    try {
      await fetch(`${API}/dispatch/transportation/recommendation/audit`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          event,
          recommendation_id: data?.recommendation_id,
          driver_id: data?.recommended?.driver?.driver_id,
          carrier_id: data?.recommended?.carrier?.carrier_id,
          truck_id: data?.recommended?.truck?.truck_id,
          score: data?.recommended?.score,
          grade: data?.recommended?.grade,
          ...extra,
        }),
      });
    } catch (_e) { /* best-effort */ }
  }, [data]);

  const openDrawer = () => {
    setDrawerOpen(true);
    auditEvent("viewed");
  };

  const recommended = data?.recommended;
  const summary = useMemo(() => {
    if (!recommended) return null;
    const parts = [];
    if (recommended.carrier?.legal_name) parts.push(recommended.carrier.legal_name);
    if (recommended.driver?.display_name) parts.push(`Driver: ${recommended.driver.display_name}`);
    if (recommended.truck?.truck_number) parts.push(`Truck ${recommended.truck.truck_number}`);
    return parts.join(" / ");
  }, [recommended]);

  if (loading && !data) {
    return (
      <div className="rounded border border-dashed border-slate-300 px-3 py-2 text-xs text-slate-500"
           data-testid="dispatch-decision-chip-loading">
        Loading recommendation…
      </div>
    );
  }
  if (err) {
    return (
      <div className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800"
           data-testid="dispatch-decision-chip-error">
        Recommendation unavailable. You can keep assigning with the normal dispatch checks.
      </div>
    );
  }
  if (!data?.ok || !recommended || !summary) {
    return (
      <div className="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600"
           data-testid="dispatch-decision-chip-empty">
        <div className="flex items-center gap-2">
          <Info className="h-3.5 w-3.5 text-slate-400" />
          No ready recommendation is available right now.
        </div>
      </div>
    );
  }

  const watchCount = (recommended.watch || []).length;
  const headline = watchCount > 0
    ? "Recommended with watchouts"
    : "Recommended assignment";

  return (
    <>
      <button
        type="button"
        onClick={openDrawer}
        data-testid="dispatch-decision-chip"
        className="w-full text-left rounded border border-emerald-300 bg-emerald-50 hover:bg-emerald-100 px-3 py-2 transition"
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <Sparkles className="h-4 w-4 text-emerald-700 shrink-0" />
            <div className="min-w-0">
              <div className="text-[10px] uppercase tracking-wider text-emerald-800 font-semibold">
                {headline}
              </div>
              <div className="text-xs text-slate-800 truncate" data-testid="dispatch-decision-summary">
                {summary}
              </div>
            </div>
          </div>
          <GradeChip score={recommended.score} grade={recommended.grade} />
        </div>
        {watchCount > 0 && (
          <div className="mt-1 text-[10px] text-amber-800 inline-flex items-center gap-1"
               data-testid="dispatch-decision-watch-count">
            <AlertTriangle className="h-3 w-3" /> {watchCount} watch item{watchCount === 1 ? "" : "s"}
          </div>
        )}
      </button>
      {drawerOpen && (
        <WhyDrawer
          data={data}
          onClose={() => setDrawerOpen(false)}
          onSelectRecommendation={() => {
            auditEvent("selected");
            onSelectRecommendation?.(recommended);
            setDrawerOpen(false);
          }}
          onSelectAlternative={(alt, type) => {
            const ev = (
              alt?.driver_id === recommended?.driver?.driver_id
              && alt?.truck_id === recommended?.truck?.truck_id
              && alt?.carrier_id === recommended?.carrier?.carrier_id
            ) ? "selected" : "non_recommended_selected";
            auditEvent(ev, {
              selected_driver_id: alt?.driver_id,
              selected_truck_id: alt?.truck_id,
              selected_carrier_id: alt?.carrier_id,
            });
            // Compose minimal triple so the parent can populate fields.
            const triple = { driver: null, truck: null, carrier: null };
            if (type === "drivers") triple.driver = alt;
            if (type === "trucks") triple.truck = alt;
            if (type === "carriers") triple.carrier = alt;
            onSelectRecommendation?.(triple);
            setDrawerOpen(false);
          }}
          onIgnore={() => {
            auditEvent("ignored");
            setDrawerOpen(false);
          }}
        />
      )}
    </>
  );
}


function WhyDrawer({ data, onClose, onSelectRecommendation,
                     onSelectAlternative, onIgnore }) {
  const rec = data?.recommended || {};
  const alt = data?.alternatives || {};
  const exc = data?.excluded || {};

  return (
    <>
      <div className="fixed inset-0 bg-slate-950/50 z-[60]"
           onClick={onClose}
           data-testid="dispatch-decision-drawer-scrim" />
      <aside
        data-testid="dispatch-decision-why-drawer"
        className="fixed inset-y-0 right-0 w-full sm:w-[560px] bg-white shadow-2xl z-[70] overflow-y-auto"
      >
        <header className="sticky top-0 bg-white border-b border-slate-200 px-5 py-4 flex items-start justify-between">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-emerald-700 font-bold">
              Dispatch recommendation details
            </div>
            <div className="text-lg font-black text-slate-900 mt-1">Why this assignment is recommended</div>
            <div className="text-xs text-slate-500 mt-0.5">
              Built {formatPlatformTime(data.generated_at)}
            </div>
          </div>
          <button type="button" onClick={onClose}
                  className="inline-flex items-center justify-center h-10 w-10 -mr-2 text-slate-500 hover:text-slate-900"
                  data-testid="dispatch-decision-why-close">
            <X className="w-5 h-5" />
          </button>
        </header>

        <section className="px-5 py-4 space-y-4 text-xs">
          {/* Recommended triple */}
          <div className="rounded border border-emerald-300 bg-emerald-50 p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="font-semibold text-emerald-900">Recommended assignment</div>
              <GradeChip score={rec.score} grade={rec.grade} />
            </div>
            <Row label="Carrier" value={rec.carrier?.legal_name} testid="dispatch-why-carrier" />
            <Row label="Driver" value={rec.driver?.display_name} testid="dispatch-why-driver" />
            <Row label="Truck" value={rec.truck?.truck_number} testid="dispatch-why-truck" />
            <div className="mt-2">
              <div className="font-medium text-emerald-800 mb-0.5">Why</div>
              <ul className="space-y-0.5">
                {(rec.why || []).map((w, i) => (
                  <li key={i} data-testid={`dispatch-why-${i}`}>• {sanitizeOperatorCopy(w, w)}</li>
                ))}
                {(rec.why || []).length === 0 && (
                  <li className="text-slate-500">Best fit among the ready driver, truck, and carrier options.</li>
                )}
              </ul>
            </div>
            {rec.watch?.length > 0 && (
              <div className="mt-2">
                <div className="font-medium text-amber-800 mb-0.5">Watchouts</div>
                <ul className="space-y-0.5">
                  {rec.watch.map((w, i) => (
                    <li key={i} data-testid={`dispatch-watch-${i}`}>• {sanitizeOperatorCopy(w, w)}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="mt-3 flex items-center gap-2">
              <button
                type="button"
                onClick={onSelectRecommendation}
                data-testid="dispatch-decision-select-recommended"
                className="inline-flex items-center gap-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 text-xs font-medium"
              >
                Use this assignment
              </button>
              <button
                type="button"
                onClick={onIgnore}
                data-testid="dispatch-decision-ignore"
                className="rounded border border-slate-200 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50"
              >
                Ignore
              </button>
            </div>
          </div>

          {/* Alternatives */}
          <AlternativesSection
            title="Other driver options"
            items={alt.drivers}
            type="drivers"
            onSelect={onSelectAlternative}
            testid="dispatch-decision-alt-drivers"
          />
          <AlternativesSection
            title="Other truck options"
            items={alt.trucks}
            type="trucks"
            onSelect={onSelectAlternative}
            testid="dispatch-decision-alt-trucks"
          />
          <AlternativesSection
            title="Other carrier options"
            items={alt.carriers}
            type="carriers"
            onSelect={onSelectAlternative}
            testid="dispatch-decision-alt-carriers"
          />

          {/* Excluded */}
          <section className="rounded border border-slate-200 bg-white p-3"
                   data-testid="dispatch-decision-excluded">
            <div className="font-semibold text-slate-800 mb-2 inline-flex items-center gap-1">
              <ShieldOff className="h-4 w-4 text-rose-600" /> Options held out
            </div>
            {["drivers", "trucks", "carriers"].map((k) => (
              <div key={k} className="mb-2 last:mb-0">
                <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">{k}</div>
                {(exc[k] || []).length === 0 ? (
                  <div className="text-[11px] text-slate-400">None.</div>
                ) : (
                  <ul className="space-y-1">
                    {(exc[k] || []).slice(0, 5).map((it) => (
                      <li key={it.id} className="border border-slate-200 rounded px-2 py-1"
                          data-testid={`dispatch-decision-excluded-${k}-${it.id}`}>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-800">{it.name}</span>
                          <span className="text-[10px] uppercase tracking-wider text-rose-700">
                            {String(it.state).replace("_", " ")}
                          </span>
                        </div>
                        {it.reasons?.length > 0 && (
                          <div className="text-[10px] text-slate-500 mt-0.5">
                            {it.reasons.slice(0, 3).map((r) => sanitizeOperatorCopy(r.label, r.label)).join(" · ")}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </section>

          <div className="text-[10px] text-slate-400">
            These recommendations are read-only. Final assignment still passes the normal dispatch checks.
          </div>
        </section>
      </aside>
    </>
  );
}

function AlternativesSection({ title, items, type, onSelect, testid }) {
  return (
    <section className="rounded border border-slate-200 bg-white p-3" data-testid={testid}>
      <div className="font-semibold text-slate-800 mb-2 inline-flex items-center gap-1">
        <ListChecks className="h-4 w-4 text-slate-500" /> {title}
      </div>
      {(items || []).length === 0 ? (
        <div className="text-[11px] text-slate-400">No other ready options are available.</div>
      ) : (
        <ul className="space-y-1">
          {(items || []).slice(0, 5).map((it, i) => {
            const id = it.driver_id || it.truck_id || it.carrier_id;
            const name = it.display_name || it.truck_number || it.legal_name || id;
            return (
              <li key={id || i} className="border border-slate-200 rounded px-2 py-1"
                  data-testid={`${testid}-item-${i}`}>
                <div className="flex items-center justify-between">
                  <span className="text-slate-800 truncate">{name}</span>
                  <div className="flex items-center gap-2">
                    <GradeChip score={it.overall?.score} grade={it.overall?.grade} />
                    <button
                      type="button"
                      onClick={() => onSelect(it, type)}
                      className="text-[10px] rounded border border-slate-200 px-2 py-0.5 text-slate-700 hover:bg-slate-50"
                      data-testid={`${testid}-select-${i}`}
                    >
                      Use option
                    </button>
                  </div>
                </div>
                {it.why?.length > 0 && (
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    {it.why.slice(0, 3).map((item) => sanitizeOperatorCopy(item, item)).join(" · ")}
                  </div>
                )}
                {it.watch?.length > 0 && (
                  <div className="text-[10px] text-amber-700 mt-0.5">
                    Watchouts: {it.watch.slice(0, 2).map((item) => sanitizeOperatorCopy(item, item)).join(" · ")}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function Row({ label, value, testid }) {
  return (
    <div className="flex items-center justify-between py-0.5" data-testid={testid}>
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-900 font-medium">{value || "—"}</span>
    </div>
  );
}
