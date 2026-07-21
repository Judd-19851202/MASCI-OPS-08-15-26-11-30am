// TRACK 25 · SPRINT 3 · Shared trust primitives.
//
// Extracted from `pages/OperationsControlCenter.jsx` so every Admin OS
// domain landing that renders a status card (Storage & Recovery,
// eventually AI Ops, Communications, etc.) reuses the exact same
// visual language: same status pills, same card shape, same evidence
// drawer, same attention-first sort. No new "one-off" component per
// domain — the platform is one product, not a collage.
//
// Contracts (stable across all domains):
//   status  ∈ { "green", "yellow", "red", "unknown" }
//   card    = {
//     id, title, summary, endpoint, drilldown, evidence,
//     recommended_action, checked_at, status,
//   }
//
// Zero-UTC: `checked_at` is fed to `formatPlatformTime` /
// `formatRelativeTime` — never rendered as a raw ISO to operators.

import React, { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, ExternalLink } from "lucide-react";

import { formatPlatformTime, formatRelativeTime } from "@/lib/platformTime";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";

function labelizeKey(key) {
  return String(key || "")
    .replace(/[_-]+/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^./, (c) => c.toUpperCase());
}

function isPlainObject(value) {
  return Object.prototype.toString.call(value) === "[object Object]";
}

function scalarText(value) {
  if (value == null || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function flattenEvidence(value, prefix = "", depth = 0, rows = [], limit = 18) {
  if (rows.length >= limit) return rows;

  if (value == null || value === "") {
    rows.push({ label: prefix || "Value", value: "—" });
    return rows;
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    rows.push({ label: prefix || "Value", value: scalarText(value) });
    return rows;
  }

  if (Array.isArray(value)) {
    if (!value.length) {
      rows.push({ label: prefix || "Items", value: "None recorded." });
      return rows;
    }
    value.slice(0, 5).forEach((item, index) => {
      if (rows.length >= limit) return;
      if (isPlainObject(item) || Array.isArray(item)) {
        flattenEvidence(item, `${prefix || "Item"} ${index + 1}`, depth + 1, rows, limit);
      } else {
        rows.push({
          label: `${prefix || "Item"} ${index + 1}`,
          value: scalarText(item),
        });
      }
    });
    if (value.length > 5 && rows.length < limit) {
      rows.push({ label: prefix || "Items", value: `+${value.length - 5} more item(s)` });
    }
    return rows;
  }

  if (isPlainObject(value)) {
    Object.entries(value)
      .filter(([, item]) => item !== undefined)
      .slice(0, 8)
      .forEach(([key, item]) => {
        if (rows.length >= limit) return;
        const nextLabel = prefix ? `${prefix} • ${labelizeKey(key)}` : labelizeKey(key);
        if (isPlainObject(item) || Array.isArray(item)) {
          flattenEvidence(item, nextLabel, depth + 1, rows, limit);
        } else {
          rows.push({ label: nextLabel, value: scalarText(item) });
        }
      });
    return rows;
  }

  rows.push({ label: prefix || "Value", value: String(value) });
  return rows;
}

export function EvidenceSummary({ value, testidPrefix = "evidence-summary" }) {
  const rows = flattenEvidence(value);
  return (
    <div className="space-y-2" data-testid={testidPrefix}>
      {rows.length ? (
        <dl className="grid gap-2">
          {rows.map((row, index) => (
            <div
              key={`${testidPrefix}-${index}`}
              className="rounded-md border border-slate-200 bg-white p-2"
              data-testid={`${testidPrefix}-row-${index}`}
            >
              <dt className="mb-1 text-[10px] font-mono uppercase tracking-widest text-slate-500">
                {row.label}
              </dt>
              <dd className="text-xs text-slate-800 break-words">{row.value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <div className="text-xs text-slate-500" data-testid={`${testidPrefix}-empty`}>
          No structured evidence captured.
        </div>
      )}
    </div>
  );
}

// ── Canonical status palette ────────────────────────────────────
export const TRUST_STATUS_STYLES = {
  green: {
    bg: "bg-emerald-100",
    text: "text-emerald-800",
    ring: "ring-emerald-200",
    stripe: "#059669",
    label: "HEALTHY",
  },
  yellow: {
    bg: "bg-amber-100",
    text: "text-amber-900",
    ring: "ring-amber-200",
    stripe: "#d97706",
    label: "ATTENTION",
  },
  red: {
    bg: "bg-rose-100",
    text: "text-rose-900",
    ring: "ring-rose-200",
    stripe: "#e11d48",
    label: "CRITICAL",
  },
  unknown: {
    bg: "bg-slate-200",
    text: "text-slate-700",
    ring: "ring-slate-300",
    stripe: "#64748b",
    label: "UNKNOWN",
  },
};

// Worst-case aggregate — used by the Executive Verdict on every
// domain landing to compute the domain's overall pill.
const _ORDER = { red: 3, yellow: 2, unknown: 1, green: 0 };
export function worstStatus(cards) {
  let worst = "green";
  for (const c of cards || []) {
    const s = c?.status || "green";
    if ((_ORDER[s] ?? 0) > (_ORDER[worst] ?? 0)) worst = s;
  }
  return worst;
}

// Attention-first sort — every list of cards is ordered
// red → yellow → unknown → green.
export function sortCardsByAttention(cards) {
  return [...(cards || [])].sort(
    (a, b) =>
      (_ORDER_ASC[a?.status] ?? 4) - (_ORDER_ASC[b?.status] ?? 4),
  );
}
const _ORDER_ASC = { red: 0, yellow: 1, unknown: 2, green: 3 };

// ── Status pill ────────────────────────────────────────────────
export function TrustStatusPill({ status, testid }) {
  const s = TRUST_STATUS_STYLES[status] || TRUST_STATUS_STYLES.unknown;
  return (
    <span
      data-testid={testid}
      className={`inline-flex items-center rounded px-2 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-widest ${s.bg} ${s.text} ring-1 ${s.ring}`}
    >
      {s.label}
    </span>
  );
}

// ── HealthCard ─────────────────────────────────────────────────
// Read-only status tile. Clicking opens the evidence drawer. Actions
// are NEVER wired inline — they live only in the OCC maintenance
// console (single source of action truth).
export function HealthCard({ card, onOpen, testidPrefix = "trust-card" }) {
  const style = TRUST_STATUS_STYLES[card.status] || TRUST_STATUS_STYLES.unknown;
  return (
    <button
      type="button"
      onClick={() => onOpen(card)}
      data-testid={`${testidPrefix}-${card.id}`}
      className="group relative flex w-full flex-col rounded-lg border border-slate-200 bg-white text-left shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-150 overflow-hidden"
    >
      <span
        aria-hidden="true"
        className="absolute left-0 top-0 bottom-0 w-1"
        style={{ backgroundColor: style.stripe }}
      />
      <div className="p-4 pl-5 flex flex-col gap-2 min-h-[128px]">
        <div className="flex items-start justify-between gap-2">
          <h4
            className="font-display text-sm font-black tracking-tight text-slate-900 leading-tight"
            data-testid={`${testidPrefix}-${card.id}-title`}
          >
            {card.title}
          </h4>
          <TrustStatusPill
            status={card.status}
            testid={`${testidPrefix}-${card.id}-status`}
          />
        </div>
        <p
          className="text-[12px] text-slate-700 leading-snug"
          data-testid={`${testidPrefix}-${card.id}-summary`}
        >
          {card.summary || "No summary."}
        </p>
        {card.recommended_action ? (
          <p
            className="text-[11px] text-slate-500 leading-snug"
            data-testid={`${testidPrefix}-${card.id}-action`}
          >
            <span className="font-semibold text-slate-600">Action: </span>
            {card.recommended_action}
          </p>
        ) : null}
        <div className="mt-auto flex items-center justify-between pt-2 border-t border-slate-100 gap-2">
          <div className="min-w-0 flex-1">
            <div
              className="text-[10px] font-mono text-slate-500 truncate"
              title={card.endpoint || ""}
              data-testid={`${testidPrefix}-${card.id}-endpoint`}
            >
              {card.endpoint || "—"}
            </div>
            {card.checked_at ? (
              <div
                className="text-[10px] font-mono text-slate-400"
                title="Last checked (your local time)"
                data-testid={`${testidPrefix}-${card.id}-stamp`}
              >
                {formatRelativeTime(card.checked_at)}
              </div>
            ) : null}
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-700 group-hover:translate-x-0.5 transition-all shrink-0" />
        </div>
      </div>
    </button>
  );
}

// ── EvidenceDrawer ─────────────────────────────────────────────
export function EvidenceDrawer({ card, open, onOpenChange, testidPrefix = "trust-evidence-drawer" }) {
  if (!card) return null;
  const style = TRUST_STATUS_STYLES[card.status] || TRUST_STATUS_STYLES.unknown;
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-lg overflow-y-auto"
        data-testid={testidPrefix}
      >
        <SheetHeader>
          <div className="flex items-start justify-between gap-2 pr-6">
            <SheetTitle
              className="text-slate-900 pr-4"
              data-testid={`${testidPrefix}-title`}
            >
              {card.title}
            </SheetTitle>
            <TrustStatusPill
              status={card.status}
              testid={`${testidPrefix}-status`}
            />
          </div>
          <SheetDescription className="text-slate-600 text-xs">
            {card.summary}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-5 space-y-4 text-sm">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
              Source endpoint
            </div>
            <div
              className="font-mono text-xs bg-slate-50 border border-slate-200 rounded px-2 py-1.5 break-all"
              data-testid={`${testidPrefix}-endpoint`}
            >
              {card.endpoint || "—"}
            </div>
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
              Last checked
            </div>
            <div
              className="text-xs text-slate-800"
              data-testid={`${testidPrefix}-checked-at`}
            >
              {card.checked_at ? formatPlatformTime(card.checked_at) : "—"}
            </div>
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
              Why this status
            </div>
            <div
              className={`text-xs rounded px-2 py-1.5 border ${style.bg} ${style.text} ring-1 ${style.ring}`}
              data-testid={`${testidPrefix}-reason`}
            >
              {card.summary}
            </div>
          </div>

          {card.recommended_action ? (
            <div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
                Recommended action
              </div>
              <div
                className="text-xs text-slate-800 bg-amber-50 border border-amber-200 rounded px-2 py-1.5"
                data-testid={`${testidPrefix}-action`}
              >
                {card.recommended_action}
              </div>
            </div>
          ) : null}

          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
              Evidence observed
            </div>
            <div className="rounded-md border border-slate-200 bg-slate-50 p-2">
              <EvidenceSummary
                value={card.evidence || {}}
                testidPrefix={`${testidPrefix}-payload`}
              />
            </div>
          </div>

          {card.drilldown ? (
            <Link
              to={card.drilldown}
              className="inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800"
              data-testid={`${testidPrefix}-drilldown`}
              onClick={() => onOpenChange(false)}
            >
              Open {card.drilldown}
              <ExternalLink className="w-3 h-3" />
            </Link>
          ) : null}
        </div>
      </SheetContent>
    </Sheet>
  );
}

// ── Optional hook for drawer state ─────────────────────────────
// Simple helper so each domain page uses the same open/close pattern.
export function useEvidenceDrawer() {
  const [card, setCard] = useState(null);
  const [open, setOpen] = useState(false);
  const openWith = useCallback((c) => {
    setCard(c);
    setOpen(true);
  }, []);
  return { card, open, setOpen, openWith };
}

// Utility — group of cards -> executive verdict summary object.
export function executiveVerdict(cards) {
  const counts = { green: 0, yellow: 0, red: 0, unknown: 0 };
  for (const c of cards) counts[c.status] = (counts[c.status] || 0) + 1;
  const overall = worstStatus(cards);
  const highest = sortCardsByAttention(cards).find((c) => c.status !== "green") || null;
  return { counts, overall, highest };
}

// ── Re-export the raw palette for pages that need custom labels ─
export const TRUST_STATUS_LABELS = Object.fromEntries(
  Object.entries(TRUST_STATUS_STYLES).map(([k, v]) => [k, v.label]),
);

// Kept explicit for consumers using the module version.
export const __TRUST_PRIMITIVES_VERSION__ = 1;
