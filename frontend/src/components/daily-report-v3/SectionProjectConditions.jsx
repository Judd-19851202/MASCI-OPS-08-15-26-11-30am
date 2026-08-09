// TRACK 23.1 · V3 Section 01 · Project + Conditions
//
// Elite section shell — dropdown-first, GPS + weather auto-fill,
// zero coaching clutter. Composes JobPicker + FlUserCombo. Same
// payload keys as V1 so the submit contract is untouched.
import React from "react";
import { JobPicker } from "@/components/JobPicker";
import { FlUserCombo } from "@/components/FlUserCombo";
import { Button } from "@/components/ui/button";
import { MapPin, Cloud, CalendarClock } from "lucide-react";
import { useT } from "@/lib/i18n";
import { RequiredLabel } from "@/components/RequiredLabel";
import { findJob } from "@/lib/jobLibrary";

export function SectionProjectConditions({
  data,
  patch,
  onUseGps,
  onRefreshWeather,
  isFetchingGps,
  isFetchingWeather,
  weatherLabel,
  reportNumberPreview,
}) {
  const { t } = useT();
  const [manualProjectMode, setManualProjectMode] = React.useState(false);
  const hasKnownProject = React.useMemo(
    () => Boolean(findJob(data.project_number || "")),
    [data.project_number],
  );

  React.useEffect(() => {
    if ((data.project_name || data.project_number) && !hasKnownProject) {
      setManualProjectMode(true);
    }
  }, [data.project_name, data.project_number, hasKnownProject]);

  const showManualProjectFields = manualProjectMode && !hasKnownProject;

  return (
    <section
      data-testid="dr-v3-section-project"
      className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm"
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600">
            {t("Step 1 · Where were we?")}
          </p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">
            {t("Project & Conditions")}
          </h2>
        </div>
        {reportNumberPreview && (
          <span
            data-testid="dr-v3-report-number-preview"
            className="hidden rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 sm:inline-flex"
          >
            {reportNumberPreview}
          </span>
        )}
      </header>

      <div className="space-y-4">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">
            <RequiredLabel label={t("Current Job")} />
          </label>
          <JobPicker
            projectNumber={data.project_number}
            projectName={data.project_name}
            publicFallback
            onSelect={(job) => {
              // TRACK 24.9 Phase C · Full project-context commit.
              //
              // Capture the metadata snapshot the field crew relies
              // on (client / PM / co-PMs) at select-time so PDF
              // headers and downstream consumers have a truthful
              // record of what the operator saw when they picked.
              // Empty string / [] when jobs_master has no value
              // for that field — no fabrication, honest fallback.
              // The `location` merge keeps a hand-typed location
              // when the jobs_master row lacks one.
              if (!job) {
                setManualProjectMode(true);
                patch({
                  project_number: "",
                  project_name: "",
                  client: "",
                  project_manager: "",
                  pm_email: "",
                  co_pm_emails: [],
                });
                return;
              }
              setManualProjectMode(false);
              patch({
                project_number: job?.project_number || "",
                project_name: job?.project_name || "",
                location: job?.location || data.location,
                client: job?.client || "",
                project_manager: job?.project_manager || "",
                pm_email: job?.pm_email || "",
                co_pm_emails: Array.isArray(job?.co_pm_emails)
                  ? job.co_pm_emails.filter(Boolean)
                  : [],
              });
            }}
            data-testid="dr-v3-job-picker"
          />
          {showManualProjectFields ? (
            <div
              className="mt-3 rounded-lg border border-amber-200 bg-amber-50/70 p-3"
              data-testid="dr-v3-custom-job-fields"
            >
              <div className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-amber-800">
                {t("Custom Job")}
              </div>
              <p className="mb-3 text-xs text-amber-900">
                {t("Enter the project number and name exactly as you want them saved in this draft.")}
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-700">
                    <RequiredLabel label={t("Project Number")} />
                  </label>
                  <input
                    type="text"
                    value={data.project_number || ""}
                    onChange={(e) => patch({ project_number: e.target.value })}
                    placeholder={t("e.g. LIVE-AI-DRY-RUN-NO-SUBMIT")}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                    data-testid="dr-v3-custom-project-number"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-700">
                    <RequiredLabel label={t("Project Name")} />
                  </label>
                  <input
                    type="text"
                    value={data.project_name || ""}
                    onChange={(e) => patch({ project_name: e.target.value })}
                    placeholder={t("e.g. Live AI Dry Run No Submit")}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                    data-testid="dr-v3-custom-project-name"
                  />
                </div>
              </div>
            </div>
          ) : null}
          {/* TRACK 24.9 Phase C · Project metadata card.
              Shows the client / PM / co-PM context AFTER project
              select so the field foreman can visually confirm the
              right project was picked. Only renders once a project
              is bound so anonymous-form blank-state stays clean. */}
          {data.project_number && (
            <div
              data-testid="dr-v3-project-meta"
              className="mt-3 rounded-lg border border-emerald-100 bg-emerald-50/60 px-3 py-2 text-xs text-emerald-900 grid gap-1 sm:grid-cols-2"
            >
              <div>
                <span className="font-semibold uppercase tracking-wide text-[10px] text-emerald-700">{t("Client")}: </span>
                <span data-testid="dr-v3-project-meta-client">
                  {data.client || <em className="text-emerald-700/70">{t("Not set")}</em>}
                </span>
              </div>
              <div>
                <span className="font-semibold uppercase tracking-wide text-[10px] text-emerald-700">{t("PM")}: </span>
                <span data-testid="dr-v3-project-meta-pm">
                  {data.project_manager || data.pm_email || <em className="text-emerald-700/70">{t("Not set")}</em>}
                </span>
              </div>
              {(data.co_pm_emails || []).length > 0 && (
                <div className="sm:col-span-2">
                  <span className="font-semibold uppercase tracking-wide text-[10px] text-emerald-700">{t("Co-PMs")}: </span>
                  <span data-testid="dr-v3-project-meta-co-pms">
                    {(data.co_pm_emails || []).join(", ")}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              <RequiredLabel label={t("Location")} />
            </label>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <input
                data-testid="dr-v3-location"
                type="text"
                value={data.location || ""}
                onChange={(e) => {
                  const newLocation = e.target.value;
                  // TRACK 26.14 · Set location_source to "manual" when user types
                  // a location manually. This satisfies the location_source
                  // readiness requirement without requiring GPS.
                  const patchData = { location: newLocation };
                  if (newLocation.trim() && !data.location_source) {
                    patchData.location_source = "manual";
                  }
                  patch(patchData);
                }}
                placeholder={t("e.g. Sta 12+50 · North side")}
                spellCheck
                className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-sm placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onUseGps}
                disabled={isFetchingGps}
                data-testid="dr-v3-use-gps-btn"
                className="w-full shrink-0 sm:w-auto"
              >
                <MapPin className="mr-1.5 h-4 w-4" />
                {isFetchingGps ? t("Locating…") : t("Use My Location")}
              </Button>
            </div>
            <div className="mt-2 text-xs text-slate-600" data-testid="dr-v3-location-status">
              {isFetchingGps
                ? t("Locating…")
                : data.location_capture_result === "failed"
                  ? (data.location_error_code === "PREVIEW_IFRAME_PERMISSION_BLOCK"
                    ? t("Embedded preview blocked location access. Open the preview in a new tab to test GPS.")
                    : (data.location_error_message || t("Location capture failed.")))
                  : data.location_source === "device_gps"
                    ? t("Location captured")
                    : data.location_source === "project_coordinates"
                      ? t("Using verified project coordinates")
                      : data.location_source === "saved_draft_location"
                        ? t("Using saved draft location")
                        : data.location_source === "manual"
                          ? t("Using manual location")
                          : t("Tap Use My Location or enter a verified location.")}
            </div>
            {data.gps_lat != null && data.gps_lng != null && (
              <div className="mt-1 text-[11px] text-slate-500" data-testid="dr-v3-location-coords-summary">
                {t("Source")}: {data.location_source || "—"} · {Number(data.gps_lat).toFixed(5)}, {Number(data.gps_lng).toFixed(5)}
                {data.gps_accuracy != null ? ` · ±${Math.round(data.gps_accuracy)} m` : ""}
              </div>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              <RequiredLabel label={t("Date")} />
            </label>
            <input
              data-testid="dr-v3-report-date"
              type="date"
              value={data.report_date || ""}
              onChange={(e) => patch({ report_date: e.target.value })}
              spellCheck={false}
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              <RequiredLabel label={t("Prepared By")} />
            </label>
            <FlUserCombo
              value={data.prepared_by || ""}
              onChange={(v) => patch({ prepared_by: v })}
              placeholder={t("Field supervisor")}
              testId="dr-v3-prepared-by"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              {t("Superintendent")}
            </label>
            <FlUserCombo
              value={data.superintendent || ""}
              onChange={(v) => patch({ superintendent: v })}
              placeholder={t("Optional")}
              testId="dr-v3-superintendent"
            />
          </div>
        </div>

        <div
          data-testid="dr-v3-weather-block"
          className="mt-2 flex items-center justify-between rounded-xl border border-sky-100 bg-sky-50 px-4 py-3"
        >
          <div className="flex items-center gap-3">
            <Cloud className="h-5 w-5 text-sky-600" />
            <div className="text-sm text-sky-900">
              <div className="font-medium">
                {data.weather_summary || t("Weather not captured yet")}
              </div>
              <div className="text-xs text-sky-700">
                {weatherLabel || t("Tap Use My Location to refresh weather from verified coordinates.")}
              </div>
              {data.weather_snapshot_meta?.gps_lat != null && data.weather_snapshot_meta?.gps_lng != null && (
                <div className="mt-1 text-[11px] text-sky-700" data-testid="dr-v3-weather-coord-summary">
                  {t("Weather source")}: {data.weather_snapshot_meta?.provider || data.weather_snapshot_meta?.source || "—"} ·
                  {` ${Number(data.weather_snapshot_meta.gps_lat).toFixed(5)}, ${Number(data.weather_snapshot_meta.gps_lng).toFixed(5)}`}
                  {data.weather_snapshot_meta?.timezone ? ` · ${data.weather_snapshot_meta.timezone}` : ""}
                </div>
              )}
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onRefreshWeather}
            disabled={isFetchingWeather || !data.gps_lat}
            data-testid="dr-v3-refresh-weather-btn"
            className="text-sky-700 hover:bg-sky-100"
          >
            <CalendarClock className="mr-1.5 h-4 w-4" />
            {isFetchingWeather ? "…" : t("Refresh")}
          </Button>
        </div>
      </div>
    </section>
  );
}
