// Field Leadership Hub — landing page after the MASCIGC password gate.
//
// Layout mirrors the main MASCI Hub: blueprint-bg + caution-stripe chrome,
// slate-900 header w/ MasciLogo + LangToggle + CompanyInfoDialog, page-eyebrow
// + display headline, then GROUPED `SectionTile` rows (same shared component
// used on Hub.jsx / FieldSection / SafetySection / QaqcSection so every tile
// in the system is the exact same size and rhythm).
//
// Forms are organized into 4 logical groups instead of dumped in build order:
//   01 · Daily Crew Documentation
//   02 · Evaluations & Career Path
//   03 · Equipment Accountability
//   04 · HR Actions
//
// Each group renders its own `SectionHeader` (kicker + dashed rule + h2) and
// a `SectionTile` grid underneath. Bullets per form live in the BULLETS table
// below — keeps each tile body skim-able and consistent.

import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Lock, ListChecks, Loader2, BookOpen, Receipt, Shield, Truck, NotebookPen } from "lucide-react";
import { OfflineIndicator } from "@/lib/resiliency";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { isAdmin } from "@/lib/adminAuth";
import { paletteFor } from "@/lib/portalPalette";
import { getPmToken } from "@/lib/pmAuth";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { usePageTitle } from "@/lib/usePageTitle";
import { PortalShell } from "@/design-system";
import {
  clearLeadershipToken,
} from "@/lib/leadershipAuth";
// iter342 · Hub now also accepts the modern per-user FL portal token
// (iter314). Operators who sign in at /leadership/login (modern email +
// password) get straight into the Hub without needing the legacy
// shared-password gate.
import { getFlToken, clearFlToken } from "@/lib/flAuth";
import { setPortalContext } from "@/lib/portalContext";
import {
  FIELD_LEADERSHIP_FORMS,
  SAFETY_EQUIPMENT_ISSUANCE_LINK,
} from "@/lib/fieldLeadershipSchemas";
import { PasskeyEnrollPrompt } from "@/components/auth/PasskeyEnrollPrompt";
import LastActivityLine from "@/components/admin/LastActivityLine";

const FL_PAL = paletteFor("leadership");

// iter319 · Calm tile palette — mirrors HR/Safety pattern. Left-edge
// stripe + soft slate border + white background. Identity preserved
// via the stripe, never via a hot bg fill.
const STRIPE = {
  red:     "border-l-red-600",
  redDeep: "border-l-red-900",
  amber:   "border-l-amber-500",
  orange:  "border-l-orange-600",
  yellow:  "border-l-yellow-500",
  lime:    "border-l-lime-600",
  emerald: "border-l-emerald-600",
  cyan:    "border-l-cyan-600",
  blue:    "border-l-blue-600",
  indigo:  "border-l-indigo-600",
  purple:  "border-l-purple-600",
  slate:   "border-l-slate-500",
};
const BTN = {
  red:     "bg-red-700 hover:bg-red-800",
  redDeep: "bg-red-900 hover:bg-red-950",
  amber:   "bg-amber-700 hover:bg-amber-800",
  orange:  "bg-orange-700 hover:bg-orange-800",
  yellow:  "bg-yellow-600 hover:bg-yellow-700",
  lime:    "bg-lime-700 hover:bg-lime-800",
  emerald: "bg-emerald-700 hover:bg-emerald-800",
  cyan:    "bg-cyan-700 hover:bg-cyan-800",
  blue:    "bg-blue-700 hover:bg-blue-800",
  indigo:  "bg-indigo-700 hover:bg-indigo-800",
  purple:  "bg-purple-700 hover:bg-purple-800",
  slate:   "bg-slate-700 hover:bg-slate-800",
};

// Tiles that link to other in-app surfaces (not "/leadership/{kind}/new"
// forms). Currently PO Requests + (iter445) JHA Plans + Asset Transfers
// — surfaces field crews routinely call the office to ask about, that
// they can self-serve here.
const FL_EXTERNAL_TILES = {
  po_requests: {
    kind: "po_requests",
    to: "/po-requests",
    icon: Receipt,
    accent: "amber",
    title: {
      en: "PO Requests & Receipts",
      es: "Solicitudes de OC y Recibos",
    },
    desc: {
      // iter242 — Operational authority clarification. Field Leadership
      // REQUESTS purchases. PM / Co-PMs / HR / Accounting issue the
      // official PO and assign the PO number. Receipt upload after
      // purchase is correct Field Leadership scope.
      en: "Submit purchase requests from the field for PM, Co-PM, HR, or Accounting approval — they issue the official PO. After purchase, upload receipts (camera supported) and respond to clarification requests.",
      es: "Envía solicitudes de compra desde el campo para que el PM, Co-PM, RH o Contabilidad las aprueben — ellos emiten la OC oficial. Después de la compra, sube los recibos (compatible con cámara) y responde a las solicitudes de aclaración.",
    },
  },
  // iter445 · F-004 fix · Job Hazard Plans — field crews need this on
  // site for trenching, confined-space, hot-work, etc. Previously only
  // surfaced on the root Hub, forcing supers to memorize the route.
  jha_plans: {
    kind: "jha_plans",
    to: "/jha",
    icon: Shield,
    accent: "orange",
    title: {
      en: "Job Hazard Plans (JHA)",
      es: "Análisis de Riesgos del Trabajo (JHA)",
    },
    desc: {
      en: "Open today's JHA before high-risk work (trenching ≥ 5', confined space, hot work). Acknowledge with crew. View the full library by task type.",
      es: "Abre el JHA del día antes de trabajo de alto riesgo (excavación ≥ 5', espacio confinado, trabajo en caliente). Confirma con el equipo. Consulta la biblioteca completa por tipo de tarea.",
    },
  },
  // iter445 · F-005 fix · Asset Transfers — superintendents need to
  // confirm equipment in/out from the yard without phoning dispatch.
  asset_transfers: {
    kind: "asset_transfers",
    to: "/asset-transfers",
    icon: Truck,
    accent: "blue",
    title: {
      en: "Asset Transfers",
      es: "Transferencias de Equipos",
    },
    desc: {
      en: "See incoming and outgoing equipment for your jobs. Track in-transit deliveries from the yard, returns to storage, and inter-job moves.",
      es: "Consulta equipos entrantes y salientes en tus obras. Sigue entregas en tránsito desde el patio, devoluciones a almacenamiento y movimientos entre obras.",
    },
  },
  // Track 13.10 · Surfacing — Operational Daily Records (ODR) FL Command
  // Center entry. ODR backend ships with FLL-1..FLL-6 role-aware projection
  // (visibility.py). Tile is link-only; no new route, no new endpoint, no
  // new permission. Discoverability fix for the largest dormant operational
  // asset on the platform (Tracks 13.9 + 13.9.1 certified).
  operational_daily_records: {
    kind: "operational_daily_records",
    to: "/odr/center",
    icon: NotebookPen,
    accent: "indigo",
    title: {
      en: "Operational Daily Records",
      es: "Registros Operacionales Diarios",
    },
    desc: {
      en: "Field-day operational record · one document per project · crew · date. Submit, review, amend. FLL-aware role projection · public-link continuity · 5-audience PDF.",
      es: "Registro operacional del día · un documento por proyecto · cuadrilla · fecha. Enviar, revisar, enmendar. Proyección por rol FLL · enlaces públicos · PDF de 5 audiencias.",
    },
  },
};

// 4 logical groups — ordered most-used → least-used.
// `kinds` is a list of form `kind` keys; tiles render in this exact order.
const GROUPS = [
  {
    kicker: "01",
    title: { en: "Daily Crew Documentation", es: "Documentación Diaria del Personal" },
    subtitle: { en: "What you fill out at the end of a shift to keep the paper trail clean.",
                es: "Lo que llenas al final del turno para mantener el registro limpio." },
    kinds: ["verbal_coaching", "write_up", "attendance", "recognition"],
  },
  {
    kicker: "02",
    title: { en: "Evaluations & Career Path", es: "Evaluaciones y Carrera Profesional" },
    subtitle: { en: "Performance, promotions, and training accountability.",
                es: "Desempeño, ascensos y responsabilidad de capacitación." },
    kinds: ["new_employee_eval", "crew_eval", "promotion_recommendation", "training_deficiency"],
  },
  {
    kicker: "03",
    title: { en: "Equipment Accountability", es: "Responsabilidad de Equipo" },
    subtitle: { en: "Who's responsible for what — checkout, return, and PPE issuance.",
                es: "Quién es responsable de qué — entrega, devolución y emisión de EPP." },
    kinds: ["equipment_checkout", "equipment_return", "safety_equipment_issuance"],
  },
  {
    kicker: "04",
    title: { en: "HR Actions", es: "Acciones de RRHH" },
    subtitle: { en: "Routes straight to the HR Portal for approval or final processing.",
                es: "Se enrutan al Portal de RRHH para aprobación o procesamiento final." },
    kinds: ["time_off_request", "employee_termination"],
  },
  {
    kicker: "05",
    title: { en: "Operations & Spending", es: "Operaciones y Gastos" },
    // iter242 — Authority clarification copy. Field Leadership submits
    // PO _requests_ (not official POs). Issuance + PO number assignment
    // belongs to PM / Co-PMs / HR / Accounting. Visibility/notification
    // already fans out to PM-role users (which includes both primary PM
    // and Co-PMs) plus HR.
    subtitle: { en: "Submit purchase requests, upload receipts, respond to clarifications, and track spending tied to your jobs. The assigned PM, any Co-PMs, HR, and Admin issue the official PO.",
                es: "Envía solicitudes de compra, sube recibos, responde aclaraciones y haz seguimiento de gastos. El PM asignado, los Co-PMs, RH y Admin emiten la OC oficial." },
    kinds: ["po_requests"],
  },
  // iter445 · F-004 + F-005 fixes — surfaces field crews routinely call
  // the office to ask about. JHA must be visible BEFORE high-risk work;
  // asset-transfer visibility eliminates "where's my roller?" phone tag.
  {
    kicker: "06",
    title: { en: "On-Site Reference", es: "Referencia en Obra" },
    subtitle: { en: "Look up before you start. Find JHAs and confirm equipment is in transit.",
                es: "Consulta antes de comenzar. Encuentra JHAs y confirma que el equipo está en tránsito." },
    kinds: ["jha_plans", "asset_transfers"],
  },
  // Track 13.10 · Operational Daily Records surfacing — FL Command Center
  // entry for the field-day system of record (ODR). Backend ships with
  // FLL-aware role projection so the SAME destination serves Foreman
  // (own ODRs), Super tier (crew/project/regional), and PM (consumption
  // panel via /pm/odr — separate). Link-only · zero backend touch.
  {
    kicker: "07",
    title: { en: "Operational Daily Record", es: "Registro Operacional Diario" },
    subtitle: { en: "The field-day system of record. One document per project · crew · date. FLL-aware projection · public-link continuity.",
                es: "El registro del día en campo. Un documento por proyecto · cuadrilla · fecha. Proyección por rol FLL · enlaces públicos." },
    kinds: ["operational_daily_records"],
  },
];

function SectionHeader({ title, subtitle }) {
  // iter319 · matches HR (iter317-C) + Safety (iter318) section heading
  // style: mono kicker · thin slate-200 divider · italic muted subtitle.
  return (
    <div className="mb-4 flex items-baseline gap-3 flex-wrap">
      <h2 className={`font-mono text-xs uppercase tracking-[0.22em] ${FL_PAL.hubKicker}`}>
        {title}
      </h2>
      <span className="hidden sm:inline-block h-px flex-1 bg-slate-200" aria-hidden="true" />
      <span className="text-xs text-slate-500 italic">{subtitle}</span>
    </div>
  );
}

// iter319 · Calm tile. Mirrors HR/Safety calm tile shape. Handles the
// SectionTile feature set we actually use: disabled (admin-only forms
// for non-admins), internal `to`, external `href`, accent color, testId.
function LeadershipTile({ to, href, icon: Icon, title, desc, accent = "red", ctaLabel = "OPEN", disabled = false, disabledLabel, testId }) {
  const stripe = STRIPE[accent] || STRIPE.red;
  const btn = BTN[accent] || BTN.red;
  const base = `block rounded-lg border border-slate-200 border-l-4 ${stripe} bg-white p-5 transition-all duration-150 relative ${
    disabled
      ? "opacity-60 cursor-not-allowed"
      : "hover:shadow-md hover:-translate-y-0.5 hover:border-slate-300"
  }`;
  const inner = (
    <div className="flex items-start gap-3">
      <Icon className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
      <div className="flex-1 min-w-0">
        <h3 className="font-display text-lg font-black">{title}</h3>
        <p className="text-sm text-slate-600 mt-1">{desc}</p>
        <span className={`mt-3 inline-flex items-center h-9 px-3 rounded-md ${
          disabled ? "bg-slate-300 text-slate-600" : `${btn} text-white`
        } font-bold uppercase tracking-wide text-xs`}>
          {disabled ? (disabledLabel || "Locked") : `${ctaLabel} →`}
        </span>
      </div>
    </div>
  );
  if (disabled) return <div className={base} data-testid={testId} aria-disabled="true">{inner}</div>;
  if (href) return <a href={href} className={base} data-testid={testId}>{inner}</a>;
  return <Link to={to} className={base} data-testid={testId}>{inner}</Link>;
}

/**
 * Resolve a `kind` key to a form definition. Schema kinds come from
 * FIELD_LEADERSHIP_FORMS; the one external kind comes from
 * SAFETY_EQUIPMENT_ISSUANCE_LINK.
 */
function resolveForm(kind) {
  if (kind === SAFETY_EQUIPMENT_ISSUANCE_LINK.kind) {
    return { ...SAFETY_EQUIPMENT_ISSUANCE_LINK, external: true };
  }
  if (FL_EXTERNAL_TILES[kind]) {
    // Internal-app tile (e.g., /po-requests). Uses `to` (Link route),
    // NOT `href` (which would mark it external/new-tab).
    return { ...FL_EXTERNAL_TILES[kind], internalRoute: true };
  }
  const f = FIELD_LEADERSHIP_FORMS.find((x) => x.kind === kind);
  return f ? { ...f, external: false } : null;
}

export default function FieldLeadershipHub() {
  usePageTitle("Field Leadership · MASCI");
  const { t, lang } = useT();
  const navigate = useNavigate();
  const [authed, setAuthed] = useState(
    () => Boolean(getFlToken()) || isAdmin() || Boolean(getPmToken())
  );

  useEffect(() => {
    const next = Boolean(getFlToken()) || isAdmin() || Boolean(getPmToken());
    setAuthed(next);
    // TRUST-PO-1 · 2026-05-28 — declare portal context on every mount
    // so shared pages (e.g., /po-requests) can render capability-scoped
    // UI even when admin/pm tokens coexist in storage. This is the
    // surgical fix for Super-Admin-in-FL approval-control bleed.
    if (next) {
      try { setPortalContext("field-leadership"); } catch { /* noop */ }
    }
    if (!next) {
      navigate("/leadership/login", { replace: true });
    }
  }, [navigate]);

  if (!authed) {
    return null;
  }

  const signOut = () => {
    clearLeadershipToken();
    // iter342 · also clear the modern FL portal token so the per-user
    // session ends cleanly. No silent ghost sessions.
    try { clearFlToken(); } catch { /* noop */ }
    navigate("/");
  };

  const admin = isAdmin();

  return (
    <PortalShell
      portalName="MASCI"
      portalRole={t("Field Leadership")}
      pageTitle={t("Field Leadership")}
      subtitle={t("Crew documentation, accountability, and field requests in one operational workspace.")}
      showBack
      backHref="/"
      portalSwitcherCurrent="leadership"
      showNotifications={false}
      onSignOut={signOut}
      primaryActions={
        <div className="flex items-center gap-2" data-testid="leadership-header-actions">
          <OfflineIndicator />
          <Button
            asChild
            variant="outline"
            size="sm"
            className="hidden md:inline-flex h-9 px-3 text-xs font-bold uppercase tracking-wide"
            data-testid="leadership-records-link"
          >
            <Link to="/leadership/records">
              <ListChecks className="w-3.5 h-3.5 mr-1.5" />
              {t("Records")}
            </Link>
          </Button>
          <Button
            asChild
            variant="outline"
            size="sm"
            className="hidden md:inline-flex h-9 px-3 text-xs font-bold uppercase tracking-wide"
            data-testid="leadership-training-link"
          >
            <Link to="/guidance?from=leadership">
              <BookOpen className="w-3.5 h-3.5 mr-1.5" />
              {t("Guides")}
            </Link>
          </Button>
          <div className="hidden md:flex" data-testid="leadership-company-info">
            <CompanyInfoDialog />
          </div>
        </div>
      }
    >
      <div data-testid="leadership-hub-root">
        <section className="wp17-mission-banner mb-6" data-testid="fl-portal-mission-banner">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="wp17-kicker text-white/70">{t("Portal mission")}</div>
              <h2 className="mt-2 font-display text-xl font-black text-white">{t("Keep crew documentation, accountability, and field requests in one clear workflow home.")}</h2>
            </div>
          </div>
        </section>

        {/* iter429 · Phase 28 · Optional device sign-in enrollment ·
            self-gated · dismissible · single-card · NEVER nags */}
        <div className="mb-8">
          <PasskeyEnrollPrompt />
        </div>

        {/* iter440 · calm "Last activity" trace · quiet proof of platform usage. */}
        <div className="mb-8">
          <LastActivityLine portal="field_leadership" />
        </div>

        <div className="space-y-10">
          {GROUPS.map((group) => (
            <section key={group.kicker} data-testid={`leadership-group-${group.kicker}`}>
              <SectionHeader
                title={t(group.title[lang] || group.title.en)}
                subtitle={t(group.subtitle[lang] || group.subtitle.en)}
              />
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {group.kinds.map((kind) => {
                  const form = resolveForm(kind);
                  if (!form) return null;
                  const title = form.title[lang] || form.title.en;
                  const desc = form.desc[lang] || form.desc.en;
                  const locked = Boolean(form.admin_only) && !admin;
                  const isExternal = Boolean(form.external);
                  const isInternalRoute = Boolean(form.internalRoute);
                  return (
                    <LeadershipTile
                      key={kind}
                      to={isExternal
                        ? undefined
                        : (isInternalRoute ? form.to : `/leadership/${kind}/new`)}
                      href={isExternal ? form.to : undefined}
                      icon={form.icon}
                      title={title}
                      desc={desc}
                      accent={form.accent}
                      ctaLabel={isExternal
                        ? t("OPEN FORM")
                        : (isInternalRoute ? t("OPEN") : t("NEW ENTRY"))}
                      disabled={locked}
                      disabledLabel={t("Sign in as Admin to unlock")}
                      testId={`leadership-tile-${kind}`}
                    />
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      </div>
    </PortalShell>
  );
}
