# Track 19.09 · Bilingual Parity Amendment · Verification Report

## Doctrine

Every new operator-facing string introduced during any redesign iteration must exist in both English and Spanish via the existing `frontend/src/lib/i18n.js` dictionary. Missing keys silently fall back to the English literal — from the operator's perspective this is broken Spanish mode.

## Audit performed

Every string introduced in Tracks 19.06 Amendment · 19.07 · 19.09 (Phases 3, 5, 8) was scanned. Missing Spanish translations were identified and added.

## Coverage table (35 new translation keys)

### Phase 3 · Equipment Pre-Op Camera Gate (14 keys)

| English | Spanish | Test |
| --- | --- | --- |
| Camera System Safety Check | Verificación de Seguridad del Sistema de Cámaras | ✅ |
| Does this equipment have a camera system? | ¿Este equipo tiene un sistema de cámaras? | ✅ |
| Are the front-facing camera and interior-facing camera free and clear of obstructions? | ¿Las cámaras delantera e interior están libres y despejadas de obstrucciones? | ✅ |
| Yes | Sí | ✅ |
| No | No | ✅ (whitelisted — identical in ES) |
| Not sure | No estoy seguro | ✅ |
| Yes — clear | Sí — despejadas | ✅ |
| No — obstruction present | No — hay obstrucción | ✅ |
| Safety-critical · Submission blocked | Crítico de seguridad · Envío bloqueado | ✅ |
| Clear the obstruction before operating. Camera visibility must be free and clear. | Despeje la obstrucción antes de operar. La visibilidad de las cámaras debe estar libre y clara. | ✅ |
| Describe the obstruction (optional — for shop record) | Describa la obstrucción (opcional — para el registro del taller) | ✅ |
| e.g. mud on lens, cracked housing, tape covering camera | p. ej., lodo en el lente, carcasa rota, cinta cubriendo la cámara | ✅ |
| Answer the camera system question before submitting | Responda la pregunta del sistema de cámaras antes de enviar | ✅ |
| Confirm whether the cameras are free and clear of obstructions | Confirme si las cámaras están libres y despejadas de obstrucciones | ✅ |

### Phase 5 · DVIR Camera Gate (1 key — rest are shared)

| English | Spanish | Test |
| --- | --- | --- |
| Does this truck have a camera system? | ¿Este camión tiene un sistema de cámaras? | ✅ |

### Phase 8 · Downstream commitment confirmation (10 keys)

| English | Spanish | Test |
| --- | --- | --- |
| Submitted — here's what happens next | Enviado — esto es lo que sigue | ✅ |
| PDF is being rendered and stored. | Se está generando y guardando el PDF. | ✅ |
| Auto-emails have been queued. | Los correos automáticos se pusieron en cola. | ✅ |
| Shop and Dispatch will see any defects immediately. | El taller y despacho verán cualquier defecto de inmediato. | ✅ |
| Safety and the PM will be notified per project routing. | Seguridad y el PM serán notificados según la ruta del proyecto. | ✅ |
| Show technical details | Mostrar detalles técnicos | ✅ |
| Hide technical details | Ocultar detalles técnicos | ✅ |
| Correlation ID | ID de correlación | ✅ |
| PDF ID | ID del PDF | ✅ |
| Done | Listo | ✅ |

### Track 19.06 Amendment retro-fill (6 keys — previously EN-only)

| English | Spanish | Test |
| --- | --- | --- |
| Prefilled from previous report | Rellenado del informe anterior | ✅ |
| Crew and equipment were prefilled from the previous matching report. Review and adjust hours before submitting. | La cuadrilla y el equipo se rellenaron desde el informe anterior coincidente. Revise y ajuste las horas antes de enviar. | ✅ |
| Got it | Entendido | ✅ |
| Prior common time pattern is prefilled — you review and adjust hours before submit. | Se rellenó el patrón de horario previo común — usted revisa y ajusta las horas antes de enviar. | ✅ |
| Reset hours | Reiniciar horas | ✅ |
| Clear this row's prefilled start / stop / lunch — name and trade stay. | Borra la entrada / salida / almuerzo rellenados de esta fila — el nombre y el oficio permanecen. | ✅ |

### Track 19.07 cognitive checkpoints retro-fill (8 keys — previously EN-only)

| English | Spanish | Test |
| --- | --- | --- |
| Who was there | Quiénes estuvieron | ✅ |
| What got done | Qué se hizo | ✅ |
| What impacted today | Qué impactó hoy | ✅ |
| What moved | Qué se movió | ✅ |
| Was the job safe | El trabajo fue seguro | ✅ |
| What happens next | Qué sigue | ✅ |
| Additional context (rarely needed) | Contexto adicional (rara vez necesario) | ✅ |
| Operational notes (optional) | Notas operacionales (opcional) | ✅ |

## Regression test

`backend/tests/test_track_19_09_operational_forms_modernization.py` parametrizes over every one of these keys via `test_spanish_translation_exists[…]`. Any future PR that removes a key or replaces the ES value with a placeholder fails this test.

## Preserved translate-on-submit contract

* When a Spanish crew member fills out any operational form in ES mode, they type freely in Spanish.
* On submit, `translateUserInput(payload, "es")` translates the free-text fields via the platform's OpenAI-backed translator before the payload leaves the client.
* Backend, PDFs, emails, PM/Admin/Safety portals, and historical records all remain in English — as documented in the Track 19.09 Amendment doctrine.
* This contract is preserved verbatim by Track 19.09 (no changes to `translateOnSubmit.js`, no changes to the submit-language payload key).

## Result

**Zero EN-only strings introduced by Track 19.09.** Full bilingual parity locked by 35 `test_spanish_translation_exists` assertions.
