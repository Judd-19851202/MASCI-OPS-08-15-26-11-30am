import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Home } from "lucide-react";
import { cn } from "@/lib/utils";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";

const ACCENT_DOT_CLASS = {
  default: "bg-sky-300",
  cyan: "bg-cyan-300",
  amber: "bg-amber-300",
  red: "bg-rose-300",
  emerald: "bg-emerald-300",
  blue: "bg-blue-300",
};

function HeaderNavButton({ to, label, icon: Icon, testId }) {
  return (
    <Link
      to={to}
      className="masci-canonical-header__button wp16-focus-ring inline-flex h-10 items-center gap-1.5 rounded-full border border-white/12 bg-white/10 px-3 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-white transition-[background-color,border-color,color,box-shadow] duration-[140ms] hover:bg-white/16"
      data-testid={testId}
    >
      <Icon className="h-3.5 w-3.5" />
      <span className="hidden sm:inline">{label}</span>
    </Link>
  );
}

export function CanonicalHeader({
  portalLabel = "MASCI Operations Platform",
  pageLabel = "Operational workflow",
  accent = "default",
  backTo = null,
  backLabel = "Back",
  homeTo = "/",
  showHomeLink = true,
  showLangToggle = true,
  centerSlot = null,
  preControlsSlot = null,
  postControlsSlot = null,
  containerClassName = "max-w-6xl",
  testIdPrefix = "masci-header",
}) {
  const accentClass = ACCENT_DOT_CLASS[accent] || ACCENT_DOT_CLASS.default;

  return (
    <header className="masci-canonical-header app-sticky-header relative" data-testid={`${testIdPrefix}-header`}>
      <div className={cn("mx-auto grid h-16 items-center gap-3 px-4 sm:px-6", containerClassName, centerSlot ? "grid-cols-[minmax(0,1fr)_auto] xl:grid-cols-[minmax(0,1fr)_minmax(0,22rem)_auto]" : "grid-cols-[minmax(0,1fr)_auto]") }>
        <div className="flex min-w-0 items-center gap-3" data-testid={`${testIdPrefix}-identity`}>
          <MasciLogo variant="mark" size="sm" className="shrink-0" homeLink="/" />

          <div className="min-w-0 space-y-0.5" data-testid={`${testIdPrefix}-labels`}>
            <div className="inline-flex min-w-0 items-center gap-2">
              <span className={cn("h-2 w-2 shrink-0 rounded-full", accentClass)} aria-hidden />
              <span className="truncate font-mono text-[10px] uppercase tracking-[0.24em] text-white/70">
                {portalLabel}
              </span>
            </div>
            <div className="truncate text-[13px] font-semibold text-white sm:text-sm" data-testid={`${testIdPrefix}-page-label`}>
              {pageLabel}
            </div>
          </div>
        </div>

        {centerSlot ? (
          <div className="hidden min-w-0 xl:flex xl:justify-center" data-testid={`${testIdPrefix}-center`}>
            {centerSlot}
          </div>
        ) : null}

        <div className="flex items-center justify-end gap-2" data-testid={`${testIdPrefix}-actions`}>
          {backTo ? <HeaderNavButton to={backTo} label={backLabel} icon={ArrowLeft} testId={`${testIdPrefix}-back`} /> : null}
          {preControlsSlot}
          {showLangToggle ? <LangToggle variant="dark" testId={`${testIdPrefix}-language`} /> : null}
          {showHomeLink ? <HeaderNavButton to={homeTo} label="Home" icon={Home} testId={`${testIdPrefix}-home`} /> : null}
          {postControlsSlot}
        </div>
      </div>
    </header>
  );
}

export default CanonicalHeader;