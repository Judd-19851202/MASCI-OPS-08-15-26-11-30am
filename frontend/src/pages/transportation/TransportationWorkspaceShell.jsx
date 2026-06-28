/**
 * TRACK 18.00 · Universal Transportation Operations shell.
 *
 *   ┌────────────────────────────────────────────────────────┐
 *   │ TxOpsHeader (workspace title · context · actions)      │
 *   ├──────────────────────────────────────┬─────────────────┤
 *   │ BODY (workspace-specific content)    │ RIGHT RAIL      │
 *   │                                      │  · Recent       │
 *   │                                      │  · Timeline     │
 *   │                                      │  · Related      │
 *   │                                      │  · Open Actions │
 *   │                                      │  · Audit        │
 *   └──────────────────────────────────────┴─────────────────┘
 *
 * Phase A — shell + scaffolded right rail.
 * Phase D — right rail wired to the universal relationships
 * composer at GET /api/admin/transportation/related/{entity_type}/{entity_id}.
 *
 * Doctrine:
 *   - One card, one chip, one header library.
 *   - No new collections.
 *   - No new scoring.
 *   - 30-second in-memory cache per entity (entity_type:entity_id).
 *   - Graceful loading / empty / error states.
 *   - Every row deep-links via the source-labeled `route` field.
 */
import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Activity, History, Inbox, Link2, Sparkles,
} from "lucide-react";
import { txGet, useTxPathPrefix } from "./_shared";

/* ─────────────────────────────────────────────────────────────────
 * One shared header.
 * ────────────────────────────────────────────────────────────── */
export function TxOpsHeader({
  workspace, title, subtitle, rightSlot, testid,
}) {
  return (
    <header
      data-testid={testid || "txops-header"}
      className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-3 mb-4"
    >
      <div className="min-w-0">
        {workspace ? (
          <div
            data-testid="txops-header-group"
            className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold"
          >
            {workspace}
          </div>
        ) : null}
        <h1
          data-testid="txops-header-title"
          className="text-2xl font-semibold text-slate-900 leading-tight"
        >
          {title}
        </h1>
        {subtitle ? (
          <p className="text-sm text-slate-600 mt-1 max-w-2xl">{subtitle}</p>
        ) : null}
      </div>
      {rightSlot ? (
        <div
          data-testid="txops-header-actions"
          className="flex items-center gap-2 flex-shrink-0"
        >
          {rightSlot}
        </div>
      ) : null}
    </header>
  );
}

/* ─────────────────────────────────────────────────────────────────
 * Section wrapper.
 * ────────────────────────────────────────────────────────────── */
function RailSection({ icon: Icon, title, testid, count, children }) {
  return (
    <section
      data-testid={testid}
      className="rounded-md border border-slate-200 bg-white"
    >
      <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-slate-100">
        <div className="flex items-center gap-2">
          {Icon ? <Icon className="h-3.5 w-3.5 text-slate-500" /> : null}
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-700">
            {title}
          </div>
        </div>
        {typeof count === "number" ? (
          <span
            data-testid={`${testid}-count`}
            className="text-[10px] font-semibold text-slate-500 bg-slate-100 rounded px-1.5 py-0.5"
          >
            {count}
          </span>
        ) : null}
      </div>
      <div className="p-3 text-xs text-slate-600">{children}</div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────
 * Live data fetch with 30 s in-memory cache, keyed by entity tuple.
 * ────────────────────────────────────────────────────────────── */
const RELATED_CACHE = new Map(); // key → { at, payload }
const CACHE_TTL_MS = 30 * 1000;

function _key(ctx) {
  if (!ctx || !ctx.type || !ctx.id) return null;
  return `${ctx.type}::${ctx.id}`;
}

export function useTransportationRelationships(entityContext) {
  const [state, setState] = React.useState({
    loading: false, error: null, payload: null,
  });
  const key = _key(entityContext);

  React.useEffect(() => {
    let cancelled = false;
    if (!key) {
      setState({ loading: false, error: null, payload: null });
      return () => { cancelled = true; };
    }
    const cached = RELATED_CACHE.get(key);
    if (cached && (Date.now() - cached.at) < CACHE_TTL_MS) {
      setState({ loading: false, error: null, payload: cached.payload });
      return () => { cancelled = true; };
    }
    setState((s) => ({ ...s, loading: true, error: null }));
    (async () => {
      try {
        const resp = await txGet(
          `/admin/transportation/related/${entityContext.type}/${encodeURIComponent(entityContext.id)}`
        );
        const payload = resp && resp.data ? resp.data : resp;
        if (cancelled) return;
        RELATED_CACHE.set(key, { at: Date.now(), payload });
        setState({ loading: false, error: null, payload });
      } catch (err) {
        if (cancelled) return;
        setState({
          loading: false,
          error: err && err.message ? err.message : "Unable to load relationships",
          payload: null,
        });
      }
    })();
    return () => { cancelled = true; };
  }, [key, entityContext]);

  return state;
}

/* ─────────────────────────────────────────────────────────────────
 * Row primitives.
 * ────────────────────────────────────────────────────────────── */
function _rewriteToPrefix(target, prefix) {
  // TRACK 18.12 · Rewrite any backend-emitted /admin/transportation
  // user-facing route to the active prefix so dispatch-authenticated
  // users never bounce into the admin shell.
  if (typeof target !== "string") return target;
  if (target.startsWith("/admin/transportation")) {
    return prefix + target.slice("/admin/transportation".length);
  }
  return target;
}

function RelatedRow({ row, testid }) {
  const prefix = useTxPathPrefix();
  return (
    <Link
      to={_rewriteToPrefix(row.route, prefix) || "#"}
      data-testid={testid}
      className="block hover:bg-slate-50 rounded px-2 py-1.5 -mx-2"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          {row.type || "record"}
        </span>
        {row.status ? (
          <span className="text-[10px] text-slate-500 italic">{row.status}</span>
        ) : null}
      </div>
      <div className="text-xs font-medium text-slate-800 truncate">
        {row.title || "—"}
      </div>
      {row.subtitle ? (
        <div className="text-[11px] text-slate-500 truncate">{row.subtitle}</div>
      ) : null}
    </Link>
  );
}

function AuditRow({ row, testid }) {
  const prefix = useTxPathPrefix();
  const target = _rewriteToPrefix(row.route, prefix) || `${prefix}/administration/audit`;
  return (
    <Link
      to={target}
      data-testid={testid}
      className="block hover:bg-slate-50 rounded px-2 py-1 -mx-2"
    >
      <div className="text-[11px] font-mono text-slate-700 truncate">
        {row.kind || "event"}
      </div>
      <div className="text-[10px] text-slate-500 truncate">
        {row.at || ""}{row.actor ? ` · ${row.actor}` : ""}
      </div>
    </Link>
  );
}

function EmptyHint({ testid, label }) {
  return (
    <div
      data-testid={testid}
      className="text-[11px] text-slate-400 italic"
    >
      {label}
    </div>
  );
}

function LoadingHint({ testid }) {
  return (
    <div
      data-testid={testid}
      className="text-[11px] text-slate-400 italic"
    >
      Loading…
    </div>
  );
}

function ErrorHint({ testid, message }) {
  return (
    <div
      data-testid={testid}
      className="text-[11px] text-rose-700 italic"
    >
      {message || "Unable to load."}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────
 * Universal right rail — live in Phase D.
 * ────────────────────────────────────────────────────────────── */
export function TxOpsRightRail({
  entityContext,
  auditHref,
  testid,
}) {
  const location = useLocation();
  // Allow ?entity_type=&entity_id= to drive the rail when no explicit
  // context is passed. Lets Universal Search deep-link into any
  // workspace and immediately populate the rail.
  const ctx = React.useMemo(() => {
    if (entityContext && entityContext.type && entityContext.id) {
      return entityContext;
    }
    try {
      const sp = new URLSearchParams(location.search || "");
      const t = sp.get("entity_type");
      const i = sp.get("entity_id");
      if (t && i) return { type: t, id: i };
    } catch (_e) {
      /* ignore */
    }
    return null;
  }, [entityContext, location.search]);

  const { loading, error, payload } = useTransportationRelationships(ctx);
  const sections = (payload && payload.sections) || {
    recent_activity: [], timeline: [], related_records: [],
    open_actions: [], audit: [],
  };
  const counts = (payload && payload.counts) || {};

  const noContext = !ctx;
  const auditFallback = auditHref || "/admin/transportation/administration/audit";

  const renderBody = (section, render, emptyLabel, emptyTestid) => {
    if (noContext) {
      return (
        <EmptyHint
          testid={emptyTestid}
          label="Select an entity to see live relationships."
        />
      );
    }
    if (loading) return <LoadingHint testid={`${emptyTestid}-loading`} />;
    if (error) {
      return <ErrorHint testid={`${emptyTestid}-error`} message={error} />;
    }
    const rows = sections[section] || [];
    if (!rows.length) {
      return <EmptyHint testid={emptyTestid} label={emptyLabel} />;
    }
    return render(rows);
  };

  return (
    <aside
      data-testid={testid || "txops-right-rail"}
      data-entity-type={ctx ? ctx.type : ""}
      data-entity-id={ctx ? ctx.id : ""}
      className="hidden xl:flex flex-col gap-3 w-72 shrink-0"
    >
      {ctx && payload && payload.entity ? (
        <div
          data-testid="txops-rail-entity-banner"
          className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2"
        >
          <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">
            {payload.entity.type}
          </div>
          <Link
            to={payload.entity.route || "#"}
            data-testid="txops-rail-entity-link"
            className="text-sm font-semibold text-slate-900 hover:underline"
          >
            {payload.entity.title}
          </Link>
          {payload.entity.subtitle ? (
            <div
              data-testid="txops-rail-entity-subtitle"
              className="text-[11px] text-slate-500 truncate"
            >
              {payload.entity.subtitle}
            </div>
          ) : null}
        </div>
      ) : null}

      <RailSection
        icon={Activity}
        title="Recent Activity"
        testid="txops-rail-recent-activity"
        count={counts.recent_activity}
      >
        {renderBody(
          "recent_activity",
          (rows) => (
            <div className="space-y-1">
              {rows.map((r, i) => (
                <AuditRow
                  key={`ra-${i}`}
                  row={r}
                  testid={`txops-rail-recent-activity-row-${i}`}
                />
              ))}
            </div>
          ),
          "No recent activity.",
          "txops-rail-recent-activity-empty",
        )}
      </RailSection>

      <RailSection
        icon={History}
        title="Timeline"
        testid="txops-rail-timeline"
        count={counts.timeline}
      >
        {renderBody(
          "timeline",
          (rows) => (
            <div className="space-y-1">
              {rows.map((r, i) => (
                <AuditRow
                  key={`tl-${i}`}
                  row={r}
                  testid={`txops-rail-timeline-row-${i}`}
                />
              ))}
            </div>
          ),
          "No timeline events.",
          "txops-rail-timeline-empty",
        )}
      </RailSection>

      <RailSection
        icon={Link2}
        title="Related Records"
        testid="txops-rail-related"
        count={counts.related_records}
      >
        {renderBody(
          "related_records",
          (rows) => (
            <div className="space-y-1">
              {rows.map((r, i) => (
                <RelatedRow
                  key={`rr-${i}`}
                  row={r}
                  testid={`txops-rail-related-row-${i}`}
                />
              ))}
            </div>
          ),
          "No related records.",
          "txops-rail-related-empty",
        )}
      </RailSection>

      <RailSection
        icon={Inbox}
        title="Open Actions"
        testid="txops-rail-open-actions"
        count={counts.open_actions}
      >
        {renderBody(
          "open_actions",
          (rows) => (
            <div className="space-y-1">
              {rows.map((r, i) => (
                <RelatedRow
                  key={`oa-${i}`}
                  row={r}
                  testid={`txops-rail-open-actions-row-${i}`}
                />
              ))}
            </div>
          ),
          "No open actions.",
          "txops-rail-open-actions-empty",
        )}
      </RailSection>

      <RailSection
        icon={Sparkles}
        title="Audit"
        testid="txops-rail-audit"
        count={counts.audit}
      >
        {renderBody(
          "audit",
          (rows) => (
            <div className="space-y-1">
              {rows.map((r, i) => (
                <AuditRow
                  key={`au-${i}`}
                  row={r}
                  testid={`txops-rail-audit-row-${i}`}
                />
              ))}
              <Link
                to={auditFallback}
                data-testid="txops-rail-audit-link"
                className="block mt-1 text-amber-700 hover:text-amber-900 underline-offset-2 hover:underline"
              >
                Open the full audit timeline →
              </Link>
            </div>
          ),
          "No audit events.",
          "txops-rail-audit-empty",
        )}
        {noContext ? (
          <Link
            to={auditFallback}
            data-testid="txops-rail-audit-link"
            className="block mt-2 text-amber-700 hover:text-amber-900 underline-offset-2 hover:underline"
          >
            Open the full audit timeline →
          </Link>
        ) : null}
      </RailSection>
    </aside>
  );
}

/* ─────────────────────────────────────────────────────────────────
 * Shell wrapper.
 * ────────────────────────────────────────────────────────────── */
export default function TransportationWorkspaceShell({
  workspace,
  title,
  subtitle,
  rightSlot,
  entityContext,
  hideRightRail = false,
  children,
}) {
  return (
    <div
      data-testid="txops-workspace-shell"
      className="space-y-3"
    >
      <TxOpsHeader
        workspace={workspace}
        title={title}
        subtitle={subtitle}
        rightSlot={rightSlot}
      />
      <div className="flex gap-6">
        <main
          data-testid="txops-workspace-body"
          className="flex-1 min-w-0 space-y-4"
        >
          {children}
        </main>
        {hideRightRail ? null : (
          <TxOpsRightRail entityContext={entityContext} />
        )}
      </div>
    </div>
  );
}
