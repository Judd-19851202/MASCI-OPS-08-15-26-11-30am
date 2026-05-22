import React, { useEffect, useRef, useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";

/**
 * MentionTextarea — textarea with @-autocomplete against /api/users/directory.
 * Drop-in replacement for shadcn <Textarea>.
 *
 * Props: value, onChange(next), ...rest (forwarded to Textarea).
 */
let _directoryCache = null;
let _directoryPromise = null;

async function loadDirectory() {
  if (_directoryCache) return _directoryCache;
  if (!_directoryPromise) {
    _directoryPromise = api
      .get("/users/directory")
      .then((r) => {
        _directoryCache = r.data || [];
        return _directoryCache;
      })
      .catch(() => (_directoryCache = []));
  }
  return _directoryPromise;
}

export function MentionTextarea({
  value,
  onChange,
  "data-testid": testId,
  className = "",
  ...rest
}) {
  const ref = useRef(null);
  const [directory, setDirectory] = useState([]);
  const [menu, setMenu] = useState(null); // { query, matches, caret }
  const [activeIdx, setActiveIdx] = useState(0);

  useEffect(() => {
    loadDirectory().then(setDirectory);
  }, []);

  const computeMenu = (text, caret) => {
    // Find the @-trigger just before the caret, not followed by whitespace.
    const slice = text.slice(0, caret);
    const m = slice.match(/(^|\s)@([A-Za-z0-9._%+-]*)$/);
    if (!m) return null;
    const query = m[2].toLowerCase();
    const matches = directory
      .filter((u) => {
        const hay = `${u.name || ""} ${u.email || ""}`.toLowerCase();
        return query === "" || hay.includes(query);
      })
      .slice(0, 6);
    if (matches.length === 0) return null;
    return { query, matches, caret };
  };

  const onChangeInner = (e) => {
    const next = e.target.value;
    onChange(next);
    const caret = e.target.selectionStart ?? next.length;
    const m = computeMenu(next, caret);
    setMenu(m);
    setActiveIdx(0);
  };

  const onKeyDown = (e) => {
    if (!menu) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => (i + 1) % menu.matches.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => (i - 1 + menu.matches.length) % menu.matches.length);
    } else if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      insertMention(menu.matches[activeIdx]);
    } else if (e.key === "Escape") {
      setMenu(null);
    }
  };

  const insertMention = (user) => {
    const el = ref.current;
    const caret = menu?.caret ?? value.length;
    const before = value.slice(0, caret);
    const after = value.slice(caret);
    // Replace trailing @query with full @email + trailing space.
    const replaced = before.replace(/@([A-Za-z0-9._%+-]*)$/, `@${user.email} `);
    const next = replaced + after;
    onChange(next);
    setMenu(null);
    // Restore focus + caret after React updates value
    requestAnimationFrame(() => {
      if (el) {
        el.focus();
        const newCaret = replaced.length;
        el.setSelectionRange(newCaret, newCaret);
      }
    });
  };

  return (
    <div className="relative">
      <Textarea
        ref={ref}
        value={value}
        onChange={onChangeInner}
        onKeyDown={onKeyDown}
        onBlur={() => setTimeout(() => setMenu(null), 150)}
        data-testid={testId}
        className={className}
        {...rest}
      />
      {menu && (
        <div
          className="absolute z-50 left-2 bottom-full mb-2 w-80 max-h-72 overflow-y-auto bg-white border border-slate-200 rounded-md shadow-lg"
          data-testid="mention-autocomplete"
        >
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-500 font-bold px-3 py-2 border-b border-slate-100">
            People — press Enter
          </div>
          {menu.matches.map((u, i) => (
            <button
              key={u.id}
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                insertMention(u);
              }}
              className={`w-full text-left px-3 py-2 flex items-center gap-2 text-sm ${
                i === activeIdx ? "bg-red-50" : "hover:bg-slate-50"
              }`}
              data-testid={`mention-option-${u.email}`}
            >
              <span className="w-6 h-6 rounded-full bg-red-700 text-white font-display font-black text-[10px] flex items-center justify-center shrink-0">
                {(u.name || u.email || "?").charAt(0).toUpperCase()}
              </span>
              <span className="flex-1 min-w-0">
                <div className="font-bold text-slate-900 truncate">{u.name || u.email}</div>
                <div className="font-mono text-[10px] text-slate-500 truncate">{u.email}</div>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
