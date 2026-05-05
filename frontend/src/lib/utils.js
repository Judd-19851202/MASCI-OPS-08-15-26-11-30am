import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Compress an image File -> base64 JPEG ~ targetMaxDim px on the longest side.
export async function compressImage(file, targetMaxDim = 1280, quality = 0.78) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => {
      const img = new Image();
      img.onerror = reject;
      img.onload = () => {
        let { width, height } = img;
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
        ctx.drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL("image/jpeg", quality));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
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
