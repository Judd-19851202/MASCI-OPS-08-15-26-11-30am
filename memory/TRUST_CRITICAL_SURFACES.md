# Trust-Critical Surfaces
## Phase TRUST-1 · 2026-05-27

> The set of platform surfaces a foreman / PM / Safety / FL / superintendent
> actually depends on. Each entry cites the code path and the trust
> categories that apply.

---

## 1 · P0 — Field-critical (audited fully)

### 1.1 · Daily Report (foreman / superintendent · iPhone Safari primary)
| Attribute | Detail |
|---|---|
| Pages | `pages/NewDailyReport.jsx` · `pages/ViewDailyReport.jsx` |
| Lifecycle | autosave (`useFormDraft`) → submit (online OR `enqueueUpload` offline) → commit → confirm |
| Trust categories in play | DATA · CONTEXT · OPERATIONAL · MOBILE · VISIBILITY · CALMNESS |
| Status | iter440/442 hardened · 28/28 P0 regression green |
| Open finds | TF-001 (T4) · TF-004 (T3) · TF-005 (T2) · TF-011 (T3) · TF-016 (T2) |

### 1.2 · Auth / Portal Access
| Pages | `admin/login` · `pm/login` · `hr/login` · `safety/login` · `dispatch/login` · `field-leadership/portal/login` · `auth/multi-login` |
| Backend | `_require_any_portal_token`, per-portal middleware |
| Trust | ACCESS · DATA (indirect via token-rotation) |
| Status | iter440 closed the draft-orphaning consequence |
| Open finds | TF-010 (T3) |

### 1.3 · Shared Navigation / Return Paths
| Pages | `ViewIncident.jsx` (iter443 ✅) · `ViewCAPA.jsx` · `ViewInspection.jsx` · `ViewMeeting.jsx` |
| Hook | `lib/returnContext.js::useReturnContext` |
| Trust | CONTEXT |
| Status | Incident done · CAPA / Inspection / Meeting pending |
| Open finds | TF-003 (T2) · TF-008 (T2) · TF-017 (T2) |

### 1.4 · PM Portal shared operational surfaces
| Pages | `IncidentsDashboard.jsx` (under `/pm/`) · `PmHub.jsx` · PM Project Dashboard |
| Trust | CONTEXT · OPERATIONAL |
| Status | iter443 wired state.from on dashboard click |
| Open finds | TF-017 (T2) |

### 1.5 · Safety shared operational surfaces
| Pages | `SafetyIncidents.jsx` (iter443 ✅) · `SafetyShell` · Incident Center |
| Trust | CONTEXT · OPERATIONAL |
| Status | iter440 V2 default flip · iter443 return-path retargeted |
| Open finds | (none directly · inherits TF-003) |

### 1.6 · Mobile Safari survivability
| Surface | All form pages on iPhone (390x844) viewport |
| Mechanisms | `useFormDraft` lifecycle handlers · `quotaProbe` · `photoDraftStore` · `deviceId` · iter440 page-lifecycle wiring |
| Trust | DATA · MOBILE · VISIBILITY |
| Open finds | TF-001 (T4) · TF-004 (T3) · TF-009 (T2) |

### 1.7 · Draft survivability system
| Files | `lib/resiliency/draftStore.js` · `useFormDraft.js` · `photoDraftStore.js` · `draftTelemetry.js` |
| Status | iter440 architecture |
| Open finds | TF-001 (T4) · TF-002 (T3) · TF-011 (T3) · TF-016 (T2) |

### 1.8 · Restore flows
| Component | `DraftRestorePrompt.jsx` (resilience) · `CrewSetupRestorePrompt.jsx` (memory) |
| Status | iter440 timestamp + cross-token note · iter442 confidence-tiered coaching |
| Open finds | TF-016 (T2) |

### 1.9 · Crew / equipment preload logic
| File | `lib/crewMemory.js` · `components/daily-report/CrewSetupRestorePrompt.jsx` |
| Trust | DATA · CONTEXT · OPERATIONAL · CALMNESS |
| Status | iter442 confidence accrual + project-change guard |
| Open finds | TF-001 (T4) · TF-006 (T2) · TF-007 (T1) |

---

## 2 · P1 — High operational impact (sampled audit)

### 2.1 · JHA · Trench Reports · Inspections · CAPA · Incident workflows
| Surface | Multiple form pages · multiple detail pages |
| Inheritance | All forms use `useFormDraft` (iter440 fixes propagate) |
| Trust | DATA (inherited) · CONTEXT (return-path partial) |
| Open finds | TF-002 (T3) · TF-003 (T2) · TF-015 (T2) |

### 2.2 · PM detail surfaces · Meeting / detail shared views
| Surface | Project Dashboard · CAPA detail · Meeting detail |
| Trust | CONTEXT · CALMNESS |
| Open finds | TF-014 (T1) · TF-017 (T2) |

---

## 3 · P2 — Operationally adjacent (light audit)

### 3.1 · HR · Dispatch · Fleet · Shop · Governance widgets
| Trust | ACCESS · DATA · VISIBILITY |
| Status | Inherits iter440 resiliency primitives where forms are used |
| Open finds | TF-015 (T2 · backend hygiene) |

---

## 4 · Surfaces explicitly OUT of scope

| Surface | Reason |
|---|---|
| Internal admin housekeeping pages | Not field-critical |
| Read-only marketing / landing pages | No operator workflow |
| Internal CI/CD dashboards | Not user-facing |
| Settings / Profile / Preferences pages | No data-loss risk |

---

## 5 · Pattern observed

Across surfaces, the trust-critical components reduce to a small
set of shared primitives:

| Primitive | Surfaces consuming |
|---|---|
| `useFormDraft` | Every long-form editor |
| `lib/resiliency/*` (deviceId, draftStore, photoDraftStore, telemetry, quotaProbe) | Every form |
| `BackLink` + `useReturnContext` | Every shared detail surface |
| `crewMemory` | Daily Report (today) · could extend to Inspections / DPRs in future |
| Draft Health tile + telemetry collection | Admin observability of all forms |

**Hardening the primitives lifts every consuming surface at once.**
This is the leverage point and explains why iter440 (one library
pass) closed 5 distinct field-reported symptoms.

---

## 6 · Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 Surface set bounded · primitives identified
- **Next reading:** `TRUST_GOVERNANCE_STANDARD.md`
