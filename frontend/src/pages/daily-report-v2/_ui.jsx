import React from "react";

/** Reusable section chrome — dark card with title + optional badge. */
export function SectionCard({ id, title, badge, children }) {
  return (
    <section
      id={id}
      data-testid={`dr-v2-section-${id}`}
      className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5 space-y-4"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{title}</h2>
        {badge ? (
          <span
            className="text-xs uppercase tracking-widest rounded-full border border-neutral-700 px-2 py-0.5 opacity-70"
            data-testid={`dr-v2-badge-${id}`}
          >
            {badge}
          </span>
        ) : null}
      </div>
      {children}
    </section>
  );
}

/** Reusable placeholder pane for panels/sections not yet wired. */
export function PlaceholderPane({ testid, note }) {
  return (
    <div
      className="rounded-md border border-dashed border-neutral-700 bg-neutral-950/40 px-4 py-6 text-sm opacity-75"
      data-testid={testid}
    >
      {note}
    </div>
  );
}

export default { SectionCard, PlaceholderPane };
