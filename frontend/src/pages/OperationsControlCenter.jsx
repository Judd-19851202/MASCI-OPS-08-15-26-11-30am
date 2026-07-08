// TRACK 24.17 · Operations Control Center — unified super-admin
// maintenance console. Renders one card per registered operation with:
//   · live status snapshot
//   · description + read/write/never-touches contract
//   · dry-run button
//   · apply button (disabled until dry-run completes + phrase entered)
//   · audit log tab
//
// TRACK 25.01 · Phase C — OCC is now the canonical home for
// deploy readiness, recovery playbook, integration probes, and
// scheduler run history. Legacy pages render a LegacyMovedBanner
// pointing here. A `?highlight=<operation-id>` query param scrolls
// the target card into view and pulses it so operators arriving
// from a legacy banner land exactly on the right tool.
//
// This is the single place a non-coder platform owner runs cleanup,
// health, and R2 migration. No shell required.
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import axios from "axios";

const API = (
  (typeof process !== "undefined" &&
    process.env &&
    process.env.REACT_APP_BACKEND_URL) ||
  ""
) + "/api";

const CATEGORY_LABELS = {
  health: "System Health",
  storage: "Storage & Disk",
  r2: "R2 Object Storage",
  backups: "Backups",
  daily_reports: "Daily Reports",
  ai: "AI Intelligence",
  documents: "Documents & OCR",
  photos: "Photos",
  email: "Email & Notifications",
  data_integrity: "Data Integrity",
  queues: "Queues & Schedulers",
  security: "Security & Deployment",
};

const CATEGORY_ORDER = [
  "health",
  "storage",
  "r2",
  "backups",
  "daily_reports",
  "ai",
  "email",
  "security",
  "documents",
  "photos",
  "data_integrity",
  "queues",
];

const RISK_STYLES = {
  info: { bg: "bg-slate-100", fg: "text-slate-700", label: "read-only" },
  safe_cleanup: { bg: "bg-emerald-100", fg: "text-emerald-800", label: "safe cleanup" },
  data_migration: { bg: "bg-amber-100", fg: "text-amber-800", label: "data migration" },
  destructive: { bg: "bg-rose-100", fg: "text-rose-800", label: "destructive" },
  external_provider: { bg: "bg-sky-100", fg: "text-sky-800", label: "external provider" },
  security_sensitive: { bg: "bg-purple-100", fg: "text-purple-800", label: "security sensitive" },
};

const STATUS_STYLES = {
  healthy: "bg-emerald-50 text-emerald-700 border-emerald-200",
  warning: "bg-amber-50 text-amber-800 border-amber-200",
  critical: "bg-rose-50 text-rose-800 border-rose-200",
  unavailable: "bg-slate-50 text-slate-600 border-slate-200",
  dry_run_ready: "bg-sky-50 text-sky-800 border-sky-200",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  failed: "bg-rose-50 text-rose-800 border-rose-200",
};

function adminToken() {
  try {
    // TRACK 24.17 · order matters — check the canonical portal-token
    // key the platform sign-in flow writes to first, then fall back
    // to the legacy alias keys some older admin surfaces used.
    return (
      localStorage.getItem("masci.admin.token") ||
      localStorage.getItem("adminToken") ||
      localStorage.getItem("admin_token") ||
      ""
    );
  } catch (_e) {
    return "";
  }
}

function authHeaders() {
  const t = adminToken();
  return t ? { "X-Admin-Token": t } : {};
}

async function fetchOverview() {
  const r = await axios.get(`${API}/admin/operations-control/overview`, {
    headers: authHeaders(),
  });
  return r.data;
}

async function fetchAudit(limit = 50) {
  const r = await axios.get(
    `${API}/admin/operations-control/audit?limit=${limit}`,
    { headers: authHeaders() },
  );
  return r.data;
}

async function runOperation(operationId, mode, payload) {
  const r = await axios.post(
    `${API}/admin/operations-control/operations/${encodeURIComponent(operationId)}/${mode}`,
    payload || {},
    { headers: { "Content-Type": "application/json", ...authHeaders() } },
  );
  return r.data;
}

function RiskChip({ risk }) {
  const style = RISK_STYLES[risk] || RISK_STYLES.info;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${style.bg} ${style.fg}`}
      data-testid={`occ-risk-${risk}`}
    >
      {style.label}
    </span>
  );
}

function StatusPill({ status, children }) {
  const cls = STATUS_STYLES[status] || STATUS_STYLES.unavailable;
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-semibold uppercase tracking-wider ${cls}`}
      data-testid={`occ-status-${status}`}
    >
      {children || status || "—"}
    </span>
  );
}

function OperationCard({ op, onRun, onApply, dryRunState, highlighted, cardRef }) {
  const [expanded, setExpanded] = useState(false);
  const [confirmPhrase, setConfirmPhrase] = useState("");
  const [reason, setReason] = useState("");
  const snapshot = op.status_snapshot || {};
  const canDryRun = op.has_dry_run;
  const canApply =
    op.has_apply &&
    (!op.requires_dry_run || dryRunState?.dry_run_id) &&
    (!op.requires_confirmation ||
      confirmPhrase === (dryRunState?.confirmation_phrase || ""));
  const applyReason = !op.has_apply
    ? op.manual_reason || "Read-only operation — no apply available."
    : op.requires_dry_run && !dryRunState?.dry_run_id
      ? "Run the preview first."
      : op.requires_confirmation && !confirmPhrase
        ? `Type the confirmation phrase to enable apply.`
        : null;
  return (
    <div
      ref={cardRef}
      className={`rounded-lg border bg-white p-4 shadow-sm transition-all duration-500 ${
        highlighted
          ? "border-amber-500 ring-4 ring-amber-200"
          : "border-slate-200"
      }`}
      data-testid={`occ-card-${op.id}`}
      data-occ-op-id={op.id}
      data-occ-highlighted={highlighted ? "true" : "false"}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-900 truncate">
              {op.title}
            </h3>
            <RiskChip risk={op.risk} />
          </div>
          <p className="mt-1 text-xs text-slate-600 leading-relaxed">
            {op.description}
          </p>
        </div>
        <StatusPill status={snapshot.status || "unavailable"}>
          {snapshot.status || "—"}
        </StatusPill>
      </div>

      {snapshot.summary && (
        <div
          className="mt-2 rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-700"
          data-testid={`occ-summary-${op.id}`}
        >
          {snapshot.summary}
        </div>
      )}
      {snapshot.warnings && snapshot.warnings.length > 0 && (
        <ul className="mt-2 space-y-1 text-xs text-amber-800">
          {snapshot.warnings.map((w, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-amber-500">⚠</span>
              <span>{w}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        {canDryRun && (
          <button
            type="button"
            className="rounded-md border border-sky-200 bg-sky-50 px-3 py-1.5 text-xs font-medium text-sky-800 hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-50"
            onClick={() => onRun(op)}
            data-testid={`occ-dry-run-${op.id}`}
          >
            {op.risk === "info" ? "Refresh status" : "Preview / dry-run"}
          </button>
        )}
        {op.has_apply ? (
          <>
            {op.requires_confirmation && dryRunState?.dry_run_id && (
              <input
                type="text"
                value={confirmPhrase}
                onChange={(e) => setConfirmPhrase(e.target.value)}
                placeholder={`type: ${dryRunState.confirmation_phrase || ""}`}
                className="rounded-md border border-slate-300 px-2 py-1 text-xs font-mono"
                data-testid={`occ-confirm-${op.id}`}
              />
            )}
            <button
              type="button"
              disabled={!canApply}
              className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() =>
                onApply(op, {
                  dry_run_id: dryRunState?.dry_run_id,
                  confirmation_phrase:
                    dryRunState?.confirmation_phrase || undefined,
                  reason,
                })
              }
              data-testid={`occ-apply-${op.id}`}
              title={applyReason || "Ready to apply."}
            >
              Apply
            </button>
          </>
        ) : (
          <span
            className="text-[11px] italic text-slate-400"
            data-testid={`occ-manual-${op.id}`}
          >
            Read-only
          </span>
        )}
        <button
          type="button"
          className="ml-auto text-[11px] text-slate-500 underline"
          onClick={() => setExpanded((x) => !x)}
          data-testid={`occ-expand-${op.id}`}
        >
          {expanded ? "Hide contract" : "Show contract"}
        </button>
      </div>

      {expanded && (
        <div className="mt-3 rounded-md bg-slate-50 p-3 text-[11px] text-slate-600 font-mono">
          <div>
            <span className="text-slate-400">reads:</span>{" "}
            {op.reads.length ? op.reads.join(" · ") : "—"}
          </div>
          <div>
            <span className="text-slate-400">writes:</span>{" "}
            {op.writes.length ? op.writes.join(" · ") : "—"}
          </div>
          <div>
            <span className="text-slate-400">never touches:</span>{" "}
            {op.never_touches.length ? op.never_touches.join(" · ") : "—"}
          </div>
        </div>
      )}

      {dryRunState?.last_result && (
        <details className="mt-2 rounded-md bg-slate-900 text-slate-100 px-3 py-2">
          <summary className="cursor-pointer text-[11px] font-medium">
            Last result
          </summary>
          <pre
            className="mt-2 whitespace-pre-wrap break-all text-[10px] leading-snug"
            data-testid={`occ-result-${op.id}`}
          >
            {JSON.stringify(dryRunState.last_result, null, 2)}
          </pre>
        </details>
      )}

      {op.has_apply && (
        <div className="mt-2">
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Reason (recorded in audit log, optional)"
            className="w-full rounded-md border border-slate-200 px-2 py-1 text-[11px]"
            data-testid={`occ-reason-${op.id}`}
          />
        </div>
      )}
    </div>
  );
}

function AuditPanel({ rows }) {
  return (
    <div
      className="rounded-lg border border-slate-200 bg-white"
      data-testid="occ-audit-panel"
    >
      <div className="border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-900">Maintenance history</h3>
        <p className="text-xs text-slate-500">
          Immutable record of every dry-run and apply. Newest first.
        </p>
      </div>
      <ul className="divide-y divide-slate-100 max-h-[420px] overflow-y-auto">
        {rows.length === 0 && (
          <li className="px-4 py-4 text-xs text-slate-500">
            No maintenance actions yet.
          </li>
        )}
        {rows.map((r) => (
          <li
            key={r.action_id}
            className="px-4 py-2 text-xs"
            data-testid={`occ-audit-row-${r.action_id}`}
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-slate-800">{r.operation_id}</span>
              <span
                className={`ml-2 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                  r.mode === "apply"
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-sky-100 text-sky-800"
                }`}
              >
                {r.mode}
              </span>
            </div>
            <div className="text-slate-500 flex items-center justify-between mt-0.5">
              <span>{r.actor_email || r.actor_id}</span>
              <span>{new Date(r.ts).toLocaleString()}</span>
            </div>
            {r.error && (
              <div className="mt-1 text-rose-700 text-[11px]">error: {r.error}</div>
            )}
            {r.result?.summary && (
              <div className="mt-1 text-slate-700 text-[11px]">
                {r.result.summary}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function OperationsControlCenter() {
  const [overview, setOverview] = useState(null);
  const [audit, setAudit] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dryRunState, setDryRunState] = useState({}); // op.id -> { dry_run_id, confirmation_phrase, last_result }
  const [error, setError] = useState(null);
  // TRACK 25.01 · Phase C — deep-link highlight from LegacyMovedBanner.
  const highlightOpId = useMemo(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      return params.get("highlight") || "";
    } catch (_e) {
      return "";
    }
  }, []);
  const cardRefs = useRef({});

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [o, a] = await Promise.all([fetchOverview(), fetchAudit(60)]);
      setOverview(o);
      setAudit(a.audit || []);
      setError(null);
    } catch (e) {
      setError(
        e?.response?.status === 401 || e?.response?.status === 403
          ? "Super-admin access required."
          : e?.message || String(e),
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  // TRACK 25.01 · Phase C — scroll the highlighted card into view once
  // the overview loads. Runs on every overview change so a re-navigation
  // (same route, different highlight) still pulses the right card.
  useEffect(() => {
    if (!highlightOpId || !overview) return;
    const el = cardRefs.current[highlightOpId];
    if (el && typeof el.scrollIntoView === "function") {
      // Defer to next tick so layout settles before scrolling.
      requestAnimationFrame(() => {
        try {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        } catch (_e) {
          /* no-op */
        }
      });
    }
  }, [highlightOpId, overview]);

  const onRun = useCallback(
    async (op) => {
      try {
        const { result } = await runOperation(op.id, "dry-run", {});
        setDryRunState((s) => ({
          ...s,
          [op.id]: {
            dry_run_id: result?.dry_run_id,
            confirmation_phrase: op.requires_confirmation
              ? "MIGRATE TO R2"
              : undefined,
            last_result: result,
          },
        }));
        toast.success(`${op.title}: ${result?.status || "complete"}`);
        reload();
      } catch (e) {
        toast.error(
          `${op.title}: ${e?.response?.data?.detail || e?.message || "failed"}`,
        );
      }
    },
    [reload],
  );

  const onApply = useCallback(
    async (op, payload) => {
      try {
        const { result } = await runOperation(op.id, "apply", payload);
        if (result?.status === "failed") {
          toast.error(`${op.title}: ${result.error || "failed"}`);
        } else {
          toast.success(
            `${op.title}: ${result?.status || "applied"} · ${result?.reclaimed_human || ""}`,
          );
        }
        setDryRunState((s) => ({
          ...s,
          [op.id]: { ...(s[op.id] || {}), last_result: result, dry_run_id: null },
        }));
        reload();
      } catch (e) {
        toast.error(
          `${op.title}: ${e?.response?.data?.detail || e?.message || "failed"}`,
        );
      }
    },
    [reload],
  );

  const grouped = useMemo(() => {
    const groups = {};
    (overview?.operations || []).forEach((op) => {
      const key = op.category || "misc";
      (groups[key] ||= []).push(op);
    });
    return groups;
  }, [overview]);

  return (
    <div
      className="min-h-screen bg-slate-50"
      data-testid="operations-control-center"
    >
      <div className="mx-auto max-w-7xl px-4 py-6">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-widest text-rose-600 font-semibold">
              Platform Operations
            </div>
            <h1 className="text-2xl font-black text-slate-900">
              Operations Control Center
            </h1>
            <p className="mt-1 text-sm text-slate-600 max-w-2xl">
              Unified maintenance console. Run health probes and cleanup
              from one place. Every action is dry-run first, confirmed,
              and recorded in the audit log.
            </p>
          </div>
          <button
            type="button"
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100"
            onClick={reload}
            data-testid="occ-refresh-all"
          >
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </header>

        {error && (
          <div
            className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
            data-testid="occ-error"
          >
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {CATEGORY_ORDER.map((cat) => {
              const ops = grouped[cat];
              if (!ops || ops.length === 0) return null;
              return (
                <section key={cat} data-testid={`occ-section-${cat}`}>
                  <h2 className="mb-2 text-xs font-bold uppercase tracking-widest text-slate-500">
                    {CATEGORY_LABELS[cat] || cat}
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {ops.map((op) => (
                      <OperationCard
                        key={op.id}
                        op={op}
                        onRun={onRun}
                        onApply={onApply}
                        dryRunState={dryRunState[op.id]}
                        highlighted={op.id === highlightOpId}
                        cardRef={(node) => {
                          if (node) cardRefs.current[op.id] = node;
                        }}
                      />
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
          <div>
            <AuditPanel rows={audit} />
          </div>
        </div>
      </div>
    </div>
  );
}
