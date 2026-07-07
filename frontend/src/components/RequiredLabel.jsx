// TRACK 24.3 · Shared required-marker label.
//
// Composes a translated label with a red required asterisk. Prevents
// hard-coding `"Field name *"` strings that would otherwise become
// untranslatable JSX composites in Daily Report V3.
//
// Usage:
//   import { RequiredLabel } from "@/components/RequiredLabel";
//   <RequiredLabel label={t("Prepared By")} className="mb-1.5 ..." />
import React from "react";

export function RequiredLabel({ label, className = "", testId }) {
  return (
    <span className={className} data-testid={testId}>
      {label}
      <span className="text-red-600" aria-hidden> *</span>
    </span>
  );
}

export default RequiredLabel;
