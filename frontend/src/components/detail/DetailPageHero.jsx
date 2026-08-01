import React from "react";
import BackLink from "@/components/BackLink";
import { PageHeader } from "@/design-system";

export function DetailPageHero({
  backHref,
  backLabel,
  kicker,
  title,
  description,
  actions = null,
  chips = null,
  toolbar = null,
  testId = "detail-page-hero",
}) {
  return (
    <div className="space-y-4 print:hidden" data-testid={testId}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <BackLink
          to={backHref}
          label={backLabel}
          variant="body"
          className="text-slate-600 hover:text-red-700"
          testId={`${testId}-back`}
        />
        {toolbar ? <div className="flex flex-wrap items-center justify-end gap-2">{toolbar}</div> : null}
      </div>
      <PageHeader
        kicker={kicker}
        title={title}
        description={description}
        meta={
          actions || chips ? (
            <div className="space-y-4">
              {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
              {chips ? <div className="flex flex-wrap items-center gap-2">{chips}</div> : null}
            </div>
          ) : null
        }
        titleClassName="text-3xl sm:text-4xl lg:text-5xl"
        descriptionClassName="max-w-3xl leading-6"
        metaClassName="text-slate-600"
        stacked
        data-testid={`${testId}-card`}
      />
    </div>
  );
}

export default DetailPageHero;