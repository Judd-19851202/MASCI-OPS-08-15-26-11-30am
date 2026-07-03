# SIX PILLAR SCORING RUBRIC

**Doctrine:** The Six Pillars are the north star for every operational decision in MASCI / ForgedOps. Every feature is scored against them.
**Established:** Track 19.30 · 2026-07-03
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

---

## The Six Pillars

1. **Powerful** — increases operational capability
2. **Simple** — the actual user understands it immediately
3. **Beautiful** — polished, intentional, modern
4. **Trusted** — predictable behavior, no surprises
5. **Proven** — tested, verified, documented, observed
6. **Operational** — works in real field/company conditions

---

## Scoring rubric (0 – 10 per pillar)

### 1 · Powerful

Does it increase the operator's ability to run the business better than before?

| Score | Meaning |
|---|---|
| 10 | Category-defining capability. Unique in the industry. |
| 9 | Meets or exceeds industry leaders on this dimension. |
| 8 | Matches industry leaders (HCSS · Procore · Raken · SafetyCulture · Samsara). |
| 7 | Clear operational lift versus previous state. |
| 6 | Marginal lift. |
| 5 | Feature exists but doesn't move the operational needle. |
| < 5 | Regressive or busywork. |

### 2 · Simple

Would the actual field user (foreman, operator, mechanic, HR reviewer) understand what to do without a training session?

| Score | Meaning |
|---|---|
| 10 | Self-explanatory · zero training required · zero friction. |
| 9 | One label read, then obvious. |
| 8 | Clear after 5 seconds of orientation. |
| 7 | Clear after seeing it once with a peer. |
| 6 | Requires a short guided pass. |
| 5 | Requires ongoing help documentation. |
| < 5 | Users abandon or misuse. |

### 3 · Beautiful

Does it look and feel like something an executive would proudly show?

| Score | Meaning |
|---|---|
| 10 | Category-benchmark visual polish. |
| 9 | Matches the elite of construction SaaS (Procore · Autodesk CC). |
| 8 | Fully aligned to MASCI design-system primitives (`PortalShell` · `Card` · `StatusChip` · `EmptyState`) with intentional typography/spacing. |
| 7 | Consistent with platform conventions, minor visual drift. |
| 6 | Functional but visually inconsistent. |
| 5 | Feels stitched together. |
| < 5 | Draft-quality. |

### 4 · Trusted

Does it behave predictably? No surprises, no data loss, no silent failures?

| Score | Meaning |
|---|---|
| 10 | Full audit trail · rollback · draft restore · idempotent · zero-drift verified. |
| 9 | Complete audit trail + graceful failure paths. |
| 8 | Audit trail exists + error states well-defined. |
| 7 | Reliable but partial audit coverage. |
| 6 | Reliable in happy path only. |
| 5 | Occasional surprises or silent data loss risk. |
| < 5 | Unpredictable. |

### 5 · Proven

Is there evidence — tests, lock tests, real-user validation, documentation?

| Score | Meaning |
|---|---|
| 10 | Full test suite + Playwright smoke + pilot validation + executive signoff. |
| 9 | Full test suite + Playwright smoke + pilot validation. |
| 8 | Full test suite + Playwright smoke. |
| 7 | Full test suite. |
| 6 | Partial test coverage. |
| 5 | Manual verification only. |
| < 5 | Untested. |

### 6 · Operational

Does it work in real field/company conditions — mobile, slow network, gloves, dust, glare, bilingual crews, interrupted sessions?

| Score | Meaning |
|---|---|
| 10 | Field-hardened · autosave · draft restore · session-recovery · bilingual · offline-tolerant. |
| 9 | Field-hardened · bilingual · autosave. |
| 8 | Mobile-first · bilingual. |
| 7 | Mobile-first, English only or partial ES. |
| 6 | Works on mobile with friction. |
| 5 | Desktop-only. |
| < 5 | Doesn't function in field. |

---

## Aggregate scoring bands

| Aggregate | Band | Meaning |
|---|---|---|
| 60 / 60 | **Elite** | Category-defining. Executive-showcase quality. |
| 54 – 59 | **Production Strong** | Ready for broad customer rollout. |
| 48 – 53 | **Pilot Acceptable** | Ready for pilot rollout with monitoring. |
| < 48 | **Not Acceptable** | Do not ship. |

## Automatic NO-GO gates

Regardless of aggregate:
- **Any single pillar below 7 / 10** → NO-GO.
- **Any open P0 defect** → NO-GO.
- **Any open P1 defect** → NO-GO.
- **Any un-documented schema/route/payload drift** → NO-GO.
- **Missing rollback path on a canonicalization change** → NO-GO.

## Scoring discipline

- Score conservatively. A 10 is a category benchmark — reserve it.
- Score with evidence. Every score should reference a specific artifact (test file, audit doc, screenshot, pilot observation).
- Score in the track's closeout document under **SIX PILLAR SCORE**.
- Do not average away a single-pillar failure. A 10/10/10/10/10/6 is still a NO-GO for that pillar.

## Historical scoring reference

- Track 19.29 (Pilot Certification): **55/60** — Powerful 9 · Simple 9 · Beautiful 9 · Trusted 10 · Proven 9 · Operational 9 → **Production Strong · Pilot Ready**.
- Track 19.27 (Platform Truth Pass baseline) per-domain scoring available in `TRACK_19_27_EXECUTIVE_SUMMARY.md`.
