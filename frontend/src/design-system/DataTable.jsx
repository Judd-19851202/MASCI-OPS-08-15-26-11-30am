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
        padding: "12px 14px",
        background: "linear-gradient(135deg, rgba(15, 28, 51, 0.96), rgba(29, 53, 91, 0.94))",
        color: "rgba(248, 250, 252, 0.96)",
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: "0.18em",
        textTransform: "uppercase",
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
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
              color: isSorted ? "rgba(255, 255, 255, 0.96)" : "rgba(226, 232, 240, 0.8)",
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
  emptyText = "No records.",
  tableMinWidth = null,
  getRowClassName,
  getRowTestId,
  getCellTestId,
  "data-testid": testId = "ds-datatable",
}) {
  const cellPadY = density === "compact" ? 6 : 10;
  const cellPadX = density === "compact" ? 10 : 12;

  return (
    <div
      data-testid={testId}
      className={`wp17-data-table ${className}`.trim()}
      style={{
        overflow: "hidden",
      }}
    >
      {caption && (
        <div className="wp17-data-table__caption">
          {caption}
        </div>
      )}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            minWidth: tableMinWidth || undefined,
            borderCollapse: "separate",
            borderSpacing: 0,
            fontSize: 13,
            color: "var(--wp17-navy-900)",
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
                    padding: "1rem",
                    textAlign: "center",
                    color: "var(--wp17-muted)",
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
                        padding: "1rem",
                        textAlign: "center",
                        color: "var(--wp17-muted)",
                        fontSize: 12,
                      }}
                    >
                      {emptyText}
                    </div>
                  )}
                </td>
              </tr>
            )}
            {!loading &&
              rows.map((row, idx) => {
                const key = rowKey(row, idx);
                const clickable = !!onRowClick;
                const rowTestId = typeof getRowTestId === "function"
                  ? getRowTestId(row, key, idx)
                  : `ds-datatable-row-${key}`;
                return (
                  <tr
                    key={key}
                    data-testid={rowTestId}
                    className={typeof getRowClassName === "function" ? getRowClassName(row, idx) : undefined}
                    onClick={clickable ? () => onRowClick(row) : undefined}
                    style={{
                      background: idx % 2 === 0 ? "rgba(255, 255, 255, 0.98)" : "rgba(244, 248, 252, 0.92)",
                      cursor: clickable ? "pointer" : "default",
                    }}
                  >
                    {columns.map((col) => (
                      <td
                        key={col.key}
                        data-testid={typeof getCellTestId === "function"
                          ? getCellTestId(row, col, key, idx)
                          : col.testid ? `${col.testid}-${key}` : undefined}
                        style={{
                          padding: `${cellPadY}px ${cellPadX}px`,
                          textAlign: col.align || "left",
                          borderBottom: "1px solid rgba(30, 64, 108, 0.08)",
                          color: "var(--wp17-navy-900)",
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
