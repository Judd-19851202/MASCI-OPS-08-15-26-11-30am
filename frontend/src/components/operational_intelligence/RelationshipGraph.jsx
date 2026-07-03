// Track 19.55 · Universal Operational Threads Foundation.
//
// RelationshipGraph — the ONE reusable relationship-graph primitive.
// Every future Operational Thread (Employee, Project, Incident,
// Vendor, Asset) will render its "Section 5 · Relationships" using
// THIS component. If a domain builds a custom relationship visual,
// the platform has drifted.
//
// Read-only. Callers supply an array of typed nodes with directional
// relationships. Each node may carry a React-Router deep_link — the
// graph never fetches, mutates, or infers.
//
// Node schema:
//   { id: "unit-412", kind: "unit", label: "Unit 412",
//     sublabel: "CAT 349F", deep_link: "/fleet/unit/412" }
//
// The primitive renders a compact vertical chain (mobile-first) with
// the subject node at the top and related nodes stacked below, each
// connected by a lightweight "↓" separator.

import React from "react";
import { Link } from "react-router-dom";

const KIND_TONE = {
  subject:  { chip: "bg-slate-900 text-white border-slate-900" },
  unit:     { chip: "bg-slate-100 text-slate-900 border-slate-300" },
  operator: { chip: "bg-indigo-100 text-indigo-900 border-indigo-300" },
  project:  { chip: "bg-sky-100 text-sky-900 border-sky-300" },
  pm:       { chip: "bg-sky-100 text-sky-900 border-sky-300" },
  foreman:  { chip: "bg-sky-100 text-sky-900 border-sky-300" },
  shop:     { chip: "bg-orange-100 text-orange-900 border-orange-300" },
  wo:       { chip: "bg-orange-100 text-orange-900 border-orange-300" },
  incident: { chip: "bg-red-100 text-red-900 border-red-300" },
  safety:   { chip: "bg-red-100 text-red-900 border-red-300" },
  po:       { chip: "bg-emerald-100 text-emerald-900 border-emerald-300" },
  hold:     { chip: "bg-red-100 text-red-900 border-red-300" },
  inspection: { chip: "bg-sky-100 text-sky-900 border-sky-300" },
  document: { chip: "bg-slate-100 text-slate-800 border-slate-300" },
  photo:    { chip: "bg-slate-100 text-slate-800 border-slate-300" },
  other:    { chip: "bg-slate-100 text-slate-800 border-slate-300" },
};

function toneFor(kind) {
  return KIND_TONE[kind] || KIND_TONE.other;
}

export default function RelationshipGraph({
  subject,
  edges = [],
  title = "Relationships",
  testId = "relationship-graph",
}) {
  return (
    <section
      data-testid={testId}
      className="rounded-md border-2 border-slate-200 bg-white"
    >
      <div className="px-4 py-3 border-b border-slate-200">
        <div className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500">
          {title}
        </div>
      </div>

      <div className="p-4 flex flex-col items-center gap-1">
        {/* Subject node */}
        <RelationshipNode
          node={{ ...subject, kind: "subject" }}
          testId={`${testId}-subject`}
        />

        {edges.length === 0 ? (
          <div
            data-testid={`${testId}-empty`}
            className="mt-2 text-xs text-slate-500 italic"
          >
            No related operational objects on record.
          </div>
        ) : (
          edges.map((edge, i) => (
            <React.Fragment key={edge.id || `edge-${i}`}>
              <EdgeLabel label={edge.label} />
              <RelationshipNode
                node={edge}
                testId={`${testId}-node-${i}`}
              />
            </React.Fragment>
          ))
        )}
      </div>
    </section>
  );
}

function EdgeLabel({ label }) {
  return (
    <div className="flex flex-col items-center py-0.5">
      <div className="h-3 w-px bg-slate-300" aria-hidden="true" />
      {label && (
        <div className="font-mono text-[10px] uppercase tracking-widest text-slate-500 my-0.5">
          {label}
        </div>
      )}
      <div className="h-3 w-px bg-slate-300" aria-hidden="true" />
    </div>
  );
}

function RelationshipNode({ node, testId }) {
  if (!node) return null;
  const tone = toneFor(node.kind);
  const body = (
    <div
      className={`inline-flex flex-col items-center rounded-md border-2 px-3 py-1.5 ${tone.chip} min-w-[140px] text-center`}
    >
      <div className="text-[10px] font-mono uppercase tracking-widest opacity-80">
        {node.kind || "node"}
      </div>
      <div className="text-sm font-bold leading-snug">{node.label || "—"}</div>
      {node.sublabel && (
        <div className="text-[11px] opacity-80 leading-snug">{node.sublabel}</div>
      )}
    </div>
  );
  return node.deep_link ? (
    <Link
      to={node.deep_link}
      data-testid={testId}
      className="hover:brightness-95 transition"
    >
      {body}
    </Link>
  ) : (
    <div data-testid={testId}>{body}</div>
  );
}
