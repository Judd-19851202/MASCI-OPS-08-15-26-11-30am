// TRACK 23.4A · Shared time math for V3 crew rows.
//
// Mirrors V1's `computeHours` / `grossNetPreview` semantics so V3 crew
// rows show the same auto-calculated net hours the foreman is used to
// (start/stop/lunch → decimal hours). Kept as a plain module (no React)
// so it's straightforward to unit-test and share.

export function computeCrewHours(start, stop, lunchMinutes) {
  if (!start || !stop) return "";
  const [sh, sm] = String(start).split(":").map(Number);
  const [eh, em] = String(stop).split(":").map(Number);
  if ([sh, sm, eh, em].some((n) => Number.isNaN(n))) return "";
  let mins = eh * 60 + em - (sh * 60 + sm);
  if (mins < 0) mins += 24 * 60; // overnight shift
  mins -= Number(lunchMinutes) || 0;
  if (mins < 0) mins = 0;
  return (mins / 60).toFixed(2);
}

export function grossNetPreview(start, stop, lunchMinutes) {
  if (!start || !stop) return null;
  const [sh, sm] = String(start).split(":").map(Number);
  const [eh, em] = String(stop).split(":").map(Number);
  if ([sh, sm, eh, em].some((n) => Number.isNaN(n))) return null;
  let grossMin = eh * 60 + em - (sh * 60 + sm);
  if (grossMin < 0) grossMin += 24 * 60;
  const lunchM = Number(lunchMinutes) || 0;
  const netMin = Math.max(0, grossMin - lunchM);
  const hr = (m) => (m / 60).toFixed(m % 60 === 0 ? 1 : 2);
  const fmt = (s) => {
    const [h, m] = String(s).split(":").map(Number);
    if (Number.isNaN(h) || Number.isNaN(m)) return String(s);
    const ampm = h >= 12 ? "PM" : "AM";
    const h12 = h % 12 === 0 ? 12 : h % 12;
    return `${h12}:${String(m).padStart(2, "0")} ${ampm}`;
  };
  return {
    label: `${fmt(start)} \u2192 ${fmt(stop)}`,
    math: `${hr(grossMin)} h gross \u2212 ${(lunchM / 60).toFixed(
      lunchM % 60 === 0 ? 1 : 2,
    )} h lunch = ${hr(netMin)} h net`,
    gross: grossMin / 60,
    net: netMin / 60,
  };
}

export function sumCrewHours(crews) {
  return (crews || []).reduce((acc, c) => {
    const h = Number(c?.hours) || 0;
    return acc + (h > 0 ? h : 0);
  }, 0);
}

export function sumEquipmentHours(equipment, key) {
  return (equipment || []).reduce((acc, e) => {
    const v = Number(e?.[key]) || 0;
    return acc + (v > 0 ? v : 0);
  }, 0);
}
