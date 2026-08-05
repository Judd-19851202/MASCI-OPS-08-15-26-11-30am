export const RELEASE_DEFERRED_SURFACES = Object.freeze({
  executiveMondayBriefingPdf: true,
  pmProjectPerformanceCsvExport: true,
  pmScheduleEmailReview: true,
});

export function isReleaseDeferred(surfaceKey) {
  return Boolean(RELEASE_DEFERRED_SURFACES?.[surfaceKey]);
}
