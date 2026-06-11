/* Operational vocabulary translator for the MASCI Operations Center
 * Live Map. Converts raw Motive telematics families and source strings
 * into the platform-native language used elsewhere in the operator UI.
 *
 * One source of truth — consumed by AssetCardSheet, MapTimelineDock,
 * and MapTrustChip so the surface never leaks vendor / SDK terms.
 */

export const EVENT_FAMILY_LABEL = {
  vehicle_gps:           "Position Update",
  vehicle_location:      "Position Update",
  vehicle_location_received: "Position Update",
  geofence_enter:        "Arrived",
  geofence_exit:         "Departed",
  asset_geofence_enter:  "Arrived",
  asset_geofence_exit:   "Departed",
  harsh_event:           "Safety Event",
  fault_code:            "Mechanical Fault",
  dvir:                  "Inspection Logged",
  ai_coach_recap:        "Coaching Event",
  ignition_on:           "Ignition On",
  ignition_off:          "Ignition Off",
  trip_start:            "Trip Started",
  trip_end:              "Trip Ended",
};

export function describeEventFamily(family) {
  if (!family) return "Event";
  return EVENT_FAMILY_LABEL[family] || "Event";
}

/* MASCI-native source labels — replaces "motive:webhook" / "motive:poll"
 * / "motive:mapping" with operator-readable telemetry attribution.
 * Vendor name is retained ONLY inside the trust attribution detail
 * because operators need to know the data origin for trust grading. */
export const SOURCE_LABEL = {
  "motive:webhook":  "Live Telemetry",
  "motive:poll":     "Telemetry Poll",
  "motive:mapping":  "Last Known",
  "equipment_master": "Equipment Master",
  "unknown":         "Unknown",
};

export function describeSource(source) {
  if (!source) return "Unknown";
  return SOURCE_LABEL[source] || source.replace(/^motive:/, "Telemetry · ");
}

/* Operational state translator — used by health badges and card chips. */
export const OPERATIONAL_STATE_LABEL = {
  green: "Working",
  amber: "Idle",
  red:   "Needs Attention",
  gray:  "Offline",
};

export function describeOperationalState(band) {
  return OPERATIONAL_STATE_LABEL[band] || "Unknown";
}
