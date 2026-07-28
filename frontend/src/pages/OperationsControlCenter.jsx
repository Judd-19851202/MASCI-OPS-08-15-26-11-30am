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
// TRACK 25 · SPRINT 2 — OCC becomes the platform's Trust Center.
// A read-only Health Layer above the maintenance console shows 8
// operational sections × N live probes, each with an evidence
// drawer showing source endpoint · raw payload · reason · recommended
// action · drill-down. All child probes are fanned out server-side
// by `GET /api/admin/occ/health` — one canonical trust snapshot,
// no server-side cache, refresh triggered by the operator only.
//
// Read-only Health cards + action-first Maintenance console below =
// truth layer + action layer, no duplicated action surface.
//
// This is the single place a non-coder platform owner runs cleanup,
// health, and R2 migration. No shell required.
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import axios from "axios";
import { Link } from "react-router-dom";
import {
  Activity, AlertTriangle, RefreshCw,
  Search as SearchIcon, ShieldAlert, X,
} from "lucide-react";

// TRACK 27.03 · Phase 3 · Canonical local-time formatter.
import { formatPlatformTime } from "@/lib/platformTime";

// TRACK 25A · Universal Admin OS shell so OCC matches every other
// domain page (PortalShell + SideNavV3 + breadcrumb).
import { PortalShell } from "@/design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";

import {
  EvidenceDrawer,
  EvidenceSummary,
  HealthCard,
  TrustStatusPill,
  TruthOwnerPanel,
  TRUST_STATUS_STYLES,
  sortCardsByAttention,
} from "@/components/admin/trust/TrustPrimitives";

const API = (
  (typeof process !== "undefined" &&
    process.env &&
    process.env.REACT_APP_BACKEND_URL) ||
  ""
) + "/api";

const CATEGORY_LABELS = {
  health: "System Health",
  storage: "Storage & Disk",
  governance: "Operations Repair Console",
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
  "governance",
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

const TRUST_CANONICAL_TO_UI = {
  VERIFIED: "green",
  DEGRADED: "yellow",
  MISMATCH: "red",
  UNVERIFIABLE: "unknown",
  NOT_APPLICABLE: "unknown",
  green: "green",
  yellow: "yellow",
  red: "red",
  unknown: "unknown",
};

function normalizeTrustStatus(status) {
  if (!status) return "unknown";
  return (
    TRUST_CANONICAL_TO_UI[String(status).toUpperCase()] ||
    TRUST_CANONICAL_TO_UI[String(status).toLowerCase()] ||
    "unknown"
  );
}

function normalizeTrustCard(card) {
  return {
    ...card,
    status: normalizeTrustStatus(card?.status || card?.canonical_status),
    raw_status: card?.status || "UNKNOWN",
    raw_canonical_status: card?.canonical_status || "UNKNOWN",
  };
}

function deriveTrustCounts(snapshot) {
  const canonical = snapshot?.canonical_counts;
  if (canonical) {
    return {
      green: Number(canonical.verified || 0),
      yellow: Number(canonical.degraded || 0),
      red: Number(canonical.mismatch || 0),
      unknown: Number(canonical.unverifiable || 0),
      notApplicable: Number(canonical.not_applicable || 0),
    };
  }

  const raw = snapshot?.counts || {};
  return {
    green: Number(raw.green || raw.VERIFIED || 0),
    yellow: Number(raw.yellow || raw.DEGRADED || 0),
    red: Number(raw.red || raw.MISMATCH || 0),
    unknown: Number(raw.unknown || raw.UNVERIFIABLE || 0),
    notApplicable: Number(raw.NOT_APPLICABLE || 0),
  };
}

function TrustLayerBoundedDisclosure({ snapshot }) {
  if (!snapshot?.truth_surface || !snapshot?.truth_relationship) return null;

  const surface = snapshot.truth_surface || {};
  const relationship = snapshot.truth_relationship || {};
  const conflicts = relationship.conflicts || [];
  const unknownCount = Number(snapshot?.canonical_counts?.unverifiable || 0);
  const neutralCount = Number(snapshot?.canonical_counts?.not_applicable || 0);

  return (
    <div className="space-y-4" data-testid="trust-layer-bounded-wrapper">
      <div
        className="rounded-2xl border border-slate-200 bg-white p-4"
        data-testid="trust-layer-bounded-disclosure"
      >
        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
          Bounded aggregate disclosure
        </div>
        <p
          className="mt-2 text-sm text-slate-800"
          data-testid="trust-layer-bounded-summary"
        >
          This OCC health layer is an aggregator over shared operational posture.
          Child source owners remain authoritative, and this surface stays read-only.
        </p>
        <div
          className="mt-3 grid gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700 sm:grid-cols-2 lg:grid-cols-4"
          data-testid="trust-layer-bounded-grid"
        >
          <div data-testid="trust-layer-bounded-role"><span className="font-semibold text-slate-900">Role:</span> {relationship.role || surface.role || "UNKNOWN"}</div>
          <div data-testid="trust-layer-bounded-subject"><span className="font-semibold text-slate-900">Truth subject:</span> {surface.truth_subject || "UNKNOWN"}</div>
          <div data-testid="trust-layer-bounded-owner"><span className="font-semibold text-slate-900">Canonical owner:</span> {relationship.canonical_owner_id || surface.canonical_owner_id || "UNKNOWN"}</div>
          <div data-testid="trust-layer-bounded-owner-route"><span className="font-semibold text-slate-900">Canonical owner route:</span> {relationship.canonical_owner_route || "—"}</div>
          <div data-testid="trust-layer-bounded-unknowns"><span className="font-semibold text-slate-900">Unverifiable cards:</span> {unknownCount}</div>
          <div data-testid="trust-layer-bounded-neutral"><span className="font-semibold text-slate-900">Neutral / not applicable:</span> {neutralCount}</div>
          <div data-testid="trust-layer-bounded-canonical"><span className="font-semibold text-slate-900">Canonical status:</span> {relationship.canonical_status || snapshot.overall_canonical || "UNKNOWN"}</div>
          <div data-testid="trust-layer-bounded-derived"><span className="font-semibold text-slate-900">Displayed aggregate:</span> {relationship.derived_status || snapshot.overall_status || "UNKNOWN"}</div>
        </div>
        <div
          className={`mt-3 rounded-xl border p-3 text-xs ${
            conflicts.length
              ? "border-rose-200 bg-rose-50 text-rose-900"
              : "border-emerald-200 bg-emerald-50 text-emerald-900"
          }`}
          data-testid="trust-layer-bounded-conflicts"
        >
          {conflicts.length ? (
            <>
              <div className="font-semibold">Aggregate contradictions</div>
              <ul className="mt-1 list-disc space-y-1 pl-4">
                {conflicts.map((conflict, index) => (
                  <li key={`trust-layer-conflict-${index}`}>{conflict}</li>
                ))}
              </ul>
            </>
          ) : (
            <div>
              <span className="font-semibold">Conflict state:</span> No aggregate contradiction reported. Unknown or missing evidence still remains disclosed card-by-card.
            </div>
          )}
        </div>
      </div>

      <TruthOwnerPanel
        title="Aggregator truth relationship"
        surface={surface}
        relationship={relationship}
        checkedAt={snapshot?.generated_at || "—"}
        testidPrefix="trust-layer-owner-panel"
      />
    </div>
  );
}

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

// TRACK 25 · SPRINT 2 · Trust Layer probe — one canonical fetch.
async function fetchTrustLayer() {
  const r = await axios.get(`${API}/admin/occ/health`, { headers: authHeaders() });
  return r.data;
}

function TrustLayer({ snapshot, loading, error, onRefresh, lastFetchedAt }) {
  const [drawerCard, setDrawerCard] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all"); // all | red | yellow | unknown | green
  const [query, setQuery] = useState("");

  const openDrawer = useCallback((card) => {
    setDrawerCard(card);
    setDrawerOpen(true);
  }, []);

  const normalizedSections = useMemo(() => {
    const list = snapshot?.sections || [];
    return list.map((sec) => ({
      ...sec,
      status: normalizeTrustStatus(sec.status),
      cards: (sec.cards || []).map(normalizeTrustCard),
    }));
  }, [snapshot]);

  const filteredSections = useMemo(() => {
    const list = normalizedSections || [];
    return list.map((sec) => {
      const q = query.trim().toLowerCase();
      const filtered = sortCardsByAttention(sec.cards).filter((c) => {
        if (statusFilter !== "all" && c.status !== statusFilter) return false;
        if (!q) return true;
        return (
          c.title.toLowerCase().includes(q) ||
          (c.summary || "").toLowerCase().includes(q) ||
          (c.endpoint || "").toLowerCase().includes(q)
        );
      });
      return { ...sec, cards: filtered };
    });
  }, [normalizedSections, statusFilter, query]);

  const attentionCards = useMemo(() => {
    const all = normalizedSections.flatMap((s) => s.cards);
    return sortCardsByAttention(all).filter((c) => c.status === "red").slice(0, 4);
  }, [normalizedSections]);

  const counts = deriveTrustCounts(snapshot);
  const overall = snapshot
    ? normalizeTrustStatus(snapshot?.overall_status || snapshot?.overall_canonical)
    : "unknown";

  return (
    <section
      className="mb-8"
      data-testid="trust-layer"
    >
      {/* ── Header + refresh ────────────────────────────────── */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <div className="min-w-0">
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
            Trust Center · read-only
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2 min-w-0">
            <TrustStatusPill status={overall} testid="trust-layer-overall-pill" />
            <span
              className="text-sm font-semibold text-slate-900 min-w-0 break-words"
              data-testid="trust-layer-overall-summary"
            >
              {overall === "red"
                ? "One or more operational systems report a critical condition."
                : overall === "yellow"
                ? "One or more operational systems need attention."
                : overall === "green"
                ? "All wired operational systems report healthy."
                : snapshot
                ? "Operational posture is currently bounded by missing or unverifiable evidence."
                : "Trust snapshot unavailable — press Refresh."}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
          <div data-testid="trust-layer-count-healthy">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Healthy</div>
            <div className="font-black text-emerald-700 text-xl leading-none">{counts.green || 0}</div>
          </div>
          <div data-testid="trust-layer-count-attention">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Attention</div>
            <div className="font-black text-amber-700 text-xl leading-none">{counts.yellow || 0}</div>
          </div>
          <div data-testid="trust-layer-count-critical">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Critical</div>
            <div className="font-black text-rose-700 text-xl leading-none">{counts.red || 0}</div>
          </div>
          <div data-testid="trust-layer-count-unknown">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Unknown</div>
            <div className="font-black text-slate-600 text-xl leading-none">{counts.unknown || 0}</div>
          </div>
          {counts.notApplicable > 0 ? (
            <div data-testid="trust-layer-count-neutral">
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Neutral</div>
              <div className="font-black text-slate-600 text-xl leading-none">{counts.notApplicable || 0}</div>
            </div>
          ) : null}
          <div className="min-w-0">
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">Last refreshed</div>
            <div
              className="font-mono text-xs text-slate-800 truncate"
              data-testid="trust-layer-last-refreshed"
            >
              {lastFetchedAt ? formatPlatformTime(lastFetchedAt) : "—"}
            </div>
          </div>
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-100 disabled:opacity-60 shrink-0"
            data-testid="trust-layer-refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {error ? (
        <div
          className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
          data-testid="trust-layer-error"
        >
          {error}
        </div>
      ) : null}

      {snapshot ? <TrustLayerBoundedDisclosure snapshot={snapshot} /> : null}

      {/* ── Attention-first strip (top RED items) ─────────── */}
      {attentionCards.length > 0 && (
        <div className="mb-6" data-testid="trust-layer-attention-strip">
          <div className="mb-2 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
              Needs immediate attention
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
            {attentionCards.map((c) => (
              <HealthCard key={`attn-${c.id}`} card={c} onOpen={openDrawer} />
            ))}
          </div>
        </div>
      )}

      {/* ── Search + status filter ─────────────────────────── */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[220px] max-w-md">
          <SearchIcon className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter cards by title, summary, or endpoint…"
            className="w-full rounded-md border border-slate-300 bg-white pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-300"
            data-testid="trust-layer-search"
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
              data-testid="trust-layer-search-clear"
              aria-label="Clear filter"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          ) : null}
        </div>
        {["all", "red", "yellow", "unknown", "green"].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setStatusFilter(s)}
            className={`rounded-md border px-2 py-1 text-[11px] font-semibold uppercase tracking-wider ${
              statusFilter === s
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100"
            }`}
            data-testid={`trust-layer-filter-${s}`}
          >
            {s === "all" ? "All" : (TRUST_STATUS_STYLES[s]?.label || s)}
          </button>
        ))}
      </div>

      {/* ── 8 sections ─────────────────────────────────────── */}
      <div className="space-y-6" data-testid="trust-layer-sections">
        {filteredSections.map((sec) => (
          <div key={sec.id} data-testid={`trust-section-${sec.id}`}>
            <div className="mb-2 flex items-center gap-2">
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
                {sec.label}
              </div>
              <TrustStatusPill status={sec.status} testid={`trust-section-${sec.id}-status`} />
              <div className="text-[10px] font-mono text-slate-400">
                {sec.cards.length}/{(normalizedSections.find((x) => x.id === sec.id)?.cards?.length) || 0} card(s)
              </div>
            </div>
            {sec.cards.length === 0 ? (
              <div
                className="rounded-md border border-dashed border-slate-300 bg-white px-3 py-4 text-xs text-slate-500"
                data-testid={`trust-section-${sec.id}-empty`}
              >
                No cards match the current filter.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {sec.cards.map((c) => (
                  <HealthCard key={c.id} card={c} onOpen={openDrawer} />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* ── Evidence drawer (rendered once) ─────────────── */}
      <EvidenceDrawer
        card={drawerCard}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
      />
    </section>
  );
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

function RepairHistory({ contract, operationId }) {
  const lastDryRun = contract?.last_dry_run;
  const lastApply = contract?.last_apply;
  if (!lastDryRun && !lastApply) return null;
  return (
    <div
      className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-3"
      data-testid={`occ-repair-history-${operationId}`}
    >
      <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
        Audit-linked repair history
      </div>
      <div className="mt-2 grid gap-2 sm:grid-cols-2 text-[11px] text-slate-700">
        <div data-testid={`occ-repair-history-dry-run-${operationId}`}>
          <div className="font-semibold text-slate-900">Latest dry-run</div>
          <div>{lastDryRun ? formatPlatformTime(lastDryRun.ts) : "No preview yet"}</div>
          <div className="font-mono text-slate-500 break-words">{lastDryRun?.actor_email || lastDryRun?.actor_id || "—"}</div>
        </div>
        <div data-testid={`occ-repair-history-apply-${operationId}`}>
          <div className="font-semibold text-slate-900">Latest apply</div>
          <div>{lastApply ? formatPlatformTime(lastApply.ts) : "No apply yet"}</div>
          <div className="font-mono text-slate-500 break-words">{lastApply?.actor_email || lastApply?.actor_id || "—"}</div>
        </div>
      </div>
    </div>
  );
}

function OperationCard({ op, onRun, onApply, dryRunState, highlighted, cardRef }) {
  const [expanded, setExpanded] = useState(false);
  const [confirmPhrase, setConfirmPhrase] = useState("");
  const [reason, setReason] = useState("");
  const snapshot = op.status_snapshot || {};
  const capability = op.capability || {};
  const contract = op.repair_contract || {};
  const canDryRun = op.has_dry_run;
  const canApply =
    op.has_apply &&
    capability.available !== false &&
    (!op.requires_dry_run || dryRunState?.dry_run_id) &&
    (!op.requires_confirmation ||
      confirmPhrase === (dryRunState?.confirmation_phrase || ""));
  const applyReason = !op.has_apply
    ? op.manual_reason || "Read-only operation — no apply available."
    : capability.available === false
      ? capability.disabled_reason || "Capability unavailable."
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
      {snapshot.candidate_count > 0 ? (
        <div
          className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900"
          data-testid={`occ-candidate-count-${op.id}`}
        >
          {snapshot.candidate_count} candidate change(s) currently eligible for repair.
        </div>
      ) : null}
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
            disabled={capability.available === false}
            title={capability.disabled_reason || "Run dry-run"}
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
          <div>
            <span className="text-slate-400">dry-run required:</span>{" "}
            {op.requires_dry_run ? "yes" : "no"}
          </div>
          <div>
            <span className="text-slate-400">confirmation phrase:</span>{" "}
            {contract.confirmation_phrase || "—"}
          </div>
        </div>
      )}

      <RepairHistory contract={contract} operationId={op.id} />

      {dryRunState?.last_result && (
        <details className="mt-2 rounded-md bg-slate-900 text-slate-100 px-3 py-2">
          <summary className="cursor-pointer text-[11px] font-medium">
            Last result
          </summary>
          <div className="mt-2 rounded-md bg-slate-50 p-2 text-slate-800" data-testid={`occ-result-${op.id}`}>
            <EvidenceSummary
              value={dryRunState.last_result}
              testidPrefix={`occ-result-${op.id}-evidence`}
            />
          </div>
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
              <span>{formatPlatformTime(r.ts)}</span>
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

  // TRACK 25 · SPRINT 2 · Trust Layer state — separate from the
  // operations registry above so a slow child probe never blocks the
  // maintenance console from rendering.
  const [trustSnapshot, setTrustSnapshot] = useState(null);
  const [trustLoading, setTrustLoading] = useState(true);
  const [trustError, setTrustError] = useState(null);
  const [trustFetchedAt, setTrustFetchedAt] = useState(null);

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

  const reloadTrust = useCallback(async () => {
    setTrustLoading(true);
    try {
      const snap = await fetchTrustLayer();
      setTrustSnapshot(snap);
      // Internal UTC stamp fed into `formatPlatformTime` for the UI —
      // never displayed as a raw ISO to any operator.
      setTrustFetchedAt(new Date().toISOString()); // TRACK-27.03-EXEMPT: machine timestamp, always rendered via formatPlatformTime.
      setTrustError(null);
    } catch (e) {
      setTrustError(
        e?.response?.status === 401 || e?.response?.status === 403
          ? "Super-admin access required."
          : e?.message || String(e),
      );
    } finally {
      setTrustLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
    reloadTrust();
  }, [reload, reloadTrust]);

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
      <PortalShell
        portalName="MASCI"
        portalRole="Admin"
        pageTitle="Operations Control Center"
        subtitle="Trust Center + maintenance console — one canonical operations home."
        primaryActions={
          <div className="flex items-center gap-2">
            <Link
              to="/admin"
              className="inline-flex items-center gap-2 px-3 py-1.5 border border-slate-300 bg-white rounded-md text-xs font-semibold text-slate-800 hover:bg-slate-100"
              data-testid="occ-back-adminos"
            >
              ← Admin OS
            </Link>
          </div>
        }
        sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
      >
        <AdminBreadcrumb
          crumbs={[{ label: "Operations Control Center" }]}
          testidPrefix="occ-breadcrumb"
        />

        {/* TRACK 25 · SPRINT 2 · Trust Layer — read-only 8 sections. */}
        <TrustLayer
          snapshot={trustSnapshot}
          loading={trustLoading}
          error={trustError}
          onRefresh={reloadTrust}
          lastFetchedAt={trustFetchedAt}
        />

        {/* Divider between Trust Layer (read-only) and Maintenance Console (mutating). */}
        <div
          className="mb-6 flex items-center gap-2"
          data-testid="occ-console-divider"
        >
          <div className="h-px flex-1 bg-slate-300" />
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-mono font-bold">
            Maintenance Operations Console · dry-run / apply
          </div>
          <div className="h-px flex-1 bg-slate-300" />
        </div>

        <div className="mb-4 flex items-center justify-between">
          <p className="text-xs text-slate-600 max-w-2xl">
            Every operation below is dry-run first. Applies require the exact
            repair contract and are recorded in the immutable audit log.
          </p>
          <button
            type="button"
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100"
            onClick={reload}
            data-testid="occ-refresh-all"
          >
            {loading ? "Refreshing…" : "Refresh operations"}
          </button>
        </div>

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
      </PortalShell>
    </div>
  );
}
