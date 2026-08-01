import React from "react";

export function OperationalCoachingStrip({
  blocks = [],
  testId = "operational-coaching-strip",
  className = "",
  columnsClass = "md:grid-cols-2 xl:grid-cols-4",
}) {
  if (!blocks.length) return null;

  return (
    <section
      className={`grid grid-cols-1 gap-3 ${columnsClass} ${className}`.trim()}
      data-testid={testId}
    >
      {blocks.map((block, index) => {
        const Icon = block.icon;
        return (
          <article
            key={block.testId || `${testId}-${index}`}
            className={`wp17-coaching-card wp17-coaching-card--${block.tone || "amber"} p-4`}
            data-testid={block.testId || `${testId}-card-${index}`}
          >
            <div className="flex items-start gap-3">
              {Icon ? (
                <span className="wp17-coaching-card__icon shrink-0">
                  <Icon className="h-4 w-4" />
                </span>
              ) : null}
              <div className="min-w-0">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">
                  {block.label}
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-700">
                  {block.body}
                </p>
              </div>
            </div>
          </article>
        );
      })}
    </section>
  );
}

export default OperationalCoachingStrip;