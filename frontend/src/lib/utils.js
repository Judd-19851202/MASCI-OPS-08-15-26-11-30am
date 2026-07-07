import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Compress an image File -> base64 JPEG ~ targetMaxDim px on the longest side.
//
// TRACK 24.11 · Field foremen upload iPhone HEIC and Android camera
// photos. The previous <img>-only path silently failed on HEIC in
// Safari (img.onerror fires — no way to render HEIC via <img>). We
// now prefer `createImageBitmap(File)` which:
//   * decodes HEIC/HEIF natively on iOS 17+ Safari
//   * decodes AVIF/WEBP/PNG/JPEG on all evergreen browsers
//   * accepts a File directly (no FileReader round-trip)
//   * respects EXIF orientation via the `imageOrientation: "from-image"` option
// If `createImageBitmap` is missing or throws (older Safari, or an
// image type it doesn't recognise), we fall back to the legacy
// FileReader + <img> path. If BOTH fail we throw a diagnostic error
// carrying the source MIME so the caller can surface an actionable
// message ("Change iPhone → Settings → Camera → Formats → Most
// Compatible") instead of a silent "Could not process".
export class HeicDecodeError extends Error {
  constructor(mime) {
    super(`Cannot decode ${mime || "image"} in this browser`);
    this.name = "HeicDecodeError";
    this.mime = mime || "";
  }
}

async function _decodeViaBitmap(file) {
  if (typeof createImageBitmap !== "function") return null;
  try {
    // `imageOrientation: "from-image"` honours EXIF rotation so
    // portrait iPhone photos aren't stored sideways.
    return await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    return null;
  }
}

function _decodeViaImgTag(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new HeicDecodeError(file?.type || ""));
      img.onload = () => resolve(img);
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
}

function _drawToCanvasJpeg(bitmapOrImg, targetMaxDim, quality) {
  const width0 = bitmapOrImg.width || bitmapOrImg.naturalWidth;
  const height0 = bitmapOrImg.height || bitmapOrImg.naturalHeight;
  let width = width0;
  let height = height0;
  const longest = Math.max(width, height);
  if (longest > targetMaxDim) {
    const ratio = targetMaxDim / longest;
    width = Math.round(width * ratio);
    height = Math.round(height * ratio);
  }
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, width, height);
  ctx.drawImage(bitmapOrImg, 0, 0, width, height);
  return canvas.toDataURL("image/jpeg", quality);
}

export async function compressImage(file, targetMaxDim = 1280, quality = 0.78) {
  // Prefer createImageBitmap — handles HEIC on iOS 17+.
  const bitmap = await _decodeViaBitmap(file);
  if (bitmap) {
    try {
      return _drawToCanvasJpeg(bitmap, targetMaxDim, quality);
    } finally {
      if (typeof bitmap.close === "function") bitmap.close();
    }
  }
  // Fallback: legacy <img> tag decode (works for JPEG/PNG/WEBP/GIF).
  // Throws HeicDecodeError with the source MIME if the browser can't
  // decode the file (typically HEIC on older Safari).
  const img = await _decodeViaImgTag(file);
  return _drawToCanvasJpeg(img, targetMaxDim, quality);
}

// Format a date string for display.
//
// Calendar-date strings like "2026-05-05" (from <input type="date">) are
// parsed by JS as UTC midnight, which then renders as the PREVIOUS day in
// any browser west of UTC (e.g. "May 4" in EDT/PDT). That's the "I picked
// 5/5 but it shows 5/4" bug crews report. We detect bare YYYY-MM-DD and
// build the Date with local-time components so the displayed day matches
// the day the user picked on their calendar.
//
// Full ISO timestamps with time/zone (e.g. "2026-05-05T15:30:00Z" or
// "...+00:00") are real "moments" and we let JS parse them normally so
// they convert into the viewer's local timezone correctly.
export function formatDateLong(iso) {
  if (!iso) return "";
  try {
    let d;
    const m = typeof iso === "string" && iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (m) {
      d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    } else {
      d = new Date(iso);
    }
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleDateString(undefined, {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}
