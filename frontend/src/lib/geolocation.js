// Browser geolocation + free reverse-geocoding via OpenStreetMap Nominatim.
// No API key required. For higher-volume / stricter SLAs we can swap to
// Mapbox or Google later — same interface.

const NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse";

export function getCurrentPosition(options = {}) {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator)) {
      reject(new Error("Geolocation is not supported on this device"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve(pos),
      (err) => reject(err),
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0,
        ...options,
      }
    );
  });
}

/**
 * Reverse-geocode lat/lng to a human-readable address using Nominatim.
 * Returns { display, lat, lng, raw } where `display` is best-effort.
 */
export async function reverseGeocode(lat, lng) {
  const params = new URLSearchParams({
    format: "jsonv2",
    lat: String(lat),
    lon: String(lng),
    zoom: "18",
    addressdetails: "1",
  });
  const res = await fetch(`${NOMINATIM_URL}?${params.toString()}`, {
    headers: {
      // Nominatim TOS asks for an identifying UA. Browsers won't let us
      // override User-Agent so we send Accept-Language + Referer (auto).
      "Accept-Language": navigator.language || "en",
    },
  });
  if (!res.ok) throw new Error(`Reverse geocode failed (${res.status})`);
  const data = await res.json();
  const a = data.address || {};
  // Build a concise field-friendly string
  const street = [a.house_number, a.road].filter(Boolean).join(" ");
  const locality = a.city || a.town || a.village || a.hamlet || a.suburb || "";
  const region = a.state || a.county || "";
  const postcode = a.postcode || "";
  const display = [
    street,
    [locality, region].filter(Boolean).join(", "),
    postcode,
  ]
    .filter(Boolean)
    .join(" · ")
    .replace(/\s+·\s+$/, "");
  return {
    display: display || data.display_name || `${lat}, ${lng}`,
    lat,
    lng,
    raw: data,
  };
}

export function formatCoords(lat, lng, accuracy) {
  if (lat == null || lng == null) return "";
  const acc = accuracy ? ` ±${Math.round(accuracy)} m` : "";
  return `${Number(lat).toFixed(6)}, ${Number(lng).toFixed(6)}${acc}`;
}
