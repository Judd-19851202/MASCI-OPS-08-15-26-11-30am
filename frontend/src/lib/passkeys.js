/**
 * lib/passkeys.js · iter422 · Phase 24 · Passkey Sign-In Continuity
 * ───────────────────────────────────────────────────────────────────
 * Minimal, library-free WebAuthn helpers for MASCI Operations.
 *
 * Two entry points:
 *   - registerPasskey({ friendlyName })   — enroll on the current device
 *   - signInWithPasskey({ email })        — passwordless sign-in
 *
 * DOCTRINE GUARDS:
 *   • Uses ONLY navigator.credentials.* + base64url helpers (no JS lib).
 *   • Device handles ALL biometrics (Face ID / Touch ID / Windows Hello /
 *     Android). MASCI never sees biometric data.
 *   • Password fallback unchanged — these helpers are OPTIONAL convenience.
 */
import { api } from "@/lib/api";
import { getDirectoryToken } from "@/lib/directoryAuth";

// ─────────────────────────────────────────────────────────────────────
// base64url <→ ArrayBuffer helpers (ASCII byte-by-byte · spec-compliant)
// ─────────────────────────────────────────────────────────────────────
function bufferToBase64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function base64urlToBuffer(b64url) {
  let s = String(b64url || "").replace(/-/g, "+").replace(/_/g, "/");
  const pad = s.length % 4;
  if (pad === 2) s += "==";
  else if (pad === 3) s += "=";
  const binary = atob(s);
  const buf = new ArrayBuffer(binary.length);
  const bytes = new Uint8Array(buf);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return buf;
}

// ─────────────────────────────────────────────────────────────────────
// Feature detection
// ─────────────────────────────────────────────────────────────────────
export function passkeySupported() {
  return typeof window !== "undefined"
    && typeof window.PublicKeyCredential !== "undefined"
    && typeof navigator !== "undefined"
    && navigator.credentials
    && typeof navigator.credentials.create === "function"
    && typeof navigator.credentials.get === "function";
}

export async function platformAuthenticatorAvailable() {
  if (!passkeySupported()) return false;
  try {
    return !!(await window.PublicKeyCredential
      .isUserVerifyingPlatformAuthenticatorAvailable());
  } catch {
    return false;
  }
}

// ─────────────────────────────────────────────────────────────────────
// REGISTER · current directory user enrolls a device passkey
// ─────────────────────────────────────────────────────────────────────
export async function registerPasskey({ friendlyName } = {}) {
  if (!passkeySupported()) {
    throw new Error("Device sign-in is not available in this browser");
  }
  const dirToken = getDirectoryToken();
  if (!dirToken) {
    throw new Error("Please sign in with your password first");
  }

  // 1. Get options from server
  const optResp = await api.post("/passkeys/register/options", {});
  const options = optResp.data?.publicKey;
  if (!options) throw new Error("Could not start device enrollment");

  // 2. Convert base64url fields to ArrayBuffers
  const publicKey = {
    ...options,
    challenge: base64urlToBuffer(options.challenge),
    user: { ...options.user, id: base64urlToBuffer(options.user.id) },
    excludeCredentials: (options.excludeCredentials || []).map((c) => ({
      ...c,
      id: base64urlToBuffer(c.id),
    })),
  };

  // 3. Browser ceremony (Face ID / Touch ID / etc.)
  const credential = await navigator.credentials.create({ publicKey });
  if (!credential) throw new Error("Device sign-in cancelled");

  // 4. Encode response for server
  const attestation = {
    id: credential.id,
    rawId: bufferToBase64url(credential.rawId),
    type: credential.type,
    response: {
      clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
      attestationObject: bufferToBase64url(credential.response.attestationObject),
    },
    clientExtensionResults: credential.getClientExtensionResults
      ? credential.getClientExtensionResults() : {},
    friendly_name: friendlyName || "Device passkey",
  };

  const verifyResp = await api.post("/passkeys/register/verify", attestation);
  return verifyResp.data;
}

// ─────────────────────────────────────────────────────────────────────
// SIGN-IN · use enrolled passkey to authenticate (returns multi-login shape)
// ─────────────────────────────────────────────────────────────────────
export async function signInWithPasskey({ email }) {
  if (!passkeySupported()) {
    throw new Error("Device sign-in is not available in this browser");
  }
  const cleanEmail = (email || "").trim().toLowerCase();
  if (!cleanEmail) throw new Error("Enter your email first");

  // 1. Get options from server (returns options even if user has no passkeys,
  //    to avoid email-enumeration leakage — the ceremony just fails downstream)
  const optResp = await api.post("/passkeys/login/options", { email: cleanEmail });
  const options = optResp.data?.publicKey;
  if (!options) throw new Error("Could not start device sign-in");

  if (!options.allowCredentials || options.allowCredentials.length === 0) {
    throw new Error("No device passkey is registered for this account");
  }

  const publicKey = {
    ...options,
    challenge: base64urlToBuffer(options.challenge),
    allowCredentials: options.allowCredentials.map((c) => ({
      ...c,
      id: base64urlToBuffer(c.id),
    })),
  };

  // 2. Browser ceremony (user does Face ID / Touch ID / Hello)
  const assertion = await navigator.credentials.get({ publicKey });
  if (!assertion) throw new Error("Device sign-in cancelled");

  // 3. Encode + send to verify
  const authPayload = {
    id: assertion.id,
    rawId: bufferToBase64url(assertion.rawId),
    type: assertion.type,
    response: {
      clientDataJSON: bufferToBase64url(assertion.response.clientDataJSON),
      authenticatorData: bufferToBase64url(assertion.response.authenticatorData),
      signature: bufferToBase64url(assertion.response.signature),
      userHandle: assertion.response.userHandle
        ? bufferToBase64url(assertion.response.userHandle) : null,
    },
    clientExtensionResults: assertion.getClientExtensionResults
      ? assertion.getClientExtensionResults() : {},
  };

  const verifyResp = await api.post("/passkeys/login/verify", authPayload);
  return verifyResp.data;
}

// ─────────────────────────────────────────────────────────────────────
// LIST · enrolled passkeys for the current directory user
// ─────────────────────────────────────────────────────────────────────
export async function listPasskeys() {
  const r = await api.get("/passkeys/list");
  return r.data?.passkeys || [];
}

// ─────────────────────────────────────────────────────────────────────
// REVOKE · disable an enrolled passkey
// ─────────────────────────────────────────────────────────────────────
export async function revokePasskey(credentialId) {
  const r = await api.delete(`/passkeys/${encodeURIComponent(credentialId)}`);
  return r.data;
}
