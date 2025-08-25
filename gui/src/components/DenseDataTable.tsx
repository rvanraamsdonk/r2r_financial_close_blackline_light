import { useMemo, useState, useRef } from 'react';
import { Eye } from 'lucide-react';
import { useEvidenceStore } from '../stores/evidenceStore.js';
import clsx from 'clsx';
import { useTableNavigation, useClipboard } from '../hooks/useKeyboardNavigation.js';
import { CompactAIBadge } from './AITransparency.js';
import type { ColumnDefinition } from '../types.js';

// Re-export for component use
export type { ColumnDefinition } from '../types.js';

export type ID = string | number;

export interface DenseDataTableProps<T extends { id?: ID } = any> {
  data: T[];
  columns: ColumnDefinition[];
  drillThrough?: (record: T) => void;
  bulkActions?: { key: string; label: string; action: (ids: ID[]) => void }[];
  className?: string;
}

export const DenseDataTable: React.FC<DenseDataTableProps> = ({
  data,
  columns,
  drillThrough,
  bulkActions,
  className = ''
}) => {
  const tableRef = useRef<HTMLTableElement>(null);
  const [selected, setSelected] = useState<Record<ID, boolean>>({});
  const { copyToClipboard } = useClipboard();

  const { selectedCell, setSelectedCell, editingCell } = useTableNavigation(data.length, columns.length);
  const { openEvidence } = useEvidenceStore();

  const [sort, setSort] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null);

  const toggleAll = (checked: boolean) => {
    const next: Record<ID, boolean> = {} as Record<ID, boolean>;
    if (checked) {
      for (const row of data) {
        const id = (row as any).id ?? JSON.stringify(row);
        next[id] = true;
      }
    }
    setSelected(next);
  };

  const toggleOne = (id: ID, checked: boolean) => {
    setSelected(prev => ({ ...prev, [id]: checked }));
  };

  const sorted = useMemo(() => {
    if (!sort) return data;
    const { key, dir } = sort;
    return [...data].sort((a, b) => {
      const av = (a as any)[key];
      const bv = (b as any)[key];
      if (av == null && bv == null) return 0;
      if (av == null) return dir === 'asc' ? -1 : 1;
      if (bv == null) return dir === 'asc' ? 1 : -1;
      if (av > bv) return dir === 'asc' ? 1 : -1;
      if (av < bv) return dir === 'asc' ? -1 : 1;
      return 0;
    });
  }, [data, sort]);

  const allChecked = useMemo(() => {
    if (!data.length) return false;
    return data.every(row => selected[(row as any).id ?? JSON.stringify(row)]);
  }, [data, selected]);

  const selectedIds = Object.keys(selected).filter(id => selected[id]);

  const handleBulkAction = (action: (ids: ID[]) => void) => {
    action(selectedIds as ID[]);
    setSelected({} as Record<ID, boolean>);
  };

  const handleCellClick = (rowIndex: number, colIndex: number, value: any, row: any) => {
    setSelectedCell({ row: rowIndex, col: colIndex });
    
    // If this is a monetary value, open evidence sidebar
    if (typeof value === 'number' && value !== 0) {
      const column = columns[colIndex];
      const description = `${row.description || row.account || row.entity || 'Financial Item'} - ${column.label}`;
      
      openEvidence({
        id: `${Date.now()}`,
        value,
        description,
        account: row.account || row.accountCode,
        entity: row.entity,
        period: '2024-08',
        source: 'data_table'
      });
      
      // Also call legacy drillThrough if provided
      if (drillThrough) {
        drillThrough(row);
      }
    }
  };

  const handleCellKeyDown = (event: React.KeyboardEvent, rowIndex: number, colIndex: number) => {
    if (event.key === 'c' && (event.ctrlKey || event.metaKey)) {
      const row = data[rowIndex] as any;
      const column = columns[colIndex];
      const value = row[column.key as any];
      const textValue = typeof value === 'object' ? JSON.stringify(value) : String(value || '');
      copyToClipboard(textValue);
      event.preventDefault();
    }
  };

  const onHeaderClick = (col: ColumnDefinition) => {
    if (!col.sortable) return;
    setSort(prev => {
      if (prev && prev.key === (col.key as any)) {
        return { key: prev.key, dir: prev.dir === 'asc' ? 'desc' : 'asc' };
      }
      return { key: col.key as any, dir: 'asc' };
    });
  };

  return (
    <div className={clsx('w-full overflow-x-auto', className)}>
      {bulkActions && bulkActions.length > 0 && (
        <div className="flex items-center justify-between p-2">
          <div className="text-sm text-gray-600">Selected: {selectedIds.length}</div>
          <div className="flex gap-2">
            {bulkActions && bulkActions.map(action => (
              <button
                key={action.key}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                onClick={() => handleBulkAction(action.action)}
                disabled={selectedIds.length === 0}
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <table ref={tableRef} className="min-w-full dense-table">
        <thead>
          <tr>
            {bulkActions && bulkActions.length > 0 && (
              <th style={{ width: 36 }}>
                <input type="checkbox" checked={allChecked} onChange={e => toggleAll(e.target.checked)} />
              </th>
            )}
            {columns.map(col => (
              <th
                key={String(col.key)}
                style={{ width: col.width }}
                className={clsx(col.sortable && 'cursor-pointer select-none')}
                onClick={() => onHeaderClick(col)}
              >
                <div className="flex items-center gap-1">
                  <span>{col.label}</span>
                  {sort && sort.key === col.key && (
                    <span className="text-gray-400">{sort.dir === 'asc' ? '▲' : '▼'}</span>
                  )}
                </div>
              </th>
            ))}
            {drillThrough && <th style={{ width: 120 }}></th>}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, idx) => {
            const id = (row as any).id ?? JSON.stringify(row);
            return (
              <tr key={id ?? idx}>
                {bulkActions && bulkActions.length > 0 && (
                  <td>
                    <input
                      type="checkbox"
                      checked={!!selected[id]}
                      onChange={e => toggleOne(id, e.target.checked)}
                    />
                  </td>
                )}
                {columns.map((col, colIndex) => {
                  const raw = (row as any)[col.key as any];
                  const rendered = col.render ? col.render(raw, row) : raw;
                  const isSelected = selectedCell?.row === idx && selectedCell?.col === colIndex;
                  const isEditing = editingCell?.row === idx && editingCell?.col === colIndex;

                  return (
                    <td
                      key={String(col.key)}
                      className={clsx(
                        'dense-cell cursor-pointer',
                        isSelected && 'bg-blue-100 border-2 border-blue-500',
                        isEditing && 'bg-yellow-100'
                      )}
                      tabIndex={0}
                      onClick={() => handleCellClick(idx, colIndex, raw, row)}
                      onKeyDown={(e) => handleCellKeyDown(e, idx, colIndex)}
                    >
                      {rendered}
                      {typeof raw === 'number' && raw !== 0 && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const description = `${row.description || row.account || row.entity || 'Financial Item'} - ${col.label}`;
                            openEvidence({
                              id: `${Date.now()}`,
                              value: raw,
                              description,
                              account: row.account || row.accountCode,
                              entity: row.entity,
                              period: '2024-08',
                              source: 'evidence_button'
                            });
                          }}
                          className="ml-2 p-1 text-blue-600 hover:text-blue-800 opacity-0 group-hover:opacity-100 transition-opacity"
                          title="View evidence"
                        >
                          <Eye className="w-3 h-3" />
                        </button>
                      )}
                    </td>
                  );
                })}
                {drillThrough && (
                  <td>
                    <button className="drill-through-btn" onClick={() => drillThrough(row)}>
                      Drill-through
                    </button>
                  </td>
                )}
              </tr>
            );
          })}
          {sorted.length === 0 && (
            <tr>
              <td className="text-sm text-gray-500" colSpan={columns.length + (drillThrough ? 1 : 0) + (bulkActions && bulkActions.length > 0 ? 1 : 0)}>
                No records
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// Helpers exported for reuse in column definitions
export function renderCurrency(value: number | string | null | undefined) {
  const num = typeof value === 'number' ? value : Number(value ?? 0);
  return <span>{num.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}</span>;
}

export function renderStatus(value: string) {
  const map: Record<string, string> = {
    approved: 'status-approved',
    pending: 'status-pending',
    rejected: 'status-rejected',
    complete: 'status-approved',
    'in-progress': 'status-pending',
  };
  const cls = map[value] ?? 'bg-gray-300';
  return <span className={clsx('status-indicator', cls)} title={value}></span>;
}

export function renderAIBadge(ai: { method: 'DET' | 'AI' | 'HYBRID'; confidence: number }) {
  if (!ai) return null;
  return <CompactAIBadge method={ai.method} confidence={ai.confidence} />;
}

