// quotaProbe.js — P0 field-incident remediation · 2026-05-27.
//
// Thin wrapper around navigator.storage.estimate(). Returns a
// uniform shape regardless of platform support. Used by the
// telemetry layer and by the autosave hook to surface a quota
// warning to the operator BEFORE the silent QuotaExceededError
// strikes.

const MB = 1024 * 1024;

export async function estimateQuota() {
  try {
    if (
      typeof navigator !== "undefined" &&
      navigator.storage &&
      typeof navigator.storage.estimate === "function"
    ) {
      const r = await navigator.storage.estimate();
      const quota = r.quota || 0;
      const usage = r.usage || 0;
      const free = Math.max(0, quota - usage);
      const ratio = quota > 0 ? usage / quota : null;
      return {
        quotaMb: quota ? +(quota / MB).toFixed(2) : null,
        usageMb: usage ? +(usage / MB).toFixed(2) : null,
        freeMb: quota ? +(free / MB).toFixed(2) : null,
        ratio,
        supported: true,
      };
    }
  } catch { /* fall through */ }
  return { quotaMb: null, usageMb: null, freeMb: null, ratio: null, supported: false };
}
