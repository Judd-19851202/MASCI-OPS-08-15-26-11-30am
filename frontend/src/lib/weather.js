// Open-Meteo free weather (no API key required).
// Provides current forecast + past-7-day historical data via the same
// `forecast` endpoint with past_days param. For older dates we hit the
// `archive-api` endpoint.
//
// TRACK 26.02 · D-04 P1 recovery:
//   Previously we sampled only 06:00 / 12:00 / 16:00 and took the
//   middle-of-day condition as the day's summary. This missed
//   overnight rain that cleared by dawn — leading to reports that
//   said "Clear" when it had rained all night.
//
//   The new logic samples ALL 24 hourly WMO codes for the date and
//   picks the MAX-SEVERITY condition (rain > drizzle > cloudy > clear)
//   for the summary word. Total precipitation is summed across all
//   24 hours. Snapshots surfaced to the UI include midnight (00:00)
//   and 03:00 in addition to the daytime picks so operators can
//   review the overnight signal directly.
//
// API docs: https://open-meteo.com/en/docs

const PICK_HOURS = ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"];

// WMO weather-code severity ordering — higher rank == more severe.
// Used to pick the day's summary word across all 24 hourly samples.
// Reference: https://open-meteo.com/en/docs (WMO Weather interpretation)
const WMO_SEVERITY = {
  0: 0,   // Clear
  1: 1,   // Mainly Clear
  2: 2,   // Partly Cloudy
  3: 3,   // Overcast
  45: 4, 48: 4,                   // Fog
  51: 5, 53: 5, 55: 5,            // Drizzle
  61: 7, 63: 8, 65: 9,            // Rain (light / rain / heavy)
  71: 6, 73: 7, 75: 8,            // Snow (light / snow / heavy)
  77: 5,                          // Snow Grains
  80: 7, 81: 8, 82: 9,            // Showers
  85: 7, 86: 8,                   // Snow Showers
  95: 10, 96: 11, 99: 12,         // Thunderstorm / Hail / Severe
};

function conditionFromCode(code) {
  const map = {
    0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime Fog",
    51: "Light Drizzle", 53: "Drizzle", 55: "Heavy Drizzle",
    61: "Light Rain", 63: "Rain", 65: "Heavy Rain",
    71: "Light Snow", 73: "Snow", 75: "Heavy Snow", 77: "Snow Grains",
    80: "Light Showers", 81: "Showers", 82: "Heavy Showers",
    85: "Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ Hail", 99: "Severe Thunderstorm",
  };
  return map[code] || "—";
}

function isOlderThanForecastWindow(dateStr) {
  const today = new Date();
  const target = new Date(dateStr + "T12:00:00");
  const diffDays = Math.floor((today - target) / (1000 * 60 * 60 * 24));
  return diffDays > 7;
}

/**
 * Fetch weather snapshots for a given lat/lng/date.
 * Returns: {
 *   summary, snapshots: [...], fetched_at_iso, total_precip_in,
 *   max_severity_code, source_hours_sampled, overridden: false
 * }
 *
 * Throws on network error.
 *
 * TRACK 26.02 · D-04: `summary` is now derived from the MAX-SEVERITY
 * hourly WMO code across all 24 hours, and total precipitation is
 * summed. Overnight rain surfaces in `snapshots` at 00:00/03:00.
 */
export async function fetchDailyWeather(lat, lng, dateStr) {
  if (lat == null || lng == null) throw new Error("Missing GPS coordinates");
  const baseUrl = isOlderThanForecastWindow(dateStr)
    ? "https://archive-api.open-meteo.com/v1/archive"
    : "https://api.open-meteo.com/v1/forecast";

  const params = new URLSearchParams({
    latitude: lat,
    longitude: lng,
    hourly: "temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m,weather_code",
    temperature_unit: "fahrenheit",
    wind_speed_unit: "mph",
    precipitation_unit: "inch",
    timezone: "auto",
    start_date: dateStr,
    end_date: dateStr,
  });

  const res = await fetch(`${baseUrl}?${params.toString()}`);
  if (!res.ok) throw new Error(`Weather API error ${res.status}`);
  const data = await res.json();

  const times = data?.hourly?.time || [];
  const temps = data?.hourly?.temperature_2m || [];
  const precs = data?.hourly?.precipitation || [];
  const hums = data?.hourly?.relative_humidity_2m || [];
  const winds = data?.hourly?.wind_speed_10m || [];
  const codes = data?.hourly?.weather_code || [];

  // ── snapshots for the UI (8-hour picks including overnight) ────
  const snapshots = PICK_HOURS.map((hh) => {
    const targetSlice = `${dateStr}T${hh}`;
    let idx = times.findIndex((t) => t.startsWith(targetSlice));
    if (idx < 0) return null;
    return {
      time: hh,
      condition: conditionFromCode(codes[idx]),
      code: codes[idx] ?? null,
      temp_f: temps[idx] != null ? Math.round(temps[idx]) : null,
      precip_in: precs[idx] != null ? Number(precs[idx].toFixed(2)) : 0,
      humidity_pct: hums[idx] != null ? Math.round(hums[idx]) : null,
      wind_mph: winds[idx] != null ? Math.round(winds[idx]) : null,
    };
  }).filter(Boolean);

  // ── summary uses the MAX-SEVERITY code across ALL 24 hours ─────
  let maxSeverity = -1;
  let maxSeverityCode = null;
  let totalPrecip = 0;
  for (let i = 0; i < codes.length; i += 1) {
    const c = codes[i];
    const sev = WMO_SEVERITY[c] ?? -1;
    if (sev > maxSeverity) {
      maxSeverity = sev;
      maxSeverityCode = c;
    }
    if (precs[i] != null) totalPrecip += Number(precs[i]);
  }
  const validTemps = temps.filter((v) => v != null);
  const minT = validTemps.length ? Math.round(Math.min(...validTemps)) : null;
  const maxT = validTemps.length ? Math.round(Math.max(...validTemps)) : null;
  const dominantCondition = maxSeverityCode != null
    ? conditionFromCode(maxSeverityCode)
    : "";
  const precipNote = totalPrecip >= 0.02
    ? ` · ${totalPrecip.toFixed(2)}″ precipitation`
    : "";
  const summary =
    dominantCondition && minT != null && maxT != null
      ? `${dominantCondition}, ${minT}–${maxT}°F${precipNote}`
      : "";

  return {
    summary,
    snapshots,
    fetched_at_iso: new Date().toISOString(),
    total_precip_in: Number(totalPrecip.toFixed(2)),
    max_severity_code: maxSeverityCode,
    source_hours_sampled: codes.length,
    overridden: false,
  };
}
