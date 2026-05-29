# Advisory Flag · Certification

_Phase V.2 · Wave-1A · 2026-05-29 · informational signals only._

> Advisory flags surface **signals**, not actions. They never create
> RFIs. They never modify schedules. They never notify anyone. They
> simply tell the PM what the foreman just told them — restated as
> a structured flag.

---

## 1 · The two flags

| Flag | Lives on | Meaning |
|---|---|---|
| `may_require_rfi` | `ConstraintRow` | The foreman's constraint looks like the kind of issue that often becomes an RFI candidate |
| `may_affect_schedule` | `ConstraintRow` | The foreman's constraint looks like the kind that often pushes schedule |

Both default to `false`. Server overwrites `true` at insert based
on the operator-approved heuristic table below.

## 2 · Derivation table (operator-approved · deterministic)

| `constraint_type` | `may_require_rfi` | `may_affect_schedule` | Rationale |
|---|---|---|---|
| `weather` | ❌ | ✅ | weather rarely needs an RFI but often shifts production |
| `utility` | ✅ | ✅ | undocumented utilities are textbook RFI material AND delay-causing |
| `survey` | ✅ | ❌ | bad layout / missing control is RFI material; rarely the schedule driver alone |
| `material` | ❌ | ✅ | late delivery shifts schedule; rarely an RFI |
| `equipment` | ❌ | ✅ | breakdown shifts schedule; rarely an RFI |
| `trucking` | ❌ | ❌ | usually absorbed by dispatch |
| `mot` | ❌ | ✅ | MOT changes shift schedule; the contract change is owner-engineer-driven |
| `cei_inspection` | ✅ | ❌ | CEI holds are RFI candidates against the spec |
| `owner_engineer` | ✅ | ❌ | owner direction is RFI material almost by definition |
| `safety` | ❌ | ❌ | safety holds are governed by safety, not RFI or schedule |
| `other` | ❌ | ❌ | catch-all — no presumption |

The table is **operator-approved and editable.** No machine
learning. No drift over time. Changes require a doctrine update,
not a silent code change.

## 3 · What the flags do NOT do

| Action | Status |
|---|---|
| Create an RFI | ❌ NEVER (no RFI module exists in this wave; locked behind separate authorization) |
| Modify any schedule | ❌ NEVER (no schedule module; locked behind separate authorization) |
| Push to P6 | ❌ NEVER (no P6 integration; locked behind separate authorization) |
| Send a notification | ❌ NEVER |
| Auto-create dispatch tasks | ❌ NEVER |
| Change foreman workflow | ❌ NEVER (foreman doesn't see them at all) |
| Add a foreman field | ❌ NEVER (flags derive from `constraint_type`) |

## 4 · Surface placement

| Surface | Visibility |
|---|---|
| Foreman entry flow | INVISIBLE · server-side only |
| PM panel · constraint detail | VISIBLE · informational chip ("Potential RFI candidate" · "Potential schedule impact") · Wave-1B / Wave-1C UI |
| Superintendent review queue | VISIBLE · grouped by flag · Wave-1B / Wave-1C UI |
| External PDF (DOT / FAA / CEI / owner) | INVISIBLE · stripped per audience projection · operator metadata only |
| Audit log | OBSERVABLE · part of the canonical envelope |

## 5 · Surface copy (operator-approved · calm)

| Flag true | UI copy (informational only) |
|---|---|
| `may_require_rfi` | "Potential RFI candidate" |
| `may_affect_schedule` | "Potential schedule impact" |

No alarm. No call-to-action. No exclamation. The PM decides what,
if anything, to do.

## 6 · Backward compatibility

Existing daily_reports rows have no `constraints` field and
therefore no advisory flags. New rows derive flags at insert.
Re-inserts (e.g. via PUT) re-derive at write time.

## 7 · Test coverage

`tests/odr/test_wave_1a.py::test_advisory_flags_derived` — 🟢

Verifies:
- `utility` row gets BOTH flags = true
- `weather` row gets `may_affect_schedule = true` only
- `other` row gets neither

## 8 · Forward operator decisions (NOT in scope)

| Future option | Status |
|---|---|
| Operator-defined override on a row (e.g. lock `may_require_rfi = false` even though server would derive true) | Wave-2 candidate · requires a `_advisory_locked: bool` field; not in Wave-1A |
| Per-project derivation overrides | Wave-2+ |
| Confidence score (probabilistic) | Out of scope · operator wants deterministic signals only |
| ML-driven derivation | Forbidden · the contract is operator-defined, not learned |

## 9 · Doctrine alignment

| Doctrine | Alignment |
|---|---|
| Doctrine Lock #1 (Simplicity Test) | ✅ Foreman sees nothing new |
| Doctrine Lock #2 (Platform Inheritance) | ✅ No new component; flag rendering reuses the PM panel chip pattern |
| Operational Calmness | ✅ "Potential" copy · no urgency · no red |
| Cross-Portal Coaching Standard | ✅ Non-punitive |

## 10 · Operator-facing one-liner

> **The platform notices patterns. The platform does not act on
> them.** Flags inform PMs in calm, non-punitive language. Whether
> an RFI gets opened, a schedule gets adjusted, or nothing happens
> at all — that remains a human decision.

---

_End of ADVISORY_FLAG_CERTIFICATION.md._
