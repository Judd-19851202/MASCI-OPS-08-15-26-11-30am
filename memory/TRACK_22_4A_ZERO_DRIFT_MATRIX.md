# TRACK 22.4A · Zero-Drift Matrix

**Date:** 2026-02-04
**Attestation:** Backend is byte-for-byte behavior-identical post-refactor.

| Layer | Before | After | Δ | Verified by |
|---|---:|---:|---:|---|
| Route count | 1,441 | 1,441 | 0 | `test_route_and_openapi_parity` |
| Method count | 1,445 | 1,445 | 0 | `test_route_and_openapi_parity` |
| OpenAPI paths | 1,264 | 1,264 | 0 | `test_route_and_openapi_parity` |
| Middleware | 7 | 7 | 0 | Runtime probe |
| `LIFECYCLE_STEPS` | 51 | 51 | 0 | `platform_status()` |
| `SHUTDOWN_STEPS` | 1 | 1 | 0 | `platform_status()` |
| `on_startup` legacy | 0 | 0 | 0 | `test_lifecycle_complete_unchanged` |
| `on_shutdown` legacy | 0 | 0 | 0 | `test_lifecycle_complete_unchanged` |
| Bytecode fingerprints | 9/9 clean | 9/9 clean | 0 | `verify_locked_bytecode` |
| `lifecycle_complete` | true | true | 0 | `platform_status()` |
| `EMAIL_SAFETY_MODE` | strict | strict | 0 | `test_email_safety_strict_mode_intact` |
| `resend_sdk_patched` | true | true | 0 | `test_email_safety_strict_mode_intact` |
| `live_emails_possible` | false | false | 0 | `test_email_safety_strict_mode_intact` |
| `GenericPayload.model_fields` | `{}` | `{}` | 0 | Runtime probe |
| `GenericPayload.model_config.extra` | `"allow"` | `"allow"` | 0 | `model_config = ConfigDict(extra="allow")` |
| Pydantic V1 `class Config` count | 1 | **0** | **−1** | `test_zero_pydantic_v1_class_config_in_backend` |
| Runtime `PydanticDeprecatedSince20` from passkeys | 1 | **0** | **−1** | `test_runtime_no_pydantic_class_config_deprecation` |

## Semantic parity — the only change
```diff
-    class Config:
-        extra = "allow"
+    model_config = ConfigDict(extra="allow")
```
Both forms configure the same `model_config["extra"] = "allow"` at the Pydantic V2 core level. Zero behavioral change.

## Constitutional attestation
- Behavior identical: ✅
- Contract identical: ✅
- Warnings reduced: ✅ (only movement is downward)
- Fingerprints stable: ✅
- No suppression added: ✅
