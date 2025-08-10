/**
 * DataTable Component
 * ==================
 * 
 * Comprehensive data table with sorting, filtering, pagination, and selection.
 * Integrates with TaxPoynt design system and supports responsive layouts.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useMemo } from 'react';
import { colors, typography, spacing, borders, shadows, animations } from '../../design_system/tokens';

export interface Column<T = any> {
  key: string;
  title: string;
  width?: number | string;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  sorter?: (a: T, b: T) => number;
  filterType?: 'text' | 'select' | 'date' | 'number';
  filterOptions?: Array<{ label: string; value: any }>;
}

export interface DataTableProps<T = any> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  empty?: boolean;
  emptyMessage?: string;
  size?: 'sm' | 'md' | 'lg';
  role?: 'si' | 'app' | 'hybrid' | 'admin';
  striped?: boolean;
  hoverable?: boolean;
  bordered?: boolean;
  selectable?: boolean;
  selection?: 'single' | 'multiple';
  selectedKeys?: (string | number)[];
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
    showSizeChanger?: boolean;
    pageSizeOptions?: number[];
  };
  onSelectionChange?: (selectedKeys: (string | number)[], selectedRows: T[]) => void;
  onPaginationChange?: (page: number, pageSize: number) => void;
  onSort?: (sortKey: string, sortOrder: 'asc' | 'desc') => void;
  onFilter?: (filters: Record<string, any>) => void;
  getRowKey?: (record: T, index: number) => string | number;
  className?: string;
  'data-testid'?: string;
}

export const DataTable = <T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  empty = false,
  emptyMessage = 'No data available',
  size = 'md',
  role,
  striped = true,
  hoverable = true,
  bordered = true,
  selectable = false,
  selection = 'multiple',
  selectedKeys = [],
  pagination,
  onSelectionChange,
  onPaginationChange,
  onSort,
  onFilter,
  getRowKey = (record, index) => index.toString(),
  className = '',
  'data-testid': testId,
}: DataTableProps<T>) => {
  const [sortConfig, setSortConfig] = useState<{key: string; order: 'asc' | 'desc'} | null>(null);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [internalSelection, setInternalSelection] = useState<(string | number)[]>(selectedKeys);
  
  const roleColor = role ? colors.roles[role] : colors.brand.primary;

  // Update internal selection when prop changes
  React.useEffect(() => {
    setInternalSelection(selectedKeys);
  }, [selectedKeys]);

  // Table size configurations
  const getSizeConfig = () => {
    switch (size) {
      case 'sm':
        return {
          padding: spacing[2],
          fontSize: typography.sizes.sm,
          headerPadding: spacing[3],
        };
      case 'lg':
        return {
          padding: spacing[5],
          fontSize: typography.sizes.base,
          headerPadding: spacing[4],
        };
      default:
        return {
          padding: spacing[3],
          fontSize: typography.sizes.sm,
          headerPadding: spacing[4],
        };
    }
  };

  const sizeConfig = getSizeConfig();

  // Styles
  const tableContainerStyles = {
    width: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: borders.radius.lg,
    overflow: 'hidden',
    boxShadow: bordered ? shadows.sm : 'none',
    border: bordered ? `${borders.width[1]} solid ${colors.neutral[200]}` : 'none',
    fontFamily: typography.fonts.sans.join(', '),
  };

  const tableStyles = {
    width: '100%',
    borderCollapse: 'collapse' as const,
    fontSize: sizeConfig.fontSize,
  };

  const headerStyles = {
    backgroundColor: colors.neutral[50],
    borderBottom: `${borders.width[2]} solid ${colors.neutral[200]}`,
  };

  const headerCellStyles = (column: Column<T>) => ({
    padding: sizeConfig.headerPadding,
    textAlign: column.align || 'left' as const,
    fontWeight: typography.weights.semibold,
    color: colors.neutral[700],
    borderRight: bordered ? `${borders.width[1]} solid ${colors.neutral[200]}` : 'none',
    cursor: column.sortable ? 'pointer' : 'default',
    userSelect: 'none' as const,
    position: 'relative' as const,
    transition: animations.transition.fast,
  });

  const bodyCellStyles = (align?: string) => ({
    padding: sizeConfig.padding,
    textAlign: align || 'left' as const,
    borderRight: bordered ? `${borders.width[1]} solid ${colors.neutral[200]}` : 'none',
    borderBottom: `${borders.width[1]} solid ${colors.neutral[100]}`,
    verticalAlign: 'middle' as const,
  });

  const rowStyles = (index: number, isSelected: boolean) => ({
    backgroundColor: 
      isSelected 
        ? `${roleColor}10`
        : striped && index % 2 === 1 
          ? colors.neutral[25] 
          : 'transparent',
    transition: animations.transition.fast,
  });

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig) return data;

    const column = columns.find(col => col.key === sortConfig.key);
    if (!column) return data;

    return [...data].sort((a, b) => {
      if (column.sorter) {
        const result = column.sorter(a, b);
        return sortConfig.order === 'desc' ? -result : result;
      }

      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const result = aValue.localeCompare(bValue);
        return sortConfig.order === 'desc' ? -result : result;
      }

      if (aValue < bValue) return sortConfig.order === 'desc' ? 1 : -1;
      if (aValue > bValue) return sortConfig.order === 'desc' ? -1 : 1;
      return 0;
    });
  }, [data, sortConfig, columns]);

  // Filter data
  const filteredData = useMemo(() => {
    if (Object.keys(filters).length === 0) return sortedData;

    return sortedData.filter(record => {
      return Object.entries(filters).every(([key, filterValue]) => {
        if (!filterValue || filterValue === '') return true;
        
        const recordValue = record[key];
        if (recordValue === null || recordValue === undefined) return false;

        if (typeof filterValue === 'string') {
          return recordValue.toString().toLowerCase().includes(filterValue.toLowerCase());
        }

        return recordValue === filterValue;
      });
    });
  }, [sortedData, filters]);

  // Paginated data
  const paginatedData = useMemo(() => {
    if (!pagination) return filteredData;
    
    const startIndex = (pagination.current - 1) * pagination.pageSize;
    const endIndex = startIndex + pagination.pageSize;
    return filteredData.slice(startIndex, endIndex);
  }, [filteredData, pagination]);

  // Handle sorting
  const handleSort = (column: Column<T>) => {
    if (!column.sortable) return;

    const newSortConfig = sortConfig?.key === column.key && sortConfig.order === 'asc'
      ? { key: column.key, order: 'desc' as const }
      : { key: column.key, order: 'asc' as const };

    setSortConfig(newSortConfig);
    onSort?.(newSortConfig.key, newSortConfig.order);
  };

  // Handle selection
  const handleRowSelection = (recordKey: string | number, record: T) => {
    if (!selectable) return;

    let newSelection: (string | number)[];
    
    if (selection === 'single') {
      newSelection = internalSelection.includes(recordKey) ? [] : [recordKey];
    } else {
      if (internalSelection.includes(recordKey)) {
        newSelection = internalSelection.filter(key => key !== recordKey);
      } else {
        newSelection = [...internalSelection, recordKey];
      }
    }

    setInternalSelection(newSelection);
    
    const selectedRows = data.filter((item, index) => 
      newSelection.includes(getRowKey(item, index))
    );
    
    onSelectionChange?.(newSelection, selectedRows);
  };

  // Handle select all
  const handleSelectAll = (checked: boolean) => {
    if (!selectable || selection === 'single') return;

    const newSelection = checked 
      ? paginatedData.map((record, index) => getRowKey(record, index))
      : [];

    setInternalSelection(newSelection);
    
    const selectedRows = data.filter((item, index) => 
      newSelection.includes(getRowKey(item, index))
    );
    
    onSelectionChange?.(newSelection, selectedRows);
  };

  // Loading state
  if (loading) {
    return (
      <div style={tableContainerStyles} className={className} data-testid={testId}>
        <div style={{ 
          padding: spacing[8], 
          textAlign: 'center', 
          color: colors.neutral[600] 
        }}>
          <div style={{
            width: '32px',
            height: '32px',
            border: `3px solid ${colors.neutral[200]}`,
            borderTop: `3px solid ${roleColor}`,
            borderRadius: borders.radius.full,
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px',
          }} />
          Loading data...
        </div>
        <style jsx>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Empty state
  if (empty || paginatedData.length === 0) {
    return (
      <div style={tableContainerStyles} className={className} data-testid={testId}>
        <div style={{ 
          padding: spacing[8], 
          textAlign: 'center', 
          color: colors.neutral[500] 
        }}>
          <div style={{ fontSize: '48px', marginBottom: spacing[4], opacity: 0.5 }}>
            📄
          </div>
          <div style={{ fontWeight: typography.weights.medium, marginBottom: spacing[2] }}>
            No Data
          </div>
          <div style={{ fontSize: typography.sizes.sm }}>
            {emptyMessage}
          </div>
        </div>
      </div>
    );
  }

  const allSelected = paginatedData.every((record, index) => 
    internalSelection.includes(getRowKey(record, index))
  );
  const someSelected = paginatedData.some((record, index) => 
    internalSelection.includes(getRowKey(record, index))
  );

  return (
    <div style={tableContainerStyles} className={className} data-testid={testId}>
      {/* Role-based accent bar */}
      {role && (
        <div style={{
          width: '100%',
          height: '3px',
          backgroundColor: roleColor,
        }} />
      )}
      
      <table style={tableStyles}>
        <thead style={headerStyles}>
          <tr>
            {selectable && (
              <th style={{ ...headerCellStyles({ key: '', title: '' }), width: '40px' }}>
                {selection === 'multiple' && (
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={input => {
                      if (input) input.indeterminate = !allSelected && someSelected;
                    }}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    style={{ cursor: 'pointer' }}
                  />
                )}
              </th>
            )}
            
            {columns.map((column, index) => (
              <th
                key={column.key}
                style={{
                  ...headerCellStyles(column),
                  width: column.width,
                  borderRight: index === columns.length - 1 ? 'none' : headerCellStyles(column).borderRight,
                }}
                onClick={() => handleSort(column)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: spacing[1] }}>
                  {column.title}
                  {column.sortable && (
                    <span style={{ fontSize: '10px', color: colors.neutral[400] }}>
                      {sortConfig?.key === column.key ? 
                        (sortConfig.order === 'asc' ? '▲' : '▼') : '↕'
                      }
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        
        <tbody>
          {paginatedData.map((record, rowIndex) => {
            const recordKey = getRowKey(record, rowIndex);
            const isSelected = internalSelection.includes(recordKey);
            
            return (
              <tr
                key={recordKey}
                style={rowStyles(rowIndex, isSelected)}
                onMouseEnter={hoverable ? (e) => {
                  if (!isSelected) {
                    (e.currentTarget as HTMLElement).style.backgroundColor = colors.neutral[50];
                  }
                } : undefined}
                onMouseLeave={hoverable ? (e) => {
                  if (!isSelected) {
                    (e.currentTarget as HTMLElement).style.backgroundColor = 
                      striped && rowIndex % 2 === 1 ? colors.neutral[25] : 'transparent';
                  }
                } : undefined}
              >
                {selectable && (
                  <td style={bodyCellStyles('center')}>
                    <input
                      type={selection === 'single' ? 'radio' : 'checkbox'}
                      checked={isSelected}
                      onChange={() => handleRowSelection(recordKey, record)}
                      style={{ cursor: 'pointer' }}
                    />
                  </td>
                )}
                
                {columns.map((column, colIndex) => (
                  <td
                    key={column.key}
                    style={{
                      ...bodyCellStyles(column.align),
                      borderRight: colIndex === columns.length - 1 ? 'none' : bodyCellStyles().borderRight,
                    }}
                  >
                    {column.render 
                      ? column.render(record[column.key], record, rowIndex)
                      : record[column.key]
                    }
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
      
      {/* Pagination */}
      {pagination && (
        <div style={{
          padding: spacing[4],
          borderTop: `${borders.width[1]} solid ${colors.neutral[200]}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: typography.sizes.sm,
          color: colors.neutral[600],
        }}>
          <span>
            Showing {((pagination.current - 1) * pagination.pageSize) + 1} to{' '}
            {Math.min(pagination.current * pagination.pageSize, pagination.total)} of{' '}
            {pagination.total} entries
          </span>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: spacing[2] }}>
            {/* Pagination controls would go here */}
            <button
              disabled={pagination.current === 1}
              onClick={() => onPaginationChange?.(pagination.current - 1, pagination.pageSize)}
              style={{
                padding: `${spacing[1]} ${spacing[2]}`,
                border: `${borders.width[1]} solid ${colors.neutral[300]}`,
                borderRadius: borders.radius.sm,
                backgroundColor: '#FFFFFF',
                color: colors.neutral[700],
                cursor: pagination.current === 1 ? 'not-allowed' : 'pointer',
                opacity: pagination.current === 1 ? 0.5 : 1,
              }}
            >
              Previous
            </button>
            
            <span style={{ padding: `0 ${spacing[3]}` }}>
              Page {pagination.current} of {Math.ceil(pagination.total / pagination.pageSize)}
            </span>
            
            <button
              disabled={pagination.current * pagination.pageSize >= pagination.total}
              onClick={() => onPaginationChange?.(pagination.current + 1, pagination.pageSize)}
              style={{
                padding: `${spacing[1]} ${spacing[2]}`,
                border: `${borders.width[1]} solid ${colors.neutral[300]}`,
                borderRadius: borders.radius.sm,
                backgroundColor: '#FFFFFF',
                color: colors.neutral[700],
                cursor: pagination.current * pagination.pageSize >= pagination.total ? 'not-allowed' : 'pointer',
                opacity: pagination.current * pagination.pageSize >= pagination.total ? 0.5 : 1,
              }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataTable;