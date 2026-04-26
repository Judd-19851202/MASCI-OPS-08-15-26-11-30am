import axios from "axios";
import { getAdminToken, clearAdminToken } from "@/lib/adminAuth";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  headers: { "Content-Type": "application/json" },
  // Photos as base64 can be large — bump limits
  maxContentLength: 50 * 1024 * 1024,
  maxBodyLength: 50 * 1024 * 1024,
});

// Attach the admin token automatically when present.
api.interceptors.request.use((config) => {
  const token = getAdminToken();
  if (token) {
    config.headers["X-Admin-Token"] = token;
  }
  return config;
});

// On 401 from a protected endpoint, drop the token so the next admin route
// click bounces to /admin/login. We do NOT redirect from here — the
// RequireAdmin guard handles navigation cleanly.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      clearAdminToken();
    }
    return Promise.reject(err);
  }
);
