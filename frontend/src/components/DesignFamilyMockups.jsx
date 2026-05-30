// DesignFamilyMockups.jsx — Pass-7 · Design-system family visual mockups.
//
// Self-contained mockup pages for the 4 workflow families. Used by the
// operator to review each family's intentional design BEFORE the
// platform-wide UX modernization rollout.
//
// Routes:
//   /__design                  · Index of all family mockups
//   /__design/family-a         · Field forms (Daily Reports / JHA / Meetings / Incidents / QA-QC)
//   /__design/family-b         · Approval consoles (PO / Time Verify / Payroll / HR Approvals)
//   /__design/family-c         · Operational status (Equipment / Fleet / Shop / Dispatch)
//   /__design/family-d         · Configuration consoles (Admin / Settings / Users)
//
// These pages are NOT linked from any portal sidebar and are
// preview-only. Static data. No backend calls.

import React from "react";
import { Link } from "react-router-dom";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import {
  ChevronRight, Camera, ClipboardCheck, Wrench, AlertTriangle, CheckCircle2,
  XCircle, Filter, FileDown, Search, Plus, Trash2, Save, Send, Settings,
  Users, Database, Bell, Shield, Truck, Activity, MapPin, Clock,
} from "lucide-react";

// ────────────────────────────────────────────────────────────
// INDEX
// ────────────────────────────────────────────────────────────
export function DesignIndex() {
  const families = [
    { id: "a", title: "Family A · Field Forms", desc: "Daily Reports · JHA / JHP · Safety Meetings · Incident Reports · QA / QC", accent: "blue", surfaces: 5 },
    { id: "b", title: "Family B · Approval Consoles", desc: "PO Requests · Time Verification · Payroll Variance · HR Approvals", accent: "purple", surfaces: 4 },
    { id: "c", title: "Family C · Operational Status", desc: "Equipment · Fleet · Shop · Dispatch", accent: "emerald", surfaces: 4 },
    { id: "d", title: "Family D · Configuration Consoles", desc: "Admin · Settings · User Management", accent: "slate", surfaces: 3 },
  ];
  return (
    <div className="min-h-screen bg-slate-50 p-6 lg:p-10">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-slate-500">Pass 7 · Design System Audit</div>
          <h1 className="font-display text-3xl lg:text-4xl font-black text-slate-900 mt-1">Workflow Family Mockups</h1>
          <p className="mt-2 text-slate-600 max-w-2xl">
            Each family has a dedicated layout doctrine. These mockups exist for operator review prior to platform-wide rollout. Static data · preview-only.
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {families.map(f => (
            <Link to={`/__design/family-${f.id}`} key={f.id}>
              <Card className={`p-6 border-2 hover:border-${f.accent}-500 transition-colors cursor-pointer h-full`}>
                <div className={`text-xs font-mono uppercase tracking-[0.3em] text-${f.accent}-700`}>FAMILY {f.id.toUpperCase()}</div>
                <h2 className="font-display text-xl font-black mt-1">{f.title}</h2>
                <p className="mt-2 text-sm text-slate-600">{f.desc}</p>
                <div className="mt-4 flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-500">{f.surfaces} surfaces</span>
                  <ChevronRight className={`w-5 h-5 text-${f.accent}-700`} />
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// FAMILY A · FIELD FORMS — Daily Report mockup
// ────────────────────────────────────────────────────────────
export function FamilyAMockup() {
  return (
    <div className="min-h-screen bg-slate-50">
      <FamilyHeader id="A" title="Field Forms" accent="blue" subtitle="Long-form field data entry · large touch targets · section progress" />
      <div className="max-w-5xl mx-auto p-5 lg:p-8">
        {/* Section progress strip */}
        <div className="flex gap-2 mb-5 overflow-x-auto">
          {[
            { n: 1, t: "Project Info", done: true },
            { n: 2, t: "Crew & Hours", done: true },
            { n: 3, t: "Weather", done: false, active: true },
            { n: 4, t: "Deliveries", done: false },
            { n: 5, t: "Photos", done: false },
            { n: 6, t: "Submit", done: false },
          ].map(s => (
            <div key={s.n} className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-mono uppercase tracking-wider whitespace-nowrap border-2 ${
              s.active ? "border-blue-700 bg-blue-50 text-blue-900 font-bold" :
              s.done ? "border-emerald-400 bg-emerald-50/40 text-emerald-700" :
                       "border-slate-200 bg-white text-slate-500"
            }`}>
              {s.done && <CheckCircle2 className="w-3.5 h-3.5" />}
              <span>{s.n}. {s.t}</span>
            </div>
          ))}
        </div>

        {/* Section card */}
        <Card className="p-5 lg:p-7 mb-5 border-2 border-blue-200">
          <div className="mb-5">
            <div className="text-xs font-mono uppercase tracking-[0.3em] text-blue-700">SECTION 3 OF 6</div>
            <h2 className="font-display text-2xl font-black mt-1">Weather & Site Conditions</h2>
            <p className="mt-1 text-sm text-slate-600">Record observed conditions at the time of crew start. These drive delay analysis downstream.</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-5">
            <div>
              <Label className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-700 font-bold">High Temperature (°F)</Label>
              <Input defaultValue="78" className="h-12 text-lg border-2 border-slate-300" />
            </div>
            <div>
              <Label className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-700 font-bold">Low Temperature (°F)</Label>
              <Input defaultValue="62" className="h-12 text-lg border-2 border-slate-300" />
            </div>
            <div className="lg:col-span-2">
              <Label className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-700 font-bold">Sky Conditions</Label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-1">
                {["Clear", "Partly Cloudy", "Overcast", "Rain"].map((c, i) => (
                  <button key={c} className={`h-12 rounded-md border-2 text-sm font-bold transition-colors ${
                    i === 1 ? "border-blue-700 bg-blue-50 text-blue-900" : "border-slate-300 text-slate-700 hover:bg-slate-50"
                  }`}>{c}</button>
                ))}
              </div>
            </div>
            <div className="lg:col-span-2">
              <Label className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-700 font-bold">Notes (Optional)</Label>
              <Textarea rows={3} placeholder="e.g. light morning fog cleared by 0700; afternoon humidity affected concrete cure." className="border-2 border-slate-300 text-base" />
            </div>
          </div>

          {/* Section footer with primary action */}
          <div className="mt-6 pt-5 border-t border-blue-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500">
              SAVED LOCALLY · <span className="text-emerald-700 font-bold">just now</span>
            </div>
            <div className="flex gap-2 sm:ml-auto">
              <Button variant="outline" className="h-12 px-5">Back</Button>
              <Button className="h-12 px-7 bg-blue-700 hover:bg-blue-800 text-white font-bold">
                Continue · Section 4 <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </div>
        </Card>

        {/* Photo upload doctrine demo */}
        <Card className="p-5 border-2 border-slate-200">
          <h3 className="font-display text-lg font-black">Photo Evidence</h3>
          <p className="text-sm text-slate-600 mt-1 mb-4">Up to 12 photos · tap to add from gallery or camera</p>
          <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            {[1, 2, 3].map(i => <div key={i} className="aspect-square rounded-md bg-slate-100 border-2 border-slate-200 flex items-center justify-center text-slate-400 text-xs">Photo {i}</div>)}
            <button className="aspect-square rounded-md border-2 border-dashed border-blue-300 bg-blue-50/30 flex flex-col items-center justify-center text-blue-700 text-xs font-bold gap-1">
              <Camera className="w-6 h-6" />ADD
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// FAMILY B · APPROVAL CONSOLES — PO Requests + Approve drawer mockup
// (mirrors Pass-6 HR Time Verification doctrine but for approval queues)
// ────────────────────────────────────────────────────────────
export function FamilyBMockup() {
  return (
    <div className="min-h-screen bg-slate-50">
      <FamilyHeader id="B" title="Approval Consoles" accent="purple" subtitle="Operations admin · filter · review queue · approve/reject" />
      <div className="max-w-7xl mx-auto p-5 lg:p-8">
        {/* Filter card with action footer */}
        <Card className="p-5 mb-5 border-2 border-purple-200 bg-purple-50/30">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
            <div className="min-w-0">
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Status</Label>
              <Input defaultValue="Pending Receipt" className="h-10 w-full border-2 border-slate-300" />
            </div>
            <div className="min-w-0">
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Vendor</Label>
              <Input placeholder="Name contains..." className="h-10 w-full border-2 border-slate-300" />
            </div>
            <div className="min-w-0">
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Project #</Label>
              <Input placeholder="e.g. 25-103" className="h-10 w-full border-2 border-slate-300" />
            </div>
            <div className="min-w-0">
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Amount Range</Label>
              <Input placeholder="$0 - $5000" className="h-10 w-full border-2 border-slate-300" />
            </div>
          </div>
          <div className="mt-5 pt-4 border-t border-purple-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-slate-500">
              QUEUE · <span className="text-slate-700 font-bold">7 pending</span> · <span className="text-amber-700 font-bold">2 over-threshold</span>
            </div>
            <div className="flex gap-2 sm:ml-auto">
              <Button variant="outline" className="h-10"><FileDown className="w-4 h-4 mr-1" /> Export CSV</Button>
              <Button className="h-10 px-6 bg-purple-700 hover:bg-purple-800 text-white"><Filter className="w-4 h-4 mr-1" /> Apply Filters</Button>
            </div>
          </div>
        </Card>

        {/* Queue list */}
        <Card className="border-2 border-slate-200">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between">
            <h2 className="font-display text-lg font-black">Pending Approval Queue</h2>
            <Badge variant="outline" className="font-mono">7 ITEMS</Badge>
          </div>
          <div className="divide-y divide-slate-200">
            {[
              { id: "PO-2451", vendor: "Hilti Concrete Supply", proj: "25-103", amount: "$2,840.00", flag: "over-threshold", date: "2026-05-29" },
              { id: "PO-2450", vendor: "Sunbelt Rentals", proj: "25-088", amount: "$1,210.00", flag: null, date: "2026-05-29" },
              { id: "PO-2449", vendor: "AT&T Fiber Crew", proj: "25-103", amount: "$640.00", flag: null, date: "2026-05-28" },
            ].map(po => (
              <div key={po.id} className="p-4 hover:bg-slate-50 cursor-pointer">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-slate-900">{po.id}</span>
                      {po.flag && <Badge className="bg-amber-100 text-amber-900 border-amber-400 font-mono text-[10px]">OVER THRESHOLD</Badge>}
                    </div>
                    <div className="mt-1 text-sm text-slate-700">{po.vendor}</div>
                    <div className="mt-0.5 text-xs font-mono text-slate-500">PROJ {po.proj} · {po.date}</div>
                  </div>
                  <div className="font-display text-2xl font-black text-slate-900">{po.amount}</div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="h-9 border-red-300 text-red-700">Reject</Button>
                    <Button size="sm" className="h-9 bg-emerald-700 hover:bg-emerald-800 text-white">Approve</Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// FAMILY C · OPERATIONAL STATUS — Equipment grid + dispatch
// ────────────────────────────────────────────────────────────
export function FamilyCMockup() {
  return (
    <div className="min-h-screen bg-slate-50">
      <FamilyHeader id="C" title="Operational Status" accent="emerald" subtitle="Real-time state · color-coded badges · status-first cards" />
      <div className="max-w-7xl mx-auto p-5 lg:p-8">
        {/* Health strip — single Card with internal divider grid (Pass-6 doctrine) */}
        <Card className="p-5 mb-5 border-2 border-slate-200">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-5 sm:divide-x sm:divide-slate-200">
            {[
              { l: "FLEET ONLINE", v: "23 / 28", c: "text-emerald-700" },
              { l: "PRE-OP FAILED", v: "2", c: "text-red-700", sub: "needs shop attention" },
              { l: "AWAITING DISPATCH", v: "5", c: "text-amber-700" },
              { l: "OUT OF SERVICE", v: "3", c: "text-slate-500" },
            ].map((s, i) => (
              <div key={s.l} className={`flex flex-col ${i > 0 ? "sm:pl-6" : ""}`}>
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">{s.l}</div>
                <div className={`font-display text-3xl font-black mt-1.5 leading-none ${s.c}`}>{s.v}</div>
                {s.sub && <div className="mt-1 text-[10px] font-mono uppercase tracking-wider text-red-700">{s.sub}</div>}
              </div>
            ))}
          </div>
        </Card>

        {/* Equipment cards grid — status-first */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[
            { id: "EX-301", t: "CAT 320 Excavator", status: "OK", op: "M. Reyes", proj: "25-103", color: "emerald" },
            { id: "EX-205", t: "CAT 305 Mini-Ex", status: "FAILED", op: null, proj: null, color: "red", note: "hydraulic leak · port-side cylinder" },
            { id: "LB-118", t: "John Deere 624K", status: "OK", op: "T. Park", proj: "25-088", color: "emerald" },
            { id: "TR-042", t: "Mack Triaxle", status: "DISPATCH", op: "C. Wright", proj: "25-103", color: "amber", note: "awaiting load" },
            { id: "SK-009", t: "Bobcat S650", status: "OOS", op: null, proj: null, color: "slate", note: "scheduled service 06-02" },
            { id: "PR-201", t: "Vermeer Trencher", status: "OK", op: "D. Webb", proj: "25-103", color: "emerald" },
          ].map(eq => (
            <Card key={eq.id} className={`p-5 border-2 border-${eq.color}-300 ${eq.status === "FAILED" ? "bg-red-50/40" : ""}`}>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-500">{eq.id}</div>
                  <div className="font-display text-base font-black mt-0.5">{eq.t}</div>
                </div>
                <Badge className={`font-mono text-[10px] bg-${eq.color}-100 text-${eq.color}-900 border border-${eq.color}-400`}>{eq.status}</Badge>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 text-xs font-mono text-slate-600 space-y-1">
                {eq.op ? <div className="flex items-center gap-2"><Wrench className="w-3.5 h-3.5" />{eq.op}</div> :
                          <div className="flex items-center gap-2 text-slate-400"><Wrench className="w-3.5 h-3.5" />unassigned</div>}
                {eq.proj ? <div className="flex items-center gap-2"><MapPin className="w-3.5 h-3.5" />PROJ {eq.proj}</div> : null}
                {eq.note ? <div className={`mt-2 text-${eq.color}-700 font-bold normal-case`}>{eq.note}</div> : null}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// FAMILY D · CONFIGURATION CONSOLES — Admin User Management mockup
// ────────────────────────────────────────────────────────────
export function FamilyDMockup() {
  return (
    <div className="min-h-screen bg-slate-50">
      <FamilyHeader id="D" title="Configuration Consoles" accent="slate" subtitle="Utility-focused · search-first · dense lists · power-user defaults" />
      <div className="max-w-7xl mx-auto p-5 lg:p-8">
        {/* Search + action bar — single dense row */}
        <Card className="p-4 mb-5 border-2 border-slate-200">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input placeholder="Search users by name, email, role..." className="h-10 pl-10 border-2 border-slate-300" />
            </div>
            <div className="flex gap-2">
              <Button variant="outline" className="h-10"><Filter className="w-4 h-4 mr-1" /> Filters</Button>
              <Button className="h-10 px-5 bg-slate-900 hover:bg-slate-800 text-white"><Plus className="w-4 h-4 mr-1" /> New User</Button>
            </div>
          </div>
        </Card>

        {/* Dense user list */}
        <Card className="border-2 border-slate-200">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between text-xs font-mono uppercase tracking-[0.2em] text-slate-600 font-bold">
            <div className="flex-1">User</div>
            <div className="w-40 hidden sm:block">Role</div>
            <div className="w-32 hidden md:block">Last Active</div>
            <div className="w-32 hidden md:block">Portal</div>
            <div className="w-20 text-right">Actions</div>
          </div>
          <div className="divide-y divide-slate-100">
            {[
              { name: "Jaymn Judd",     email: "jaymn.judd@mascigc.com",     role: "SUPER ADMIN",     active: "2 min ago", portal: "Admin" },
              { name: "Chris Wright",   email: "chriswright@mascigc.com",    role: "PM",              active: "1 hr ago",  portal: "PM" },
              { name: "Mark Reyes",     email: "mreyes@mascigc.com",         role: "OPERATOR",        active: "3 hr ago",  portal: "Field" },
              { name: "Tina Park",      email: "tpark@mascigc.com",          role: "SAFETY MGR",      active: "yesterday", portal: "Safety" },
              { name: "Dana Webb",      email: "dwebb@mascigc.com",          role: "MECHANIC",        active: "today",     portal: "Shop" },
            ].map(u => (
              <div key={u.email} className="p-4 flex items-center hover:bg-slate-50 cursor-pointer">
                <div className="flex-1">
                  <div className="font-bold text-slate-900">{u.name}</div>
                  <div className="text-xs font-mono text-slate-500">{u.email}</div>
                </div>
                <div className="w-40 hidden sm:block">
                  <Badge variant="outline" className="font-mono text-[10px]">{u.role}</Badge>
                </div>
                <div className="w-32 hidden md:block text-xs font-mono text-slate-600">{u.active}</div>
                <div className="w-32 hidden md:block text-xs font-mono text-slate-700">{u.portal}</div>
                <div className="w-20 flex justify-end gap-1">
                  <Button variant="ghost" size="icon" className="h-8 w-8"><Settings className="w-4 h-4" /></Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-red-600"><Trash2 className="w-4 h-4" /></Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Shared header for mockup pages
// ────────────────────────────────────────────────────────────
function FamilyHeader({ id, title, accent, subtitle }) {
  return (
    <header className={`bg-${accent}-700 text-white py-6 px-5 lg:px-10`}>
      <div className="max-w-7xl mx-auto">
        <Link to="/__design" className="text-xs font-mono uppercase tracking-[0.3em] opacity-70 hover:opacity-100">← all families</Link>
        <div className="mt-1 flex items-baseline gap-3">
          <span className="font-mono text-xs uppercase tracking-[0.3em] opacity-80">FAMILY {id}</span>
          <h1 className="font-display text-2xl lg:text-3xl font-black">{title}</h1>
        </div>
        <p className="mt-1 text-sm opacity-90">{subtitle}</p>
      </div>
    </header>
  );
}
