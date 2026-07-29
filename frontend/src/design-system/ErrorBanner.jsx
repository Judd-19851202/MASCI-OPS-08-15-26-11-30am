import React from "react";
import { PlatformIcon } from "./icons";

const STYLES = {
  info: "wp16-state-band--info",
  warning: "wp16-state-band--warning",
  danger: "wp16-state-band--danger",
};

export function ErrorBanner({
  title,
  message,
  nextStep,
  tone = "danger",
  className = "",
  "data-testid": testId = "ds-error-banner",
}) {
  return (
    <section className={`wp16-card border-l-4 p-4 ${className}`} data-testid={testId} style={{ borderLeftColor: tone === "warning" ? "var(--wp16-warning)" : tone === "info" ? "var(--wp16-info)" : "var(--wp16-danger)" }}>
      <div className="flex items-start gap-3">
        <span className={`wp16-state-band ${STYLES[tone] || STYLES.danger}`} data-testid={`${testId}-tone`}>
          <PlatformIcon name={tone === "info" ? "review" : tone === "warning" ? "clock" : "shield-alert"} className="h-3.5 w-3.5" />
          {tone === "info" ? "Heads up" : tone === "warning" ? "Needs attention" : "Action needed"}
        </span>
      </div>
      <h3 className="mt-3 wp16-section-title text-lg">{title}</h3>
      {message ? <p className="mt-1 text-sm text-zinc-700">{message}</p> : null}
      {nextStep ? <p className="mt-2 text-sm font-medium text-zinc-950">Next: {nextStep}</p> : null}
    </section>
  );
}

export default ErrorBanner;