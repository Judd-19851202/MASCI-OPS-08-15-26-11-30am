import React from "react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { SemanticIcon } from "@/components/icons/AppIcon";
import { useT } from "@/lib/i18n";

function HeaderNavButton({ to, label, iconName, testId }) {
  return (
    <Link
      to={to}
      className="masci-canonical-header__button wp16-focus-ring inline-flex h-9 items-center gap-1.5 rounded-full border border-white/12 bg-white/6 px-3 text-[11px] font-mono font-bold uppercase tracking-[0.16em] text-white transition-[background-color,border-color,color,box-shadow] duration-[140ms] hover:bg-white/14"
      data-testid={testId}
    >
      <SemanticIcon name={iconName} size="xs" tone="inverse" />
      <span>{label}</span>
    </Link>
  );
}

export function CanonicalHeader({
  variant = "default",
  portalLabel = "MASCI Operations Platform",
  pageLabel = null,
  contextLabel = null,
  contextMeta = null,
  accent = "default",
  backTo = null,
  backLabel = "Back",
  homeTo = "/",
  showHomeLink = false,
  showLangToggle = true,
  headerControlsSlot = null,
  centerSlot = null,
  preControlsSlot = null,
  postControlsSlot = null,
  utilitySlot = null,
  containerClassName = "max-w-6xl",
  testIdPrefix = "masci-header",
}) {
  const { t } = useT();
  const hasUtilityRail = Boolean(utilitySlot || centerSlot || preControlsSlot || postControlsSlot);
  const isHomeVariant = variant === "home";
  const brandCompany = "MASCI";
  const brandProduct = t("Operations Platform");
  const utilityContent = utilitySlot || (
    <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
      {centerSlot ? <div className="min-w-0" data-testid={`${testIdPrefix}-utility-primary`}>{centerSlot}</div> : <div />}
      {(preControlsSlot || postControlsSlot) ? (
        <div className="flex flex-wrap items-center gap-2 lg:justify-end" data-testid={`${testIdPrefix}-utility-secondary`}>
          {preControlsSlot}
          {postControlsSlot}
        </div>
      ) : null}
    </div>
  );
  const homeControlAllowed = Boolean(showHomeLink && homeTo);
  const resolvedContextLabel = contextLabel || (!isHomeVariant ? pageLabel || portalLabel || t("Operational workflow") : null);
  const resolvedContextMeta = !isHomeVariant ? contextMeta : null;

  return (
    <>
      <header className="masci-canonical-header app-sticky-header relative" data-testid={`${testIdPrefix}-header`}>
        <div className={cn("mx-auto px-4 sm:px-6", containerClassName)}>
          <div className="masci-canonical-header__row masci-canonical-header__row--global" data-testid={`${testIdPrefix}-global-row`}>
            <div className="flex min-w-0 items-center gap-2.5" data-testid={`${testIdPrefix}-identity`}>
              <MasciLogo variant="mark" size="md" className="shrink-0" homeLink={homeTo || "/"} />
              {backTo ? <HeaderNavButton to={backTo} label={t(backLabel)} iconName="back" testId={`${testIdPrefix}-back`} /> : null}
              {homeControlAllowed ? <HeaderNavButton to={homeTo} label={t("Home")} iconName="home" testId={`${testIdPrefix}-home`} /> : null}
            </div>

            <div className="flex items-center justify-end gap-2" data-testid={`${testIdPrefix}-actions`}>
              {headerControlsSlot}
              {showLangToggle ? <LangToggle variant="header" className="h-9" testId={`${testIdPrefix}-language`} /> : null}
            </div>
          </div>

          <div
            className={cn(
              "masci-canonical-header__row masci-canonical-header__row--identity",
              isHomeVariant && "masci-canonical-header__row--home-identity",
            )}
            data-testid={`${testIdPrefix}-workflow-row`}
          >
            <div className="masci-canonical-header__identity-grid" data-testid={`${testIdPrefix}-identity-grid`}>
              <div className="masci-canonical-header__brand-block" data-testid={`${testIdPrefix}-home-brand`}>
                <div className="masci-canonical-header__brand-company" data-testid={`${testIdPrefix}-portal-label`}>
                  {brandCompany}
                </div>
                <div className="masci-canonical-header__brand-product" data-testid={`${testIdPrefix}-page-label`}>
                  {brandProduct}
                </div>
              </div>

              {resolvedContextLabel ? (
                <div className="masci-canonical-header__context-block" data-testid={`${testIdPrefix}-context-block`}>
                  <div className="masci-canonical-header__context-label" data-testid={`${testIdPrefix}-context-label`}>
                    {resolvedContextLabel}
                  </div>
                  {resolvedContextMeta ? (
                    <div className="masci-canonical-header__context-meta" data-testid={`${testIdPrefix}-context-meta`}>
                      {resolvedContextMeta}
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </header>

      {hasUtilityRail ? (
        <div className="masci-canonical-header__utility-rail" data-testid={`${testIdPrefix}-utility`}>
          <div className={cn("mx-auto px-4 sm:px-6 py-3", containerClassName)}>{utilityContent}</div>
        </div>
      ) : null}
    </>
  );
}

export default CanonicalHeader;