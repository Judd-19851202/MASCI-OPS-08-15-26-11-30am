# CUSTOMER #2 TABLETOP EXECUTION GUIDE
## OCEP Operational Completion Sprint · Phase 5

**Date**: 2026-06-02
**Authority**: OMEGA · OPERATIONAL COMPLETION SPRINT
**Mode**: READ-ONLY · tabletop simulation script
**Status**: Script ready · operator-conducted simulation pending
**Companion**: `CUSTOMER2_TABLETOP_RISK_REGISTER.md`

---

## 0 · Doctrine

Customer #2 is the litmus test for tribal-knowledge elimination. Every assumption that survives only because Jaymn / Emergent / a developer knows it is a Customer #2 onboarding landmine.

This guide is a tabletop walk-through — no real Customer #2 account is provisioned, no real data is created. The simulation produces evidence of every hidden assumption.

---

## 1 · Simulation framing

> Pretend: A new GC named "Acme Heavy Civil" calls Jaymn on a Monday and says "We want to use your platform. Set us up. We start hiring crews next Monday." Jaymn says yes. The clock starts. The platform is the platform — no engineering changes allowed during the simulation.

Tabletop participants ("the table"):
- **Facilitator** (operator running the tabletop · could be Jaymn for the first run)
- **Recorder** (captures findings · DOES NOT contribute to the simulation)
- **Acme Persona Stand-ins** (one operator playing each of: Acme HR · Acme Safety · Acme PM · Acme Dispatch · Acme Shop · Acme Foreman · Acme Laborer · Acme Executive)

Minimum 3 humans. Recommended 5 humans (HR/Safety/PM in one head; Dispatch/Shop in another; the rest in the Facilitator).

Session length: 4 hours (2 sittings of 2 hours each works).

---

## 2 · Pre-tabletop setup (one-time, ≤ 30 min)

| Step | Owner | Notes |
|---|---|---|
| 1 | Facilitator | Open this guide + the Risk Register in another tab |
| 2 | Facilitator | Open the preview platform (NOT production) |
| 3 | Recorder | Create `/app/memory/customer_2_tabletop_{date}.md` with the empty findings template (§7) |
| 4 | Facilitator | Read §1 framing aloud · table acknowledges |
| 5 | All | No engineering / configuration changes during the simulation. Any hidden config request becomes a finding. |

---

## 3 · The 12-step Customer #2 onboarding walkthrough

For each step:
- Facilitator narrates the step as if they were Acme staff
- Table identifies every assumption that requires Jaymn / Emergent / developer / hidden config knowledge
- Recorder logs findings to the Risk Register

### Step 1 — Tenant / account creation
> "Acme calls Jaymn. Acme is now a customer. Where do they live in the platform?"
- **Probe**: Does Acme get a separate tenant? Subdomain? Database? Or does Acme share the MASCI tenant?
- **Probe**: Who creates the first admin account?
- **Probe**: What email domain do Acme accounts use?

### Step 2 — Branding
> "Acme wants their logo, colours, company name in headers."
- **Probe**: Is there a configurable brand surface?
- **Probe**: Are there hardcoded "MASCI" strings anywhere a user sees?
- **Probe**: Does the JHP poster QR template carry MASCI branding?

### Step 3 — Admin first-login
> "Acme's CFO logs in for the first time as admin. What do they see?"
- **Probe**: Empty-state coaching? Onboarding wizard? Or empty hubs?
- **Probe**: What's the first action they should take? Is it obvious?

### Step 4 — HR seeding (employees + roles)
> "Acme imports their 60 employees. How?"
- **Probe**: CSV upload? Manual? API? Where is the format documented?
- **Probe**: Do they need to seed lifecycle_state per employee?
- **Probe**: How are foreman / super / PM roles assigned?
- **Probe**: What happens with employees who have no email?

### Step 5 — Projects / jobs seeding
> "Acme has 3 active jobs. How do they appear?"
- **Probe**: Project seeding mechanism?
- **Probe**: Are project_numbers free-form or constrained?
- **Probe**: Sub-vendor relationships — how seeded?

### Step 6 — Equipment / fleet seeding
> "Acme has 18 trucks and 22 pieces of yellow iron. How?"
- **Probe**: Fleet seeding mechanism?
- **Probe**: VIN format constraints?
- **Probe**: How is initial pre-shift baseline established?

### Step 7 — JHP library
> "Acme has 25 existing JHPs. Upload them."
- **Probe**: Admin JHP upload (per-project) — does Acme's admin discover this surface?
- **Probe**: Bulk upload? Or one-at-a-time?

### Step 8 — Safety / training records
> "Acme employees have CDLs, medical cards, fall-protection training, OSHA-10/30 cards."
- **Probe**: Where do these records live? Are they HR-side or Safety-side?
- **Probe**: How are expirations seeded?

### Step 9 — Dispatch ramp
> "Acme dispatcher builds tomorrow's board for the first time."
- **Probe**: Empty board · what's the entry-point UX?
- **Probe**: How does Acme dispatcher know which drivers are qualified?

### Step 10 — First production Daily Report
> "Acme's first foreman submits the first DR Monday evening."
- **Probe**: Does the foreman know what to put in each field?
- **Probe**: Where does the DR route? To Acme office? To MASCI? To Jaymn?

### Step 11 — First incident
> "An Acme laborer twists an ankle Tuesday afternoon."
- **Probe**: Who in Acme catches the incident?
- **Probe**: Does the OSHA-recordable path apply?
- **Probe**: Where does the incident route?

### Step 12 — First payroll variance
> "Friday — first variance run for Acme."
- **Probe**: Variance batch finalization gate — who has authority?
- **Probe**: Does Acme see only Acme variance or MASCI's too?

---

## 4 · Cross-cutting probes (run after each step)

After every step, the table answers all four:

| # | Probe | Capture as |
|---|---|---|
| Q1 | Did anyone say "Jaymn would set that up"? | **JAYMN KNOWLEDGE** finding |
| Q2 | Did anyone say "Emergent would do that"? | **EMERGENT KNOWLEDGE** finding |
| Q3 | Did anyone say "We'd need a developer for that"? | **DEVELOPER KNOWLEDGE** finding |
| Q4 | Did anyone say "There's a config / env var for that somewhere"? | **HIDDEN CONFIG** finding |

Each finding goes to the Risk Register with severity.

---

## 5 · Severity scale

| Severity | Trigger | Implication for Customer #2 readiness |
|---|---|---|
| **BLOCKER** | Step cannot proceed without Jaymn / Emergent / developer intervention | Customer #2 cannot onboard self-serve |
| **CRITICAL** | Step proceeds but Acme would have to call Jaymn within 7 days | Customer #2 requires hand-holding |
| **HIGH** | Step proceeds with significant tribal knowledge transfer | Customer #2 needs ≥ 2 hours onboarding |
| **MEDIUM** | Step proceeds but the platform's empty-state UX is unclear | Customer #2 needs ≤ 1 hour onboarding |
| **LOW** | Friction-only; no real blocker | Customer #2 can self-serve with backlog item |

---

## 6 · Pass/fail gates for Customer #2 Readiness

| Gate | Threshold |
|---|---|
| BLOCKER findings open | 0 |
| CRITICAL findings open | ≤ 2 |
| Total findings | ≤ 25 |
| Aggregate Customer #2 Readiness Score | ≥ 70 (see scoring in Risk Register) |

If any gate fails, Customer #2 is **NOT READY** regardless of engineering completion percentage.

---

## 7 · Tabletop output template

The recorder creates `/app/memory/customer_2_tabletop_{date}.md` from this template:

```markdown
# Customer #2 Tabletop · {date}

Facilitator : _________
Recorder    : _________
Persona stand-ins: _________

## Step 1 · Tenant / account creation
Verbatim conversation (paraphrased OK):

Findings raised:
- C2-NNNN  category={JAYMN|EMERGENT|DEVELOPER|HIDDEN_CONFIG}  severity={BLOCKER|CRITICAL|HIGH|MEDIUM|LOW}
  Description: ___
  Suggested fix: ___ (NOT BUILD-AUTHORIZED · candidate only)

(repeat for steps 2-12)

## Aggregate counts
BLOCKER:    ___
CRITICAL:   ___
HIGH:       ___
MEDIUM:     ___
LOW:        ___
TOTAL:      ___

## Customer #2 Readiness Score
{computed per Risk Register scoring formula}

## Facilitator notes
___

## Recorder signature
___
```

---

## 8 · Refusal conditions

The AI agent MUST refuse to:
- Generate fake tabletop transcripts
- Score Customer #2 Readiness without a real tabletop file in `/app/memory/customer_2_tabletop_*.md`
- Mark any §6 gate PASS without explicit operator sign-off
- Add a finding to the Risk Register without it coming from a real tabletop session (AI-inferred candidates go into §3 of the Risk Register as CANDIDATEs only)

---

**End of CUSTOMER #2 TABLETOP EXECUTION GUIDE · OCEP Phase 5**
