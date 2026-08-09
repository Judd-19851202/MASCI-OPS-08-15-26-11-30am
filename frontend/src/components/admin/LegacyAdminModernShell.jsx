// TRACK 25C · ADMIN OS FINAL UNIFICATION
// ────────────────────────────────────────────────────────────────
// One shell to modernize every legacy admin page.
//
// The Admin OS ships one shell — PortalShell + SideNavV3 +
// AdminBreadcrumb. Domain landings (Sprint 3-6) use
// `DomainLandingShell` which composes those primitives on top of a
// declarative manifest. Legacy admin pages predate that shell and
// still render inside `components/AdminShell.jsx` (red top-bar,
// bespoke sidebar, breadcrumb chip).
//
// This shell is the light-touch wrapper legacy pages swap into so
// they instantly inherit the modern chrome without a rewrite of
// their bodies. Every legacy page becomes:
//
//   <LegacyAdminModernShell
//     title="Sessions"
//     subtitle="Read-only forensic view — last 50 portal sessions."
//     breadcrumb={[
//       { label: "Identity & Security", to: "/admin/identity-security" },
//       { label: "Sessions" },
//     ]}
//     testidPrefix="admin-sessions"
//     primaryActions={<RefreshButton />}
//   >
//     {/* original body — unchanged panels / tables / forms */}
//   </LegacyAdminModernShell>
//
// Zero behavioural change to the body — just consistent shell.
// Zero-UTC compliant (no timestamps rendered here).
//
// Rule #7 · single action engine: legacy pages MUST NOT execute
// destructive actions inline. If a legacy page had a "run backup",
// "clear cache", "prune…" button it should be redirected to
// `/admin/operations-control?highlight=<op-id>` via a deep-link chip
// during modernization. The shell does not enforce this — it's a
// per-page decision recorded in TRACK_25B_IA_AUDIT.md.
//
import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PortalShell } from "@/design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";

const LEGACY_ADMIN_TEXT_ES = {
  "Communications": "Comunicaciones",
  "Maintenance": "Mantenimiento",
  "Identity & Security": "Identidad y Seguridad",
  "Governance & Trust": "Gobernanza y Confianza",
  "Diagnostics": "Diagnósticos",
  "Platform Configuration": "Configuración de la Plataforma",
  "Operations Control": "Control de Operaciones",
  "Organization Structure": "Estructura organizativa",
  "Governed organization hierarchy.": "Jerarquía organizativa gobernada.",
  "Identity Projections": "Proyecciones de identidad",
  "Policy-ready identity context derived from canonical auth owners.": "Contexto de identidad listo para políticas derivado de responsables canónicos de autenticación.",
  Roles: "Roles",
  "Configurable enterprise roles.": "Roles empresariales configurables.",
  Permissions: "Permisos",
  "Registry-controlled permissions.": "Permisos controlados por registro.",
  Policies: "Políticas",
  "Versioned governance policies.": "Políticas de gobernanza versionadas.",
  "Approval Flows": "Flujos de aprobación",
  "Reusable approval definitions and requests.": "Definiciones y solicitudes de aprobación reutilizables.",
  Delegations: "Delegaciones",
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
  "Governance Registry": "Registro de gobernanza",
  "Canonical enterprise governance artifacts.": "Artefactos canónicos de gobernanza empresarial.",
  "Governance Versions": "Versiones de gobernanza",
  "Registry and baseline version references.": "Referencias de registro y versiones base.",
  "Governance Health": "Salud de la gobernanza",
  "Enterprise governance health summary.": "Resumen de salud de la gobernanza empresarial.",
  "Enterprise Governance": "Gobernanza empresarial",
  Organization: "Organización",
  Identities: "Identidades",
  Registry: "Registro",
  Versions: "Versiones",
  Health: "Salud",
  Audit: "Auditoría",
  Authority: "Autoridad",
  Decisions: "Decisiones",
};

function localizeLegacyAdminText(value, t, lang) {
  if (typeof value !== "string") return value;
  const translated = t(value);
  if (lang !== "es" || translated !== value) return translated;
  return LEGACY_ADMIN_TEXT_ES[value] || value;
}

export default function LegacyAdminModernShell({
  title,
  subtitle = null,
  breadcrumb = [],
  primaryActions = null,
  testidPrefix = "legacy-admin-modern",
  experienceLevel = null,
  experienceTone = "admin",
  onSignOut = null,
  signOutCapability = null,
  children,
}) {
  const { t, lang } = useT();
  const lt = (value) => localizeLegacyAdminText(value, t, lang);
  const actions = (
    <div className="flex items-center gap-2">
      <Button
        asChild
        variant="outline"
        size="sm"
        data-testid={`${testidPrefix}-back-adminos`}
      >
        <Link to="/admin">
          <ArrowLeft className="w-3.5 h-3.5" />
          {lt("Admin OS")}
        </Link>
      </Button>
      {primaryActions}
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50" data-testid={`${testidPrefix}-root`}>
      <PortalShell
        portalName="MASCI"
        portalRole={lt("Admin")}
        shellTheme="admin"
        experienceLevel={experienceLevel}
        experienceTone={experienceTone}
        pageTitle={typeof title === "string" ? lt(title) : title}
        subtitle={typeof subtitle === "string" ? lt(subtitle) : subtitle}
        primaryActions={actions}
        onSignOut={onSignOut}
        authSessionGuard
        signOutCapability={signOutCapability}
        sideNav={<SideNavV3 variant="admin" onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
      >
        <AdminBreadcrumb
          crumbs={breadcrumb.map((crumb) => ({
            ...crumb,
            label: typeof crumb?.label === "string" ? lt(crumb.label) : crumb?.label,
          }))}
          testidPrefix={`${testidPrefix}-breadcrumb`}
        />
        {children}
      </PortalShell>
    </div>
  );
}
