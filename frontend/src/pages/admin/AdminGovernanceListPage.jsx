import React, { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowRight, Clock3, ShieldCheck, ShieldQuestion, TriangleAlert } from "lucide-react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { formatPlatformTime } from "@/lib/platformTime";
import { usePageTitle } from "@/lib/usePageTitle";
import { operationalError } from "@/lib/errors";
import { useT } from "@/lib/i18n";

const GOVERNANCE_TEXT_ES = {
  "Governance reference page": "Página de referencia de gobernanza",
  "Every card below is translated into operator language so reviewers can understand the record without reading raw payloads, enum values, or internal IDs.": "Cada tarjeta de abajo se traduce al lenguaje operativo para que los revisores entiendan el registro sin leer cargas sin procesar, valores enum o identificadores internos.",
  "Visible items": "Elementos visibles",
  "Last update": "Última actualización",
  "No timestamp reported": "No se reportó ninguna marca de tiempo",
  "Read-only evidence view": "Vista de evidencia de solo lectura",
  "Internal identifiers hidden from the primary UI": "Identificadores internos ocultos de la interfaz principal",
  "No governance records are currently available for this page. When the source collection is populated, this page will summarize each item in plain English here.": "Actualmente no hay registros de gobernanza disponibles para esta página. Cuando se complete la colección de origen, esta página resumirá cada elemento aquí en lenguaje operativo.",
  "Organization Structure": "Estructura organizativa",
  "Governed organization hierarchy.": "Jerarquía organizativa gobernada.",
  "Identity Projections": "Proyecciones de identidad",
  "Policy-ready identity context derived from canonical auth owners.": "Contexto de identidad listo para políticas derivado de responsables canónicos de autenticación.",
  "Roles": "Roles",
  "Configurable enterprise roles.": "Roles empresariales configurables.",
  "Permissions": "Permisos",
  "Registry-controlled permissions.": "Permisos controlados por registro.",
  "Policies": "Políticas",
  "Versioned governance policies.": "Políticas de gobernanza versionadas.",
  "Approval Flows": "Flujos de aprobación",
  "Reusable approval definitions and requests.": "Definiciones y solicitudes de aprobación reutilizables.",
  "Delegations": "Delegaciones",
  "Temporary and auditable delegated authority.": "Autoridad delegada temporal y auditable.",
  "Separation of Duties": "Separación de funciones",
  "Conflict-prevention governance rules.": "Reglas de gobernanza para prevenir conflictos.",
  "Authority Levels": "Niveles de autoridad",
  "Authority hierarchy for policy enforcement.": "Jerarquía de autoridad para aplicar políticas.",
  "Emergency Overrides": "Anulaciones de emergencia",
  "Preview-safe, fully auditable override records.": "Registros de anulación seguros para vista previa y totalmente auditables.",
  "Governance Decisions": "Decisiones de gobernanza",
  "Allow / deny / approval outcomes.": "Resultados de permitir / negar / aprobar.",
  "Governance Audit": "Auditoría de gobernanza",
  "Governance audit history.": "Historial de auditoría de gobernanza.",
  "Governance Versions": "Versiones de gobernanza",
  "Registry and baseline version references.": "Referencias de registro y versiones base.",
  "Enterprise governance health summary.": "Resumen de salud de la gobernanza empresarial.",
};

const HIDDEN_KEYS = new Set([
  "id",
  "canonical_user_id",
  "delegation_id",
  "override_id",
  "decision_id",
  "resource_snapshot",
  "policy_snapshot",
  "delegator_snapshot",
  "identity_snapshot",
  "policy_evaluation",
  "effective_permissions",
  "direct_permissions",
  "delegated_permissions",
  "temporary_authority",
  "governance_restrictions",
  "project_numbers",
  "crew_ids",
  "team_ids",
  "reports_to_user_id",
  "employee_id",
]);

function humanizeToken(value) {
  return String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function looksLikeIsoDate(value) {
  return typeof value === "string" && /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value);
}

function looksLikeUuid(value) {
  return typeof value === "string" && /^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(value);
}

function formatValue(key, value) {
  if (value === null || value === undefined || value === "") {
    return "Not recorded";
  }

  if (looksLikeIsoDate(value)) {
    return formatPlatformTime(value);
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      if (key.includes("permission")) return "No permissions listed";
      if (key.includes("role")) return "No roles listed";
      if (key.includes("portal")) return "No portal access listed";
      return "None recorded";
    }
    if (key === "path") {
      return value.join(" → ");
    }
    const preview = value
      .slice(0, 4)
      .map((entry) => (typeof entry === "string" ? humanizeToken(entry) : String(entry)))
      .join(" · ");
    return value.length > 4 ? `${preview} · +${value.length - 4} more` : preview;
  }

  if (typeof value === "object") {
    const entries = Object.entries(value).filter(([, nested]) => nested !== undefined && nested !== "");
    if (!entries.length) return "No structured details";
    return entries
      .slice(0, 3)
      .map(([nestedKey, nestedValue]) => `${humanizeToken(nestedKey)}: ${formatValue(nestedKey, nestedValue)}`)
      .join(" · ");
  }

  if (looksLikeUuid(value)) {
    return "Stored internally";
  }

  if (key.includes("status") || key.includes("decision") || key.includes("action") || key.includes("kind")) {
    return humanizeToken(value);
  }

  return String(value);
}

function inferTitle(item, index) {
  return (
    item.label ||
    item.display_name ||
    item.name ||
    item.email ||
    item.policy_id ||
    item.action_key ||
    item.project_number ||
    item.resource_type ||
    `Governance item ${index + 1}`
  );
}

function inferEyebrow(item) {
  return (
    item.kind ||
    item.identity_source ||
    item.delegation_type ||
    item.domain ||
    item.resource_type ||
    item.actor_kind ||
    item.module_key ||
    item.status ||
    "governance record"
  );
}

function inferSummary(item) {
  if (item.label && Array.isArray(item.permissions)) {
    return `${item.permissions.length} permissions across ${item.portal_hints?.length || 0} portal lanes.`;
  }
  if (item.domain && item.action) {
    return `Allows ${humanizeToken(item.action)} actions inside ${humanizeToken(item.domain)}.`;
  }
  if (item.action_key && Array.isArray(item.required_permissions)) {
    return `${item.required_permissions.length} required permission${item.required_permissions.length === 1 ? "" : "s"}${item.require_approval_flow ? " with a review flow" : ""}.`;
  }
  if (Array.isArray(item.required_roles) && item.min_approvals != null) {
    return `${item.min_approvals} approval${Number(item.min_approvals) === 1 ? "" : "s"} from ${item.required_roles.length} role lane${item.required_roles.length === 1 ? "" : "s"}.`;
  }
  if (item.delegator_email && item.delegate_email) {
    return `${item.delegate_email} is covering selected responsibilities for ${item.delegator_email}.`;
  }
  if (item.requesting_identity?.email && item.requested_capability) {
    return `${item.requesting_identity.email} requested temporary access to ${humanizeToken(item.requested_capability)}.`;
  }
  if (item.actor_email && item.action_key) {
    return `${item.actor_email} was evaluated for ${humanizeToken(item.action_key)}.`;
  }
  if (Array.isArray(item.path) && item.path.length) {
    return `This node sits ${item.path.length} level${item.path.length === 1 ? "" : "s"} deep in the operating structure.`;
  }
  if (Array.isArray(item.active_roles) && item.display_name) {
    return `${item.active_roles.length} active role${item.active_roles.length === 1 ? "" : "s"} across ${item.portals?.length || 0} portal lane${item.portals?.length === 1 ? "" : "s"}.`;
  }
  return "Structured governance record ready for operator review.";
}

function localizeGovernanceText(value, t, lang) {
  if (typeof value !== "string") return value;
  const translated = t(value);
  if (lang !== "es" || translated !== value) return translated;
  if (GOVERNANCE_TEXT_ES[value]) return GOVERNANCE_TEXT_ES[value];
  return value
    .replace(/permissions across/g, "permisos en")
    .replace(/portal lanes/g, "portales")
    .replace(/portal lane/g, "portal")
    .replace(/required permission/g, "permiso requerido")
    .replace(/required permissions/g, "permisos requeridos")
    .replace(/approval flow/g, "flujo de aprobación")
    .replace(/approval/g, "aprobación")
    .replace(/approvals/g, "aprobaciones")
    .replace(/role lanes/g, "canales de rol")
    .replace(/role lane/g, "canal de rol")
    .replace(/Temporary and auditable delegated authority\./g, "Autoridad delegada temporal y auditable.")
    .replace(/Structured governance record ready for operator review\./g, "Registro de gobernanza estructurado listo para revisión operativa.")
    .replace(/Not recorded/g, "No registrado")
    .replace(/No permissions listed/g, "No hay permisos listados")
    .replace(/No roles listed/g, "No hay roles listados")
    .replace(/No portal access listed/g, "No hay acceso a portales listado")
    .replace(/None recorded/g, "Nada registrado")
    .replace(/Stored internally/g, "Guardado internamente")
    .replace(/No structured details/g, "Sin detalles estructurados")
    .replace(/When the source collection is populated, this page will summarize each item in plain English here\./g, "Cuando se complete la colección de origen, esta página resumirá cada elemento aquí en lenguaje operativo.");
}

function inferStatus(item) {
  const value = item.status || item.decision || item.employment_status || item.overall_status || item.health_label;
  if (!value) return null;
  const normalized = String(value).toLowerCase();
  if (["healthy", "active", "allow", "approved", "resolved", "green", "ok", "live", "clean"].includes(normalized)) {
    return { label: humanizeToken(value), tone: "emerald", icon: ShieldCheck };
  }
  if (["pending", "pending review", "pending_review", "acknowledged", "amber", "watch", "degraded", "fair"].includes(normalized)) {
    return { label: humanizeToken(value), tone: "amber", icon: TriangleAlert };
  }
  if (["disabled", "deny", "denied", "critical", "red", "inactive", "failed"].includes(normalized)) {
    return { label: humanizeToken(value), tone: "rose", icon: TriangleAlert };
  }
  return { label: humanizeToken(value), tone: "slate", icon: ShieldQuestion };
}

function buildRows(item) {
  const preferred = [
    "name",
    "email",
    "display_name",
    "path",
    "portal_hints",
    "permissions",
    "required_permissions",
    "required_roles",
    "active_roles",
    "portals",
    "action_key",
    "reason",
    "project_number",
    "resource_type",
    "resource_id",
    "operational_urgency",
    "starts_at",
    "expires_at",
    "effective_at",
    "updated_at",
    "created_at",
  ];
  const rows = [];
  preferred.forEach((key) => {
    if (rows.length >= 6) return;
    if (!(key in item) || HIDDEN_KEYS.has(key)) return;
    const value = item[key];
    if (value === undefined || value === null || value === "") return;
    rows.push({ label: humanizeToken(key), value: formatValue(key, value) });
  });

  if (rows.length < 4) {
    Object.entries(item).forEach(([key, value]) => {
      if (rows.length >= 6) return;
      if (preferred.includes(key) || HIDDEN_KEYS.has(key)) return;
      if (key.endsWith("_id") || looksLikeUuid(value)) return;
      if (value === undefined || value === null || value === "") return;
      rows.push({ label: humanizeToken(key), value: formatValue(key, value) });
    });
  }

  return rows;
}

function statusToneClasses(tone) {
  if (tone === "emerald") return "border-emerald-200 bg-emerald-50 text-emerald-800";
  if (tone === "amber") return "border-amber-200 bg-amber-50 text-amber-800";
  if (tone === "rose") return "border-rose-200 bg-rose-50 text-rose-800";
  return "border-slate-200 bg-slate-100 text-slate-700";
}

export default function AdminGovernanceListPage({
  title,
  subtitle,
  breadcrumb,
  testidPrefix,
  loader,
  itemKey = "items",
  transform = (data) => data,
}) {
  const { t, lang } = useT();
  const gt = useCallback((value) => localizeGovernanceText(value, t, lang), [t, lang]);
  usePageTitle(`${title} · Admin`);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const raw = await loader();
      setData(transform(raw));
      setError("");
    } catch (e) {
      setError(operationalError(e, `Could not load ${title}.`));
    }
  }, [loader, title, transform]);

  useEffect(() => { load(); }, [load]);

  const items = data?.[itemKey] || [];
  const normalized = Array.isArray(items)
    ? items
    : Object.entries(items).map(([id, value]) => ({ id, ...(typeof value === "object" ? value : { value }) }));
  const lastUpdated = useMemo(() => {
    const candidates = normalized
      .flatMap((item) => [item.updated_at, item.created_at, item.effective_at, item.starts_at])
      .filter(Boolean)
      .filter(looksLikeIsoDate)
      .sort()
      .reverse();
    return candidates[0] || "";
  }, [normalized]);

  return (
    <LegacyAdminModernShell title={title} subtitle={subtitle} breadcrumb={breadcrumb} testidPrefix={testidPrefix}>
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid={`${testidPrefix}-overview`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl space-y-2">
            <div className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-[11px] font-mono uppercase tracking-[0.18em] text-slate-700">
              {gt("Governance reference page")}
            </div>
            <h2 className="text-2xl font-black text-slate-950">{gt(title)}</h2>
            <p className="text-sm text-slate-700 leading-relaxed">
              {gt(subtitle)} {gt("Every card below is translated into operator language so reviewers can understand the record without reading raw payloads, enum values, or internal IDs.")}
            </p>
          </div>
          <div className="grid min-w-[220px] grid-cols-2 gap-3" data-testid={`${testidPrefix}-metrics`}>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-mono">{gt("Visible items")}</div>
              <div className="mt-2 text-2xl font-black text-slate-950" data-testid={`${testidPrefix}-count`}>{normalized.length}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-mono">{gt("Last update")}</div>
              <div className="mt-2 text-sm font-semibold text-slate-950" data-testid={`${testidPrefix}-last-updated`}>
                {lastUpdated ? formatPlatformTime(lastUpdated) : gt("No timestamp reported")}
              </div>
            </div>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-600">
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1">
            <Clock3 className="h-3.5 w-3.5" />
            {gt("Read-only evidence view")}
          </span>
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1">
            <ShieldCheck className="h-3.5 w-3.5" />
            {gt("Internal identifiers hidden from the primary UI")}
          </span>
        </div>
      </section>

      {error ? <div className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" data-testid={`${testidPrefix}-error`}>{error}</div> : null}

      {!error && normalized.length === 0 ? (
        <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center text-sm text-slate-600" data-testid={`${testidPrefix}-empty`}>
          {gt("No governance records are currently available for this page. When the source collection is populated, this page will summarize each item in plain English here.")}
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid={`${testidPrefix}-list`}>
        {normalized.map((item, index) => {
          const status = inferStatus(item);
          const titleText = inferTitle(item, index);
          const eyebrow = inferEyebrow(item);
          const summary = inferSummary(item);
          const rows = buildRows(item);
          const StatusIcon = status?.icon || ArrowRight;
          return (
            <article key={item.id || item.email || item.user_id || index} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid={`${testidPrefix}-item-${item.id || index}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-2 min-w-0">
                  <div className="text-[11px] uppercase tracking-[0.22em] text-slate-500 font-mono">{localizeGovernanceText(humanizeToken(eyebrow), t, lang)}</div>
                  <div className="text-lg font-black text-slate-950 break-words">{titleText}</div>
                  <p className="text-sm text-slate-700 leading-relaxed">{localizeGovernanceText(summary, t, lang)}</p>
                </div>
                {status ? (
                  <div className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-[11px] font-semibold ${statusToneClasses(status.tone)}`} data-testid={`${testidPrefix}-item-status-${index}`}>
                    <StatusIcon className="h-3.5 w-3.5" />
                    {localizeGovernanceText(status.label, t, lang)}
                  </div>
                ) : null}
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-2" data-testid={`${testidPrefix}-item-rows-${index}`}>
                {rows.map((row) => (
                  <div key={`${titleText}-${row.label}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">{localizeGovernanceText(row.label, t, lang)}</div>
                    <div className="mt-1 text-sm text-slate-900 break-words">{localizeGovernanceText(row.value, t, lang)}</div>
                  </div>
                ))}
              </div>
            </article>
          );
        })}
      </div>
    </LegacyAdminModernShell>
  );
}
