/**
 * Design System Components
 * ========================
 * 
 * Core primitive components with role-aware theming.
 * These are the foundation building blocks for all UI across TaxPoynt Platform.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

// Export all primitive components
export { Button, buttonVariants } from './Button';
export type { ButtonProps } from './Button';

export { Input, inputVariants } from './Input';  
export type { InputProps } from './Input';

// Default export for convenience
const DesignSystemComponents = {
  Button,
  Input
};

export default DesignSystemComponents;

/**
 * Design System Principles:
 * 
 * Role-Based Theming:
 * - SI (System Integrator): TaxPoynt blue (#0054B0)
 * - APP (Access Point Provider): Nigerian green (#008751)  
 * - Hybrid: Premium indigo (#6366F1)
 * - Admin: Distinctive purple (#7C3AED)
 * 
 * Component Variants:
 * - Primary: Main actions (role-aware colors)
 * - Secondary: Alternative actions (neutral)
 * - Outline: Subtle actions (borders only)
 * - Ghost: Minimal actions (background on hover)
 * - Destructive: Delete/remove actions (red)
 * 
 * Sizes:
 * - sm: Compact UI (h-8)
 * - md: Standard UI (h-10) 
 * - lg: Prominent UI (h-12)
 * - xl: Hero sections (h-14)
 * 
 * Accessibility:
 * - ARIA labels and roles
 * - Keyboard navigation
 * - Focus management
 * - Screen reader support
 * 
 * Usage Guidelines:
 * - Use these primitives as building blocks
 * - Compose complex components in shared_components/
 * - Apply role prop based on user context
 * - Follow TaxPoynt visual hierarchy
 */