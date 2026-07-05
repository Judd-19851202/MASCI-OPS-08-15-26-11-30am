import React from "react";
import { Section } from "@/components/Section";
import { JobPicker } from "@/components/JobPicker";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { MapPin, CloudSun, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getCurrentPosition, reverseGeocode, formatCoords } from "@/lib/geolocation";
import { fetchDailyWeather } from "@/lib/weather";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2";

/**
 * DR-ROI-001F-REPAIR · Day Setup — wired to the existing platform data.
 * Uses V1's Section grammar + JobPicker + weather + GPS hooks. No mocks.
 */
export default function DaySetupSection({ draft, setDraft }) {
  const setup = draft.day_setup || {};
  const set = (k, v) =>
    setDraft((d) => ({ ...d, day_setup: { ...(d.day_setup || {}), [k]: v } }));
  const [busy, setBusy] = React.useState({});

  const pickGPS = async () => {
    try {
      setBusy((b) => ({ ...b, gps: true }));
      const pos = await getCurrentPosition();
      const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      set("gps", coords);
      const label = await reverseGeocode(coords.lat, coords.lng);
      if (label) set("location_label", label);
    } finally {
      setBusy((b) => ({ ...b, gps: false }));
    }
  };
  const pickWeather = async () => {
    try {
      setBusy((b) => ({ ...b, weather: true }));
      const w = await fetchDailyWeather(setup.date, setup.gps?.lat, setup.gps?.lng);
      if (w) setDraft((d) => ({ ...d, weather: w }));
    } finally {
      setBusy((b) => ({ ...b, weather: false }));
    }
  };

  return (
    <Section number="01" title="Day Setup" testId="dr-v2-section-day-setup">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        <div className="lg:col-span-2">
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">Project</Label>
          <JobPicker
            projectName={setup.project_name || ""}
            projectNumber={setup.project_number || ""}
            onSelect={(job) => {
              set("project_name", job?.project_name || "");
              set("project_number", job?.project_number || "");
            }}
          />
        </div>
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">Report date</Label>
          <Input
            type="date"
            value={setup.date || ""}
            onChange={(e) => set("date", e.target.value)}
            className={inputCls}
            data-testid="dr-v2-daysetup-date"
          />
        </div>
        <div>
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">Shift</Label>
          <select
            value={setup.shift || "day"}
            onChange={(e) => set("shift", e.target.value)}
            className={inputCls + " w-full rounded-md bg-white"}
            data-testid="dr-v2-daysetup-shift"
          >
            <option value="day">Day</option>
            <option value="night">Night</option>
            <option value="weekend">Weekend</option>
          </select>
        </div>
        <div className="lg:col-span-2">
          <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">Supervisor / Prepared by</Label>
          <Input
            value={setup.supervisor || ""}
            onChange={(e) => set("supervisor", e.target.value)}
            className={inputCls}
            placeholder="Full name"
            data-testid="dr-v2-daysetup-supervisor"
          />
        </div>
        <div className="lg:col-span-2 flex flex-wrap gap-2 items-end">
          <Button
            type="button"
            variant="outline"
            onClick={pickGPS}
            disabled={busy.gps}
            data-testid="dr-v2-daysetup-gps"
            className="border-2 border-slate-300 h-11"
          >
            {busy.gps ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <MapPin className="w-4 h-4 mr-1" />}
            Capture GPS
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={pickWeather}
            disabled={busy.weather}
            data-testid="dr-v2-daysetup-weather"
            className="border-2 border-slate-300 h-11"
          >
            {busy.weather ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <CloudSun className="w-4 h-4 mr-1" />}
            Fetch weather
          </Button>
          {setup.gps ? (
            <span className="text-xs font-mono text-slate-600">{formatCoords(setup.gps.lat, setup.gps.lng)}</span>
          ) : null}
        </div>
      </div>
    </Section>
  );
}
