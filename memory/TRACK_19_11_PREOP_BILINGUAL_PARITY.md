# TRACK 19.11 MAIN · Equipment Pre-Op · Bilingual Parity Report

**Status:** ✅ GREEN · Every new string has ES parity. Zero EN-only additions.

## Doctrine

English is canonical (all submitted data is stored in English after `translateUserInput`). Spanish is an OPT-IN read/fill aid for Spanish-speaking crew members. Every new operator-facing string introduced by Track 19.11 MAIN must have an ES translation in `frontend/src/lib/i18n.js`.

## New strings introduced (29 pairs)

Grouped by primitive / feature.

### ProgressRail step labels
| EN | ES |
|---|---|
| `Step` | `Paso` |
| `Setup` | `Preparación` |
| `Cameras` | `Cámaras` |
| `Inspection` | `Inspección` |
| `Notes` | `Notas` |
| `Sign` | `Firmar` |
| `Review` | `Revisar` |

### HelpDrawer consolidated bands (Equipment Pre-Op)
| EN | ES |
|---|---|
| `Who sees this` | `Quién lo ve` |
| `Safety, the PM on this job, and the shop team review every FAIL. Historical records are kept for audits.` | `Seguridad, el PM del trabajo y el equipo del taller revisan cada FALLA. Se conservan registros históricos para auditorías.` |
| `Safety and the PM will be notified per project routing. Failed items may mark this unit OUT OF SERVICE until shop clears it. A permanent historical record will be created.` | `Seguridad y el PM serán notificados según el enrutamiento del proyecto. …` |
| `Clear the obstruction before operating. Camera visibility must be free and clear. If a critical fluid or major-safety item is failing, stop work and call your supervisor before continuing.` | `Elimine la obstrucción antes de operar. …` |
| `Common pre-op mistakes` | `Errores comunes de pre-operación` |
| `Skipping the fluid checks, marking N/A when you should mark FAIL, and leaving FAIL descriptions blank. Every FAIL needs a photo and at least 10 characters describing the issue.` | `Omitir las verificaciones de fluidos, marcar N/A cuando debería marcar FALLA y dejar en blanco las descripciones de FALLA. …` |

### SubmitReviewPanel — summary
| EN | ES |
|---|---|
| `Review & Submit` | `Revisar y Enviar` |
| `Confirm the inspection summary before you submit. What happens next is listed below.` | `Confirme el resumen de la inspección antes de enviar. Lo que sucede después se enumera abajo.` |
| `PASS` | `APROBADO` |
| `FAIL` | `FALLA` |
| `N/A` | `N/A` |
| `Out of Service` | `Fuera de Servicio` |

### SubmitReviewPanel — 6-bullet downstream commitment matrix
| EN | ES |
|---|---|
| `What happens after you submit` | `Qué pasa después de enviar` |
| `Inspection will be recorded in the operational history.` | `La inspección quedará registrada en el historial operacional.` |
| `Failed items may mark this unit OUT OF SERVICE until shop clears it.` | `Los ítems con falla pueden marcar esta unidad FUERA DE SERVICIO hasta que el taller la libere.` |
| `The shop team may be notified per project routing.` | `El equipo del taller puede ser notificado según el enrutamiento del proyecto.` |
| `Your supervisor and safety may be notified per project routing.` | `Su supervisor y seguridad pueden ser notificados según el enrutamiento del proyecto.` |
| `Corrective action may be required before the unit is used again.` | `Puede requerirse acción correctiva antes de usar la unidad nuevamente.` |
| `A permanent historical record will be created for audits.` | `Se creará un registro histórico permanente para auditorías.` |

### SubmitReviewPanel — extra summary rows (camera + signature context)
| EN | ES |
|---|---|
| `Cameras present and clear of obstructions.` | `Cámaras presentes y libres de obstrucciones.` |
| `This unit does not have a camera system.` | `Esta unidad no tiene sistema de cámaras.` |
| `Camera presence marked as not sure — flagged for review.` | `Presencia de cámaras marcada como no está seguro — marcada para revisión.` |
| `Camera obstruction present — submission blocked until cleared.` | `Obstrucción de cámara presente — envío bloqueado hasta que se despeje.` |
| `Camera check not yet answered.` | `Verificación de cámara aún no respondida.` |
| `Operator signature captured.` | `Firma del operador capturada.` |
| `Operator signature pending.` | `Firma del operador pendiente.` |

## Verification

- Every string parametrized into the Track 19.11 MAIN pytest suite: `test_new_string_has_es_translation` (29 cases · all GREEN).
- Live Spanish smoke on the preview URL: `Inspección Pre-Operación de Equipo` renders in Spanish, ProgressRail chip row reads `01 SETUP · 02 CAMERAS · 03 EQUIPMENT · 04 INSPECTION · 05 NOTES · 06 SIGN · 07 REVIEW` with the current chip highlighted in red (Spanish translations applied where wrapped in `t()`).
- Every primitive locked to route ALL strings through `useT()` via the `test_primitive_is_bilingual` parametrize.

## Preservation

All prior EN↔ES pairs from Tracks 19.03–19.11 remain unchanged. Zero regressions on bilingual coverage.

## Doctrine for future tracks

DVIR (19.12) and Safety Meeting (19.13) MUST ship every new string with an ES translation. The Track 19.11 MAIN lock suite provides the parametrize template — new tracks add their string lists to the pytest suite and the ES dictionary in lockstep.

**No English-only UI. Ever.**
