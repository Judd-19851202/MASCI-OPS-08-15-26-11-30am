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
import { useT } from "@/lib/i18n";
import { sanitizeOperatorReference } from "@/lib/operatorLanguage";

const TRUST_TEXT_EXACT_ES = {
  HEALTHY: "SALUDABLE",
  ATTENTION: "ATENCIÓN",
  CRITICAL: "CRÍTICO",
  UNKNOWN: "DESCONOCIDO",
  "Evidence source": "Fuente de evidencia",
  "Evidence timestamp": "Marca de tiempo de la evidencia",
  "Last successful refresh": "Última actualización exitosa",
  "Last verified": "Última verificación",
  "Produced by": "Generado por",
  "Why this status": "Por qué este estado",
  "Why this number?": "¿Por qué este número?",
  "Affected assets": "Activos afectados",
  "Recommended action": "Acción recomendada",
  "Evidence observed": "Evidencia observada",
  "Open": "Abrir",
  "No structured evidence captured.": "No se capturó evidencia estructurada.",
  "Truth ownership": "Propiedad de la verdad",
  "Conflict state": "Estado del conflicto",
  "Upstream owners": "Responsables ascendentes",
  "This surface is the source owner.": "Esta superficie es la fuente responsable.",
  "No contradiction detected for this surface.": "No se detectó ninguna contradicción para esta superficie.",
  "Owner endpoint:": "Endpoint responsable:",
  "Owner module:": "Módulo responsable:",
  "Canonical owner:": "Responsable canónico:",
  "Evidence age:": "Antigüedad de la evidencia:",
  "Why:": "Por qué:",
  "Action:": "Acción:",
  Evidence: "Evidencia",
  Refreshed: "Actualizado",
};

const TRUST_TEXT_REPLACEMENTS_ES = [
  [/Business definition/g, "Definición operativa"],
  [/Source of truth/g, "Fuente de verdad"],
  [/Calculation/g, "Cálculo"],
  [/Refresh cadence/g, "Frecuencia de actualización"],
  [/Last refresh/g, "Última actualización"],
  [/Data age/g, "Antigüedad de los datos"],
  [/Confidence/g, "Confianza"],
  [/Thresholds/g, "Umbrales"],
  [/Status explanation/g, "Explicación del estado"],
  [/Drill-down target/g, "Destino del detalle"],
  [/Owning subsystem/g, "Subsistema responsable"],
  [/No structured evidence captured\./g, "No se capturó evidencia estructurada."],
  [/Truth ownership/g, "Propiedad de la verdad"],
  [/Canonical /g, "Canónico "] ,
  [/Displayed /g, "Mostrado "] ,
  [/Structured truth contract\./g, "Contrato estructurado de verdad."],
  [/Owner endpoint:/g, "Endpoint responsable:"],
  [/Owner module:/g, "Módulo responsable:"],
  [/Canonical owner:/g, "Responsable canónico:"],
  [/Evidence age:/g, "Antigüedad de la evidencia:"],
  [/Upstream owners/g, "Responsables ascendentes"],
  [/This surface is the source owner\./g, "Esta superficie es la fuente responsable."],
  [/Conflict state/g, "Estado del conflicto"],
  [/No contradiction detected for this surface\./g, "No se detectó ninguna contradicción para esta superficie."],
  [/No summary\./g, "Sin resumen."],
  [/Why: /g, "Por qué: "],
  [/Action: /g, "Acción: "],
  [/Evidence /g, "Evidencia "],
  [/Refreshed /g, "Actualizado "],
  [/Evidence source/g, "Fuente de evidencia"],
  [/Evidence timestamp/g, "Marca de tiempo de la evidencia"],
  [/Last successful refresh/g, "Última actualización exitosa"],
  [/Last verified/g, "Última verificación"],
  [/Produced by/g, "Generado por"],
  [/Why this status/g, "Por qué este estado"],
  [/Why this number\?/g, "¿Por qué este número?"],
  [/Affected assets/g, "Activos afectados"],
  [/Recommended action/g, "Acción recomendada"],
  [/Evidence observed/g, "Evidencia observada"],
  [/Open /g, "Abrir "],
  [/Value/g, "Valor"],
  [/Items/g, "Elementos"],
  [/Item/g, "Elemento"],
  [/None recorded\./g, "Nada registrado."],
  [/more item\(s\)/g, "elemento(s) más"],
  [/Yes/g, "Sí"],
  [/No/g, "No"],
  [/routes configured/g, "rutas configuradas"],
  [/critical empty/g, "vacías críticas"],
  [/integrations configured/g, "integraciones configuradas"],
  [/missing config/g, "configuración faltante"],
  [/notification sections configured/g, "secciones de notificaciones configuradas"],
  [/for role/g, "para el rol"],
  [/operation\(s\)/g, "operación(es)"],
  [/critical ·/g, "críticas ·"],
  [/attention/g, "atención"],
  [/healthy/g, "saludables"],
  [/failed/g, "fallidas"],
];

function localizeTrustText(value, t, lang) {
  if (typeof value !== "string") return value;
  const translated = t(value);
  if (lang !== "es" || translated !== value) return translated;
  if (TRUST_TEXT_EXACT_ES[value]) return TRUST_TEXT_EXACT_ES[value];
  return TRUST_TEXT_REPLACEMENTS_ES.reduce(
    (result, [pattern, replacement]) => result.replace(pattern, replacement),
    value,
  );
}

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

function renderMetadataRows(meta) {
  if (!meta) return [];
  const formula = meta.formula || {};
  return [
    ["Business definition", meta.business_definition],
    ["Source of truth", meta.source_of_truth],
    ["Calculation", formula],
    ["Refresh cadence", meta.refresh_cadence],
    ["Last refresh", meta.last_refresh],
    ["Data age", meta.data_age],
    ["Confidence", meta.confidence],
    ["Thresholds", meta.thresholds],
    ["Status explanation", meta.status_reason],
    ["Drill-down target", meta.drilldown_source],
    ["Owning subsystem", meta.owner],
  ].filter(([, value]) => value !== undefined && value !== null && value !== "");
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
  const { t, lang } = useT();
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
                {localizeTrustText(row.label, t, lang)}
              </dt>
              <dd className="text-xs text-slate-800 break-words">{localizeTrustText(row.value, t, lang)}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <div className="text-xs text-slate-500" data-testid={`${testidPrefix}-empty`}>
          {t("No structured evidence captured.")}
        </div>
      )}
    </div>
  );
}

export function TruthOwnerPanel({
  title = "Truth ownership",
  surface,
  relationship,
  checkedAt,
  testidPrefix = "truth-owner-panel",
}) {
  const { t, lang } = useT();
  if (!surface) return null;
  const role = relationship?.role || surface.role || "UNREGISTERED";
  const canonicalStatus = relationship?.canonical_status || "UNVERIFIABLE";
  const derivedStatus = relationship?.derived_status || canonicalStatus;
  const conflicts = relationship?.conflicts || [];
  const primaryOwner = String(relationship?.canonical_owner_id || surface.canonical_owner_id || surface.surface_id || "")
    .replace(/runtime state authority/gi, "current state authority")
    .replace(/runtime_state_authority/gi, "current_state_authority");
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3" data-testid={testidPrefix}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">{localizeTrustText(title, t, lang)}</span>
        <span className="inline-flex rounded-full bg-slate-100 px-2 py-1 text-[10px] font-mono uppercase tracking-widest text-slate-700" data-testid={`${testidPrefix}-role`}>{sanitizeOperatorReference(role, "Owner")}</span>
        <span className="inline-flex rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-mono uppercase tracking-widest text-emerald-700" data-testid={`${testidPrefix}-canonical-status`}>{sanitizeOperatorReference(localizeTrustText(`Primary ${canonicalStatus}`, t, lang), `Primary ${canonicalStatus}`)}</span>
        <span className="inline-flex rounded-full bg-amber-50 px-2 py-1 text-[10px] font-mono uppercase tracking-widest text-amber-700" data-testid={`${testidPrefix}-derived-status`}>{sanitizeOperatorReference(localizeTrustText(`Shown ${derivedStatus}`, t, lang), `Shown ${derivedStatus}`)}</span>
      </div>
      <p className="text-sm text-slate-800" data-testid={`${testidPrefix}-summary`}>{sanitizeOperatorReference(localizeTrustText(relationship?.derivation_explanation || surface.surface_name || "Structured truth contract.", t, lang), "This summary reflects the current source relationship.")}</p>
      <div className="grid gap-2 md:grid-cols-2 text-xs text-slate-600">
        <div data-testid={`${testidPrefix}-owner-endpoint`}><span className="font-semibold text-slate-800">{t("Owner endpoint:")}</span> {sanitizeOperatorReference(surface.owner_endpoint, "Linked service")}</div>
        <div data-testid={`${testidPrefix}-owner-module`}><span className="font-semibold text-slate-800">{t("Owner module:")}</span> {sanitizeOperatorReference(surface.owner_module, "Platform service")}</div>
        <div data-testid={`${testidPrefix}-canonical-owner`}><span className="font-semibold text-slate-800">Primary owner:</span> {sanitizeOperatorReference(primaryOwner, "Primary source")}</div>
        <div data-testid={`${testidPrefix}-evidence-age`}><span className="font-semibold text-slate-800">{t("Evidence age:")}</span> {checkedAt || relationship?.evidence_age_source || "—"}</div>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid={`${testidPrefix}-upstream`}>
          <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-2">{t("Upstream owners")}</div>
          {surface.upstream_owner_ids?.length ? (
            <ul className="space-y-1 text-xs text-slate-700">
              {surface.upstream_owner_ids.map((id) => <li key={id}>{sanitizeOperatorReference(id, "Upstream source")}</li>)}
            </ul>
          ) : <div className="text-xs text-slate-500">{t("This surface is the source owner.")}</div>}
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid={`${testidPrefix}-conflicts`}>
          <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-2">{t("Conflict state")}</div>
          {conflicts.length ? (
            <ul className="space-y-1 text-xs text-rose-700">
              {conflicts.map((conflict, index) => <li key={`${testidPrefix}-conflict-${index}`}>{sanitizeOperatorReference(localizeTrustText(conflict, t, lang), "Review this conflict before continuing.")}</li>)}
            </ul>
          ) : <div className="text-xs text-emerald-700">{t("No contradiction detected for this surface.")}</div>}
        </div>
      </div>
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
  const { t } = useT();
  const s = TRUST_STATUS_STYLES[status] || TRUST_STATUS_STYLES.unknown;
  return (
    <span
      data-testid={testid}
      className={`inline-flex items-center rounded px-2 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-widest ${s.bg} ${s.text} ring-1 ${s.ring}`}
    >
      {t(s.label)}
    </span>
  );
}

// ── HealthCard ─────────────────────────────────────────────────
// Read-only status tile. Clicking opens the evidence drawer. Actions
// are NEVER wired inline — they live only in the OCC maintenance
// console (single source of action truth).
export function HealthCard({ card, onOpen, testidPrefix = "trust-card" }) {
  const { t, lang } = useT();
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
            {localizeTrustText(card.title, t, lang)}
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
          {localizeTrustText(card.summary || "No summary.", t, lang)}
        </p>
        {card.root_cause_explanation && card.root_cause_explanation !== card.summary ? (
          <p
            className="text-[11px] text-slate-500 leading-snug"
            data-testid={`${testidPrefix}-${card.id}-root-cause`}
          >
            <span className="font-semibold text-slate-600">{t("Why:")}</span>{" "}
            {localizeTrustText(card.root_cause_explanation, t, lang)}
          </p>
        ) : null}
        {card.recommended_action ? (
          <p
            className="text-[11px] text-slate-500 leading-snug"
            data-testid={`${testidPrefix}-${card.id}-action`}
          >
            <span className="font-semibold text-slate-600">{t("Action:")}</span>{" "}
            {localizeTrustText(card.recommended_action, t, lang)}
          </p>
        ) : null}
        <div className="mt-auto flex items-center justify-between pt-2 border-t border-slate-100 gap-2">
          <div className="min-w-0 flex-1">
            <div
              className="text-[10px] font-mono text-slate-500 truncate"
              title={card.evidence_source_label || card.endpoint || ""}
              data-testid={`${testidPrefix}-${card.id}-endpoint`}
            >
              {localizeTrustText(card.evidence_source_label || card.endpoint || "—", t, lang)}
            </div>
            {card.checked_at ? (
              <div
                className="text-[10px] font-mono text-slate-400"
                title="Last checked (your local time)"
                data-testid={`${testidPrefix}-${card.id}-stamp`}
              >
                {t("Evidence")} {formatRelativeTime(card.checked_at)}
              </div>
            ) : null}
            {card.last_successful_refresh ? (
              <div
                className="text-[10px] font-mono text-slate-400"
                title="Last successful refresh"
                data-testid={`${testidPrefix}-${card.id}-refresh`}
              >
                {t("Refreshed")} {formatRelativeTime(card.last_successful_refresh)}
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
  const { t, lang } = useT();
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
              {localizeTrustText(card.title, t, lang)}
            </SheetTitle>
            <TrustStatusPill
              status={card.status}
              testid={`${testidPrefix}-status`}
            />
          </div>
          <SheetDescription className="text-slate-600 text-xs">
            {localizeTrustText(card.summary, t, lang)}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-5 space-y-4 text-sm">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
              {t("Evidence source")}
            </div>
            <div
              className="font-mono text-xs bg-slate-50 border border-slate-200 rounded px-2 py-1.5 break-all"
              data-testid={`${testidPrefix}-endpoint`}
            >
              {localizeTrustText(card.evidence_source_label || card.endpoint || "—", t, lang)}
            </div>
            {card.endpoint && card.evidence_source_label && card.evidence_source_label !== card.endpoint ? (
              <div className="mt-2 text-xs text-slate-500 break-all" data-testid={`${testidPrefix}-endpoint-raw`}>
                {card.endpoint}
              </div>
            ) : null}
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
              {t("Evidence timestamp")}
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
              {t("Last successful refresh")}
            </div>
            <div className="text-xs text-slate-800" data-testid={`${testidPrefix}-last-refresh`}>
              {card.last_successful_refresh ? formatPlatformTime(card.last_successful_refresh) : "—"}
            </div>
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
              {t("Last verified")}
            </div>
            <div className="text-xs text-slate-800" data-testid={`${testidPrefix}-verified-at`}>
              {card.verified_at ? formatPlatformTime(card.verified_at) : (card.checked_at ? formatPlatformTime(card.checked_at) : "—")}
            </div>
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
              {t("Produced by")}
            </div>
            <div className="text-xs text-slate-800 break-words" data-testid={`${testidPrefix}-producer`}>
              {localizeTrustText(card.producer || "—", t, lang)}
            </div>
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
              {t("Why this status")}
            </div>
            <div
              className={`text-xs rounded px-2 py-1.5 border ${style.bg} ${style.text} ring-1 ${style.ring}`}
              data-testid={`${testidPrefix}-reason`}
            >
              {localizeTrustText(card.root_cause_explanation || card.summary, t, lang)}
            </div>
          </div>

          {card.kpi_metadata ? (
            <div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
                {t("Why this number?")}
              </div>
              <dl className="grid gap-2" data-testid={`${testidPrefix}-kpi-metadata`}>
                {renderMetadataRows(card.kpi_metadata).map(([label, value], index) => (
                  <div key={`${testidPrefix}-kpi-${index}`} className="rounded-md border border-slate-200 bg-slate-50 p-2">
                    <dt className="mb-1 text-[10px] font-mono uppercase tracking-widest text-slate-500">{t(label)}</dt>
                    <dd className="text-xs text-slate-800 break-words">
                      {isPlainObject(value) || Array.isArray(value) ? (
                        <EvidenceSummary value={value} testidPrefix={`${testidPrefix}-kpi-${index}-value`} />
                      ) : localizeTrustText(scalarText(value), t, lang)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          ) : null}

          {card.affected_assets ? (
            <div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
                {t("Affected assets")}
              </div>
              <div className="rounded-md border border-slate-200 bg-slate-50 p-2">
                <EvidenceSummary value={card.affected_assets} testidPrefix={`${testidPrefix}-affected-assets`} />
              </div>
            </div>
          ) : null}

          {card.recommended_action ? (
            <div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
                {t("Recommended action")}
              </div>
              <div
                className="text-xs text-slate-800 bg-amber-50 border border-amber-200 rounded px-2 py-1.5"
                data-testid={`${testidPrefix}-action`}
              >
                {localizeTrustText(card.recommended_action, t, lang)}
              </div>
            </div>
          ) : null}

          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500 font-bold mb-1">
              {t("Evidence observed")}
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
              {t("Open")} {card.drilldown}
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
