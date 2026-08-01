import React from "react";
import { useT } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { SemanticIcon } from "@/components/icons/AppIcon";

/**
 * Compact EN / ES segmented toggle. Persists to localStorage via useT().
 * Visible on every form header so a Spanish-speaking crew member can flip
 * the UI without touching submitted data.
 */
export function LangToggle({ className = "", variant = "dark", testId = "lang-toggle" }) {
  const { lang, setLang } = useT();
  const enTestId = `${testId}-en`;
  const esTestId = `${testId}-es`;

  const baseBtn =
    "min-h-[36px] min-w-[36px] inline-flex items-center justify-center px-2.5 py-1 text-[11px] font-mono font-bold uppercase tracking-[0.18em] transition-[background-color,border-color,color,box-shadow] duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400/70 focus-visible:ring-offset-0";
  const dark = {
    wrap: "border-2 border-slate-700 bg-slate-800 text-white",
    active: "bg-red-700 text-white",
    inactive: "text-white/70 hover:text-white",
  };
  const light = {
    wrap: "border-2 border-slate-300 bg-white text-slate-900",
    active: "bg-slate-900 text-white",
    inactive: "text-slate-600 hover:text-slate-900",
  };
  const header = {
    wrap: "wp17-lang-toggle wp17-lang-toggle--header border border-red-500/38 bg-white/8 text-white/90 shadow-[0_10px_22px_rgba(2,6,23,0.18)] ring-1 ring-white/10 backdrop-blur-md",
    active: "bg-red-700 text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.08)]",
    inactive: "text-white/80 hover:bg-white/8 hover:text-white",
  };
  const styles = variant === "light" ? light : variant === "header" ? header : dark;

  return (
    <div
      role="radiogroup"
      aria-label="Select language"
      className={cn(
        variant === "header" ? "inline-flex items-center rounded-full overflow-hidden h-9" : "inline-flex items-center rounded-md overflow-hidden h-10 sm:h-9",
        styles.wrap,
        className
      )}
      data-testid={testId}
    >
      {variant !== "header" ? (
        <span
          className={cn(
            "px-2 inline-flex items-center gap-1 border-r-2 border-current/20 sm:px-1.5",
            variant === "light" ? "border-slate-300" : "border-slate-700"
          )}
          aria-hidden
        >
          <SemanticIcon name="language" size="sm" tone={variant === "light" ? "default" : "inverse"} className="opacity-90" />
        </span>
      ) : null}
      <button
        type="button"
        role="radio"
        aria-checked={lang === "en"}
        onClick={() => setLang("en")}
        className={cn(baseBtn, lang === "en" ? styles.active : styles.inactive)}
        data-testid={enTestId}
      >
        EN
      </button>
      <button
        type="button"
        role="radio"
        aria-checked={lang === "es"}
        onClick={() => setLang("es")}
        className={cn(baseBtn, lang === "es" ? styles.active : styles.inactive)}
        data-testid={esTestId}
      >
        ES
      </button>
    </div>
  );
}
