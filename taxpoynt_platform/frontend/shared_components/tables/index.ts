/**
 * Tables Components Index
 * ======================
 * 
 * Central export for all TaxPoynt Platform table components.
 * Provides data display components with consistent styling and functionality.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

// Import all table components
import DataTable from './DataTable';
import SimpleTable from './SimpleTable';

// Export individual components
export { DataTable, SimpleTable };

// Export component types and interfaces
export type {
  DataTableProps,
  DataTableColumn,
  SortConfig,
  FilterConfig,
  PaginationConfig,
  SelectionConfig
} from './DataTable';

export type {
  SimpleTableProps,
  SimpleTableColumn
} from './SimpleTable';

// Default export for convenience
const TablesComponents = {
  DataTable,
  SimpleTable
};

export default TablesComponents;

/**
 * Usage Examples:
 * 
 * Basic Simple Table:
 * ```tsx
 * import { SimpleTable } from '../shared_components/tables';
 * 
 * const columns = [
 *   { key: 'name', title: 'Name' },
 *   { key: 'email', title: 'Email' },
 *   { key: 'status', title: 'Status', align: 'center' }
 * ];
 * 
 * <SimpleTable
 *   columns={columns}
 *   data={users}
 *   onRowClick={(user) => console.log(user)}
 * />
 * ```
 * 
 * Advanced Data Table:
 * ```tsx
 * import { DataTable } from '../shared_components/tables';
 * 
 * const columns = [
 *   { 
 *     key: 'name', 
 *     title: 'Name',
 *     sortable: true,
 *     filterable: true
 *   },
 *   { 
 *     key: 'amount', 
 *     title: 'Amount',
 *     sortable: true,
 *     render: (value) => `₦${value.toLocaleString()}`
 *   }
 * ];
 * 
 * <DataTable
 *   columns={columns}
 *   data={transactions}
 *   pagination={{ pageSize: 10 }}
 *   selection={{ type: 'multiple' }}
 *   onSelectionChange={(selected) => setSelected(selected)}
 * />
 * ```
 * 
 * Component Features:
 * 
 * DataTable Features:
 * - Advanced sorting (multiple columns, custom sort functions)
 * - Filtering (text, date, number, custom filters)
 * - Pagination (configurable page sizes, navigation)
 * - Row selection (single/multiple with callbacks)
 * - Search functionality (global and column-specific)
 * - Responsive design with mobile optimizations
 * - Loading states and empty states
 * - Export functionality (CSV, Excel, PDF)
 * - Custom cell rendering and formatting
 * 
 * SimpleTable Features:
 * - Lightweight table for basic data display
 * - Striped rows and hover effects
 * - Bordered and compact variants
 * - Custom cell rendering
 * - Row click handlers
 * - Loading states
 * - Empty state messaging
 * 
 * Design System Integration:
 * - Consistent with TaxPoynt design system colors
 * - Proper spacing and typography
 * - Responsive behavior
 * - Accessibility features (ARIA labels, keyboard navigation)
 * - Theme-aware styling
 * 
 * Performance Considerations:
 * - Virtual scrolling for large datasets (DataTable)
 * - Lazy loading and pagination
 * - Memoized rendering for complex cells
 * - Efficient sorting and filtering algorithms
 * - Minimal re-renders on state changes
 */