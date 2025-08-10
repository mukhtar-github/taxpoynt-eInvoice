/**
 * TaxPoynt Input Component
 * ========================
 * Strategic input component with role-aware styling and enterprise polish.
 * Foundation primitive for all text input needs across the platform.
 */

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { clsx } from 'clsx';

const inputVariants = cva(
  // Base styles - Strategic foundation
  [
    'w-full rounded-md border transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:cursor-not-allowed disabled:opacity-50',
    'placeholder:text-gray-400'
  ],
  {
    variants: {
      variant: {
        // Default - Clean professional input
        default: [
          'border-gray-300 bg-white text-gray-900',
          'focus:border-blue-500 focus:ring-blue-500',
          'hover:border-gray-400'
        ],
        
        // Filled - Subtle background
        filled: [
          'border-gray-200 bg-gray-50 text-gray-900',
          'focus:border-blue-500 focus:ring-blue-500 focus:bg-white',
          'hover:bg-white hover:border-gray-300'
        ],
        
        // Ghost - Minimal styling
        ghost: [
          'border-transparent bg-transparent text-gray-900',
          'focus:border-blue-500 focus:ring-blue-500 focus:bg-white',
          'hover:bg-gray-50'
        ]
      },
      
      size: {
        sm: 'px-3 py-1.5 text-sm h-8',
        md: 'px-3 py-2 text-sm h-10',
        lg: 'px-4 py-3 text-base h-12'
      },
      
      // Role-aware styling for strategic user experience
      role: {
        si: '',      // System Integrator (default)
        app: '',     // Access Point Provider (Nigerian compliance)
        hybrid: '',  // Hybrid users (premium styling)
        admin: ''    // Admin interface (distinctive styling)
      },
      
      // State variants
      error: {
        true: 'border-red-500 focus:border-red-500 focus:ring-red-500 text-red-900',
        false: ''
      },
      
      success: {
        true: 'border-green-500 focus:border-green-500 focus:ring-green-500',
        false: ''
      }
    },
    
    defaultVariants: {
      variant: 'default',
      size: 'md',
      role: 'si',
      error: false,
      success: false
    },
    
    // Role-specific compound variants
    compoundVariants: [
      // APP role uses Nigerian compliance green
      {
        variant: 'default',
        role: 'app',
        class: 'focus:border-green-600 focus:ring-green-600'
      },
      
      // Hybrid role uses premium indigo
      {
        variant: 'default',
        role: 'hybrid',
        class: 'focus:border-indigo-500 focus:ring-indigo-500'
      },
      
      // Admin role uses distinctive purple
      {
        variant: 'default',
        role: 'admin',
        class: 'focus:border-purple-500 focus:ring-purple-500'
      }
    ]
  }
);

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  error?: boolean;
  success?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

/**
 * Input Component
 * ===============
 * Strategic input with role-aware styling and enterprise polish.
 * 
 * Features:
 * - Role-based theming (SI, APP, Hybrid, Admin)
 * - Multiple variants and sizes
 * - Icon support for enhanced UX
 * - Error and success states
 * - Accessibility-first design
 * 
 * @example
 * ```tsx
 * <Input 
 *   variant="default" 
 *   role="app" 
 *   placeholder="Enter invoice number"
 *   leftIcon={<InvoiceIcon />}
 * />
 * ```
 */
export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant, size, role, error, success, leftIcon, rightIcon, ...props }, ref) => {
    return (
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-400">{leftIcon}</span>
          </div>
        )}
        
        <input
          className={clsx(
            inputVariants({ variant, size, role, error, success }),
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            className
          )}
          ref={ref}
          {...props}
        />
        
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <span className="text-gray-400">{rightIcon}</span>
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { inputVariants };