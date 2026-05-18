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
import { ArrowLeft, Lock, ListChecks, Loader2, BookOpen, Home, Receipt } from "lucide-react";
import GlobalSearch from "@/components/GlobalSearch";
import NotificationBell from "@/components/NotificationBell";
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
import { SectionTile } from "@/components/SectionTile";
import {
  getLeadershipToken,
  loginLeadership,
  clearLeadershipToken,
} from "@/lib/leadershipAuth";
import {
  FIELD_LEADERSHIP_FORMS,
  SAFETY_EQUIPMENT_ISSUANCE_LINK,
} from "@/lib/fieldLeadershipSchemas";

const FL_PAL = paletteFor("leadership");

// Tiles that link to other in-app surfaces (not "/leadership/{kind}/new"
// forms). Currently only PO Requests — but the structure scales to any
// future cross-portal operational tile we want surfaced in FL.
const FL_EXTERNAL_TILES = {
  po_requests: {
    kind: "po_requests",
    to: "/po-requests",
    icon: Receipt,
    accent: "amber",
    title: {
      en: "PO Requests & Receipts",
      es: "Solicitudes y Recibos de OC",
    },
    desc: {
      en: "Submit purchase orders from the field, track approvals, upload receipts (camera supported), and respond to clarification requests.",
      es: "Envía órdenes de compra desde el campo, sigue aprobaciones, sube recibos (con cámara) y responde aclaraciones.",
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
    subtitle: { en: "Submit PO requests, upload receipts, respond to clarifications, and track spending tied to your jobs.",
                es: "Envía solicitudes de orden de compra, sube recibos, responde aclaraciones y haz seguimiento de gastos." },
    kinds: ["po_requests"],
  },
];

function SectionHeader({ kicker, title, subtitle }) {
  return (
    <div className="flex items-baseline gap-3 mb-4 sm:mb-5 mt-10 sm:mt-12 first:mt-0">
      <span className={`font-mono text-[11px] uppercase tracking-[0.3em] ${FL_PAL.hubKicker} font-black`}>{kicker}</span>
      <span className="h-px flex-1 bg-slate-300 max-w-6" />
      <div className="flex-1 min-w-0">
        <h2 className="font-display text-lg sm:text-xl font-black tracking-tight text-slate-900">{title}</h2>
        {subtitle && <p className="text-xs sm:text-sm text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

function PasswordGate({ onAuthed }) {
  const { t } = useT();
  const [pw, setPw] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!pw.trim()) return;
    setBusy(true);
    try {
      await loginLeadership(pw.trim());
      toast.success(t("Access granted"));
      onAuthed();
    } catch {
      toast.error(t("Incorrect password"));
      setPw("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen blueprint-bg flex flex-col">
      <div className="caution-stripe" />
      <header className={`bg-slate-900 border-b-4 ${FL_PAL.hubHeaderBar}`}>
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/"
            className={`inline-flex items-center text-white ${FL_PAL.hubLinkHover} text-sm font-bold uppercase tracking-wide`}
            data-testid="leadership-login-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
          </div>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border-2 border-slate-300 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-700 text-white">
              <Lock className="w-6 h-6" />
            </div>
            <div>
              <div className={`font-mono text-[10px] uppercase tracking-[0.25em] ${FL_PAL.hubKicker}`}>
                {t("Restricted Area")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Field Leadership Sign In")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-3 mb-6">
            {t("This section is restricted to MASCI field supervisors, foremen, superintendents, PMs, Safety, and Admin. Enter the leadership password to continue.")}
          </p>

          <form onSubmit={submit} className="space-y-4" data-testid="leadership-gate-form">
            <div>
              <Label htmlFor="leadership-password" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Leadership Password")}
              </Label>
              <PasswordInput
                id="leadership-password"
                value={pw}
                onChange={(e) => setPw(e.target.value)}
                autoFocus
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600"
                data-testid="leadership-pw-input"
                toggleTestId="leadership-pw-toggle"
              />
            </div>
            <Button
              type="submit"
              disabled={busy || !pw.trim()}
              className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="leadership-pw-submit"
            >
              {busy ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Verifying…")}
                </>
              ) : (
                <>{t("Sign In")}</>
              )}
            </Button>
          </form>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          {t("MASCI · Field Leadership · Restricted")}
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
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
  const { t, lang } = useT();
  const navigate = useNavigate();
  const [authed, setAuthed] = useState(
    () => Boolean(getLeadershipToken()) || isAdmin() || Boolean(getPmToken())
  );

  useEffect(() => {
    const next = Boolean(getLeadershipToken()) || isAdmin() || Boolean(getPmToken());
    setAuthed(next);
    // Pass 4 — first-class /leadership/login. If not authed, send the
    // user to the dedicated portal door instead of rendering the
    // inline password gate. The inline PasswordGate below is retained
    // as a safety net (link from older bookmarks / mid-session token
    // expiry) but the canonical entry is /leadership/login.
    if (!next) {
      navigate("/leadership/login", { replace: true });
    }
  }, [navigate]);

  if (!authed) {
    return <PasswordGate onAuthed={() => setAuthed(true)} />;
  }

  const signOut = () => {
    clearLeadershipToken();
    navigate("/");
  };

  const admin = isAdmin();

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className={`bg-slate-900 border-b-4 ${FL_PAL.hubHeaderBar}`}>
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-5 sm:py-7 flex items-center gap-3 flex-wrap">
          {/* iter145 — Home + Back text-links for parity with HR / Shop /
              Dispatch sub-hub headers. On small screens the labels
              collapse and only the icons render so the right-hand
              action button row keeps room. */}
          <Link
            to="/"
            className={`inline-flex items-center text-white ${FL_PAL.hubLinkHover} text-xs sm:text-sm font-bold uppercase tracking-wide`}
            data-testid="leadership-nav-home"
            title="Home"
          >
            <Home className="w-4 h-4 sm:mr-1" />
            <span className="hidden sm:inline">{t("Home")}</span>
          </Link>
          <button
            onClick={() => navigate(-1)}
            className={`inline-flex items-center text-white ${FL_PAL.hubLinkHover} text-xs sm:text-sm font-bold uppercase tracking-wide`}
            data-testid="leadership-nav-back"
            title="Back"
          >
            <ArrowLeft className="w-4 h-4 sm:mr-1" />
            <span className="hidden sm:inline">{t("Back")}</span>
          </button>
          <MasciLogo variant="mark" size="2xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="lg" className="sm:hidden" homeLink="/" />
          <div className="flex-1" />
          <div className="flex items-center gap-2 flex-wrap">
            <GlobalSearch accent="dark" />
            <NotificationBell accent="white" />
            <OfflineIndicator />
            <LangToggle />
            <CompanyInfoDialog />
            <Button
              asChild
              variant="outline"
              className="h-10 px-3 border-2 border-slate-600 bg-slate-800 text-white hover:border-indigo-400 hover:text-white text-xs font-bold uppercase tracking-wide"
              data-testid="leadership-training-link"
            >
              <Link to="/guidance">
                <BookOpen className="w-3.5 h-3.5 mr-1" />
                {t("Guides")}
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="h-10 px-3 border-2 border-slate-600 bg-slate-800 text-white hover:border-amber-500 hover:text-white text-xs font-bold uppercase tracking-wide"
              data-testid="leadership-records-link"
            >
              <Link to="/leadership/records">
                <ListChecks className="w-3.5 h-3.5 mr-1" />
                {t("Records")}
              </Link>
            </Button>
            <Button
              onClick={signOut}
              variant="outline"
              className="h-10 px-3 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:text-white text-xs font-bold uppercase tracking-wide"
              data-testid="leadership-signout"
            >
              {t("Sign Out")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-8 sm:mb-10">
          <span className={`font-mono text-xs uppercase tracking-[0.25em] ${FL_PAL.hubKicker} font-bold`}>
            {t("Restricted · Crew Documentation")}
          </span>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 mt-2">
            {t("Field Leadership")}
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
            {t("Crew accountability, employee documentation, equipment responsibility, recognition, and workforce-management tools for MASCI field leadership.")}
          </p>
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-amber-50 border border-amber-300 text-amber-900 text-xs font-mono uppercase tracking-[0.18em] font-bold">
            <Lock className="w-3.5 h-3.5" />
            {t("All forms must be factual, professional, and compliant with employment-documentation best practices.")}
          </div>
        </div>

        {GROUPS.map((group) => (
          <section key={group.kicker} className="mb-2">
            <SectionHeader
              kicker={group.kicker}
              title={t(group.title[lang] || group.title.en)}
              subtitle={t(group.subtitle[lang] || group.subtitle.en)}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
              {group.kinds.map((kind) => {
                const form = resolveForm(kind);
                if (!form) return null;
                const title = form.title[lang] || form.title.en;
                const desc = form.desc[lang] || form.desc.en;
                const locked = Boolean(form.admin_only) && !admin;
                const isExternal = Boolean(form.external);
                const isInternalRoute = Boolean(form.internalRoute);
                return (
                  <SectionTile
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
                      ? t("Open form")
                      : (isInternalRoute ? t("Open") : t("New entry"))}
                    disabled={locked}
                    disabledLabel={t("Sign in as Admin to unlock")}
                    testId={`leadership-tile-${kind}`}
                  />
                );
              })}
            </div>
          </section>
        ))}
      </main>
    </div>
  );
}
