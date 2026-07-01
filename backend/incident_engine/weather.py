"""Track 19.16 · UX Hardening Batch 1 · Weather auto-fetch.

Small helper that fetches current weather from a public no-key API
(Open-Meteo) so field crews never have to type weather into an
incident report. Returns a compact structured payload the frontend
can auto-fill onto the location step.

READ-ONLY. Zero-Drift. Never mutates any incident collection.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

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


__all__ = ["fetch_current_weather"]
