/**
 * TaxPoynt Button Component
 * ========================
 * Strategic button component with role-aware styling and enterprise polish.
 * Follows Steve Jobs' principle: "Simplicity is the ultimate sophistication"
 */

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { clsx } from 'clsx';
import { colors } from '../tokens';

const buttonVariants = cva(
  // Base styles - Strategic foundation
  [
    'inline-flex items-center justify-center whitespace-nowrap',
    'rounded-md text-sm font-medium transition-all duration-200',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
    'disabled:pointer-events-none disabled:opacity-50',
    'select-none cursor-pointer',
    // Steve Jobs principle: "Perfection in details"
    'hover:scale-[1.02] active:scale-[0.98]',
    'shadow-sm hover:shadow-md transition-shadow'
  ],
  {
    variants: {
      variant: {
        // Primary - TaxPoynt brand leadership
        primary: [
          'bg-blue-600 text-white border border-blue-600',
          'hover:bg-blue-700 hover:border-blue-700',
          'focus-visible:ring-blue-500',
          'shadow-blue-500/20'
        ],
        
        // Success - Nigerian compliance green
        success: [
          'bg-green-600 text-white border border-green-600',
          'hover:bg-green-700 hover:border-green-700',
          'focus-visible:ring-green-500',
          'shadow-green-500/20'
        ],
        
        // Secondary - Professional enterprise
        secondary: [
          'bg-white text-gray-900 border border-gray-300',
          'hover:bg-gray-50 hover:border-gray-400',
          'focus-visible:ring-gray-500',
          'shadow-gray-500/10'
        ],
        
        // Ghost - Minimal elegance
        ghost: [
          'text-gray-700 hover:text-gray-900',
          'hover:bg-gray-100',
          'focus-visible:ring-gray-500',
          'border-transparent shadow-none'
        ],
        
        // Outline - Clean precision
        outline: [
          'text-gray-700 border border-gray-300',
          'hover:bg-gray-50 hover:text-gray-900',
          'focus-visible:ring-gray-500',
          'bg-transparent shadow-none'
        ],
        
        // Destructive - Clear warning
        destructive: [
          'bg-red-600 text-white border border-red-600',
          'hover:bg-red-700 hover:border-red-700',
          'focus-visible:ring-red-500',
          'shadow-red-500/20'
        ]
      },
      
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 py-2',
        lg: 'h-12 px-8 text-base',
        xl: 'h-14 px-10 text-lg',
        icon: 'h-10 w-10 p-0'
      },
      
      // Role-aware styling for strategic user experience
      role: {
        si: '',      // System Integrator (default TaxPoynt styling)
        app: '',     // Access Point Provider (Nigerian compliance)
        hybrid: '',  // Hybrid users (premium styling)
        admin: ''    // Admin interface (distinctive styling)
      },
      
      // Strategic states
      loading: {
        true: 'cursor-wait opacity-70',
        false: ''
      }
    },
    
    defaultVariants: {
      variant: 'primary',
      size: 'md',
      role: 'si',
      loading: false
    },
    
    // Role-specific compound variants
    compoundVariants: [
      // APP role uses Nigerian compliance green
      {
        variant: 'primary',
        role: 'app',
        class: [
          'bg-green-600 hover:bg-green-700',
          'border-green-600 hover:border-green-700',
          'focus-visible:ring-green-500'
        ]
      },
      
      // Hybrid role uses premium indigo
      {
        variant: 'primary',
        role: 'hybrid',
        class: [
          'bg-indigo-600 hover:bg-indigo-700',
          'border-indigo-600 hover:border-indigo-700',
          'focus-visible:ring-indigo-500'
        ]
      },
      
      // Admin role uses distinctive purple
      {
        variant: 'primary',
        role: 'admin',
        class: [
          'bg-purple-600 hover:bg-purple-700',
          'border-purple-600 hover:border-purple-700',
          'focus-visible:ring-purple-500'
        ]
      }
    ]
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children?: React.ReactNode;
}

/**
 * Button Component
 * ===============
 * Strategic button with role-aware styling and enterprise polish.
 * 
 * Features:
 * - Role-based theming (SI, APP, Hybrid, Admin)
 * - Loading states with visual feedback
 * - Icon support for enhanced UX
 * - Accessibility-first design
 * - Strategic hover and focus states
 * 
 * @example
 * ```tsx
 * <Button variant="primary" role="app" loading={isSubmitting}>
 *   Submit Invoice
 * </Button>
 * ```
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, role, loading, leftIcon, rightIcon, children, disabled, ...props }, ref) => {
    return (
      <button
        className={clsx(buttonVariants({ variant, size, role, loading }), className)}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="mr-2 h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        
        {!loading && leftIcon && (
          <span className="mr-2">{leftIcon}</span>
        )}
        
        {children}
        
        {!loading && rightIcon && (
          <span className="ml-2">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { buttonVariants };