# TRACK 19.51 · Command Center Standard

Every portal home must comply with this 8-section canonical structure.
The reference implementation is the OI Cockpit at
`/admin/operational-intelligence`.

## 1. Mission Header
- **Purpose statement** — one sentence, states who the portal is for.
- **Current operating state** — score or attention indicator when the portal has an OI product; otherwise a single-line status.
- **Refresh action** — refresh + optional deep-link to registry / JSON.

## 2. Attention Strip
- **3–5 highest-value items only.** Never more.
- Each item: label · numeric value · tone (colour · arrow · attention level).
- No decorative KPIs, no "Total X" without meaning.

## 3. Today / This Week Action Queue
- List of items the user must act on **today**.
- Every row: item · owner · age · urgency · direct link.
- Empty state must say what to do next (never a blank card).

## 4. Operational Intelligence Snapshot (when applicable)
- Pull the score, attention level, trend arrow, and top-attention label from the linked OI product.
- Do **not** re-derive scoring.
- Link "Open in Cockpit" for drill-down.

## 5. Primary Workflows
- Clear buttons for the 3–6 main jobs this portal performs.
- Labels are verbs (Add · Review · Approve · Reject · Return-to-service).

## 6. Recent Activity / Proof
- Time-bounded (last 24h / 7d) — never a raw audit dump.
- Every row must explain **why the user should care**.
- Preferred: the shared `operational_intelligence_audit` and `operational_intelligence_history` collections where relevant.

## 7. Guidance / Help
- Short, contextual copy.
- Link to Guidance Center if a workflow doc exists.
- Never stale route mentions.

## 8. Empty State
- Every panel must render a clear empty state.
- Empty state must tell the user what to do next.
- No blank cards. No spinner-only fallbacks. No demo/fake data.

## Six-Pillar compliance rules
- **Powerful** — every widget answers "what needs attention now?".
- **Simple** — user understands the screen in 10 seconds.
- **Beautiful** — sticky headers, calm spacing, no vanity KPIs.
- **Trusted** — every value traces to a real collection; `insufficient_data` shown honestly.
- **Proven** — every interactive element carries a stable `data-testid`.
- **Operational** — every action button opens the actual workflow, not another dashboard.

## Non-compliance triggers
A portal home is out of compliance if it violates any of:
- ≥1 NOISE-classified tile on the primary above-the-fold view.
- Any tile shows a value without explaining what to do about it.
- Missing empty state on any panel.
- Duplicates scoring / attention logic from an OI product.
- Sends real emails from a hub tile action.
