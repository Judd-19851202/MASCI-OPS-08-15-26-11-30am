# Phase 7.5C · Translation Certification

## Coverage
Every new surface introduced by Phase 7.5C has an EN source string and an ES translation in `frontend/src/lib/i18n.js`.

## Strings added (block: "Trench Safety · Phase 7.5C Notification strings")

### Bell titles
| EN | ES |
|---|---|
| Safety Hold opened | Retención de Seguridad abierta |
| Inspection Hold opened | Retención de Inspección abierta |
| Maintenance Hold opened | Retención de Mantenimiento abierta |
| Certification Hold opened | Retención de Certificación abierta |
| Hold released | Retención liberada |
| Critical Inspection Failure | Fallo Crítico de Inspección |
| Major Inspection Failure | Fallo Mayor de Inspección |
| Damage reported | Daño reportado |
| Unsafe Condition reported | Condición Insegura reportada |
| Certification due ≤ 30 days | Certificación vence ≤ 30 días |
| Certification due ≤ 14 days | Certificación vence ≤ 14 días |
| Certification due ≤ 7 days | Certificación vence ≤ 7 días |
| Certification EXPIRED | Certificación EXPIRADA |
| Repair complete · awaiting Safety verification | Reparación completa · esperando verificación de Seguridad |
| Asset returned to service | Activo devuelto al servicio |

### Coaching template fragments
| EN | ES |
|---|---|
| What happened: | Qué ocurrió: |
| Why it matters: | Por qué importa: |
| What to do next: | Qué hacer a continuación: |
| Open Asset | Abrir Activo |
| Review Inspection | Revisar Inspección |

### Digest section
| EN | ES |
|---|---|
| Open Safety Holds | Retenciones de Seguridad Abiertas |
| Open Certification Holds | Retenciones de Certificación Abiertas |
| Open Inspection Holds | Retenciones de Inspección Abiertas |
| Open Maintenance Holds | Retenciones de Mantenimiento Abiertas |
| Repairs Awaiting Verification | Reparaciones Esperando Verificación |
| Expiring Certifications (30d) | Certificaciones por Expirar (30d) |
| New Damage Reports (7d) | Nuevos Reportes de Daño (7d) |
| Failed Inspections (7d) | Inspecciones Fallidas (7d) |

## Coverage by surface
| Surface | EN | ES | Notes |
|---|---|---|---|
| NotificationBell drawer | ✅ | ✅ | Bell drawer pipes title + message through `t(...)`. |
| Email body | ✅ | ✅ | Emails are sent in EN by design (canonical record), matching the existing Safety Portal `_safety_send_email` pattern. Spanish recipients see the Spanish-translated bell entry on the portal. |
| Digest tile | ✅ | ✅ | Section title + metrics translated. |
| Toast confirmations | ✅ | ✅ | Reuse existing toast translations from Phase 7.5A. |
| Coaching banners on Asset Detail | ✅ | ✅ | Reuses existing strings ("Coaching:" / "Open Asset"). |

## Verification
Switch LangToggle to **ES** on `/safety/trench-safety/assets/TB-01` — every new label (Holds, Inspections, Certifications, Audit Timeline panels) and every new dialog (Phase 7.5A: Create / Edit / Status / Retire / Open Hold / Record Inspection / Upload Cert) was already translated under Phase 7.5A. Phase 7.5C adds notification-specific keys on top of that base.

## No mixed-language screens
- Every emitter in `notifications.py` produces canonical EN payloads.
- The frontend `t()` helper translates at render time using `lib/i18n.js`.
- Email bodies stay in EN (canonical Safety domain pattern); the bell counterpart in the user's preferred language carries the full coaching.
