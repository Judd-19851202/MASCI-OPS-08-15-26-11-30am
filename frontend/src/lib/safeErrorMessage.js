/**
 * safeErrorMessage(value, fallback)
 * ---------------------------------
 * PROD-FRONTEND-ERROR-001 · Convert any error-shaped value (string,
 * Error, FastAPI/Pydantic validation detail object, validation detail
 * array, undefined) into a guaranteed plain string.
 *
 * Never returns an object. Never returns undefined. Never returns null.
 * Always returns a renderable string safe to drop into a React child
 * or a sonner toast.
 *
 * Examples:
 *   safeErrorMessage("boom")                              → "boom"
 *   safeErrorMessage(new Error("x"))                      → "x"
 *   safeErrorMessage({msg:"field required"})              → "field required"
 *   safeErrorMessage([{msg:"a"},{msg:"b"}])               → "a; b"
 *   safeErrorMessage({detail:[{msg:"x"}]})                → "x"
 *   safeErrorMessage({type:"x",loc:["body"],msg:"x"})     → "x"
 *   safeErrorMessage({unknown:"thing"})                   → fallback
 *   safeErrorMessage(undefined)                           → fallback
 */
export const safeErrorMessage = (v, fallback = "Something went wrong. Please try again.") => {
  if (v == null) return fallback;
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (v instanceof Error) return v.message || fallback;
  // FastAPI shape: { detail: ... } — unwrap once, retry.
  if (typeof v === "object" && "detail" in v) return safeErrorMessage(v.detail, fallback);
  // Pydantic validation detail array.
  if (Array.isArray(v)) {
    const msgs = v
      .map((item) => (item && typeof item === "object" && typeof item.msg === "string" ? item.msg : null))
      .filter(Boolean);
    if (msgs.length) return msgs.join("; ");
    // array of strings
    const strs = v.filter((x) => typeof x === "string");
    if (strs.length) return strs.join("; ");
    return fallback;
  }
  // Pydantic single-detail object.
  if (typeof v === "object" && typeof v.msg === "string") return v.msg;
  if (typeof v === "object" && typeof v.message === "string") return v.message;
  return fallback;
};

export default safeErrorMessage;
