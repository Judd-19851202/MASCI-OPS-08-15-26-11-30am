"""Open-Meteo weather helpers for operational forms and Daily Reports."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx


_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


# WMO codes → concise English description.
_WMO_CODES: Dict[int, str] = {
    0: "Clear",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Light rain showers", 81: "Rain showers", 82: "Violent showers",
    85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Severe thunderstorm w/ hail",
}


def _describe(code: Optional[int]) -> str:
    if code is None:
        return ""
    try:
        return _WMO_CODES.get(int(code), "")
    except Exception:
        return ""


async def fetch_current_weather(lat: float, lng: float) -> Dict[str, Any]:
    """Fetch current conditions from Open-Meteo. Free, no key required."""
    params = {
        "latitude":  f"{float(lat):.5f}",
        "longitude": f"{float(lng):.5f}",
        "current": ("temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "precipitation,rain,weather_code,wind_speed_10m,"
                    "wind_direction_10m,wind_gusts_10m"),
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=6.0) as client:
        resp = await client.get(_WEATHER_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    cur = data.get("current") or {}
    code = cur.get("weather_code")
    description = _describe(code)
    return {
        "provider":            "open-meteo",
        "observed_at":         cur.get("time") or "",
        "timezone":            data.get("timezone") or "",
        "description":         description,
        "weather_code":        code,
        "temperature_f":       cur.get("temperature_2m"),
        "apparent_temperature_f": cur.get("apparent_temperature"),
        "relative_humidity":   cur.get("relative_humidity_2m"),
        "precipitation_in":    cur.get("precipitation"),
        "rain_in":             cur.get("rain"),
        "wind_speed_mph":      cur.get("wind_speed_10m"),
        "wind_direction":      cur.get("wind_direction_10m"),
        "wind_gusts_mph":      cur.get("wind_gusts_10m"),
        # Ready-to-paste one-liner for the FieldBlock.weather string.
        "summary":             _summary(description,
                                        cur.get("temperature_2m"),
                                        cur.get("wind_speed_10m")),
    }


def _summary(desc: str, temp_f: Any, wind_mph: Any) -> str:
    parts = []
    if desc:
        parts.append(desc)
    if isinstance(temp_f, (int, float)):
        parts.append(f"{round(temp_f)}°F")
    if isinstance(wind_mph, (int, float)):
        parts.append(f"wind {round(wind_mph)} mph")
    return " · ".join(parts)


def _round_number(value: Any, digits: int = 1) -> Optional[float]:
    if not isinstance(value, (int, float)):
        return None
    return round(float(value), digits)


def _pick_hour_indexes(times: List[Any]) -> List[int]:
    wanted = {"00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"}
    out: List[int] = []
    for idx, raw in enumerate(times):
        text = str(raw or "")
        if len(text) >= 16 and text[11:16] in wanted:
            out.append(idx)
    return out


async def fetch_daily_report_weather(lat: float, lng: float, report_date: str) -> Dict[str, Any]:
    params = {
        "latitude": f"{float(lat):.5f}",
        "longitude": f"{float(lng):.5f}",
        "hourly": (
            "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,"
            "wind_gusts_10m,precipitation,rain"
        ),
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto",
        "start_date": report_date,
        "end_date": report_date,
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(_WEATHER_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    hums = hourly.get("relative_humidity_2m") or []
    codes = hourly.get("weather_code") or []
    winds = hourly.get("wind_speed_10m") or []
    gusts = hourly.get("wind_gusts_10m") or []
    precs = hourly.get("precipitation") or []
    rains = hourly.get("rain") or []

    picked = _pick_hour_indexes(times)
    snapshots = []
    for idx in picked:
        snapshots.append({
            "time": str(times[idx])[11:16],
            "timestamp": times[idx],
            "condition": _describe(codes[idx] if idx < len(codes) else None),
            "weather_code": codes[idx] if idx < len(codes) else None,
            "temp_f": _round_number(temps[idx] if idx < len(temps) else None, 0),
            "humidity_pct": _round_number(hums[idx] if idx < len(hums) else None, 0),
            "wind_mph": _round_number(winds[idx] if idx < len(winds) else None, 0),
            "wind_gust_mph": _round_number(gusts[idx] if idx < len(gusts) else None, 0),
            "precip_in": _round_number(precs[idx] if idx < len(precs) else None, 2) or 0,
            "rain_in": _round_number(rains[idx] if idx < len(rains) else None, 2) or 0,
        })

    valid_temps = [float(v) for v in temps if isinstance(v, (int, float))]
    valid_hums = [float(v) for v in hums if isinstance(v, (int, float))]
    valid_winds = [float(v) for v in winds if isinstance(v, (int, float))]
    valid_gusts = [float(v) for v in gusts if isinstance(v, (int, float))]
    total_precip = round(sum(float(v) for v in precs if isinstance(v, (int, float))), 2)
    total_rain = round(sum(float(v) for v in rains if isinstance(v, (int, float))), 2)

    severity_rank = {
        0: 0, 1: 1, 2: 2, 3: 3,
        45: 4, 48: 4,
        51: 5, 53: 5, 55: 5, 56: 5, 57: 5,
        61: 7, 63: 8, 65: 9, 66: 8, 67: 9,
        71: 6, 73: 7, 75: 8, 77: 5,
        80: 7, 81: 8, 82: 9, 85: 7, 86: 8,
        95: 10, 96: 11, 99: 12,
    }
    peak_idx = 0
    peak_severity = -1
    for i, code in enumerate(codes):
        sev = severity_rank.get(int(code) if isinstance(code, (int, float)) else -1, -1)
        if sev > peak_severity:
            peak_severity = sev
            peak_idx = i

    peak_condition = _describe(codes[peak_idx] if peak_idx < len(codes) else None)
    peak_time = times[peak_idx] if peak_idx < len(times) else ""
    summary_bits = []
    if peak_condition:
        summary_bits.append(f"Observed conditions: {peak_condition}")
    if valid_temps:
        summary_bits.append(f"temperature {round(min(valid_temps))}–{round(max(valid_temps))}°F")
    if valid_hums:
        summary_bits.append(f"humidity {round(sum(valid_hums) / len(valid_hums))}% avg")
    if valid_winds:
        wind_text = f"wind up to {round(max(valid_winds))} mph"
        if valid_gusts:
            wind_text += f", gusts up to {round(max(valid_gusts))} mph"
        summary_bits.append(wind_text)
    if total_precip > 0:
        summary_bits.append(f"precipitation {total_precip:.2f} in")
    elif total_rain > 0:
        summary_bits.append(f"rainfall {total_rain:.2f} in")
    if peak_time:
        summary_bits.append(f"peak weather signal at {peak_time}")

    return {
        "provider": "open-meteo",
        "report_date": report_date,
        "timezone": data.get("timezone") or "",
        "fetched_at_iso": datetime.now(timezone.utc).isoformat(),
        "gps": {"lat": float(lat), "lng": float(lng)},
        "summary": "; ".join(summary_bits),
        "snapshots": snapshots,
        "meta": {
            "provider": "open-meteo",
            "source": "open-meteo",
            "report_date": report_date,
            "timezone": data.get("timezone") or "",
            "gps_lat": float(lat),
            "gps_lng": float(lng),
            "observation_timestamp": peak_time,
            "peak_condition": peak_condition,
            "peak_timestamp": peak_time,
            "temperature_min_f": round(min(valid_temps)) if valid_temps else None,
            "temperature_max_f": round(max(valid_temps)) if valid_temps else None,
            "humidity_avg_pct": round(sum(valid_hums) / len(valid_hums)) if valid_hums else None,
            "wind_max_mph": round(max(valid_winds)) if valid_winds else None,
            "wind_gust_max_mph": round(max(valid_gusts)) if valid_gusts else None,
            "precipitation_total_in": total_precip,
            "rain_total_in": total_rain,
        },
    }


__all__ = ["fetch_current_weather", "fetch_daily_report_weather"]
