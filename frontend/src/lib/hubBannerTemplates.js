/**
 * HUB_BANNER_TEMPLATES — preloaded message templates the admin can
 * pick from when composing a banner. Each template defines a default
 * severity, ack policy, and an expiration window (in hours from "now")
 * so the admin doesn't have to think about every field — they just pick
 * the situation, optionally tweak the text, and ship it.
 *
 * Adding a template?
 *  - Pick a stable `id` (snake_case).
 *  - Provide both an English title/body. Spanish is auto-translated on
 *    save via Claude Haiku — admins don't need to write it.
 *  - Severity must be one of: info | advisory | warning | critical.
 *  - `default_expires_hours`: when set, the admin compose UI prefills
 *    expires_at = now + N hours. Pass null to mean "no auto-expire".
 *
 * Order matters — the picker renders templates in this order.
 */
export const HUB_BANNER_TEMPLATES = [
  {
    id: "heat_advisory",
    label: "Heat Advisory",
    icon: "thermometer-sun",
    severity: "advisory",
    require_ack: false,
    default_expires_hours: 10,
    title_en: "Heat Advisory in Effect",
    body_en:
      "Temperatures will exceed 95°F today. Take a 10-minute shade " +
      "break every 60 minutes. Drink 8 oz of water every 15 minutes. " +
      "Watch your crew for cramps, dizziness, or confusion — STOP work " +
      "and call your foreman if anyone shows symptoms.",
  },
  {
    id: "heat_warning",
    label: "Excessive Heat Warning",
    icon: "thermometer-sun",
    severity: "warning",
    require_ack: true,
    default_expires_hours: 10,
    title_en: "EXCESSIVE HEAT WARNING — Mandatory Cooling Cycle",
    body_en:
      "Heat index will exceed 108°F. OSHA-mandatory 15-minute shaded " +
      "break every 45 minutes of work. Buddy-check your crew every 30 " +
      "minutes. Any sign of heat illness — STOP work immediately and " +
      "call 911. No outdoor work between 12 PM – 3 PM.",
  },
  {
    id: "hurricane_watch",
    label: "Hurricane Watch (48–72h)",
    icon: "cloud-rain-wind",
    severity: "warning",
    require_ack: true,
    default_expires_hours: 48,
    title_en: "Hurricane Watch Issued",
    body_en:
      "A hurricane is possible in our area within 48–72 hours. Foremen: " +
      "begin securing loose tools, signage, and fuel. PMs: confirm " +
      "everyone has reviewed the Storm Plan. Monitor updates — Warning " +
      "status is next. No new excavations until the storm passes.",
  },
  {
    id: "hurricane_warning",
    label: "Hurricane Warning (within 36h)",
    icon: "cloud-rain-wind",
    severity: "critical",
    require_ack: true,
    default_expires_hours: 36,
    title_en: "HURRICANE WARNING — STAND DOWN",
    body_en:
      "A hurricane will impact our area within 36 hours. Stop all field " +
      "operations by end of shift. Secure every site: tools, trench " +
      "boxes, MOT signage, fuel, generators. All crews report storm " +
      "prep complete to your PM before leaving. Office will email when " +
      "it is safe to return.",
  },
  {
    id: "lightning",
    label: "Severe Thunderstorm / Lightning",
    icon: "cloud-lightning",
    severity: "warning",
    require_ack: false,
    default_expires_hours: 4,
    title_en: "Lightning in Area — Pause Work",
    body_en:
      "Lightning has been detected within 10 miles. 30-minute rule: " +
      "wait 30 minutes after the last strike before returning to open " +
      "work. Get crews off lifts, off rebar, out of trenches, and " +
      "into vehicles or hard-roofed structures.",
  },
  {
    id: "flood_watch",
    label: "Flood Watch",
    icon: "waves",
    severity: "advisory",
    require_ack: false,
    default_expires_hours: 24,
    title_en: "Flood Watch in Effect",
    body_en:
      "Heavy rain is expected. Check trench-box drainage and pump " +
      "readiness before the rain starts. Do not enter any trench with " +
      "standing water until inspected by the Competent Person. Report " +
      "site flooding to your PM immediately.",
  },
  {
    id: "osha_visit",
    label: "OSHA Site Visit Today",
    icon: "shield-check",
    severity: "warning",
    require_ack: true,
    default_expires_hours: 12,
    title_en: "OSHA Compliance Officer On-Site Today",
    body_en:
      "An OSHA Compliance Officer is visiting MASCI job sites today. " +
      "100% PPE compliance — hard hat, hi-vis, safety glasses, gloves, " +
      "and boots. All daily reports, JHAs, and competent-person logs " +
      "must be current and on-site. Direct any officer to your PM " +
      "before answering questions. Be polite, be brief.",
  },
  {
    id: "stand_down",
    label: "Major Incident — Stand Down",
    icon: "octagon-alert",
    severity: "critical",
    require_ack: true,
    default_expires_hours: 8,
    title_en: "SAFETY STAND-DOWN IN EFFECT",
    body_en:
      "A serious incident has occurred on a MASCI project. All crews " +
      "stop work immediately and meet with your foreman for a safety " +
      "briefing before resuming any task. Foremen call your PM for " +
      "details. Do NOT discuss the incident on social media or with " +
      "anyone outside the company.",
  },
  {
    id: "illness_reporting",
    label: "Illness Reporting Reminder",
    icon: "thermometer",
    severity: "info",
    require_ack: false,
    default_expires_hours: 168,
    title_en: "Illness Reporting Reminder",
    body_en:
      "If you have a fever, cough, or any contagious symptoms, do NOT " +
      "report to the job site. Call your foreman or PM to report " +
      "off. Sick days are protected — your job is not at risk for " +
      "staying home when you're contagious. Protect your crew.",
  },
  {
    id: "holiday_closure",
    label: "Company Holiday / Shutdown",
    icon: "calendar-x",
    severity: "info",
    require_ack: false,
    default_expires_hours: 168,
    title_en: "Office Closed for Holiday",
    body_en:
      "The MASCI office will be closed for the holiday. Field crews: " +
      "check with your foreman for your specific schedule. For " +
      "emergencies (incidents, equipment failure that stops the job, " +
      "or any safety concern), call the on-call PM. Otherwise, see you " +
      "on the next business day.",
  },
];

/**
 * Severity → UI color + icon hint. Keep in sync with BannerStrip.jsx
 * and AdminBannersPanel.jsx (they import from here so we never drift).
 */
export const SEVERITY_META = {
  info: {
    label: "Info",
    cls_bar: "bg-blue-700 text-white border-blue-900",
    cls_chip: "bg-blue-100 text-blue-900 border-blue-300",
    cls_btn: "bg-white text-blue-900 hover:bg-blue-50",
    icon: "info",
    pulse: false,
  },
  advisory: {
    label: "Advisory",
    cls_bar: "bg-amber-500 text-slate-900 border-amber-700",
    cls_chip: "bg-amber-100 text-amber-900 border-amber-400",
    cls_btn: "bg-slate-900 text-amber-300 hover:bg-slate-800",
    icon: "alert-triangle",
    pulse: false,
  },
  warning: {
    label: "Warning",
    cls_bar: "bg-red-700 text-white border-red-900",
    cls_chip: "bg-red-100 text-red-900 border-red-400",
    cls_btn: "bg-white text-red-900 hover:bg-red-50",
    icon: "alert-octagon",
    pulse: false,
  },
  critical: {
    label: "Critical",
    cls_bar: "bg-red-950 text-red-100 border-red-700 animate-pulse-slow",
    cls_chip: "bg-red-200 text-red-950 border-red-600",
    cls_btn: "bg-red-200 text-red-950 hover:bg-red-100",
    icon: "octagon-alert",
    pulse: true,
  },
};
