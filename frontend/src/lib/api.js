import axios from "axios";
import { getAdminToken, clearAdminToken } from "@/lib/adminAuth";
import { getJwt, clearJwt } from "@/lib/jwtAuth";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  headers: { "Content-Type": "application/json" },
  // No credentials — auth is sent via the Authorization / X-Admin-Token
  // headers so browsers don't reject the wildcard CORS that Cloudflare /
  // Emergent ingress applies. (See lib/jwtAuth.js for the rationale.)
  withCredentials: false,
  // Photos as base64 can be large — bump limits
  maxContentLength: 50 * 1024 * 1024,
  maxBodyLength: 50 * 1024 * 1024,
});

// Attach Crew-Hub JWT and Safety-Admin token to every request automatically.
api.interceptors.request.use((config) => {
  const adminTok = getAdminToken();
  if (adminTok) {
    config.headers["X-Admin-Token"] = adminTok;
  }
  const jwt = getJwt();
  if (jwt && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${jwt}`;
  }
  return config;
});

// On 401, drop whichever token the request was using so the next protected
// route click bounces back to its login page. We don't redirect here — the
// route guards handle navigation cleanly.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      const cfg = err.config || {};
      // If the request had an admin token, clear that one; if it had a JWT,
      // clear that. Don't blow away both — admin and crew-hub sessions are
      // independent.
      if (cfg.headers?.["X-Admin-Token"]) clearAdminToken();
      if (cfg.headers?.Authorization) clearJwt();
    }
    return Promise.reject(err);
  }
);
