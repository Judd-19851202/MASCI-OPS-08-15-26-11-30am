// PortalLoginShell.jsx — iter346-B
//
// Shared outer chrome for every portal login screen (HR, Safety, PM,
// Shop, Dispatch, Field Leadership). Structural prevention of UI drift —
// when one portal's chrome changes, all six change together.
//
// STRICT INVISIBLE-REFACTOR CONTRACT:
//   • Same DOM order: caution-stripe → header → main → footer
//   • Same wrapper classes (blueprint-bg, max-w-6xl rhythm, etc.)
//   • Same MasciLogo dual-size pattern + LangToggle + Home back link
//   • Same ForgedOpsAttribution variant="login" footer
//   • Per-portal palette injected as **literal** class strings so the
//     Tailwind content scanner finds them in the consumer's source.
//     (Dynamic template strings like `border-${accent}` would be
//     purged silently — that risk is avoided by design.)
//   • Per-portal data-testids preserved via `backTestId` + `rootTestId`
//
// Each portal page wraps its body card inside this shell:
//
//   <PortalLoginShell
//     headerBorderClass="border-purple-700"
//     backHoverClass="hover:text-purple-300"
//     backTestId="hr-login-back"
//     rootTestId="hr-portal-login"
//     footerLabel={t("MASCI · Human Resources Portal")}
//   >
//     <AuthRequiredBanner />
//     <div className="bg-white ...">…form…</div>
//   </PortalLoginShell>
//
// Dialogs (forgot password, etc.) are passed via the `dialogs` prop so
// they sit between <main> and <footer> exactly where they sat in the
// pre-refactor pages.
import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

export function PortalLoginShell({
  headerBorderClass,   // e.g. "border-purple-700" (full literal)
  backHoverClass = "hover:text-slate-200",      // e.g. "hover:text-purple-300" (full literal)
  backTestId,          // e.g. "hr-login-back"
  rootTestId,          // optional outer div testid (e.g. "fl-portal-login")
  footerLabel,         // already-translated label string
  homeLink = "/",
  children,            // body card content
  dialogs,             // optional dialogs rendered between main + footer
}) {
  const { t } = useT();
  return (
    <div
      className="wp17-public-shell wp17-portal-login flex min-h-screen flex-col"
      data-testid={rootTestId}
    >
      <div className="caution-stripe" />
      <header className={`wp17-public-header ${headerBorderClass}`}>
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to={homeLink}
            className={`inline-flex items-center min-h-[44px] -ml-2 px-2 text-white ${backHoverClass} text-sm font-bold uppercase tracking-wide`}
            data-testid={backTestId}
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink={homeLink} />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink={homeLink} />
          <LangToggle />
        </div>
      </header>

      <main className="wp17-public-main flex-1 flex items-center justify-center py-12">
        <div className="w-full max-w-md wp17-auth-stack">
          {children}
        </div>
      </main>

      {dialogs}

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          {footerLabel}
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}

export default PortalLoginShell;
