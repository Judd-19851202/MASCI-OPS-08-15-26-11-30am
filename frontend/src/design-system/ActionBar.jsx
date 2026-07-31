import React from "react";
import { ResponsiveActionRow } from "./responsive";

export function ActionBar({
  eyebrow,
  title,
  description,
  actions,
  className = "",
  "data-testid": testId = "ds-action-bar",
}) {
  return (
    <section className={`wp16-toolbar wp17-action-bar p-4 ${className}`} data-testid={testId}>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          {eyebrow ? <div className="wp16-kicker mb-1">{eyebrow}</div> : null}
          {title ? <h2 className="wp16-section-title text-xl sm:text-2xl">{title}</h2> : null}
          {description ? <p className="mt-1 text-sm text-zinc-600">{description}</p> : null}
        </div>
        {actions ? <ResponsiveActionRow testid={`${testId}-actions`}>{actions}</ResponsiveActionRow> : null}
      </div>
    </section>
  );
}

export default ActionBar;