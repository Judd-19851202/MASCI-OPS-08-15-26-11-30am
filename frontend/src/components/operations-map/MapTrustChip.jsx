import React from "react";
import { describeFeed, describeAge } from "@/lib/operations-map/eventVocab";

/* Operator-facing trust chip.
 * Shows Live Feed / Delayed Feed / Offline Feed driven by telemetry
 * age — NEVER raw "motive:poll" or "motive:webhook" terms in primary
 * copy. Vendor source (Motive) appears only inside the asset card's
 * secondary trust line where audit-grade source attribution lives. */
const TONE = {
  emerald: { dot: "#10b981", text: "#047857", bg: "#ecfdf5", bd: "#a7f3d0" },
  amber:   { dot: "#f59e0b", text: "#b45309", bg: "#fffbeb", bd: "#fde68a" },
  slate:   { dot: "#94a3b8", text: "#475569", bg: "#f1f5f9", bd: "#cbd5e1" },
};

export default function MapTrustChip({ trust }) {
  if (!trust) return null;
  const age = trust.age_seconds ?? null;
  const grade = describeFeed(age);
  const tone = TONE[grade.tone] || TONE.slate;
  return (
    <span className="ops-map-trust-chip"
          data-testid="ops-map-trust-chip"
          style={{ background: tone.bg, color: tone.text, border: `1px solid ${tone.bd}` }}>
      <span style={{
        display: "inline-block", width: 8, height: 8, borderRadius: 4,
        background: tone.dot, marginRight: 6,
      }}/>
      <strong style={{ color: "inherit", fontWeight: 800 }}>{grade.feed}</strong>
      <span style={{ margin: "0 6px", opacity: 0.5 }}>·</span>
      <span>{describeAge(age)}</span>
      <span style={{ margin: "0 6px", opacity: 0.5 }}>·</span>
      <span style={{ fontWeight: 700 }}>{grade.confidence}</span>
    </span>
  );
}
