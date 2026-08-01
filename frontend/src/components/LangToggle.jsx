import React from "react";
import { Languages } from "lucide-react";
import { useT } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/**
 * Compact EN / ES segmented toggle. Persists to localStorage via useT().
 * Visible on every form header so a Spanish-speaking crew member can flip
 * the UI without touching submitted data.
 */
export function LangToggle({ className = "", variant = "dark", testId = "lang-toggle" }) {
  const { lang, setLang } = useT();

  // iter-RC1-FH · M-15 · guarantee a 36 px tap target for the EN/ES
  // segmented toggle. The toggle is rendered in headers across every
  // form/portal — operators in the field often use it with gloves on.
  const baseBtn =
    "min-h-[36px] min-w-[36px] inline-flex items-center justify-center px-2.5 py-1 text-[11px] font-mono font-bold uppercase tracking-wider transition-colors duration-150";
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
    wrap: "border border-white/12 bg-white/6 text-white/80 shadow-[0_8px_18px_rgba(2,6,23,0.16)]",
    active: "bg-white/16 text-white",
    inactive: "text-white/65 hover:text-white",
  };
  const styles = variant === "light" ? light : variant === "header" ? header : dark;

  return (
    <div
      role="radiogroup"
      aria-label="Language"
      className={cn(
        variant === "header" ? "inline-flex items-center rounded-full overflow-hidden h-9" : "inline-flex items-center rounded-md overflow-hidden h-10 sm:h-9",
        styles.wrap,
        className
      )}
      data-testid={testId}
    >
      <span
        className={cn(
          variant === "header" ? "px-2 inline-flex items-center gap-1 border-r border-current/20" : "px-2 inline-flex items-center gap-1 border-r-2 border-current/20 sm:px-1.5",
          variant === "light" ? "border-slate-300" : variant === "header" ? "border-white/14" : "border-slate-700"
        )}
        aria-hidden
      >
        <Languages className={cn("opacity-80", variant === "header" ? "w-3.5 h-3.5" : "w-3 h-3")} />
      </span>
      <button
        type="button"
        role="radio"
        aria-checked={lang === "en"}
        onClick={() => setLang("en")}
        className={cn(baseBtn, lang === "en" ? styles.active : styles.inactive)}
        data-testid="lang-en"
      >
        EN
      </button>
      <button
        type="button"
        role="radio"
        aria-checked={lang === "es"}
        onClick={() => setLang("es")}
        className={cn(baseBtn, lang === "es" ? styles.active : styles.inactive)}
        data-testid="lang-es"
      >
        ES
      </button>
    </div>
  );
}
