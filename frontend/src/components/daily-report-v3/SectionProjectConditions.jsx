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
  return (
    <section
      data-testid="dr-v3-section-project"
      className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm"
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600">
            Step 1 · Where were we?
          </p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">
            Project &amp; Conditions
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
            MASCI Job *
          </label>
          <JobPicker
            value={data.project_number}
            onChange={(job) => {
              patch({
                project_number: job?.project_number || "",
                project_name: job?.project_name || "",
                location: job?.location || data.location,
              });
            }}
            data-testid="dr-v3-job-picker"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Location *
            </label>
            <div className="flex items-center gap-2">
              <input
                data-testid="dr-v3-location"
                type="text"
                value={data.location || ""}
                onChange={(e) => patch({ location: e.target.value })}
                placeholder="e.g. Sta 12+50 · North side"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-sm placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onUseGps}
                disabled={isFetchingGps}
                data-testid="dr-v3-use-gps-btn"
                className="shrink-0"
              >
                <MapPin className="mr-1.5 h-4 w-4" />
                {isFetchingGps ? "…" : "GPS"}
              </Button>
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Date *
            </label>
            <input
              data-testid="dr-v3-report-date"
              type="date"
              value={data.report_date || ""}
              onChange={(e) => patch({ report_date: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Prepared By *
            </label>
            <FlUserCombo
              value={data.prepared_by || ""}
              onChange={(v) => patch({ prepared_by: v })}
              placeholder="Field supervisor"
              data-testid="dr-v3-prepared-by"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Superintendent
            </label>
            <FlUserCombo
              value={data.superintendent || ""}
              onChange={(v) => patch({ superintendent: v })}
              placeholder="Optional"
              data-testid="dr-v3-superintendent"
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
                {data.weather_summary || "Weather not captured yet"}
              </div>
              <div className="text-xs text-sky-700">{weatherLabel || "Tap GPS to auto-fill weather."}</div>
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
            {isFetchingWeather ? "…" : "Refresh"}
          </Button>
        </div>
      </div>
    </section>
  );
}
