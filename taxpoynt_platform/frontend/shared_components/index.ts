/**
 * Shared Components Index
 * =======================
 * 
 * Central export for all TaxPoynt Platform shared components.
 * Re-exports design system primitives and provides complex business logic components.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

// Re-export Design System Primitives (Button, Input, etc.)
export { Button, buttonVariants } from '../design_system/components/Button';
export type { ButtonProps } from '../design_system/components/Button';

export { Input, inputVariants } from '../design_system/components/Input';
export type { InputProps } from '../design_system/components/Input';

// Form Components (Business Logic)
export * from './forms';
export { default as FormComponents } from './forms';

// Chart Components (Business Logic) 
export * from './charts';
export { default as ChartComponents } from './charts';

// Table Components (Business Logic)
export * from './tables';
export { default as TableComponents } from './tables';

// Navigation Components (Business Logic)
export * from './navigation';
export { default as NavigationComponents } from './navigation';

// Aggregate export for all components
const SharedComponents = {
  Forms: FormComponents,
  Charts: ChartComponents,
  Tables: TableComponents,
  Navigation: NavigationComponents
};

export default SharedComponents;

/**
 * Usage Examples:
 * 
 * Design System Primitives (Button, Input, etc.):
 * ```tsx
 * import { Button } from '../shared_components';
 * // or directly from design system:
 * import { Button } from '../design_system/components/Button';
 * 
 * <Button variant="primary" role="app">Submit Invoice</Button>
 * ```
 * 
 * Business Logic Components:
 * ```tsx
 * import { DataTable, FormField, BarChart, Breadcrumb } from '../shared_components';
 * 
 * <DataTable 
 *   columns={columns} 
 *   data={invoices}
 *   pagination={{ pageSize: 10 }}
 *   selection={{ type: 'multiple' }}
 * />
 * ```
 * 
 * Category Import:
 * ```tsx
 * import { FormComponents, ChartComponents } from '../shared_components';
 * 
 * <FormComponents.FormField label="Invoice Number">
 *   <FormComponents.Select options={options} />
 * </FormComponents.FormField>
 * 
 * <ChartComponents.BarChart data={salesData} />
 * ```
 * 
 * Component Architecture:
 * 
 * Design System Primitives (from design_system/):
 * - Button (with role-based theming: SI, APP, Hybrid, Admin)
 * - Input, Card, Modal, Badge, Alert, etc. (future)
 * 
 * Shared Components (business logic):
 * - Form Components: FormField, FormSection, Select (with validation)
 * - Chart Components: BaseChart, BarChart, LineChart (with data processing)
 * - Table Components: DataTable (with sorting, filtering, pagination)
 * - Navigation Components: Breadcrumb, Pagination, Tabs (with state management)
 * 
 * Design Principles:
 * - Primitives live in design_system/ (single source of truth for visual design)
 * - Business logic lives in shared_components/ (reusable functionality)
 * - All components use TailwindCSS from design system tokens
 * - Role-based theming for TaxPoynt user types (SI, APP, Hybrid, Admin)
 * - Accessibility-first design (ARIA, keyboard navigation)
 * - TypeScript interfaces for all props and consistent API patterns
 */