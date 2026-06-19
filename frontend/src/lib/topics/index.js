// Aggregator for the per-domain Safety Meeting topic libraries (EN).
// Domains are in operational field-workflow order — DO NOT alphabetize.
// Adding a new domain: create /lib/topics/<key>.js, add import + spread here,
// and add the domain chip to TopicPicker.jsx DOMAIN_CHIPS in the same order.

import { TOPICS_PIPE } from "./pipe.js";
import { TOPICS_EXCAVATION } from "./excavation.js";
import { TOPICS_GRADING } from "./grading.js";
import { TOPICS_CONCRETE } from "./concrete.js";
import { TOPICS_PAVING } from "./paving.js";
import { TOPICS_MILLING } from "./milling.js";
import { TOPICS_MOT } from "./mot.js";
import { TOPICS_TRUCKING } from "./trucking.js";
import { TOPICS_DEWATERING } from "./dewatering.js";
import { TOPICS_SHOP } from "./shop.js";
import { TOPICS_PLANT } from "./plant.js";
import { TOPICS_LAB } from "./lab.js";
import { TOPICS_AIRPORT } from "./airport.js";
import { TOPICS_UTILITIES } from "./utilities.js";
import { TOPICS_RIGGING } from "./rigging.js";
import { TOPICS_FALL_PROTECTION } from "./fall_protection.js";
import { TOPICS_ELECTRICAL } from "./electrical.js";
import { TOPICS_CONFINED_SPACE } from "./confined_space.js";
import { TOPICS_ENVIRONMENTAL } from "./environmental.js";
import { TOPICS_WELLNESS } from "./wellness.js";
// TRACK 15.46 · Public Interaction & Conflict De-Escalation
import { TOPICS_PUBLIC_INTERACTION } from "./public_interaction.js";
import { TOPICS_OFFICE } from "./office.js";
import { TOPICS_GENERAL } from "./general.js";

export const TOPIC_LIBRARY = [
  ...TOPICS_PIPE,
  ...TOPICS_EXCAVATION,
  ...TOPICS_GRADING,
  ...TOPICS_CONCRETE,
  ...TOPICS_PAVING,
  ...TOPICS_MILLING,
  ...TOPICS_MOT,
  ...TOPICS_TRUCKING,
  ...TOPICS_DEWATERING,
  ...TOPICS_SHOP,
  ...TOPICS_PLANT,
  ...TOPICS_LAB,
  ...TOPICS_AIRPORT,
  ...TOPICS_UTILITIES,
  ...TOPICS_RIGGING,
  ...TOPICS_FALL_PROTECTION,
  ...TOPICS_ELECTRICAL,
  ...TOPICS_CONFINED_SPACE,
  ...TOPICS_ENVIRONMENTAL,
  ...TOPICS_WELLNESS,
  ...TOPICS_PUBLIC_INTERACTION,
  ...TOPICS_OFFICE,
  ...TOPICS_GENERAL,
];

export const CUSTOM_TOPIC_KEY = "__custom__";

export function findTopic(key) {
  return TOPIC_LIBRARY.find((t) => t.key === key);
}
