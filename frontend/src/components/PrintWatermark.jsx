/**
 * PrintWatermark — DEPRECATED, retained as a no-op shim.
 *
 * The diagonal/corner MASCI watermark on printed reports was removed at
 * the user's request (2026-04-29) — clean photos & PDFs make field crews'
 * job easier. The component is kept so existing imports across View pages
 * keep working without ripping every page open. Renders nothing.
 */
export const PrintWatermark = () => null;

export default PrintWatermark;
