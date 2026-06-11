import React from "react";
import { describeSource } from "@/lib/operations-map/eventVocab";

export default function MapTrustChip({ trust }) {
  if (!trust) return null;
  const c = trust.confidence || "unmapped";
  const age = trust.age_seconds;
  const ageLabel = age === null || age === undefined
    ? "no fix"
    : age < 60   ? `${age}s ago`
    : age < 3600 ? `${Math.round(age/60)}m ago`
    : age < 86400? `${Math.round(age/3600)}h ago`
    : `${Math.round(age/86400)}d ago`;
  return (
    <span className={`ops-map-trust-chip ${c}`} data-testid="ops-map-trust-chip">
      <span>{describeSource(trust.source)}</span>
      <span>·</span>
      <span>{ageLabel}</span>
      <span>·</span>
      <span style={{ textTransform: "uppercase", letterSpacing: "0.04em" }}>{c}</span>
    </span>
  );
}
