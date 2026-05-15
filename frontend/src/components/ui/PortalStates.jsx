// PortalStates — Iter136. Unified empty / loading / error state
// components. Replaces the ad-hoc "italic gray text + dashed border"
// pattern that varied across portals.
//
// Usage:
//   <EmptyState icon={Inbox} title="No incidents" body="When the field…">
//   <LoadingState label="Loading guides…">
//   <ErrorState message="Could not load. Check your connection.">
//
// All three accept optional action prop for a CTA button.
import React from "react";
import { Loader2, AlertTriangle, Inbox } from "lucide-react";

export function EmptyState({ icon: Icon = Inbox, title, body, action, testId = "ux-empty" }) {
  return (
    <div className="ux-empty" data-testid={testId} role="status">
      <Icon className="ux-empty-icon w-10 h-10" aria-hidden="true" />
      {title && <div className="ux-empty-title">{title}</div>}
      {body && <p className="ux-empty-body">{body}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}

export function LoadingState({ label = "Loading…", testId = "ux-loading" }) {
  return (
    <div className="ux-loading" data-testid={testId} role="status" aria-live="polite">
      <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-slate-400" aria-hidden="true" />
      <div className="text-slate-500 text-sm">{label}</div>
    </div>
  );
}

export function ErrorState({
  message = "Something went wrong.",
  detail = "",
  action,
  testId = "ux-error",
}) {
  return (
    <div className="ux-error flex items-start gap-2" data-testid={testId} role="alert">
      <AlertTriangle className="w-5 h-5 mt-0.5 shrink-0" aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <div className="font-bold">{message}</div>
        {detail && <div className="text-xs mt-1 opacity-80">{detail}</div>}
        {action && <div className="mt-2">{action}</div>}
      </div>
    </div>
  );
}

export default { EmptyState, LoadingState, ErrorState };
