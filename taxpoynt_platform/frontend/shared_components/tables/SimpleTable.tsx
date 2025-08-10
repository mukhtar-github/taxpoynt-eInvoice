/**
 * SimpleTable Component
 * ====================
 * 
 * Basic table component for simple data display without advanced features.
 * Lightweight alternative to DataTable for basic tabular data presentation.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React from 'react';
import { TaxPoyntDesignSystem } from '../../../design_system/core/TaxPoyntDesignSystem';

// Simple table column definition
export interface SimpleTableColumn<T = any> {
  key: keyof T | string;
  title: string;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, record: T, index: number) => React.ReactNode;
}

// Simple table props
export interface SimpleTableProps<T = any> {
  columns: SimpleTableColumn<T>[];
  data: T[];
  className?: string;
  striped?: boolean;
  bordered?: boolean;
  hover?: boolean;
  compact?: boolean;
  loading?: boolean;
  emptyText?: string;
  onRowClick?: (record: T, index: number) => void;
}

const SimpleTable = <T extends Record<string, any>>({
  columns,
  data,
  className = '',
  striped = true,
  bordered = true,
  hover = true,
  compact = false,
  loading = false,
  emptyText = 'No data available',
  onRowClick
}: SimpleTableProps<T>) => {
  const { colors, spacing, typography, shadows } = TaxPoyntDesignSystem;

  const tableStyles: React.CSSProperties = {
    width: '100%',
    borderCollapse: 'collapse',
    backgroundColor: colors.neutral.white,
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: shadows.sm,
    fontSize: typography.sizes.sm,
    ...(!bordered && { border: 'none' })
  };

  const headerStyles: React.CSSProperties = {
    backgroundColor: colors.neutral.gray[50],
    borderBottom: `1px solid ${colors.neutral.gray[200]}`,
    fontWeight: typography.weights.semibold,
    textAlign: 'left',
    color: colors.neutral.gray[700]
  };

  const cellStyles: React.CSSProperties = {
    padding: compact ? spacing.sm : spacing.md,
    borderBottom: `1px solid ${colors.neutral.gray[100]}`,
    verticalAlign: 'middle'
  };

  const rowStyles: React.CSSProperties = {
    ...(hover && {
      cursor: onRowClick ? 'pointer' : 'default',
      transition: 'background-color 0.2s ease'
    })
  };

  const stripedRowStyles: React.CSSProperties = {
    backgroundColor: colors.neutral.gray[25]
  };

  const hoverStyles: React.CSSProperties = {
    backgroundColor: colors.primary.blue[25]
  };

  const loadingOverlayStyles: React.CSSProperties = {
    position: 'relative'
  };

  const loadingSpinnerStyles: React.CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    zIndex: 1000,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    padding: spacing.lg,
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm
  };

  const getCellValue = (record: T, column: SimpleTableColumn<T>) => {
    const value = record[column.key as keyof T];
    return column.render ? column.render(value, record, data.indexOf(record)) : value;
  };

  const getCellAlignment = (align?: 'left' | 'center' | 'right'): React.CSSProperties => {
    return {
      textAlign: align || 'left'
    };
  };

  return (
    <div className={`taxpoynt-simple-table ${className}`} style={loadingOverlayStyles}>
      {loading && (
        <div style={loadingSpinnerStyles}>
          <div
            style={{
              width: '20px',
              height: '20px',
              border: `2px solid ${colors.neutral.gray[200]}`,
              borderTop: `2px solid ${colors.primary.blue[500]}`,
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }}
          />
          <span>Loading...</span>
        </div>
      )}
      
      <table style={tableStyles}>
        <thead>
          <tr>
            {columns.map((column, index) => (
              <th
                key={String(column.key) + index}
                style={{
                  ...headerStyles,
                  ...cellStyles,
                  ...getCellAlignment(column.align),
                  ...(column.width && { width: column.width })
                }}
              >
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                style={{
                  ...cellStyles,
                  textAlign: 'center',
                  color: colors.neutral.gray[500],
                  fontStyle: 'italic',
                  padding: spacing.xl
                }}
              >
                {emptyText}
              </td>
            </tr>
          ) : (
            data.map((record, rowIndex) => (
              <tr
                key={rowIndex}
                style={{
                  ...rowStyles,
                  ...(striped && rowIndex % 2 === 1 && stripedRowStyles)
                }}
                onClick={() => onRowClick?.(record, rowIndex)}
                onMouseEnter={(e) => {
                  if (hover) {
                    Object.assign(e.currentTarget.style, hoverStyles);
                  }
                }}
                onMouseLeave={(e) => {
                  if (hover) {
                    e.currentTarget.style.backgroundColor = 
                      striped && rowIndex % 2 === 1 
                        ? colors.neutral.gray[25] 
                        : colors.neutral.white;
                  }
                }}
              >
                {columns.map((column, colIndex) => (
                  <td
                    key={String(column.key) + colIndex}
                    style={{
                      ...cellStyles,
                      ...getCellAlignment(column.align)
                    }}
                  >
                    {getCellValue(record, column)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default SimpleTable;