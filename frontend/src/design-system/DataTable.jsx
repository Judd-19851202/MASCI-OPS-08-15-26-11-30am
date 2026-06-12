// Track 13.5A · Phase B1 — <DataTable> primitive.
// Token-based, presentation-only. NOT applied to any existing table in Phase B1.
//
// Contract (per MASCI_DESIGN_SYSTEM_V1.md §10):
//   columns:  Array<{ key, header, render?, align?, width?, sortable?, testid? }>
//   rows:     Array<Record>
//   rowKey:   (row) => string | number
//   loading:  boolean
//   empty:    EmptyState node (rendered when !loading && rows.length === 0)
//   density:  "compact" | "regular"
//   onRowClick?: (row) => void
//   sort?:    { key, direction: "asc" | "desc" }
//   onSortChange?: (next) => void   (controlled sort — table does NOT mutate data)
//
// Notes:
//   • This component does NOT mutate the rows array.
//   • This component does NOT fetch.
//   • Sort UI emits intent; parent is the source of truth.
import React from "react";

function HeaderCell({ col, sort, onSortChange }) {
  const isSorted = sort && sort.key === col.key;
  const dir = isSorted ? sort.direction : null;
  const align = col.align || "left";
  const sortable = !!col.sortable && !!onSortChange;
  const handleClick = () => {
    if (!sortable) return;
    const next = !isSorted
      ? { key: col.key, direction: "asc" }
      : dir === "asc"
        ? { key: col.key, direction: "desc" }
        : null;
    onSortChange(next);
  };
  return (
    <th
      data-testid={`ds-datatable-header-${col.key}`}
      scope="col"
      onClick={handleClick}
      style={{
        textAlign: align,
        width: col.width,
        padding: "10px 12px",
        background: "var(--paper-rail)",
        color: "var(--paper-rail-ink)",
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        borderBottom: "1px solid var(--border-bold)",
        whiteSpace: "nowrap",
        cursor: sortable ? "pointer" : "default",
        userSelect: "none",
      }}
    >
      <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
        {col.header}
        {sortable && (
          <span
            aria-hidden
            style={{
              fontSize: 9,
              color: isSorted ? "var(--ink-strong)" : "var(--ink-faint)",
              lineHeight: 1,
            }}
          >
            {dir === "asc" ? "▲" : dir === "desc" ? "▼" : "▾"}
          </span>
        )}
      </span>
    </th>
  );
}

export function DataTable({
  columns,
  rows,
  rowKey = (row, idx) => row?.id ?? idx,
  loading = false,
  empty = null,
  density = "regular",
  onRowClick,
  sort = null,
  onSortChange,
  caption = null,
  className = "",
  "data-testid": testId = "ds-datatable",
}) {
  const cellPadY = density === "compact" ? 6 : 10;
  const cellPadX = density === "compact" ? 10 : 12;

  return (
    <div
      data-testid={testId}
      className={className}
      style={{
        background: "var(--paper-card)",
        border: "1px solid var(--border-hairline)",
        borderRadius: "var(--radius-card)",
        overflow: "hidden",
      }}
    >
      {caption && (
        <div
          style={{
            padding: "8px 12px",
            color: "var(--ink-soft)",
            fontSize: 12,
            background: "var(--paper-base)",
            borderBottom: "1px solid var(--border-hairline)",
          }}
        >
          {caption}
        </div>
      )}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "separate",
            borderSpacing: 0,
            fontSize: 13,
            color: "var(--ink-regular)",
          }}
        >
          <thead>
            <tr>
              {columns.map((col) => (
                <HeaderCell
                  key={col.key}
                  col={col}
                  sort={sort}
                  onSortChange={onSortChange}
                />
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr data-testid="ds-datatable-loading">
                <td
                  colSpan={columns.length}
                  style={{
                    padding: "var(--pad-card)",
                    textAlign: "center",
                    color: "var(--ink-soft)",
                    fontSize: 12,
                  }}
                >
                  Loading…
                </td>
              </tr>
            )}
            {!loading && rows.length === 0 && (
              <tr data-testid="ds-datatable-empty">
                <td colSpan={columns.length} style={{ padding: 0 }}>
                  {empty || (
                    <div
                      style={{
                        padding: "var(--pad-card)",
                        textAlign: "center",
                        color: "var(--ink-soft)",
                        fontSize: 12,
                      }}
                    >
                      No records.
                    </div>
                  )}
                </td>
              </tr>
            )}
            {!loading &&
              rows.map((row, idx) => {
                const key = rowKey(row, idx);
                const clickable = !!onRowClick;
                return (
                  <tr
                    key={key}
                    data-testid={`ds-datatable-row-${key}`}
                    onClick={clickable ? () => onRowClick(row) : undefined}
                    style={{
                      background: idx % 2 === 0 ? "var(--paper-card)" : "var(--paper-base)",
                      cursor: clickable ? "pointer" : "default",
                    }}
                  >
                    {columns.map((col) => (
                      <td
                        key={col.key}
                        data-testid={col.testid ? `${col.testid}-${key}` : undefined}
                        style={{
                          padding: `${cellPadY}px ${cellPadX}px`,
                          textAlign: col.align || "left",
                          borderBottom: "1px solid var(--border-hairline)",
                          color: "var(--ink-regular)",
                          whiteSpace: col.wrap ? "normal" : "nowrap",
                          verticalAlign: "middle",
                        }}
                      >
                        {col.render ? col.render(row) : row[col.key] ?? "—"}
                      </td>
                    ))}
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DataTable;
