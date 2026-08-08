export const TRUTHFUL_DATA_STATE = {
  VALUE: "value",
  LOADING: "loading",
  TRUE_ZERO: "true_zero",
  EMPTY: "empty",
  UNKNOWN: "unknown",
  UNAVAILABLE: "unavailable",
  STALE: "stale",
  NO_ACCESS: "no_access",
  ERROR: "error",
};

function normalizeDisplayValue(value) {
  if (value == null) return "—";
  if (typeof value === "number") return String(value);
  if (typeof value === "string" && value.trim() === "") return "—";
  return String(value);
}

export function getTruthfulValuePresentation({
  value = null,
  isLoading = false,
  isEmpty = false,
  isUnknown = false,
  isUnavailable = false,
  isStale = false,
  hasAccess = true,
  error = null,
  emptyWhenZero = false,
} = {}) {
  if (isLoading) {
    return { state: TRUTHFUL_DATA_STATE.LOADING, displayValue: "—", statusLabel: "Loading", isPlaceholder: true };
  }
  if (hasAccess === false) {
    return { state: TRUTHFUL_DATA_STATE.NO_ACCESS, displayValue: "—", statusLabel: "No access", isPlaceholder: true };
  }
  if (error) {
    return { state: TRUTHFUL_DATA_STATE.ERROR, displayValue: "—", statusLabel: "Error", isPlaceholder: true };
  }
  if (isUnavailable) {
    return { state: TRUTHFUL_DATA_STATE.UNAVAILABLE, displayValue: "—", statusLabel: "Unavailable", isPlaceholder: true };
  }
  if (isUnknown) {
    return { state: TRUTHFUL_DATA_STATE.UNKNOWN, displayValue: "—", statusLabel: "Unknown", isPlaceholder: true };
  }
  if (isStale) {
    return { state: TRUTHFUL_DATA_STATE.STALE, displayValue: "—", statusLabel: "Stale", isPlaceholder: true };
  }
  if (isEmpty || (emptyWhenZero && Number(value) === 0)) {
    return { state: TRUTHFUL_DATA_STATE.EMPTY, displayValue: "—", statusLabel: "Empty", isPlaceholder: true };
  }
  if (Number(value) === 0) {
    return { state: TRUTHFUL_DATA_STATE.TRUE_ZERO, displayValue: "0", statusLabel: "Current value", isPlaceholder: false };
  }
  return {
    state: TRUTHFUL_DATA_STATE.VALUE,
    displayValue: normalizeDisplayValue(value),
    statusLabel: "Current value",
    isPlaceholder: false,
  };
}
