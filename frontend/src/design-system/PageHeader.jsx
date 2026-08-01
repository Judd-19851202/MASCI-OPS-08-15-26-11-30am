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
    ? "flex flex-col gap-5"
    : "flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between";

  return (
    <section className={`wp17-page-header p-5 sm:p-6 ${className}`} data-testid={testId}>
      <div className={layoutClass}>
        <div className="min-w-0 flex-1">
          {kicker ? <div className="wp17-kicker mb-2">{kicker}</div> : null}
          {title ? (
            <ResponsiveLongText
              as="h1"
              className={`font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 leading-[0.96] ${titleClassName}`.trim()}
              testid={`${testId}-title`}
            >
              {title}
            </ResponsiveLongText>
          ) : null}
          {description ? (
            <p className={`mt-3 max-w-4xl text-sm sm:text-base leading-7 text-slate-600 ${descriptionClassName}`.trim()} data-testid={`${testId}-description`}>
              {description}
            </p>
          ) : null}
        </div>
        {(actions || meta) ? (
          <div className="min-w-0 lg:max-w-[42rem] lg:pl-8">
            {actions ? <ResponsiveActionRow testid={`${testId}-actions`}>{actions}</ResponsiveActionRow> : null}
            {meta ? (
              <div className={`mt-4 text-xs sm:text-sm text-slate-600 ${metaClassName}`.trim()} data-testid={`${testId}-meta`}>
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