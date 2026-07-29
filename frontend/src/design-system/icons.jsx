import React from "react";
import {
  ArrowLeft,
  Award,
  BadgeCheck,
  Check,
  CheckCircle2,
  CircleDashed,
  ClipboardCheck,
  Clock3,
  Compass,
  Home,
  LogIn,
  MapPinned,
  Menu,
  PencilLine,
  RotateCcw,
  RotateCw,
  Search,
  Send,
  ShieldAlert,
  Truck,
  UserCheck,
  WifiOff,
  Wrench,
  X,
} from "lucide-react";

const ICONS = {
  "arrow-left": ArrowLeft,
  award: Award,
  check: Check,
  "check-circle": CheckCircle2,
  clipboard: ClipboardCheck,
  compass: Compass,
  clock: Clock3,
  close: X,
  edit: PencilLine,
  "edit-3": PencilLine,
  home: Home,
  "log-in": LogIn,
  map: MapPinned,
  "map-pin-off": MapPinned,
  menu: Menu,
  reopen: RotateCw,
  review: BadgeCheck,
  rotate: RotateCw,
  "rotate-ccw": RotateCcw,
  "rotate-cw": RotateCw,
  search: Search,
  send: Send,
  "shield-alert": ShieldAlert,
  truck: Truck,
  "user-check": UserCheck,
  wrench: Wrench,
  "wifi-off": WifiOff,
};

export function resolvePlatformIcon(name) {
  return ICONS[name] || CircleDashed;
}

export function PlatformIcon({ name, className = "", ...props }) {
  const Icon = resolvePlatformIcon(name);
  return <Icon aria-hidden="true" className={className} {...props} />;
}