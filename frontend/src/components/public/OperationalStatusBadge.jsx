import React from "react";

export function OperationalStatusBadge({ children, tone = "default", testId }) {
  return (
    <span
      className={`wp17-status-badge wp17-tone--${tone === "default" ? "slate" : tone}`}
      data-testid={testId}
    >
      {children}
    </span>
  );
}

export default OperationalStatusBadge;