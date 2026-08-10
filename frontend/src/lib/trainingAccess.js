import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { isShop } from "@/lib/shopAuth";
import { isHr } from "@/lib/hrAuth";
import { isFl } from "@/lib/flAuth";
import { isLeadershipAuthed } from "@/lib/leadershipAuth";

export const TRAINING_PACKET_TRACKS = new Set(["field", "shop", "pm", "admin", "hr"]);

export function hasFieldLeadershipTrainingAccess() {
  return isFl() || isLeadershipAuthed();
}

export function trainingAudienceAllowed(audience) {
  if (!audience || audience === "public") return true;
  if (isAdmin()) return true;
  if (audience === "pm") return isPm();
  if (audience === "shop") return isShop() || isPm();
  if (audience === "leadership") return hasFieldLeadershipTrainingAccess();
  if (audience === "hr") return isHr();
  return false;
}

export function trainingAudienceLoginPath(audience) {
  if (audience === "admin") return "/admin/login";
  if (audience === "pm") return "/pm/login";
  if (audience === "shop") return "/shop/login";
  if (audience === "leadership") return "/field-leadership/portal/login";
  if (audience === "hr") return "/hr/login";
  return "/";
}

export function trainingAudienceLabel(audience, lang = "en") {
  const en = {
    admin: "Admin",
    pm: "Project Manager",
    shop: "Shop",
    leadership: "Field Leadership",
    hr: "HR Manager",
  };
  const es = {
    admin: "Administrador",
    pm: "Gerente de Proyecto",
    shop: "Taller",
    leadership: "Liderazgo de Campo",
    hr: "Gerente RRHH",
  };
  return (lang === "es" ? es : en)[audience] || audience;
}

export function supportsTrainingPacket(trackSlug) {
  return TRAINING_PACKET_TRACKS.has(String(trackSlug || "").trim().toLowerCase());
}