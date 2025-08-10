/**
 * Navigation Components Index
 * ==========================
 * 
 * Central export for all TaxPoynt Platform navigation components.
 * Provides navigation and wayfinding components with consistent behavior.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

// Import all navigation components
import Breadcrumb from './Breadcrumb';
import Pagination from './Pagination';
import Tabs from './Tabs';

// Export individual components
export { Breadcrumb, Pagination, Tabs };

// Export component types and interfaces
export type {
  BreadcrumbProps,
  BreadcrumbItem
} from './Breadcrumb';

export type {
  PaginationProps
} from './Pagination';

export type {
  TabsProps,
  TabItem
} from './Tabs';

// Default export for convenience
const NavigationComponents = {
  Breadcrumb,
  Pagination,
  Tabs
};

export default NavigationComponents;

/**
 * Usage Examples:
 * 
 * Breadcrumb Navigation:
 * ```tsx
 * import { Breadcrumb } from '../shared_components/navigation';
 * 
 * const breadcrumbItems = [
 *   { label: 'Home', href: '/' },
 *   { label: 'Invoices', href: '/invoices' },
 *   { label: 'Invoice Details', active: true }
 * ];
 * 
 * <Breadcrumb
 *   items={breadcrumbItems}
 *   onItemClick={(item, index) => navigate(item.href)}
 * />
 * ```
 * 
 * Pagination:
 * ```tsx
 * import { Pagination } from '../shared_components/navigation';
 * 
 * <Pagination
 *   current={currentPage}
 *   total={totalRecords}
 *   pageSize={pageSize}
 *   showSizeChanger
 *   showQuickJumper
 *   showTotal={(total, range) => 
 *     `${range[0]}-${range[1]} of ${total} invoices`
 *   }
 *   onChange={(page, size) => {
 *     setCurrentPage(page);
 *     setPageSize(size);
 *   }}
 * />
 * ```
 * 
 * Tabs:
 * ```tsx
 * import { Tabs } from '../shared_components/navigation';
 * 
 * const tabItems = [
 *   {
 *     key: 'overview',
 *     label: 'Overview',
 *     icon: <OverviewIcon />,
 *     content: <OverviewContent />
 *   },
 *   {
 *     key: 'details',
 *     label: 'Details',
 *     icon: <DetailsIcon />,
 *     content: <DetailsContent />
 *   },
 *   {
 *     key: 'settings',
 *     label: 'Settings',
 *     icon: <SettingsIcon />,
 *     content: <SettingsContent />,
 *     closable: true
 *   }
 * ];
 * 
 * <Tabs
 *   items={tabItems}
 *   type="line"
 *   size="default"
 *   activeKey={activeTab}
 *   onChange={setActiveTab}
 *   onEdit={(key, action) => {
 *     if (action === 'remove') {
 *       removeTab(key);
 *     }
 *   }}
 * />
 * ```
 * 
 * Component Features:
 * 
 * Breadcrumb Features:
 * - Hierarchical navigation display
 * - Custom separators and icons
 * - Home icon support
 * - Maximum items with ellipsis
 * - Click handlers for navigation
 * - Responsive design
 * 
 * Pagination Features:
 * - Standard and simple pagination styles
 * - Page size selection
 * - Quick page jumper
 * - Total records display
 * - Custom page size options
 * - Responsive behavior
 * - Disabled states
 * 
 * Tabs Features:
 * - Multiple tab types (line, card, pill)
 * - Tab positioning (top, bottom, left, right)
 * - Closable tabs with edit callbacks
 * - Icons and custom content
 * - Animated transitions
 * - Disabled tab states
 * - Centered alignment option
 * 
 * Design System Integration:
 * - Consistent with TaxPoynt design system
 * - Proper color and spacing usage
 * - Typography alignment
 * - Responsive behavior
 * - Accessibility features (ARIA labels, keyboard navigation)
 * - Theme-aware styling
 * 
 * Accessibility Features:
 * - ARIA roles and labels
 * - Keyboard navigation support
 * - Screen reader compatibility
 * - Focus management
 * - Semantic HTML structure
 */