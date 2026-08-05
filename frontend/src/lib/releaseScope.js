export const RELEASE_DEFERRED_SURFACES = Object.freeze({
  dailyReportDedicatedAiSummary: true,
  executiveMondayBriefingPdf: true,
  pmProjectPerformanceCsvExport: true,
  pmScheduleEmailReview: true,
});

export function isReleaseDeferred(surfaceKey) {
  return Boolean(RELEASE_DEFERRED_SURFACES?.[surfaceKey]);
}
