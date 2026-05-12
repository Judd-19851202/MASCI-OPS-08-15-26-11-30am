/**
 * resolvePhotoSrc — turn ANY photo reference into a value safe to
 * drop directly into `<img src={...}>`.
 *
 * After the iter64 R2 photo migration (2026-05-11), photos that used
 * to be stored in Mongo as base64 `data:image/...` URLs are now stored
 * as `photo://masci-hub/photos/...` references. The browser can render
 * `data:` URLs natively but has no idea what to do with `photo://`, so
 * record-detail pages started showing blank squares.
 *
 * Three branches:
 *   1. `data:` URL  → pass-through unchanged (legacy records — browser
 *      can render this natively, no round-trip needed).
 *   2. `photo://`   → rewrite to the backend resolver endpoint
 *      `${REACT_APP_BACKEND_URL}/api/photo-bytes?ref=…` which fetches
 *      the bytes from Cloudflare R2 and returns them as a normal
 *      image response (1-year immutable cache).
 *   3. Anything else (http URLs, blob:, null, undefined, "") → pass
 *      through so we don't break legitimate non-photo:// values.
 *
 * Why a backend resolver instead of a Cloudflare presigned URL?
 *   - Presigned URLs would mean ONE extra round-trip per photo to mint
 *     the URL — a daily report with 30 photos is 30 extra requests.
 *   - The resolver endpoint is a single GET that streams bytes; the
 *     1-year immutable cache header means the browser only ever fetches
 *     each photo once.
 *   - Presigned URLs leak the R2 endpoint to every client; this hides it.
 *
 * Used by: ViewDailyReport, ViewMeeting, ViewInspection, ViewIncident,
 * ViewQaqcInspection, ViewEquipmentInspection, ViewSafetyForm,
 * FieldLeadershipView, PhotoUpload (preview tile).
 */
const API_BASE =
  (typeof process !== "undefined" && process.env && process.env.REACT_APP_BACKEND_URL) || "";

export function resolvePhotoSrc(ref) {
  if (!ref || typeof ref !== "string") return ref || "";
  if (ref.startsWith("data:")) return ref;
  if (ref.startsWith("photo://")) {
    return `${API_BASE}/api/photo-bytes?ref=${encodeURIComponent(ref)}`;
  }
  // http(s), blob:, file:, anything else — leave alone.
  return ref;
}
