import React, { useId, useMemo, useState } from "react";
import { ChevronDown, ChevronUp, Compass } from "lucide-react";
import { useT } from "@/lib/i18n";
import { sanitizeOperatorCopy } from "@/lib/operatorLanguage";

const TONE_STYLES = {
  amber: "border-amber-200 bg-amber-50/70 text-amber-950",
  sky: "border-sky-200 bg-sky-50/70 text-sky-950",
  emerald: "border-emerald-200 bg-emerald-50/70 text-emerald-950",
  slate: "border-slate-200 bg-slate-50/90 text-slate-950",
  rose: "border-rose-200 bg-rose-50/70 text-rose-950",
};

const resolveCopy = (value) => {
  if (typeof value !== "string") return value;
  return sanitizeOperatorCopy(value, value);
};

export function WorkflowCoachingDisclosure({
  blocks = [],
  title,
  eyebrow,
  description,
  icon: TriggerIcon = Compass,
  testIdPrefix = "workflow-coaching",
  className = "",
  defaultOpen = false,
  storageKey,
  open,
  onOpenChange,
  collapsedCounterLabel,
  containerTestId,
  triggerTestId,
  panelTestId,
  counterTestId,
}) {
  const { t } = useT();
  const panelId = useId();
  const visibleBlocks = useMemo(
    () => blocks.filter((block) => block && (block.body || block.label)),
    [blocks],
  );

  const [internalOpen, setInternalOpen] = useState(() => {
    if (!storageKey || typeof window === "undefined") return defaultOpen;
    try {
      const stored = window.localStorage.getItem(storageKey);
      return stored === null ? defaultOpen : stored === "1";
    } catch {
      return defaultOpen;
    }
  });

  if (!visibleBlocks.length) return null;

  const isControlled = typeof open === "boolean";
  const isOpen = isControlled ? open : internalOpen;

  const setExpanded = (next) => {
    if (!isControlled) setInternalOpen(next);
    if (storageKey && typeof window !== "undefined") {
      try {
        window.localStorage.setItem(storageKey, next ? "1" : "0");
      } catch {
        /* ignore storage unavailability */
      }
    }
    onOpenChange?.(next);
  };

  const headerTitle = resolveCopy(title) || t("Workflow tips");
  const headerEyebrow = resolveCopy(eyebrow);
  const helperCopy = collapsedCounterLabel
    || `${visibleBlocks.length} ${t("workflow tips available · tap to expand")}`;

  return (
    <section
      className={`rounded-2xl border border-slate-200 bg-white shadow-[0_16px_40px_rgba(15,23,42,0.05)] ${className}`.trim()}
      data-testid={containerTestId || testIdPrefix}
    >
      <button
        type="button"
        onClick={() => setExpanded(!isOpen)}
        className="flex min-h-[56px] w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50/80"
        data-testid={triggerTestId || `${testIdPrefix}-trigger`}
        aria-expanded={isOpen}
        aria-controls={`${panelId}-panel`}
      >
        <span className="mt-0.5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-900 text-white">
          <TriggerIcon className="h-4 w-4" />
        </span>

        <span className="min-w-0 flex-1">
          {isOpen ? (
            <>
              {headerEyebrow ? (
                <span className="block font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold">
                  {headerEyebrow}
                </span>
              ) : null}
              <span className="mt-0.5 block font-display text-lg font-black tracking-tight text-slate-900">
                {headerTitle}
              </span>
              {description ? (
                <span className="mt-1 block max-w-3xl text-sm leading-6 text-slate-600">
                  {resolveCopy(description)}
                </span>
              ) : null}
            </>
          ) : (
            <span
              className="block pt-1 font-mono text-[11px] uppercase tracking-[0.18em] text-slate-600"
              data-testid={counterTestId || `${testIdPrefix}-counter`}
            >
              {helperCopy}
            </span>
          )}
        </span>

        <span className="mt-1 shrink-0 text-slate-400">
          {isOpen ? (
            <ChevronUp className="h-5 w-5" data-testid={`${testIdPrefix}-icon-open`} />
          ) : (
            <ChevronDown className="h-5 w-5" data-testid={`${testIdPrefix}-icon-closed`} />
          )}
        </span>
      </button>

      {isOpen ? (
        <div
          id={`${panelId}-panel`}
          className="border-t border-slate-200 px-4 pb-4 pt-3"
          data-testid={panelTestId || `${testIdPrefix}-panel`}
        >
          <div className="space-y-3">
            {visibleBlocks.map((block, index) => {
              const BlockIcon = block.icon;
              const label = resolveCopy(block.label);
              const body = resolveCopy(block.body);
              const toneClass = TONE_STYLES[block.tone] || TONE_STYLES.slate;
              const blockKey = block.testId || `${testIdPrefix}-block-${index}`;
              return (
                <article
                  key={blockKey}
                  className={`rounded-2xl border px-4 py-3 ${toneClass}`}
                  data-testid={blockKey}
                >
                  <div className="flex items-start gap-3">
                    {BlockIcon ? (
                      <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/80 text-slate-700">
                        <BlockIcon className="h-4 w-4" />
                      </span>
                    ) : null}
                    <div className="min-w-0 flex-1">
                      {label ? (
                        <div className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold text-slate-600">
                          {label}
                        </div>
                      ) : null}
                      <div className={`${label ? "mt-2" : ""} text-sm leading-6 text-slate-700`}>
                        {body}
                      </div>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      ) : null}
    </section>
  );
}

export default WorkflowCoachingDisclosure;