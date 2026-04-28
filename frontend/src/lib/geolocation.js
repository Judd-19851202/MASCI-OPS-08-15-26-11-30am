// Browser geolocation + free reverse-geocoding via OpenStreetMap Nominatim.
// No API key required. For higher-volume / stricter SLAs we can swap to
// Mapbox or Google later — same interface.

const NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse";

/** Map a GeolocationPositionError to a human-readable message. */
function gpsErrorMessage(err) {
  if (!err) return "Unknown GPS error";
  // GeolocationPositionError has no .message on iOS Safari — only .code
  switch (err.code) {
    case 1: // PERMISSION_DENIED
      return "Location permission denied. Tap the AA in Safari's address bar → Website Settings → Location → Allow, then try again.";
    case 2: // POSITION_UNAVAILABLE
      return "GPS signal unavailable. Step outside or near a window and try again.";
    case 3: // TIMEOUT
      return "GPS timed out. Try again — sometimes iOS needs a second attempt.";
    default:
      return err.message || "Could not get GPS location";
  }
}

/**
 * Try to get a position, falling back from high accuracy → low accuracy →
 * cached position so iOS Safari doesn't silently fail when the GPS chip
 * isn't warm yet.
 */
export function getCurrentPosition(options = {}) {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator)) {
      reject(new Error("Geolocation is not supported on this device"));
      return;
    }
    if (!window.isSecureContext) {
      reject(
        new Error(
          "GPS requires HTTPS. Open the site at https://mascidocs.com and try again."
        )
      );
      return;
    }
    const tryHighAccuracy = () =>
      new Promise((res, rej) =>
        navigator.geolocation.getCurrentPosition(res, rej, {
          enableHighAccuracy: true,
          timeout: 12000,
          maximumAge: 30000,
          ...options,
        })
      );
    const tryLowAccuracy = () =>
      new Promise((res, rej) =>
        navigator.geolocation.getCurrentPosition(res, rej, {
          enableHighAccuracy: false,
          timeout: 12000,
          maximumAge: 5 * 60 * 1000, // accept up to 5-min cached fix
          ...options,
        })
      );

    tryHighAccuracy()
      .then(resolve)
      .catch((err) => {
        // PERMISSION_DENIED is final — no point retrying
        if (err && err.code === 1) {
          reject(new Error(gpsErrorMessage(err)));
          return;
        }
        // Otherwise retry with lower accuracy / cached fix
        tryLowAccuracy()
          .then(resolve)
          .catch((err2) => reject(new Error(gpsErrorMessage(err2))));
      });
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
