import { getAdminToken } from "@/lib/adminAuth";
import { getDirectoryToken } from "@/lib/directoryAuth";

export function buildWave3AdminHeaders(extra = {}) {
  if (typeof window === "undefined") return { ...extra };
  const adminToken = getAdminToken();
  const directoryToken = getDirectoryToken();

  return {
    ...extra,
    ...(adminToken ? { "X-Admin-Token": adminToken } : {}),
    ...(directoryToken ? { "X-Directory-Token": directoryToken } : {}),
  };
}