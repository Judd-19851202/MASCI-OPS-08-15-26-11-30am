// idempotency.js — generates uuid v4 for the Idempotency-Key header.
// Standalone helper; backend `lib/idempotency.py` consumes the value.

export function mintIdempotencyKey() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // Fallback (older Safari/iOS WebView). RFC 4122 v4.
  const r = (n) => Math.floor(Math.random() * (n + 1));
  const hex = (b) => b.toString(16).padStart(2, "0");
  const bytes = new Array(16).fill(0).map(() => r(255));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const h = bytes.map(hex).join("");
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}
