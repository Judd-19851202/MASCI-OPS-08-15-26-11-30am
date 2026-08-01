import React from "react";
import { CanonicalHeader } from "@/components/CanonicalHeader";

const ACCENT_STYLES = {
  cyan: {
    iconWrap: "border border-cyan-500/35 bg-slate-950 text-cyan-300 ring-1 ring-cyan-200/40 shadow-[0_18px_36px_rgba(8,145,178,0.24)]",
  },
  amber: {
    iconWrap: "border border-amber-500/35 bg-slate-950 text-amber-300 ring-1 ring-amber-200/40 shadow-[0_18px_36px_rgba(217,119,6,0.24)]",
  },
  red: {
    iconWrap: "border border-rose-500/35 bg-slate-950 text-rose-300 ring-1 ring-rose-200/40 shadow-[0_18px_36px_rgba(190,24,93,0.24)]",
  },
  emerald: {
    iconWrap: "border border-emerald-500/35 bg-slate-950 text-emerald-300 ring-1 ring-emerald-200/40 shadow-[0_18px_36px_rgba(5,150,105,0.24)]",
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
  showHomeLink = false,
  showLangToggle = true,
  rightSlot = null,
  testIdPrefix = "operational-page",
}) {
  return (
    <CanonicalHeader
      variant="platform"
      contextLabel={familyMeta}
      contextMeta={familyLabel === "MASCI Operations Platform" ? null : familyLabel}
      accent={accent}
      backTo={backTo}
      backLabel={backLabel}
      homeTo={homeTo}
      showHomeLink={showHomeLink}
      showLangToggle={showLangToggle}
      postControlsSlot={rightSlot}
      containerClassName="max-w-6xl"
      testIdPrefix={testIdPrefix}
    />
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
                    <div className={`inline-flex h-16 w-16 items-center justify-center rounded-[1.25rem] ${accentStyle.iconWrap}`} data-testid={`${testId}-hero-icon`}>
                      <HeroIcon className="h-8 w-8" />
                    </div>
                  ) : null}
                  {kicker ? (
                    <div className="wp17-kicker mt-4" data-testid={`${testId}-kicker`}>
                      {kicker}
                    </div>
                  ) : null}
                  {title ? (
                    <h1 className="font-display text-4xl sm:text-5xl font-black leading-[0.98] tracking-[-0.04em] text-slate-900 mt-2 break-words" data-testid={`${testId}-title`}>
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