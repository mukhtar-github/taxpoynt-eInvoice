/**
 * Mobile-Optimized Data Table Component
 * 
 * Features:
 * - Responsive card layout for mobile
 * - Table layout for desktop
 * - Touch-friendly interactions
 * - Swipe actions on mobile
 * - Infinite scroll support
 * - Search and filter capabilities
 * - Sort functionality with touch-friendly headers
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  Search, 
  Filter, 
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { SwipeableCard, TouchActionButton } from './TouchInteractions';
import { useBreakpoint } from './ResponsiveUtilities';
import { Badge } from './Badge';
import { Button } from './Button';
import { Input } from './Input';

// Column definition interface
interface Column<T = any> {
  id: string;
  header: string;
  accessor: keyof T | ((row: T) => React.ReactNode);
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
  minWidth?: string;
  align?: 'left' | 'center' | 'right';
  mobileLabel?: string; // Alternative label for mobile view
  hideOnMobile?: boolean;
  priority?: 'high' | 'medium' | 'low'; // Show priority on mobile
}

// Sort configuration
interface SortConfig {
  column: string;
  direction: 'asc' | 'desc';
}

// Row action definition
interface RowAction<T = any> {
  id: string;
  label: string;
  icon: React.ReactNode;
  onClick: (row: T) => void;
  variant?: 'default' | 'destructive' | 'success' | 'warning';
  showOnMobile?: boolean;
}

// Main props interface
interface MobileDataTableProps<T = any> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  emptyMessage?: string;
  searchPlaceholder?: string;
  onSearch?: (query: string) => void;
  onSort?: (column: string, direction: 'asc' | 'desc') => void;
  sortConfig?: SortConfig;
  rowActions?: RowAction<T>[];
  onRowClick?: (row: T) => void;
  pageSize?: number;
  totalCount?: number;
  onLoadMore?: () => void;
  hasNextPage?: boolean;
  loadingMore?: boolean;
  className?: string;
  mobileCardKey?: keyof T; // Key to use as primary identifier in mobile cards
}

// Mobile card component for individual rows
interface MobileRowCardProps<T = any> {
  row: T;
  columns: Column<T>[];
  actions?: RowAction<T>[];
  onClick?: (row: T) => void;
  primaryKey?: keyof T;
}

const MobileRowCard = <T,>({ 
  row, 
  columns, 
  actions, 
  onClick, 
  primaryKey 
}: MobileRowCardProps<T>) => {
  const [showActions, setShowActions] = useState(false);

  // Get high priority columns for mobile
  const priorityColumns = columns
    .filter(col => !col.hideOnMobile && col.priority === 'high')
    .slice(0, 3); // Limit to 3 high priority columns

  const secondaryColumns = columns
    .filter(col => !col.hideOnMobile && col.priority !== 'high')
    .slice(0, 2); // Show up to 2 secondary columns

  const getValue = (column: Column<T>) => {
    if (typeof column.accessor === 'function') {
      return column.accessor(row);
    }
    return row[column.accessor];
  };

  const leftAction = actions && actions.length > 0 ? {
    icon: <Eye className="w-4 h-4" />,
    label: 'View',
    color: 'bg-blue-500',
    action: () => actions[0].onClick(row)
  } : undefined;

  const rightAction = actions && actions.length > 1 ? {
    icon: actions[1].icon,
    label: actions[1].label,
    color: actions[1].variant === 'destructive' ? 'bg-red-500' : 'bg-green-500',
    action: () => actions[1].onClick(row)
  } : undefined;

  return (
    <SwipeableCard
      leftAction={leftAction}
      rightAction={rightAction}
      className="mb-3"
    >
      <div 
        className={cn(
          'bg-white border border-gray-200 rounded-lg p-4 shadow-sm',
          onClick && 'cursor-pointer hover:shadow-md transition-shadow'
        )}
        onClick={() => onClick?.(row)}
      >
        {/* Primary information */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            {priorityColumns.map((column) => (
              <div key={column.id} className="mb-1">
                <div className="text-sm font-medium text-gray-900">
                  {getValue(column)}
                </div>
                <div className="text-xs text-gray-500">
                  {column.mobileLabel || column.header}
                </div>
              </div>
            ))}
          </div>

          {/* Actions button */}
          {actions && actions.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowActions(!showActions);
              }}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <MoreVertical className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>

        {/* Secondary information */}
        {secondaryColumns.length > 0 && (
          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-100">
            {secondaryColumns.map((column) => (
              <div key={column.id}>
                <div className="text-xs text-gray-500 mb-1">
                  {column.mobileLabel || column.header}
                </div>
                <div className="text-sm text-gray-900">
                  {getValue(column)}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Expanded actions */}
        {showActions && actions && (
          <div className="pt-3 border-t border-gray-100 mt-3">
            <div className="flex flex-wrap gap-2">
              {actions.filter(action => action.showOnMobile !== false).map((action) => (
                <TouchActionButton
                  key={action.id}
                  icon={action.icon}
                  label={action.label}
                  onClick={() => {
                    action.onClick(row);
                    setShowActions(false);
                  }}
                  variant={action.variant === 'destructive' ? 'error' : 'secondary'}
                  size="sm"
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </SwipeableCard>
  );
};

// Desktop table header with sorting
interface TableHeaderProps<T> {
  column: Column<T>;
  sortConfig?: SortConfig;
  onSort?: (column: string) => void;
}

const TableHeader = <T,>({ column, sortConfig, onSort }: TableHeaderProps<T>) => {
  const isSorted = sortConfig?.column === column.id;
  const direction = isSorted ? sortConfig.direction : null;

  return (
    <th
      className={cn(
        'px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b border-gray-200',
        column.sortable && 'cursor-pointer hover:bg-gray-50 select-none',
        `text-${column.align || 'left'}`
      )}
      style={{
        width: column.width,
        minWidth: column.minWidth
      }}
      onClick={() => column.sortable && onSort?.(column.id)}
    >
      <div className="flex items-center space-x-1">
        <span>{column.header}</span>
        {column.sortable && (
          <div className="flex flex-col">
            <ChevronUp 
              className={cn(
                'w-3 h-3 -mb-1',
                direction === 'asc' ? 'text-primary' : 'text-gray-400'
              )} 
            />
            <ChevronDown 
              className={cn(
                'w-3 h-3',
                direction === 'desc' ? 'text-primary' : 'text-gray-400'
              )} 
            />
          </div>
        )}
      </div>
    </th>
  );
};

// Main mobile data table component
export const MobileDataTable = <T,>({
  data,
  columns,
  loading = false,
  emptyMessage = 'No data available',
  searchPlaceholder = 'Search...',
  onSearch,
  onSort,
  sortConfig,
  rowActions,
  onRowClick,
  pageSize = 10,
  totalCount,
  onLoadMore,
  hasNextPage = false,
  loadingMore = false,
  className = '',
  mobileCardKey
}: MobileDataTableProps<T>) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const isMobile = !useBreakpoint('md');
  const observerRef = useRef<HTMLDivElement>(null);

  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    onSearch?.(query);
  };

  // Handle sort
  const handleSort = (columnId: string) => {
    if (!onSort) return;
    
    const direction = sortConfig?.column === columnId && sortConfig.direction === 'asc' 
      ? 'desc' 
      : 'asc';
    
    onSort(columnId, direction);
  };

  // Infinite scroll observer
  useEffect(() => {
    if (!observerRef.current || !onLoadMore) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasNextPage && !loadingMore) {
          onLoadMore();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(observerRef.current);

    return () => observer.disconnect();
  }, [hasNextPage, loadingMore, onLoadMore]);

  // Get table value
  const getValue = (row: T, column: Column<T>) => {
    if (typeof column.accessor === 'function') {
      return column.accessor(row);
    }
    return row[column.accessor];
  };

  return (
    <div className={cn('bg-white rounded-lg shadow-sm border border-gray-200', className)}>
      {/* Header with search and filters */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                type="text"
                placeholder={searchPlaceholder}
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2"
          >
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </Button>
        </div>
      </div>

      {/* Data display */}
      <div className={cn('min-h-[200px]', isMobile ? 'p-4' : '')}>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <span className="ml-2 text-gray-600">Loading...</span>
          </div>
        ) : data.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <p className="text-lg font-medium">{emptyMessage}</p>
            <p className="text-sm mt-1">Try adjusting your search or filters</p>
          </div>
        ) : isMobile ? (
          // Mobile card layout
          <div className="space-y-3">
            {data.map((row, index) => (
              <MobileRowCard
                key={mobileCardKey ? String(row[mobileCardKey]) : index}
                row={row}
                columns={columns}
                actions={rowActions}
                onClick={onRowClick}
                primaryKey={mobileCardKey}
              />
            ))}
          </div>
        ) : (
          // Desktop table layout
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  {columns.map((column) => (
                    <TableHeader
                      key={column.id}
                      column={column}
                      sortConfig={sortConfig}
                      onSort={handleSort}
                    />
                  ))}
                  {rowActions && rowActions.length > 0 && (
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b border-gray-200 w-20">
                      Actions
                    </th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.map((row, index) => (
                  <tr
                    key={mobileCardKey ? String(row[mobileCardKey]) : index}
                    className={cn(
                      'hover:bg-gray-50 transition-colors',
                      onRowClick && 'cursor-pointer'
                    )}
                    onClick={() => onRowClick?.(row)}
                  >
                    {columns.map((column) => (
                      <td
                        key={column.id}
                        className={cn(
                          'px-4 py-3 text-sm text-gray-900',
                          `text-${column.align || 'left'}`
                        )}
                      >
                        {getValue(row, column)}
                      </td>
                    ))}
                    {rowActions && rowActions.length > 0 && (
                      <td className="px-4 py-3 text-sm">
                        <div className="flex items-center space-x-2">
                          {rowActions.slice(0, 2).map((action) => (
                            <button
                              key={action.id}
                              onClick={(e) => {
                                e.stopPropagation();
                                action.onClick(row);
                              }}
                              className="p-1 hover:bg-gray-100 rounded transition-colors"
                              title={action.label}
                            >
                              {action.icon}
                            </button>
                          ))}
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Load more trigger for infinite scroll */}
        {hasNextPage && (
          <div ref={observerRef} className="py-4 text-center">
            {loadingMore ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                <span className="ml-2 text-gray-600">Loading more...</span>
              </div>
            ) : (
              <Button
                variant="outline"
                onClick={onLoadMore}
                className="text-primary border-primary hover:bg-primary hover:text-white"
              >
                Load More
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Footer with count info */}
      {totalCount && (
        <div className="px-4 py-3 border-t border-gray-200 text-sm text-gray-600">
          Showing {data.length} of {totalCount} results
        </div>
      )}
    </div>
  );
};

export default MobileDataTable;