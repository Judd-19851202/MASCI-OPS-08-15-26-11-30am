import React from "react";
import { Link } from "react-router-dom";
import { Home } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import BackLink from "@/components/BackLink";

const ACCENT_STYLES = {
  cyan: {
    header: "from-cyan-400/25 via-sky-300/14 to-transparent",
    pill: "border-cyan-300/28 bg-cyan-400/10",
    button: "border-cyan-300/28 bg-cyan-400/12 text-cyan-50 hover:bg-cyan-400/18",
    glow: "bg-cyan-400/12 text-cyan-50",
  },
  amber: {
    header: "from-amber-300/28 via-orange-300/14 to-transparent",
    pill: "border-amber-300/28 bg-amber-400/10",
    button: "border-amber-300/28 bg-amber-400/12 text-amber-50 hover:bg-amber-400/18",
    glow: "bg-amber-400/12 text-amber-50",
  },
  red: {
    header: "from-rose-300/28 via-red-300/14 to-transparent",
    pill: "border-rose-300/28 bg-rose-400/10",
    button: "border-rose-300/28 bg-rose-400/12 text-rose-50 hover:bg-rose-400/18",
    glow: "bg-rose-400/12 text-rose-50",
  },
  emerald: {
    header: "from-emerald-300/28 via-teal-300/14 to-transparent",
    pill: "border-emerald-300/28 bg-emerald-400/10",
    button: "border-emerald-300/28 bg-emerald-400/12 text-emerald-50 hover:bg-emerald-400/18",
    glow: "bg-emerald-400/12 text-emerald-50",
  },
};

function getAccent(accent) {
  return ACCENT_STYLES[accent] || ACCENT_STYLES.cyan;
}

export function OperationalTopbar({
  backTo,
  backLabel,
  accent = "cyan",
  familyLabel = "MASCI Operations Platform",
  familyMeta = "Operational workflow",
  homeTo = "/",
  showHomeLink = true,
  showLangToggle = true,
  rightSlot = null,
  testIdPrefix = "operational-page",
}) {
  const accentStyle = getAccent(accent);

  return (
    <header className="wp17-public-header relative overflow-hidden" data-testid={`${testIdPrefix}-topbar`}>
      <div className={`pointer-events-none absolute inset-x-0 top-0 h-full bg-gradient-to-r ${accentStyle.header}`} />
      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-3 sm:gap-4">
        <div className="min-w-0 flex flex-wrap items-center gap-3 sm:gap-4">
          {backTo ? (
            <div className={`rounded-full border ${accentStyle.pill} px-3 py-2 shadow-[0_12px_26px_rgba(15,23,42,0.16)]`}>
              <BackLink
                to={backTo}
                label={backLabel}
                variant="header"
                className="text-white/88 hover:text-white"
                testId={`${testIdPrefix}-back`}
              />
            </div>
          ) : null}

          <div className="min-w-0 hidden sm:block" data-testid={`${testIdPrefix}-family`}>
            <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-white/55 truncate">
              {familyLabel}
            </div>
            <div className="text-sm font-semibold text-white truncate">{familyMeta}</div>
          </div>
        </div>

        <MasciLogo variant="mark" size="md" homeLink={homeTo} />

        <div className="flex items-center gap-2 sm:gap-3" data-testid={`${testIdPrefix}-actions`}>
          {showHomeLink ? (
            <Link
              to={homeTo}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-2 text-[11px] font-mono font-bold uppercase tracking-[0.2em] transition-colors ${accentStyle.button}`}
              data-testid={`${testIdPrefix}-home`}
            >
              <Home className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Home</span>
            </Link>
          ) : null}
          {showLangToggle ? (
            <div className="rounded-full border border-white/12 bg-white/10 px-2 py-1 shadow-[0_10px_22px_rgba(15,23,42,0.16)]" data-testid={`${testIdPrefix}-language`}>
              <LangToggle />
            </div>
          ) : null}
          {rightSlot}
        </div>
      </div>
    </header>
  );
}

export function OperationalPageFrame({
  testId = "operational-page",
  backTo,
  backLabel,
  accent = "cyan",
  familyLabel,
  familyMeta,
  homeTo = "/",
  showHomeLink = true,
  showLangToggle = true,
  topbarRightSlot = null,
  heroIcon: HeroIcon = null,
  kicker,
  title,
  description,
  heroMeta = null,
  heroAside = null,
  heroClassName = "",
  mainWidthClass = "max-w-5xl",
  footerText = "MASCI Operations Platform · Operational field view",
  children,
}) {
  const accentStyle = getAccent(accent);
  const hasHero = HeroIcon || kicker || title || description || heroMeta || heroAside;

  return (
    <div className="min-h-screen wp17-public-shell" data-testid={testId}>
      <div className="caution-stripe" />
      <OperationalTopbar
        backTo={backTo}
        backLabel={backLabel}
        accent={accent}
        familyLabel={familyLabel}
        familyMeta={familyMeta}
        homeTo={homeTo}
        showHomeLink={showHomeLink}
        showLangToggle={showLangToggle}
        rightSlot={topbarRightSlot}
        testIdPrefix={testId}
      />

      <main className="wp17-public-main">
        <div className={`${mainWidthClass} mx-auto space-y-6`}>
          {hasHero ? (
            <section className={`wp17-public-hero relative overflow-hidden ${heroClassName}`.trim()} data-testid={`${testId}-hero`}>
              <div className="pointer-events-none absolute right-0 top-0 h-40 w-40 rounded-full bg-white/55 blur-3xl" />
              <div className="relative flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0 flex-1">
                  {HeroIcon ? (
                    <div className={`inline-flex h-14 w-14 items-center justify-center rounded-2xl ${accentStyle.glow} shadow-[0_16px_32px_rgba(15,23,42,0.12)]`} data-testid={`${testId}-hero-icon`}>
                      <HeroIcon className="h-7 w-7" />
                    </div>
                  ) : null}
                  {kicker ? (
                    <div className="wp17-kicker mt-4" data-testid={`${testId}-kicker`}>
                      {kicker}
                    </div>
                  ) : null}
                  {title ? (
                    <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black leading-[0.95] tracking-[-0.04em] text-slate-900 mt-2 break-words" data-testid={`${testId}-title`}>
                      {title}
                    </h1>
                  ) : null}
                  {description ? (
                    <p className="mt-3 max-w-3xl text-sm sm:text-base leading-6 text-slate-700" data-testid={`${testId}-description`}>
                      {description}
                    </p>
                  ) : null}
                  {heroMeta ? (
                    <div className="mt-4 flex flex-wrap items-center gap-2" data-testid={`${testId}-meta`}>
                      {heroMeta}
                    </div>
                  ) : null}
                </div>

                {heroAside ? (
                  <div className="w-full lg:max-w-md" data-testid={`${testId}-hero-aside`}>
                    {heroAside}
                  </div>
                ) : null}
              </div>
            </section>
          ) : null}

          {children}

          {footerText ? (
            <footer className="pt-1 text-center font-mono text-[10px] uppercase tracking-[0.2em] text-slate-400" data-testid={`${testId}-footer`}>
              {footerText}
            </footer>
          ) : null}
        </div>
      </main>
    </div>
  );
}

export default OperationalPageFrame;