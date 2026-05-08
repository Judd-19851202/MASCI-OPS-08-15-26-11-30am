// Field Leadership Hub — landing page after the MASCIGC password gate.
//
// Visual style mirrors the main MASCI Hub: same blueprint-bg + caution-stripe
// chrome, slate-900 header w/ MasciLogo + LangToggle + CompanyInfoDialog,
// page-eyebrow + 4xl/5xl/6xl display headline + body copy, then the same
// SectionCard tile pattern used on the Hub for every other section.
//
// Each form is a SectionCard with an accent color, eyebrow tag, icon, title,
// description, and bullet list. Supervisor Notes locks out non-admin users.
// Safety Equipment Issuance opens the existing Safety Forms login.

import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, ArrowLeft, Lock, ListChecks, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { PasswordInput } from "@/components/PasswordInput";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { isAdmin } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import {
  getLeadershipToken,
  loginLeadership,
  clearLeadershipToken,
} from "@/lib/leadershipAuth";
import {
  FIELD_LEADERSHIP_FORMS,
  SAFETY_EQUIPMENT_ISSUANCE_LINK,
} from "@/lib/fieldLeadershipSchemas";

// Same accent palette as Hub.jsx SectionCard so Tailwind retains the classes.
const STYLES = {
  red:    { bg: "bg-red-700",     ring: "hover:border-red-700",     pill: "text-red-700 bg-red-50" },
  amber:  { bg: "bg-amber-600",   ring: "hover:border-amber-600",   pill: "text-amber-700 bg-amber-50" },
  orange: { bg: "bg-orange-600",  ring: "hover:border-orange-600",  pill: "text-orange-700 bg-orange-50" },
  emerald:{ bg: "bg-emerald-700", ring: "hover:border-emerald-700", pill: "text-emerald-700 bg-emerald-50" },
  blue:   { bg: "bg-blue-700",    ring: "hover:border-blue-700",    pill: "text-blue-700 bg-blue-50" },
  cyan:   { bg: "bg-cyan-600",    ring: "hover:border-cyan-600",    pill: "text-cyan-700 bg-cyan-50" },
  purple: { bg: "bg-purple-700",  ring: "hover:border-purple-700",  pill: "text-purple-700 bg-purple-50" },
  indigo: { bg: "bg-indigo-700",  ring: "hover:border-indigo-700",  pill: "text-indigo-700 bg-indigo-50" },
  fuchsia:{ bg: "bg-fuchsia-700", ring: "hover:border-fuchsia-700", pill: "text-fuchsia-700 bg-fuchsia-50" },
  lime:   { bg: "bg-lime-500",    ring: "hover:border-lime-500",    pill: "text-lime-700 bg-lime-50" },
  yellow: { bg: "bg-yellow-500",  ring: "hover:border-yellow-500",  pill: "text-yellow-800 bg-yellow-50" },
  slate:  { bg: "bg-slate-900",   ring: "hover:border-slate-900",   pill: "text-slate-800 bg-slate-100" },
};

// Bullet content per form — keeps each tile's body grounded and skim-able,
// matching the rest of the Hub which always shows 2 bullets per SectionCard.
const BULLETS = {
  write_up: { en: ["Disciplinary or corrective action", "Written/Verbal/Final · refusal-to-sign supported"],
              es: ["Acción disciplinaria o correctiva", "Verbal/Escrita/Final · admite negativa a firmar"] },
  verbal_coaching: { en: ["Coaching conversation, not a write-up", "Track follow-up date if needed"],
                     es: ["Conversación de asesoramiento, no es amonestación", "Registra fecha de seguimiento"] },
  attendance: { en: ["Late arrival · Left early · No-show", "Scheduled vs. actual times captured"],
                es: ["Llegada tardía · Salida temprana · No se presentó", "Hora programada vs. real registrada"] },
  recognition: { en: ["Safety leadership · Quality · Teamwork", "Builds positive crew culture"],
                 es: ["Liderazgo en seguridad · Calidad · Equipo", "Cultiva cultura positiva en cuadrilla"] },
  equipment_checkout: { en: ["Asset ID + 2 photos required per item", "Auto-totals replacement value"],
                        es: ["ID de activo + 2 fotos por artículo", "Calcula valor total de reemplazo"] },
  equipment_return: { en: ["Look up by serial · auto-fills checkout", "Auto-flags damage / loss vs. replacement value"],
                      es: ["Buscar por serie · autocompleta entrega", "Marca daños / pérdidas vs. valor de reemplazo"] },
  new_employee_eval: { en: ["30 / 60 / 90-day evaluation", "Ratings + recommended action"],
                       es: ["Evaluación de 30 / 60 / 90 días", "Calificaciones + acción recomendada"] },
  crew_eval: { en: ["Safety · Production · Quality · Communication", "Captures issues + positive observations"],
               es: ["Seguridad · Producción · Calidad · Comunicación", "Registra problemas y observaciones positivas"] },
  promotion_recommendation: { en: ["Promotion · Raise · Leadership development", "Strengths, leadership, safety record"],
                              es: ["Ascenso · Aumento · Desarrollo de liderazgo", "Fortalezas, liderazgo, seguridad"] },
  training_deficiency: { en: ["Document deficiency + assigned retraining", "Track due date + completion status"],
                         es: ["Documente deficiencia + reentrenamiento", "Registre fecha límite y estado"] },
  supervisor_notes: { en: ["Internal leadership documentation log", "Visible to admins, PMs, and field leadership"],
                      es: ["Registro interno de liderazgo", "Visible para administradores, PMs y liderazgo de campo"] },
};

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
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="leadership-login-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Hub")}
          </Link>
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border-2 border-slate-300 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-700 text-white">
              <Lock className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700">
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

function LeadershipTile({ form, lang, t, locked, isExternal, externalTo }) {
  const s = STYLES[form.accent] || STYLES.red;
  const Icon = form.icon;
  const title = form.title[lang] || form.title.en;
  const desc = form.desc[lang] || form.desc.en;
  const bullets = (BULLETS[form.kind] || { en: [] })[lang] || BULLETS[form.kind]?.en || [];

  if (locked) {
    return (
      <div
        className="group relative bg-white border-2 border-dashed border-slate-300 rounded-md p-6 sm:p-8 flex flex-col opacity-90 cursor-not-allowed"
        data-testid={`leadership-tile-${form.kind}`}
        aria-disabled="true"
      >
        <div className={`absolute top-0 left-0 right-0 h-1.5 rounded-t ${s.bg} opacity-60`} />
        <div className="flex items-start justify-between gap-3">
          <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${s.bg} text-white opacity-70`}>
            <Icon className="w-7 h-7" />
          </div>
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-900 text-amber-300 font-mono text-[10px] uppercase tracking-[0.2em] font-bold">
            <Lock className="w-3 h-3" /> {t("Admin Only")}
          </span>
        </div>
        <h3 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-700 mt-4">
          {title}
        </h3>
        <p className="text-slate-500 text-sm sm:text-base mt-2 leading-relaxed">{desc}</p>
        {bullets.length > 0 && (
          <ul className="mt-4 space-y-1.5 text-xs sm:text-sm text-slate-500">
            {bullets.map((b) => (
              <li key={b} className="flex items-start gap-2">
                <span className={`mt-1.5 w-1 h-1 rounded-full ${s.bg} shrink-0 opacity-60`} />
                <span>{b}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="mt-6 pt-5 border-t-2 border-dashed border-slate-200">
          <span className="font-mono text-xs uppercase tracking-[0.2em] font-bold text-slate-400">
            {t("Sign in as Admin to unlock")}
          </span>
        </div>
      </div>
    );
  }

  const className = `group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-8 transition-all duration-150 hover:-translate-y-0.5 ${s.ring} flex flex-col`;
  const inner = (
    <>
      <div className={`absolute top-0 left-0 right-0 h-1.5 rounded-t ${s.bg}`} />
      <div className="flex items-start justify-between gap-3">
        <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${s.bg} text-white`}>
          <Icon className="w-7 h-7" />
        </div>
        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded ${s.pill} font-mono text-[10px] uppercase tracking-[0.2em] font-bold`}>
          {isExternal ? t("Existing Form") : t("Field Leadership")}
        </span>
      </div>
      <h3 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-4">
        {title}
      </h3>
      <p className="text-slate-600 text-sm sm:text-base mt-2 leading-relaxed">{desc}</p>
      {bullets.length > 0 && (
        <ul className="mt-4 space-y-1.5 text-xs sm:text-sm text-slate-700">
          {bullets.map((b) => (
            <li key={b} className="flex items-start gap-2">
              <span className={`mt-1.5 w-1 h-1 rounded-full ${s.bg} shrink-0`} />
              <span>{b}</span>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-6 pt-5 border-t-2 border-slate-100 flex items-center justify-between">
        <span className="font-mono text-xs uppercase tracking-[0.2em] font-bold text-red-700">
          {isExternal ? t("Open form →") : t("New entry →")}
        </span>
        <ArrowRight className="w-5 h-5 transition-transform duration-150 group-hover:translate-x-1 text-red-700" />
      </div>
    </>
  );

  if (isExternal) {
    return (
      <a
        href={externalTo}
        className={className}
        data-testid={`leadership-tile-${form.kind}`}
      >
        {inner}
      </a>
    );
  }

  return (
    <Link
      to={`/leadership/${form.kind}/new`}
      className={className}
      data-testid={`leadership-tile-${form.kind}`}
    >
      {inner}
    </Link>
  );
}

export default function FieldLeadershipHub() {
  const { t, lang } = useT();
  const navigate = useNavigate();
  const [authed, setAuthed] = useState(
    () => Boolean(getLeadershipToken()) || isAdmin() || Boolean(getPmToken())
  );

  useEffect(() => {
    setAuthed(Boolean(getLeadershipToken()) || isAdmin() || Boolean(getPmToken()));
  }, []);

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
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-5 sm:py-7 flex items-center justify-between">
          <MasciLogo variant="lockup" size="4xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="lockup" size="xl" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
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
        <div className="mb-10 sm:mb-14">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6 mb-10">
          {FIELD_LEADERSHIP_FORMS.map((form) => (
            <LeadershipTile
              key={form.kind}
              form={form}
              lang={lang}
              t={t}
              locked={form.admin_only && !admin}
            />
          ))}
          <LeadershipTile
            form={SAFETY_EQUIPMENT_ISSUANCE_LINK}
            lang={lang}
            t={t}
            locked={false}
            isExternal
            externalTo={SAFETY_EQUIPMENT_ISSUANCE_LINK.to}
          />
        </div>
      </main>
    </div>
  );
}
