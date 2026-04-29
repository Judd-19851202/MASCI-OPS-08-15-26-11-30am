/**
 * formatApiError(err, fallback)
 * -----------------------------
 * Turn an axios error into a human-friendly message that distinguishes
 * cold-start, 5xx, timeout, and network failures from the generic
 * "save failed" — so field crews never see "Could not save daily report"
 * when the actual cause is a 60s Atlas warm-up after deploy.
 *
 * Returns a plain string, ready to drop into toast.error(...).
 *
 * Use:
 *   import { formatApiError } from "@/lib/apiErrors";
 *   try { await api.post(...) } catch (e) {
 *     toast.error(formatApiError(e, "Could not save daily report"));
 *   }
 */
export const formatApiError = (err, fallback = "Something went wrong") => {
  if (!err) return fallback;
  const status = err?.response?.status;

  // 401 — auth dropped (token expired)
  if (status === 401) return "Your session expired — please sign in again";
  // 403
  if (status === 403) return "You don't have permission to do that";
  // 404
  if (status === 404) return "The record was not found";
  // 422 — backend validation error; surface the detail when present
  if (status === 422) {
    const detail = err?.response?.data?.detail;
    if (Array.isArray(detail) && detail[0]?.msg) {
      return `Validation error: ${detail[0].msg}`;
    }
    if (typeof detail === "string") return `Validation error: ${detail}`;
    return "Validation error — check your input";
  }
  // Cloudflare edge errors → backend cold-booting on Atlas
  if (status >= 520 && status <= 524) {
    return "Server is waking up — wait ~60 seconds and try again. Your form data is safe.";
  }
  // Other 5xx
  if (status >= 500 && status < 600) {
    return `Server error (${status}) — try again in a moment. Your form data is safe.`;
  }
  // Other 4xx — surface the backend's detail when present
  if (status >= 400 && status < 500) {
    const d = err?.response?.data?.detail || err?.response?.data?.message;
    if (typeof d === "string") return d;
    return `${fallback} (${status})`;
  }
  // Axios timeout (server didn't reply within axios's deadline)
  if (err?.code === "ECONNABORTED" || /timeout/i.test(err?.message || "")) {
    return "Request timed out — server may be cold-starting. Try again. Your form data is safe.";
  }
  // No response object at all → can't reach origin
  if (!err?.response) {
    return "Can't reach the server — check your internet, then try again. Your form data is safe.";
  }
  return fallback;
};

export default formatApiError;
