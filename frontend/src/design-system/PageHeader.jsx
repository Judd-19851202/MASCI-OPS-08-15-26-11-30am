import React from "react";
import { ResponsiveActionRow, ResponsiveLongText } from "./responsive";

export function PageHeader({
  kicker,
  title,
  description,
  actions = null,
  meta = null,
  className = "",
  titleClassName = "",
  descriptionClassName = "",
  metaClassName = "",
  stacked = false,
  "data-testid": testId = "ds-page-header",
}) {
  const layoutClass = stacked
    ? "flex flex-col gap-4"
    : "flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between";

  return (
    <section className={`wp16-card wp17-page-header p-4 sm:p-5 ${className}`} data-testid={testId}>
      <div className={layoutClass}>
        <div className="min-w-0 flex-1">
          {kicker ? <div className="wp16-kicker mb-2">{kicker}</div> : null}
          {title ? (
            <ResponsiveLongText
              as="h1"
              className={`wp16-section-title text-4xl sm:text-5xl leading-[0.98] ${titleClassName}`.trim()}
              testid={`${testId}-title`}
            >
              {title}
            </ResponsiveLongText>
          ) : null}
          {description ? (
            <p className={`mt-2 max-w-4xl text-sm sm:text-base text-zinc-700 ${descriptionClassName}`.trim()} data-testid={`${testId}-description`}>
              {description}
            </p>
          ) : null}
        </div>
        {(actions || meta) ? (
          <div className="min-w-0 lg:max-w-[42rem] lg:pl-6">
            {actions ? <ResponsiveActionRow testid={`${testId}-actions`}>{actions}</ResponsiveActionRow> : null}
            {meta ? (
              <div className={`mt-3 text-xs sm:text-sm text-zinc-600 ${metaClassName}`.trim()} data-testid={`${testId}-meta`}>
                {meta}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}

export default PageHeader;