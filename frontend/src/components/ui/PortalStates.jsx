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
import { Loader2, AlertTriangle, Inbox, ShieldCheck, TriangleAlert } from "lucide-react";
import { AppIcon } from "@/components/icons/AppIcon";

function StateSurface({ icon, title, body, action, tone = "slate", testId = "ux-state", role = "status", busy = false }) {
  return (
    <div
      className={`wp17-state-surface wp17-tone--${tone}`}
      data-testid={testId}
      role={role}
      aria-live={busy ? "polite" : undefined}
    >
      <span className="wp17-state-surface__icon" aria-hidden="true">
        <AppIcon icon={icon} size="lg" tone="default" />
      </span>
      {title ? <div className="wp17-state-surface__title">{title}</div> : null}
      {body ? <p className="wp17-state-surface__body">{body}</p> : null}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}

export function EmptyState({ icon: Icon = Inbox, title, body, action, testId = "ux-empty" }) {
  return <StateSurface icon={Icon} title={title} body={body} action={action} tone="slate" testId={testId} />;
}

export function LoadingState({ label = "Loading…", testId = "ux-loading" }) {
  return <StateSurface icon={Loader2} title={label} tone="cyan" testId={testId} busy />;
}

export function ErrorState({
  message = "Something went wrong.",
  detail = "",
  action,
  testId = "ux-error",
}) {
  return <StateSurface icon={AlertTriangle} title={message} body={detail} action={action} tone="red" testId={testId} role="alert" />;
}

export function SuccessState({ title = "Complete", body = "The latest update is ready.", action, testId = "ux-success" }) {
  return <StateSurface icon={ShieldCheck} title={title} body={body} action={action} tone="emerald" testId={testId} />;
}

export function WarningState({ title = "Needs attention", body = "Review this item before you continue.", action, testId = "ux-warning" }) {
  return <StateSurface icon={TriangleAlert} title={title} body={body} action={action} tone="amber" testId={testId} />;
}

export default { EmptyState, LoadingState, ErrorState, SuccessState, WarningState };
