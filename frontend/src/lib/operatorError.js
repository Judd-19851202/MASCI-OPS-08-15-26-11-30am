const DEFAULT_MESSAGE = "Something went wrong. You can approve a manual summary and keep submitting.";

function isPlainObject(value) {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

function looksUnsafe(text) {
  const value = String(text || "").trim();
  return !value || value === "[object Object]" || value.startsWith("{") || value.startsWith("[") || /traceback|exception|token|api[_ -]?key|stack/i.test(value);
}

function firstValidationMessage(detail) {
  if (!Array.isArray(detail) || detail.length === 0) return "";
  const first = detail[0] || {};
  const loc = Array.isArray(first.loc)
    ? first.loc.filter((part) => part !== "body").join(" → ")
    : "";
  const msg = String(first.msg || first.type || "").trim();
  if (!msg) return "";
  return loc ? `${loc}: ${msg}` : msg;
}

function safeMessageFromDetail(detail) {
  if (typeof detail === "string") return looksUnsafe(detail) ? "" : detail.trim();
  if (Array.isArray(detail)) return firstValidationMessage(detail);
  if (isPlainObject(detail)) {
    const candidate = [detail.message, detail.detail, detail.error_description, detail.error]
      .find((value) => typeof value === "string" && value.trim());
    if (typeof candidate === "string" && !looksUnsafe(candidate)) return candidate.trim();
  }
  return "";
}

function classify(detail, error) {
  const code = String(
    error?.code
      || error?.response?.data?.error
      || (isPlainObject(detail) ? detail.error || detail.code : "")
      || ""
  ).trim().toLowerCase();

  if (code.includes("timeout") || error?.code === "ECONNABORTED") return "timeout";
  if (code.includes("network")) return "network_error";
  if (Array.isArray(detail)) return "validation_failed";
  if (code.includes("provider") || code.includes("assist") || code.includes("summary")) return code || "provider_unavailable";
  if (error?.response?.status >= 500) return "server_error";
  if (error?.response?.status >= 400) return "request_failed";
  return code || "unknown_error";
}

export function normalizeOperatorError(error, options = {}) {
  const fallbackMessage = options.fallbackMessage || DEFAULT_MESSAGE;
  const detail = error?.response?.data?.detail ?? error?.response?.data ?? error;
  const safeMessage = safeMessageFromDetail(detail) || safeMessageFromDetail(error?.message) || "";
  const code = classify(detail, error);

  let message = safeMessage;
  if (!message) {
    if (code === "timeout") {
      message = "Summary generation took too long. You can retry or approve a manual summary.";
    } else if (code === "network_error") {
      message = "Connection lost while generating the summary. You can retry or approve a manual summary.";
    } else if (code === "validation_failed") {
      message = "Some report details need attention before the summary can be generated.";
    } else if (code.includes("provider") || code.includes("summary")) {
      message = "Summary assist is unavailable right now. You can approve the generated summary or write a manual summary.";
    } else {
      message = fallbackMessage;
    }
  }

  return {
    message,
    code,
    meta: {
      httpStatus: Number(error?.response?.status || 0) || null,
      detailType: Array.isArray(detail) ? "validation_array" : typeof detail,
    },
  };
}