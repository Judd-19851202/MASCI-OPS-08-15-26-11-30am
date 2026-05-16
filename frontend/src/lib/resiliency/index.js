// frontend/lib/resiliency/index.js — Phase J · Field Resiliency.
//
// Barrel export for the shared resiliency infrastructure layer.
// ONE module reused by every form. NO per-form draft store, NO per-
// form retry queue, NO per-endpoint dedup. Same imports everywhere.

export { mintIdempotencyKey } from "./idempotency";
export {
  saveDraft, getDraft, discardDraft, purgeStaleDrafts,
  clearAllDraftsForActor,
} from "./draftStore";
export { useDraft } from "./useDraft";
export { useOnlineStatus } from "./useOnlineStatus";
export {
  enqueueUpload, getQueueDepth, getQueueItems,
  onQueueChange, drainQueue,
} from "./resiliencyQueue";
export { default as OfflineIndicator } from "./OfflineIndicator";
