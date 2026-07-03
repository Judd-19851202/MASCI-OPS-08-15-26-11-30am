# TRACK 19.51 · Mobile / iPad / Desktop Review

Reviewed at desktop (1920×900), iPad landscape (1024×768), iPad portrait (768×1024), and mobile (375×812).

| Portal | Desktop | iPad landscape | iPad portrait | Mobile | Notes |
|---|:-:|:-:|:-:|:-:|---|
| OI Cockpit | ✅ | ✅ | ✅ | ✅ | Reference implementation. |
| OI Recipients | ✅ | ✅ | ✅ | ✅ | Table scrolls internally. |
| Admin v1 | ✅ | ✅ | ⚠️ | ⚠️ | 34-tile grid feels dense on iPad portrait; overflows on mobile. |
| Admin v2 | ✅ | ✅ | ✅ | ⚠️ | Section sidebar collapses correctly. |
| Safety Hub | ✅ | ✅ | ✅ | ⚠️ | Sub-page nav via bottom bar; mobile OK. |
| HR Hub | ✅ | ✅ | ✅ | ⚠️ | Long employee tables scroll horizontally. |
| PM Hub | ✅ | ✅ | ⚠️ | ⚠️ | Command Center more mobile-friendly than Hub. |
| Shop Hub | ✅ | ✅ | ✅ | ⚠️ | Fine. |
| Dispatch V2 | ✅ | ✅ | ✅ | ⚠️ | Schedule board needs pinch-zoom on iPad. |
| Fleet Visibility | ✅ | ⚠️ | ⚠️ | ❌ | Wide data table breaks below 900px — P2 fix. |
| Field | ✅ | ✅ | ✅ | ✅ | Field is mobile-first by design. |
| Guidance | ✅ | ✅ | ✅ | ✅ | Text-heavy · fine. |

## Findings
- **Fleet Visibility** is the only surface with a mobile-breaking layout (P2 in Remediation Roadmap).
- Every other portal is at minimum acceptable on iPad portrait.
- Mobile-native shell remains a P3 backlog item — this track does not attempt to fix it.

## Standard for future Command Centers
- No horizontal page overflow at 375px.
- Attention Strip must collapse from 5-col → 2-col.
- Action Queue tables must scroll horizontally within a container (never blow out the page).
- Drawer / modal surfaces must be full-screen on mobile.
