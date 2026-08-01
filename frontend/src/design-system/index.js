// Track 13.5A · Phase B1 — Design System barrel.
// Re-exports the isolated primitives. NOT consumed by existing portals.
export { PortalShell } from "./PortalShell";
export { PublicShell } from "./PublicShell";
export { StatusChip } from "./StatusChip";
export { Card } from "./Card";
export { EmptyState } from "./EmptyState";
export { DataTable } from "./DataTable";
export { PageHeader } from "./PageHeader";
export {
  STATUS_REGISTRY,
  STATUS_FAMILY,
  SEVERITY_STYLE,
  FORBIDDEN_LABELS,
  lookupStatus,
} from "./statusRegistry";
