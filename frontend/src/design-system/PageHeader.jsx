import React from "react";
import { ResponsiveActionRow, ResponsiveLongText } from "./responsive";

export function PageHeader({
  kicker,
  title,
  description,
  actions = null,
  meta = null,
  className = "",
  "data-testid": testId = "ds-page-header",
}) {
  return (
    <section className={`wp16-card p-4 sm:p-5 ${className}`} data-testid={testId}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          {kicker ? <div className="wp16-kicker mb-2">{kicker}</div> : null}
          {title ? (
            <ResponsiveLongText
              as="h1"
              className="wp16-section-title text-4xl sm:text-5xl leading-[0.98]"
              testid={`${testId}-title`}
            >
              {title}
            </ResponsiveLongText>
          ) : null}
          {description ? (
            <p className="mt-2 max-w-4xl text-sm sm:text-base text-zinc-700" data-testid={`${testId}-description`}>
              {description}
            </p>
          ) : null}
        </div>
        {(actions || meta) ? (
          <div className="min-w-0 lg:max-w-[42rem] lg:pl-6">
            {actions ? <ResponsiveActionRow testid={`${testId}-actions`}>{actions}</ResponsiveActionRow> : null}
            {meta ? (
              <div className="mt-3 text-xs sm:text-sm text-zinc-600" data-testid={`${testId}-meta`}>
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