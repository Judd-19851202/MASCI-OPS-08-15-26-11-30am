// frontend/lib/resiliency/index.js — Phase J · Field Resiliency.
//
// Barrel export for the shared resiliency infrastructure layer.
// ONE module reused by every form. NO per-form draft store, NO per-
// form retry queue, NO per-endpoint dedup. Same imports everywhere.

export { mintIdempotencyKey } from "./idempotency";
export {
  saveDraft, getDraft, getDraftEntry, discardDraft, clearDraft, purgeStaleDrafts,
  clearAllDraftsForActor, migrateLegacyDrafts, recoverArchivedDraft,
  listDraftEntriesForPrefix, promoteDraftEntry,
  storeIdempotencyKey, getIdempotencyKey, clearIdempotencyKey,
} from "./draftStore";
export { useDraft } from "./useDraft";
export { useDraftSync } from "./useDraftSync";
export {
  useFormDraft, persistIdempotencyKey, loadIdempotencyKey,
} from "./useFormDraft";
export { useOnlineStatus } from "./useOnlineStatus";
export {
  enqueueUpload, getQueueDepth, getQueueItems,
  onQueueChange, onQueueItemSettled, drainQueue, retryAllFailed,
  discardQueueItem, clearQueue,
} from "./resiliencyQueue";
export {
  enqueue as enqueueOffline,
  readQueue as readOfflineQueue,
  clearQueue as clearOfflineQueue,
  replayQueue as replayOfflineQueue,
  getQueueDepth as getOfflineQueueDepth,
  onQueueChange as onOfflineQueueChange,
  registerAutoReplay as registerOfflineAutoReplay,
} from "./offlineQueue";
export {
  markPriorUsage, getPriorUsage, hasStalePriorUsage,
} from "./priorUsage";
export {
  stagePhoto, listStagedFor, listAllStaged, getStagedCount,
  flushStaged, removeStaged, onStagedChange,
} from "./photoStaging";
export {
  storePhotoBlob, getPhotoBlob, getPhotoEntry,
  listPhotoBlobs, discardPhotoBlob, discardPhotoBlobs,
} from "./photoDraftStore";
export { emitDraftEvent, flushDraftTelemetry } from "./draftTelemetry";
export { estimateQuota } from "./quotaProbe";
export {
  DAILY_REPORT_FORM_BASE,
  buildDailyReportInstanceScope,
  buildDailyReportScopedFormKey,
  buildDailyReportTelemetryContext,
} from "./dailyReportScope";
export { default as OfflineIndicator } from "./OfflineIndicator";
export { default as DraftStatusPill } from "./DraftStatusPill";
export { default as DraftRestorePrompt } from "./DraftRestorePrompt";
export { default as DraftRecoveryNotice } from "./DraftRecoveryNotice";
export { default as QuotaWarningChip } from "./QuotaWarningChip";
export { default as PriorUsageBanner } from "./PriorUsageBanner";
export { default as StagedPhotoBadge } from "./StagedPhotoBadge";
export {
  getActorId,
  getDeviceScopedActorId,
  getLegacyActorIds,
  getStableActorIdentity,
} from "./actorId";
export { getDeviceId, ensureDeviceId } from "./deviceId";
