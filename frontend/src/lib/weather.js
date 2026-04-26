// Open-Meteo free weather (no API key required).
// Provides current forecast + past-7-day historical data via the same
// `forecast` endpoint with past_days param. For older dates we hit the
// `archive-api` endpoint.
//
// API docs: https://open-meteo.com/en/docs

const PICK_HOURS = ["06:00", "12:00", "16:00"]; // morning / midday / late-day

function conditionFromCode(code) {
  // WMO weather code → plain text
  // Reference: https://open-meteo.com/en/docs (WMO Weather interpretation codes)
  const map = {
    0: "Clear",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime Fog",
    51: "Light Drizzle",
    53: "Drizzle",
    55: "Heavy Drizzle",
    61: "Light Rain",
    63: "Rain",
    65: "Heavy Rain",
    71: "Light Snow",
    73: "Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Light Showers",
    81: "Showers",
    82: "Heavy Showers",
    85: "Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ Hail",
    99: "Severe Thunderstorm",
  };
  return map[code] || "—";
}

function isOlderThanForecastWindow(dateStr) {
  // Open-Meteo forecast supports past_days up to 92, but we only need recent.
  // Switch to archive-api for anything more than 7 days back.
  const today = new Date();
  const target = new Date(dateStr + "T12:00:00");
  const diffDays = Math.floor((today - target) / (1000 * 60 * 60 * 24));
  return diffDays > 7;
}

/**
 * Fetch weather snapshots (06:00, 12:00, 16:00) for a given lat/lng/date.
 * Returns: { summary, snapshots: [{time, condition, temp_f, precip_in, humidity_pct, wind_mph}] }
 * Throws on network error.
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

  const snapshots = PICK_HOURS.map((hh) => {
    const targetSlice = `${dateStr}T${hh}`;
    let idx = times.findIndex((t) => t.startsWith(targetSlice));
    if (idx < 0) idx = times.findIndex((t) => t.startsWith(dateStr));
    if (idx < 0) return null;
    return {
      time: hh,
      condition: conditionFromCode(codes[idx]),
      temp_f: temps[idx] != null ? Math.round(temps[idx]) : null,
      precip_in: precs[idx] != null ? Number(precs[idx].toFixed(2)) : 0,
      humidity_pct: hums[idx] != null ? Math.round(hums[idx]) : null,
      wind_mph: winds[idx] != null ? Math.round(winds[idx]) : null,
    };
  }).filter(Boolean);

  // Build a one-line summary (worst-of-day condition + temp range)
  const validTemps = snapshots.map((s) => s.temp_f).filter((v) => v != null);
  const minT = validTemps.length ? Math.min(...validTemps) : null;
  const maxT = validTemps.length ? Math.max(...validTemps) : null;
  const conds = snapshots.map((s) => s.condition).filter(Boolean);
  const summary =
    conds.length && minT != null && maxT != null
      ? `${conds[Math.floor(conds.length / 2)]}, ${minT}–${maxT}°F`
      : "";

  return { summary, snapshots };
}
