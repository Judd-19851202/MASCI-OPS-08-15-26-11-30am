// Aggregator for the per-domain Safety Meeting topic libraries (ES).
// Mirrors the EN aggregator — same domain order, same keys, full parity.

import { TOPICS_PIPE_ES } from "./pipe.es.js";
import { TOPICS_EXCAVATION_ES } from "./excavation.es.js";
import { TOPICS_GRADING_ES } from "./grading.es.js";
import { TOPICS_CONCRETE_ES } from "./concrete.es.js";
import { TOPICS_PAVING_ES } from "./paving.es.js";
import { TOPICS_MILLING_ES } from "./milling.es.js";
import { TOPICS_MOT_ES } from "./mot.es.js";
import { TOPICS_TRUCKING_ES } from "./trucking.es.js";
import { TOPICS_DEWATERING_ES } from "./dewatering.es.js";
import { TOPICS_SHOP_ES } from "./shop.es.js";
import { TOPICS_PLANT_ES } from "./plant.es.js";
import { TOPICS_AIRPORT_ES } from "./airport.es.js";
import { TOPICS_UTILITIES_ES } from "./utilities.es.js";
import { TOPICS_RIGGING_ES } from "./rigging.es.js";
import { TOPICS_FALL_PROTECTION_ES } from "./fall_protection.es.js";
import { TOPICS_ELECTRICAL_ES } from "./electrical.es.js";
import { TOPICS_CONFINED_SPACE_ES } from "./confined_space.es.js";
import { TOPICS_ENVIRONMENTAL_ES } from "./environmental.es.js";
import { TOPICS_WELLNESS_ES } from "./wellness.es.js";
import { TOPICS_OFFICE_ES } from "./office.es.js";
import { TOPICS_GENERAL_ES } from "./general.es.js";

export const TOPIC_LIBRARY_ES = {
  ...TOPICS_PIPE_ES,
  ...TOPICS_EXCAVATION_ES,
  ...TOPICS_GRADING_ES,
  ...TOPICS_CONCRETE_ES,
  ...TOPICS_PAVING_ES,
  ...TOPICS_MILLING_ES,
  ...TOPICS_MOT_ES,
  ...TOPICS_TRUCKING_ES,
  ...TOPICS_DEWATERING_ES,
  ...TOPICS_SHOP_ES,
  ...TOPICS_PLANT_ES,
  ...TOPICS_AIRPORT_ES,
  ...TOPICS_UTILITIES_ES,
  ...TOPICS_RIGGING_ES,
  ...TOPICS_FALL_PROTECTION_ES,
  ...TOPICS_ELECTRICAL_ES,
  ...TOPICS_CONFINED_SPACE_ES,
  ...TOPICS_ENVIRONMENTAL_ES,
  ...TOPICS_WELLNESS_ES,
  ...TOPICS_OFFICE_ES,
  ...TOPICS_GENERAL_ES,
};
