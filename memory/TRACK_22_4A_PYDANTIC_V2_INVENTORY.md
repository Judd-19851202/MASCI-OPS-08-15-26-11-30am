# TRACK 22.4A · Pydantic V2 Completion — Inventory

**Date:** 2026-02-04
**Method:** AST scan + `grep -rn` across `/app/backend/**/*.py` (excluding `test_track_*`).

## Pre-track inventory (before fix)

| Pattern | Files | Occurrences |
|---|---:|---:|
| `class Config` in BaseModel subclass | 1 | 1 |
| `schema_extra=` | 0 | 0 |
| `json_encoders=` | 0 | 0 |
| `@validator` decorator (V1) | 0 | 0 |
| `@root_validator` decorator (V1) | 0 | 0 |
| `from pydantic import validator` (V1) | 0 | 0 |

## The one occurrence
- **File:** `backend/routes/passkeys.py`
- **Line:** 131–134
- **Class:** `GenericPayload(BaseModel)`
- **Config body:** `extra = "allow"`
- **Why it existed:** WebAuthn ceremony payloads use deep-nested JSON; `extra="allow"` accepts arbitrary keys.
- **Modern replacement:** `model_config = ConfigDict(extra="allow")` — semantically identical.

## Post-track inventory (after fix)

| Pattern | Files | Occurrences |
|---|---:|---:|
| `class Config` in BaseModel subclass | **0** | **0** |
| `schema_extra=` | 0 | 0 |
| `json_encoders=` | 0 | 0 |
| `@validator` decorator (V1) | 0 | 0 |
| `@root_validator` decorator (V1) | 0 | 0 |
| `from pydantic import validator` (V1) | 0 | 0 |

## Runtime warning delta
- Pre-fix: `PydanticDeprecatedSince20: Support for class-based `config` is deprecated ...` fires once per import chain touching `passkeys.py`.
- Post-fix: **0** such warnings.

## What was deliberately NOT touched
- **Nothing.** Backend is 100% clean of Pydantic V1 patterns after the single-file fix.

## Framework exceptions (deliberately preserved)
- Starlette CORS `allow_origin_regex=cors_origin_regex` at `server.py:15831` — not Pydantic; preserved from Track 22.3.
