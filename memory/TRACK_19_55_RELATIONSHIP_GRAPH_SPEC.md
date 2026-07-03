# TRACK 19.55 · Relationship Graph Specification

## Contract
```jsx
<RelationshipGraph
  title="Relationships"
  subject={{ id: "unit-412", kind: "unit", label: "Unit 412",
             sublabel: "CAT 349F" }}
  edges={[
    { id: "op-1",   kind: "operator", label: "John Smith",
                    sublabel: "Operator", deep_link: null },
    { id: "prj-1",  kind: "project",  label: "Project 1045",
                    sublabel: null, deep_link: "/pm/command-center" },
    { id: "wo-284", kind: "wo",       label: "WO 284",
                    deep_link: "/shop/units/412/history",
                    label_edge: "work order" },
  ]}
  testId="unit-412-relationships"
/>
```

## Node schema
| Field       | Required | Notes                                                 |
|-------------|:--------:|-------------------------------------------------------|
| `id`        | ✅       | Stable React key                                      |
| `kind`      | ✅       | One of the tone map keys (see below)                  |
| `label`     | ✅       | Primary node label                                    |
| `sublabel`  | optional | Secondary line                                        |
| `deep_link` | optional | React-Router path — node becomes a `<Link>` if set    |
| `label`     | optional (on edges) | edge label ("assigned to", "operated by") |

## Kind tone map (locked)
- `subject` (dark slate) — always the top node
- `unit` (slate)
- `operator` (indigo)
- `project` / `pm` / `foreman` (sky)
- `shop` / `wo` (orange)
- `incident` / `safety` / `hold` (red)
- `po` (emerald)
- `inspection` (sky)
- `document` / `photo` / `other` (slate)

Every future thread MUST use these kinds — no domain-invented tones.

## Read-only guarantee
`RelationshipGraph` never fetches, mutates, or infers. Callers pass a
resolved `subject` + `edges[]` array. Enforced by
`test_relationship_graph_read_only`.

## Visual layout
- Subject node at the top.
- Each edge stacks below: `↓ [edge label] ↓ [node]`.
- Mobile-first vertical chain — no horizontal overflow at any width.
- Every node with a `deep_link` renders as a `<Link>` with
  `hover:brightness-95` — click-to-drill.

## Empty state
When `edges.length === 0`: renders "No related operational objects on
record." — honest empty, no filler nodes.

## Reuse target
Every future Operational Thread uses this ONE component. No thread
may build a bespoke relationship visual. Verified by the OI-component
directory-inventory lock test which limits new JSX files.
