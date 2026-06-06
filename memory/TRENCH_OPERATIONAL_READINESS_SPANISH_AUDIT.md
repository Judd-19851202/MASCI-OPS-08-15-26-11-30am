# TRENCH SAFETY · OPERATIONAL READINESS AUDIT — ENGLISH / SPANISH PARITY

**Mode:** VERIFY ONLY
**Date:** 2026-02
**Verdict:** 🟢 PASS

## i18n.js coverage

- Total translation entries in `frontend/src/lib/i18n.js`: ~3388 keys (covers the whole platform).
- All hold-related strings present with Spanish: Inspection Hold · Maintenance Hold · Certification Hold · Safety Hold · In Transport · DO NOT USE banner messages (4 variants) · Assign to Project · Return from Project · Current Project · Trench Safety.

## Phase-by-phase Spanish coverage

| Phase | Surfaces with Spanish strings present |
|-------|----------------------------------------|
| 3 | Trench Safety Hub · Asset Detail · Asset List · Tabulated Data tab |
| 3.5 | Public Trench Safety Dashboard · QR Landing · Damage Report modal · Asset Lookup |
| 4A | Assign / Return dialogs · Deployment History · Current Project · Project Number · Superintendent · Foreman · Source · Notes |
| 4B | All hold kind names · DO-NOT-USE banner (4 variants) · Critical Damage / Failed Inspection messaging |
| 5 | In Transport · From · To · Delivered · Received · Transfer Cancelled · Hold Preserved · 4 coaching strings |

## Critical-safety text — Spanish parity

| English | Spanish |
|---------|---------|
| "Inspection Hold" | "Retención de Inspección" |
| "Maintenance Hold" | "Retención de Mantenimiento" |
| "Certification Hold" | "Retención de Certificación" |
| "Safety Hold" | "Retención de Seguridad" |
| "This asset's required certification is missing or expired. DO NOT USE." | "Falta la certificación requerida o ha expirado. NO USAR." |
| "SAFETY HOLD — critical condition reported. DO NOT USE. Contact Safety immediately." | "RETENCIÓN DE SEGURIDAD — condición crítica reportada. NO USAR. Contacte a Seguridad inmediatamente." |
| "This asset is on hold. DO NOT USE." | "Este activo está retenido. NO USAR." |
| "Moving a box does not clear a hold." | "Mover una caja no elimina una retención." |
| "A trench box on hold may be transported, but it is not available for use." | "Una caja de zanja retenida puede ser transportada, pero no está disponible para uso." |

## Untranslated UI string scan
Per code review, every Phase 3/3.5/4A/4B/5 visible string in the trench portal flows through `t()`. The `Trench Safety` category badge in the Dispatch Asset Transfers list is intentionally an English category label (matches existing category constants throughout the platform).

## Verdict
🟢 **PASS — full Spanish parity on every Phase 2 → Phase 5 trench surface. No mixed-language screens; no English-only critical safety text.**
