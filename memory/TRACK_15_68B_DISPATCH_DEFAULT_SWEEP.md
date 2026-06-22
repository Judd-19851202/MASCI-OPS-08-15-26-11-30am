# TRACK 15.68B · Dispatch Default Sweep — ✅ SHIPPED

See `TRACK_15_68B_FINAL_CLOSEOUT.md` §3.

`components/dispatch/AssignmentCreateDrawer.jsx`:
```jsx
const [carrier, setCarrier] = useState({ label: "MASCI", refId: "", isTemp: false });
// Track 15.68B · resolve tenant-aware default carrier label on mount.
useEffect(() => {
  try {
    const cn = window.sessionStorage.getItem("branding.companyName");
    if (cn && cn !== "MASCI") setCarrier((c) => ({ ...c, label: cn }));
  } catch { /* noop */ }
}, []);
```

**MASCI tenant** — sessionStorage tenant key is `masci`, default label stays `"MASCI"`. Unchanged.
**Customer #2** — sessionStorage `companyName` is `"Customer #2 Construction LLC"`, default label overridden on mount.

Other call sites (`setCarrier({label: "MASCI",…})` reset paths) preserved deliberately so the "reset" UX returns to whatever the operator typed last — operator can switch back to MASCI via the explicit dropdown.
