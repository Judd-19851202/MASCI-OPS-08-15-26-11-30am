import React from "react";

export function FormField({
  label,
  hint,
  error,
  required = false,
  children,
  className = "",
  "data-testid": testId = "ds-form-field",
}) {
  return (
    <label className={`flex flex-col gap-2 ${className}`} data-testid={testId}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm sm:text-base font-semibold text-zinc-950">{label}</span>
        {required ? <span className="wp16-state-band wp16-state-band--warning" data-testid={`${testId}-required`}>Required</span> : null}
      </div>
      {hint ? <p className="text-xs sm:text-sm text-zinc-600" data-testid={`${testId}-hint`}>{hint}</p> : null}
      {children}
      {error ? (
        <p className="text-xs sm:text-sm font-medium text-red-700" data-testid={`${testId}-error`}>
          {error}
        </p>
      ) : null}
    </label>
  );
}

export default FormField;