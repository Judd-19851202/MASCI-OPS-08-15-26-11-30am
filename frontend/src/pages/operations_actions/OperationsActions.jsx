/**
 * OA-1 · OperationsActions.jsx
 * Cross-portal inbox view. Filters · search · "Mine only" toggle.
 * Renders the mandatory coaching panel + new-action CTA at the top.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Search, Filter, RefreshCw, Loader2, ArrowLeft, Home, LayoutGrid } from "lucide-react";
import { useT } from "@/lib/i18n";
import { usePageTitle } from "@/lib/usePageTitle";
import { LangToggle } from "@/components/LangToggle";
import { MasciLogo } from "@/components/MasciLogo";
import CoachingPanel from "@/components/oa/CoachingPanel";
import StatusBadge from "@/components/oa/StatusBadge";
import {
  inferOperationsActionsPortalFromPath,
  oaApi, setOperationsActionsPortalScope, STATUSES, STATUS_LABEL, CATEGORIES, CATEGORY_LABEL,
  PRIORITIES, PRIORITY_LABEL, PRIORITY_TONE,
} from "@/lib/oa";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

export default function OperationsActions() {
  usePageTitle("Operations Actions · MASCI");
  const { t } = useT();
  const nav = useNavigate();
  const [actions, setActions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [statusF, setStatusF] = useState("");
  const [categoryF, setCategoryF] = useState("");
  const [priorityF, setPriorityF] = useState("");
  const [mine, setMine] = useState(false);

  useEffect(() => {
    setOperationsActionsPortalScope(inferOperationsActionsPortalFromPath(document.referrer || window.location.pathname));
  }, []);

  const load = useCallback(async (searchValue = q) => {
    setLoading(true); setErr("");
    try {
      const params = {};
      if (statusF) params.status = statusF;
      if (categoryF) params.category = categoryF;
      if (priorityF) params.priority = priorityF;
      if (searchValue.trim()) params.q = searchValue.trim();
      if (mine) params.mine = true;
      const [a, s] = await Promise.all([
        oaApi.list(params),
        oaApi.summary().catch(() => ({ data: null })),
      ]);
      setActions(a.data?.actions || []);
      setSummary(s.data || null);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Could not load Operations Actions.");
    } finally {
      setLoading(false);
    }
  }, [categoryF, mine, priorityF, q, statusF]);

  useEffect(() => { load(q); }, [statusF, categoryF, priorityF, mine, load, q]);
  useEffect(() => {
    const id = setTimeout(() => load(q), 250);
    return () => clearTimeout(id);

  }, [load, q]);

  const tiles = useMemo(() => {
    const c = summary?.counts || {};
    return STATUSES.map((s) => ({ key: s, label: STATUS_LABEL[s], count: c[s] || 0 }));
  }, [summary]);

  return (
    <div className="min-h-screen blueprint-bg pb-12" data-testid="oa-list-root">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-indigo-500">
        <div className="max-w-6xl mx-auto px-4 sm:px-8 py-3 flex items-center gap-3 flex-wrap">
          <Link to="/" className="inline-flex items-center text-white hover:text-indigo-200 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="oa-nav-home">
            <Home className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">{t("Home")}</span>
          </Link>
          <button onClick={() => nav(-1)} className="inline-flex items-center text-white hover:text-indigo-200 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="oa-nav-back">
            <ArrowLeft className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">{t("Back")}</span>
          </button>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <div className="flex-1" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-8 py-6">
        <div className="flex items-baseline justify-between gap-3 flex-wrap mb-2">
          <div>
            <div className="font-mono text-xs uppercase tracking-[0.22em] text-indigo-700 font-bold">OA-1 · OPERATIONS ACTIONS</div>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight mt-1">{t("Operations Actions")}</h1>
          </div>
          <button
            type="button"
            onClick={() => nav("/operations-actions/new")}
            data-testid="oa-create-cta"
            className="inline-flex items-center gap-2 px-3 py-2 rounded bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold uppercase tracking-wide"
          >
            <Plus className="w-4 h-4" /> {t("New Action")}
          </button>
        </div>
        <p className="text-sm text-slate-600 max-w-2xl mb-4" data-testid="oa-positioning-line">
          {t("Operations Action — operational ownership, not a ticket.")}
        </p>

        {/* Mandatory coaching strip */}
        <CoachingPanel className="mb-5" />

        {/* Summary tiles */}
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-5" data-testid="oa-summary-tiles">
          {tiles.map((tl) => (
            <button
              key={tl.key}
              type="button"
              onClick={() => setStatusF(statusF === tl.key ? "" : tl.key)}
              data-testid={`oa-summary-tile-${tl.key}`}
              className={`rounded-md border-2 p-2 sm:p-3 text-center transition ${statusF === tl.key ? "border-indigo-500 bg-indigo-50" : "border-slate-200 bg-white hover:border-slate-300"}`}
            >
              <div className="text-2xl font-black leading-none text-slate-900">{tl.count}</div>
              <div className="text-[9px] sm:text-[10px] font-mono uppercase tracking-[0.16em] mt-1 text-slate-600 font-bold">{t(tl.label)}</div>
            </button>
          ))}
        </div>

        {/* Filters */}
        <div className="bg-white border border-slate-200 rounded-md p-3 mb-4 grid grid-cols-1 sm:grid-cols-4 gap-2" data-testid="oa-filter-row">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("Search actions…")}
              className="w-full pl-8 pr-2 py-2 border border-slate-300 rounded text-sm"
              data-testid="oa-filter-q"
            />
          </div>
          <select value={categoryF} onChange={(e) => setCategoryF(e.target.value)} className="py-2 px-2 border border-slate-300 rounded text-sm" data-testid="oa-filter-category">
            <option value="">{t("All categories")}</option>
            {CATEGORIES.map((c) => (<option key={c} value={c}>{t(CATEGORY_LABEL[c])}</option>))}
          </select>
          <select value={priorityF} onChange={(e) => setPriorityF(e.target.value)} className="py-2 px-2 border border-slate-300 rounded text-sm" data-testid="oa-filter-priority">
            <option value="">{t("All priorities")}</option>
            {PRIORITIES.map((p) => (<option key={p} value={p}>{t(PRIORITY_LABEL[p])}</option>))}
          </select>
          <label className="flex items-center gap-2 px-2 py-2 border border-slate-300 rounded text-sm cursor-pointer" data-testid="oa-filter-mine-wrap">
            <input type="checkbox" checked={mine} onChange={(e) => setMine(e.target.checked)} data-testid="oa-filter-mine" />
            <span>{t("Mine only")}</span>
          </label>
        </div>

        {/* Action list */}
        <div className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid="oa-list-table">
          {loading ? (
            <div className="text-center text-slate-500 py-10" data-testid="oa-list-loading">
              <Loader2 className="w-5 h-5 inline animate-spin mr-2" /> {t("Loading operational visibility…") || "Loading…"}
            </div>
          ) : err ? (
            <div className="text-center py-10" data-testid="oa-list-error">
              <div className="inline-block bg-amber-50 border border-amber-200 rounded-md px-4 py-3 text-amber-900 text-sm max-w-md">
                <div className="font-mono text-[10px] uppercase tracking-wider font-bold mb-1 text-amber-700">{t("Sign-in required")}</div>
                {err}
              </div>
            </div>
          ) : actions.length === 0 ? (
            <div className="text-center text-slate-500 py-10" data-testid="oa-list-empty">
              <LayoutGrid className="w-8 h-8 mx-auto mb-2 text-slate-400" />
              {t("No actions match these filters.")}
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {actions.map((a) => (
                <li key={a.id} data-testid={`oa-list-row-${a.id}`}>
                  <button
                    type="button"
                    onClick={() => nav(`/operations-actions/${a.id}`)}
                    className="w-full flex items-start gap-3 px-3 py-3 hover:bg-slate-50 text-left"
                  >
                    <div className="shrink-0 flex flex-col gap-1 items-start min-w-[110px]">
                      <span className="font-mono text-[10px] tracking-wider text-slate-500">{a.oa_number}</span>
                      <StatusBadge status={a.status} />
                      <span className={`inline-block px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-wider font-bold ${PRIORITY_TONE[a.priority] || ""}`}>
                        {t(PRIORITY_LABEL[a.priority] || a.priority)}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-slate-900 truncate">{a.title}</div>
                      <div className="text-xs text-slate-600 mt-0.5">
                        {t(CATEGORY_LABEL[a.category] || a.category)}
                        {a.job_number ? <> · <span className="font-mono">{a.job_number}</span></> : null}
                        {a.location ? <> · {a.location}</> : null}
                      </div>
                      <div className="text-[10px] font-mono text-slate-500 mt-1">
                        {a.current_owner?.name
                          ? <>{t("Owner")}: <span className="font-bold text-slate-700">{a.current_owner.name}</span></>
                          : <span className="text-amber-700">{t("Pick an owner")}</span>}
                        <span className="opacity-50"> · </span>
                        {t("Created")} {formatPlatformDate(a.created_at)}
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Refresh */}
        <div className="mt-3 text-right">
          <button onClick={load} className="text-[10px] font-mono uppercase tracking-wider text-slate-500 hover:text-slate-800 inline-flex items-center gap-1" data-testid="oa-list-refresh">
            <RefreshCw className="w-3 h-3" /> {t("Refresh")}
          </button>
        </div>
      </main>
    </div>
  );
}
