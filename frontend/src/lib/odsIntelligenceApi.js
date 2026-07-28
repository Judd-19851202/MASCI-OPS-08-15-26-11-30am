import axios from "axios";
import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getDirectoryToken } from "@/lib/directoryAuth";

const BASE = `${process.env.REACT_APP_BACKEND_URL}/api/ods`;
const client = axios.create({ baseURL: BASE, timeout: 45000 });

client.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  const admin = getAdminToken();
  const pm = getPmToken();
  const directory = getDirectoryToken();
  if (admin) config.headers["X-Admin-Token"] = admin;
  if (pm) config.headers["X-PM-Token"] = pm;
  if (directory) config.headers["X-Directory-Token"] = directory;
  return config;
});

export async function fetchPmDashboard({ preset = "month", project_ids, date_from, date_to } = {}) {
  const params = { preset };
  if (project_ids?.length) params.project_ids = project_ids.join(",");
  if (date_from) params.date_from = date_from;
  if (date_to) params.date_to = date_to;
  const { data } = await client.get("/pm/dashboard", { params });
  return data;
}

export async function fetchPmProjectKpis(project_id, { preset = "today", date_from, date_to } = {}) {
  const params = { preset };
  if (date_from) params.date_from = date_from;
  if (date_to) params.date_to = date_to;
  const { data } = await client.get(`/pm/projects/${encodeURIComponent(project_id)}/kpis`, { params });
  return data;
}

export async function fetchPmProjectBrief(project_id, { preset = "month" } = {}) {
  const { data } = await client.get(`/pm/projects/${encodeURIComponent(project_id)}/brief`, { params: { preset } });
  return data;
}

export async function fetchAdminDashboard({ preset = "month", date_from, date_to } = {}) {
  const params = { preset };
  if (date_from) params.date_from = date_from;
  if (date_to) params.date_to = date_to;
  const { data } = await client.get("/admin/dashboard", { params });
  return data;
}

export async function fetchAdminDelays({ preset = "month" } = {}) {
  const { data } = await client.get("/admin/delays", { params: { preset } });
  return data;
}

export async function fetchExecutiveBrief({ preset = "month" } = {}) {
  const { data } = await client.get("/executive/brief", { params: { preset } });
  return data;
}

export async function fetchExecutiveHealth({ preset = "month" } = {}) {
  const { data } = await client.get("/executive/health", { params: { preset } });
  return data;
}

export async function fetchAdminAttention({ preset = "this_week", limit = 25 } = {}) {
  const { data } = await client.get("/admin/attention", { params: { preset, limit } });
  return data;
}

export async function fetchPmAttention({ preset = "this_week", project_ids, limit = 25 } = {}) {
  const params = { preset, limit };
  if (project_ids?.length) params.project_ids = project_ids.join(",");
  const { data } = await client.get("/pm/attention", { params });
  return data;
}

export async function fetchPmProjectAttention(project_id, { preset = "this_week", limit = 25 } = {}) {
  const { data } = await client.get(
    `/pm/projects/${encodeURIComponent(project_id)}/attention`,
    { params: { preset, limit } },
  );
  return data;
}

export async function fetchPmProjectOperationalIntelligence(
  project_id, { preset = "this_week", limit = 7 } = {},
) {
  const { data } = await client.get(
    `/pm/projects/${encodeURIComponent(project_id)}/operational-intelligence`,
    { params: { preset, limit } },
  );
  return data;
}

export const PRESETS = [
  { key: "today",      label: "Today" },
  { key: "yesterday",  label: "Yesterday" },
  { key: "this_week",  label: "This week" },
  { key: "last_week",  label: "Last week" },
  { key: "month",      label: "This month" },
  { key: "last_month", label: "Last month" },
  { key: "quarter",    label: "Quarter" },
  { key: "year",       label: "Year" },
];
