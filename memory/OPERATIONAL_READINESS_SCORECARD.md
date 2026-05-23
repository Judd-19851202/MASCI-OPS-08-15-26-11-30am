# OPERATIONAL READINESS SCORECARD
**Audit date:** 2026-05-23
**Scale:** 0 (broken) · 1 (technical only) · 2 (partial) · 3 (operationally usable) · 4 (strong) · 5 (production-ready enterprise)
**Average score (preview):** 3.2 / 5 — **strong technical surface · uneven operational continuity**
**Average score (production):** 2.1 / 5 — **production drift drags every score**

---

## Domain scores

### Authentication & RBAC
| Aspect | Preview | Prod | Notes |
|---|---|---|---|
| Multi-portal directory | 4 | 4 | Solid · iter82 hardened |
| Per-portal bcrypt password resets | 4 | 4 | All 6 portals working |
| Shared HR+Safety+Admin accountability gate | **4** | **0** | iter353a not deployed |
| MFA | 0 | 0 | Queued iter357 |

### Employee Accountability
| Aspect | Preview | Prod |
|---|---|---|
| Master record | 4 | 4 |
| CDL / medical lifecycle | 4 | 3 |
| Accountability timeline | **5** | **0** |
| Compliance Brief PDF | **5** | **0** |
| Cross-portal write authority (iter353a) | **5** | **0** |
| Hard-delete prevention (HR no hard delete) | 5 | n/a |

### Driver Qualification
| Aspect | Preview | Prod |
|---|---|---|
| HR dashboard | 4 | 4 |
| Bulk roster importer (iter352) | **4** | **0** |
| Dispatch read-only view (iter353b) | **4** | **0** |
| FL read-only view | 4 (rich) | 2 (slim) |
| "Drivers Available Right Now" (iter353b-availability) | **5** | **0** |

### Incidents & CAPA
| Aspect | Score |
|---|---|
| Public submission | 4 |
| Safety review | 3 |
| HR aggregate view | **1** (only via timeline drill-down) |
| FL view of own-site incidents | 0 |
| Closeout chain enforcement | 1 (CAPA exists, ladder not enforced) |
| OSHA 300/301/300A export | 2 (not directly tested this audit but routes exist in safety_exports) |

### Daily Reports
| Aspect | Score |
|---|---|
| Field submission | 4 |
| PM scoped review | 4 |
| Payroll variance | 3 |
| HR labor visibility | 0 (HR 401) |
| FL self-audit | 0 |
| Long-tail rediscoverability (>90d) | 1 |

### Equipment / Fleet
| Aspect | Score |
|---|---|
| Pre-Op submission | 4 |
| Shop sign-off + fan-out | 4 |
| PM scoped view | 4 |
| Operator employee_id linkage | 1 |
| Asset transfer audit | 3 |

### Training / Certifications
| Aspect | Score |
|---|---|
| Safety write | 4 |
| HR shared write (iter353a) | **4** preview · **0** prod |
| Expiration notification fan-out | 2 (cron live; PM/FL recipients missing) |
| PM scoped view | 0 |
| FL scoped view | 0 |

### PPE / Equipment Issuance
| Aspect | Score |
|---|---|
| Safety issuance | 4 |
| Timeline aggregation (iter353c) | **5** preview · **0** prod |
| PM scoped view | 0 |
| FL scoped view | 0 |
| Recall (lost / re-issued) | 2 |

### QA/QC
| Aspect | Score |
|---|---|
| Submission | 4 |
| PM scoped review | 4 |
| Fan-out (qaqc.deficiency observed) | 3 |
| FL recipient | 0 |
| Closeout chain | 2 |

### Notification / Escalation
| Aspect | Score |
|---|---|
| Collection populated | 3 |
| Safety + PM fan-out | 4 |
| HR fan-out | 0 |
| FL fan-out | 0 |
| Dispatch fan-out | 0 |
| Email delivery (Resend) | 4 (when AUTO_EMAIL_REPORTS=true) |
| SMS / push | 0 (delivery dict supports it, not wired) |

### Mobile / Offline
| Aspect | Score |
|---|---|
| Mobile 390 layouts | 4 (verified iter353b/c via testing agent) |
| Offline form submission | 2 (PWA partial) |
| Spotty service survival | 2 |

### Production parity
| Aspect | Score |
|---|---|
| Health endpoint up | 5 |
| iter330–iter353c deployment | **1** (24 iters pending) |
| Data parity (CDL roster) | 2 (iter351 load preview-only) |

### Audit / Governance
| Aspect | Score |
|---|---|
| Audit collection (`admin_audit`) | 4 |
| Audit attribution on shared records | 5 (iter353a/iter353c) |
| Governance gap audit docs | 5 (Phase 1 done) |
| Governance Health Tile | 0 (queued) |

### Documents / Discoverability
| Aspect | Score |
|---|---|
| Upload | 4 |
| Magic-byte validation | 4 |
| Employee linkage (iter353c timeline aggregation) | 5 |
| Long-tail recall | 2 |

---

## Roll-up
- **Strongest domains:** Employee Accountability (preview), Auth/RBAC, Driver Qualification (preview).
- **Weakest domains:** Notification/Escalation fan-out, Production parity, FL/PM cross-portal training & PPE visibility.

---

## Three-month path to 4.5+ average
1. **Deploy.** Closes ~50% of all gaps in this scorecard in one click. (iter353-deploy)
2. **Wire FL + PM read-only into training_records + equipment_issuances + incidents.** (iter353b-followup · iter353d?)
3. **Extend recipient_role fan-out to FL.** (iter356-followup)
4. **Operator-employee linkage on Pre-Op + Equipment Inspections.** (iter360)
5. **Closeout ladder enforcement: incident → CAPA → closed.** (iter361)
6. **Governance Health Tile.** (iter353-health)
