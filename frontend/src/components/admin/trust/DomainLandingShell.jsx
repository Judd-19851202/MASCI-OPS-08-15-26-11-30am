// TRACK 25 · SPRINT 4 · Admin OS · Shared Domain Landing Shell.
//
// Every Admin OS domain landing (AI Operations · Communications ·
// Identity & Security · Governance & Trust · Storage & Recovery) uses
// the SAME shell so the platform never drifts into per-page design.
//
// A domain page becomes a declarative manifest:
//   {
//     id, label, subtitle,
//     probes: [{ id, path }],
//     cards:  [{ id, section, title, endpoint, drilldown,
//                evaluator(probeMap) -> { status, summary, evidence,
//                                          recommended_action, checked_at } }],
//     sections: [{ id, label, icon, cards: [<card_id>...] }],
//     maintenance_actions: [{ id, title, description, never_touches }],
//     trust_gaps: [{ id, title, severity, owner, target_track, risk,
//                    current_status, blocks_production }],
//     source_endpoints_line: "...",
//   }
//
// The shell owns: probe fan-out, executive verdict, filter row,
// section rendering, evidence drawer, maintenance-action tiles,
// trust-gaps table, refresh, error banner.
//
// Uses shared TrustPrimitives (Sprint 3). Uses PortalShell + SideNavV3
// so navigation matches every other Admin OS page.
//
// Zero-UTC compliant — all timestamps route through platformTime.js.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { RefreshCw, Search as SearchIcon, Wrench } from "lucide-react";

import { PortalShell } from "@/design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import { getAdminToken } from "@/lib/adminAuth";
import { formatPlatformTime } from "@/lib/platformTime";
import {
  HealthCard,
  EvidenceDrawer,
  TrustStatusPill,
  TRUST_STATUS_STYLES,
  worstStatus,
  sortCardsByAttention,
  useEvidenceDrawer,
} from "./TrustPrimitives";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";

const API = (process.env.REACT_APP_BACKEND_URL || "") + "/api";

const SEVERITY_STYLES = {
  P0: "bg-rose-100 text-rose-800 ring-rose-200",
  P1: "bg-amber-100 text-amber-900 ring-amber-200",
  P2: "bg-slate-100 text-slate-700 ring-slate-300",
};

function authHeaders() {
  const t = getAdminToken();
  return t ? { "X-Admin-Token": t } : {};
}

async function probeOne(path) {
  try {
    const r = await axios.get(`${API}${path}`, { headers: authHeaders() });
    return { ok: true, body: r.data, status: r.status, error: null };
  } catch (e) {
    return {
      ok: false,
      body: null,
      status: e?.response?.status || 0,
      error: e?.response?.data?.detail || e?.message || String(e),
    };
  }
}

export function unknownCard(id, title, endpoint, drilldown, summary, err) {
  return {
    id, title, endpoint, drilldown,
    status: "unknown", summary,
    recommended_action: "Investigate why the source endpoint is unreachable.",
    checked_at: null,
    evidence: { error: err || null },
  };
}

/**
 * Renders one Admin OS domain landing page.
 * @param {object} manifest - the domain manifest object.
 * @param {string} testidPrefix - e.g. "admin-ai-ops" — all data-testids are scoped under this.
 */
export default function DomainLandingShell({ manifest, testidPrefix }) {
  const [probes, setProbes] = useState({});
  const [loading, setLoading] = useState(true);
  const [refreshedAt, setRefreshedAt] = useState(null);
  const [justRefreshed, setJustRefreshed] = useState(false);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const { card: drawerCard, open: drawerOpen, setOpen: setDrawerOpen, openWith } =
    useEvidenceDrawer();

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = manifest.probes || [];
      const results = await Promise.all(list.map((p) => probeOne(p.path)));
      const map = {};
      list.forEach((p, i) => { map[p.id] = results[i]; });
      setProbes(map);
      setRefreshedAt(new Date().toISOString()); // TRACK-27.03-EXEMPT: rendered only via formatPlatformTime.
      // Flash a transient "Refreshed" confirmation so two rapid refreshes
      // in the same clock minute are still visibly distinguishable.
      setJustRefreshed(true);
      window.setTimeout(() => setJustRefreshed(false), 1500);
      const authErr = results.find((r) => !r.ok && [401, 403].includes(r.status));
      if (authErr) setError("Super-admin access required.");
    } catch (e) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  }, [manifest.probes]);

  useEffect(() => { reload(); }, [reload]);

  const cards = useMemo(() => {
    if (loading || Object.keys(probes).length === 0) return [];
    return (manifest.cards || []).map((cardDef) => {
      try {
        const evaluated = cardDef.evaluator(probes) || {};
        return {
          id: cardDef.id,
          title: cardDef.title,
          endpoint: cardDef.endpoint,
          drilldown: cardDef.drilldown,
          status: evaluated.status || "unknown",
          summary: evaluated.summary || "No summary.",
          recommended_action: evaluated.recommended_action || "",
          checked_at: evaluated.checked_at || null,
          evidence: evaluated.evidence || {},
        };
      } catch (e) {
        return unknownCard(cardDef.id, cardDef.title, cardDef.endpoint, cardDef.drilldown,
          "Evaluator threw an exception.", String(e));
      }
    });
  }, [probes, loading, manifest.cards]);

  const cardsById = useMemo(() =>
    Object.fromEntries(cards.map((c) => [c.id, c])), [cards]);

  const counts = useMemo(() => {
    const c = { green: 0, yellow: 0, red: 0, unknown: 0 };
    cards.forEach((x) => { c[x.status] = (c[x.status] || 0) + 1; });
    return c;
  }, [cards]);
  const overall = worstStatus(cards);
  const highest = useMemo(
    () => sortCardsByAttention(cards).find((c) => c.status !== "green") || null,
    [cards],
  );

  const filterFn = useCallback((c) => {
    if (statusFilter !== "all" && c.status !== statusFilter) return false;
    const q = query.trim().toLowerCase();
    if (!q) return true;
    return (
      c.title.toLowerCase().includes(q) ||
      (c.summary || "").toLowerCase().includes(q) ||
      (c.endpoint || "").toLowerCase().includes(q)
    );
  }, [statusFilter, query]);

  return (
    <div className="min-h-screen bg-slate-50" data-testid={`${testidPrefix}-root`}>
      <PortalShell
        portalName="MASCI"
        portalRole="Admin"
        pageTitle={manifest.label}
        subtitle={manifest.subtitle}
        primaryActions={
          <div className="flex flex-wrap items-center gap-2 min-w-0">
            <Link
              to="/admin"
              className="inline-flex items-center gap-2 px-3 py-1.5 border border-slate-300 bg-white rounded-md text-xs font-semibold text-slate-800 hover:bg-slate-100"
              data-testid={`${testidPrefix}-back-adminos`}
            >
              ← Admin OS
            </Link>
            <button
              type="button"
              onClick={reload}
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-100 disabled:opacity-60"
              data-testid={`${testidPrefix}-refresh`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              {loading ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        }
        sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
      >
        {/* Universal breadcrumb — every domain page shows "Admin OS › <domain label>". */}
        <AdminBreadcrumb
          crumbs={[{ label: manifest.label }]}
          testidPrefix={`${testidPrefix}-breadcrumb`}
        />

        {/* Executive Verdict */}
        <section
          className="mb-6 rounded-lg border border-slate-200 bg-white p-4"
          data-testid={`${testidPrefix}-verdict`}
        >
          <div className="flex flex-wrap items-center gap-4">
            <div className="min-w-[220px]">
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
                Executive Verdict
              </div>
              <div className="mt-1 flex items-center gap-2">
                <TrustStatusPill status={overall} testid={`${testidPrefix}-verdict-pill`} />
                <span className="text-sm font-semibold text-slate-900" data-testid={`${testidPrefix}-verdict-summary`}>
                  {loading
                    ? `Loading ${manifest.label.toLowerCase()} evidence…`
                    : overall === "red"
                    ? `${manifest.label} has a critical condition.`
                    : overall === "yellow"
                    ? `${manifest.label} needs attention.`
                    : overall === "green"
                    ? `${manifest.label} healthy across every wired signal.`
                    : `${manifest.label} evidence unavailable — press Refresh.`}
                </span>
              </div>
              {highest ? (
                <p className="mt-2 text-xs text-slate-600" data-testid={`${testidPrefix}-verdict-highest`}>
                  Highest-risk item · <strong>{highest.title}</strong>: {highest.summary}
                </p>
              ) : null}
            </div>
            <div className="md:ml-auto flex flex-wrap items-center gap-x-4 gap-y-2 text-sm min-w-0">
              {[["green","Healthy"],["yellow","Attention"],["red","Critical"],["unknown","Unknown"]].map(([k,label])=>(
                <div key={k} data-testid={`${testidPrefix}-count-${k}`}>
                  <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">{label}</div>
                  <div className={`font-black text-xl leading-none ${TRUST_STATUS_STYLES[k]?.text || "text-slate-800"}`}>
                    {counts[k] || 0}
                  </div>
                </div>
              ))}
              <div className="min-w-0">
                <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Last refreshed</div>
                <div className="flex flex-wrap items-center gap-1.5 min-w-0">
                  <span className="font-mono text-xs text-slate-800" data-testid={`${testidPrefix}-last-refreshed`}>
                    {refreshedAt ? formatPlatformTime(refreshedAt) : "—"}
                  </span>
                  {justRefreshed ? (
                    <span
                      className="inline-flex items-center rounded px-1 py-0.5 text-[9px] font-mono font-semibold uppercase tracking-widest bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200 transition-opacity"
                      data-testid={`${testidPrefix}-refresh-flash`}
                    >
                      ✓ refreshed
                    </span>
                  ) : null}
                </div>
              </div>
            </div>
          </div>
          {manifest.source_endpoints_line ? (
            <div className="mt-3 text-[11px] font-mono text-slate-500" data-testid={`${testidPrefix}-verdict-sources`}>
              Sources: {manifest.source_endpoints_line}
            </div>
          ) : null}
        </section>

        {error ? (
          <div className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" data-testid={`${testidPrefix}-error`}>
            {error}
          </div>
        ) : null}

        {/* Filter row */}
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[220px] max-w-md">
            <SearchIcon className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter cards by title, summary, or endpoint…"
              className="w-full rounded-md border border-slate-300 bg-white pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-300"
              data-testid={`${testidPrefix}-search`}
            />
          </div>
          {["all","red","yellow","unknown","green"].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStatusFilter(s)}
              className={`rounded-md border px-2 py-1 text-[11px] font-semibold uppercase tracking-wider ${
                statusFilter === s
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100"
              }`}
              data-testid={`${testidPrefix}-filter-${s}`}
            >
              {s === "all" ? "All" : (TRUST_STATUS_STYLES[s]?.label || s)}
            </button>
          ))}
        </div>

        {/* Health sections */}
        <div className="space-y-6 min-w-0" data-testid={`${testidPrefix}-sections`}>
          {(manifest.sections || []).map((sec) => {
            const secCards = (sec.cards || []).map((id) => cardsById[id]).filter(Boolean);
            const filtered = sortCardsByAttention(secCards).filter(filterFn);
            const secStatus = worstStatus(secCards);
            const Icon = sec.icon;
            return (
              <section key={sec.id} data-testid={`${testidPrefix}-section-${sec.id}`}>
                <div className="mb-2 flex items-center gap-2">
                  {Icon ? <Icon className="w-4 h-4 text-slate-500" /> : null}
                  <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
                    {sec.label}
                  </div>
                  <TrustStatusPill status={secStatus} testid={`${testidPrefix}-section-${sec.id}-status`} />
                  <div className="text-[10px] font-mono text-slate-400">
                    {filtered.length}/{secCards.length} card(s)
                  </div>
                </div>
                {filtered.length === 0 && !loading ? (
                  <div
                    className="rounded-md border border-dashed border-slate-300 bg-white px-3 py-4 text-xs text-slate-500"
                    data-testid={`${testidPrefix}-section-${sec.id}-empty`}
                  >
                    {secCards.length === 0 ? "Loading…" : "No cards match the current filter."}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                    {filtered.map((c) => (
                      <HealthCard
                        key={c.id}
                        card={c}
                        onOpen={openWith}
                        testidPrefix={`${testidPrefix}-card`}
                      />
                    ))}
                  </div>
                )}
              </section>
            );
          })}
        </div>

        {/* Maintenance actions (deep-links only) */}
        {manifest.maintenance_actions && manifest.maintenance_actions.length > 0 && (
          <section className="mt-8" data-testid={`${testidPrefix}-actions`}>
            <div className="mb-2 flex items-center gap-2">
              <Wrench className="w-4 h-4 text-slate-500" />
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
                Maintenance Actions
              </div>
              <div className="text-[10px] font-mono text-slate-400">
                deep-link · runs in OCC console (dry-run first)
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              {manifest.maintenance_actions.map((a) => (
                <Link
                  key={a.id}
                  to={a.deep_link || `/admin/operations-control?highlight=${encodeURIComponent(a.id)}`}
                  data-testid={`${testidPrefix}-action-${a.id}`}
                  className="group relative flex flex-col rounded-lg border border-slate-200 bg-white shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-150 p-4"
                >
                  <div className="text-sm font-semibold text-slate-900 leading-tight">{a.title}</div>
                  <p className="mt-1 text-[12px] text-slate-600 leading-snug">{a.description}</p>
                  {a.never_touches ? (
                    <p className="mt-2 text-[11px] font-mono text-slate-500">
                      Never touches: {a.never_touches}
                    </p>
                  ) : null}
                  <div className="mt-3 text-[11px] font-mono text-emerald-700">Open →</div>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Trust gaps */}
        {manifest.trust_gaps && manifest.trust_gaps.length > 0 && (
          <section className="mt-8 min-w-0" data-testid={`${testidPrefix}-gaps`}>
            <div className="mb-2 flex items-center gap-2">
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
                Trust Gaps
              </div>
            </div>
            <div className="w-full max-w-full overflow-x-auto rounded-lg border border-slate-200 bg-white">
              <table className="min-w-full text-xs">
                <thead className="bg-slate-50 text-slate-500">
                  <tr>
                    <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Gap</th>
                    <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Severity</th>
                    <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Owner</th>
                    <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Target</th>
                    <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Risk</th>
                    <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Status</th>
                    <th className="text-left px-3 py-2 font-semibold uppercase tracking-wider text-[10px]">Blocks prod?</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {manifest.trust_gaps.map((g) => (
                    <tr key={g.id} data-testid={`${testidPrefix}-${g.id}`}>
                      <td className="px-3 py-2 text-slate-800 font-medium">{g.title}</td>
                      <td className="px-3 py-2">
                        <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-widest ring-1 ${SEVERITY_STYLES[g.severity] || "bg-slate-100 text-slate-700 ring-slate-300"}`}>
                          {g.severity}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-slate-700 font-mono">{g.owner}</td>
                      <td className="px-3 py-2 text-slate-700 font-mono">{g.target_track}</td>
                      <td className="px-3 py-2 text-slate-700">{g.risk}</td>
                      <td className="px-3 py-2 text-slate-700">{g.current_status}</td>
                      <td className="px-3 py-2 text-slate-700">
                        {g.blocks_production ? (
                          <span className="text-rose-700 font-semibold">YES</span>
                        ) : (
                          <span className="text-slate-500">no</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <EvidenceDrawer
          card={drawerCard}
          open={drawerOpen}
          onOpenChange={setDrawerOpen}
          testidPrefix={`${testidPrefix}-drawer`}
        />
      </PortalShell>
    </div>
  );
}
