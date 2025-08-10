/**
 * TaxPoynt Design Tokens
 * =====================
 * Design tokens for consistent styling across the platform.
 * Based on existing TaxPoynt branding and professional enterprise design standards.
 */

export const colors = {
  // TaxPoynt Brand Colors (from existing logo.svg)
  brand: {
    primary: '#0054B0',      // TaxPoynt Blue (from logo)
    secondary: '#003875',    // Darker blue variant
    accent: '#0066CC',       // Lighter blue variant
    light: '#E6F2FF',        // Very light blue
  },
  
  // Nigerian Colors (for compliance/FIRS theming)
  nigeria: {
    green: '#008751',        // Nigerian flag green
    emerald: '#00A86B',      // Emerald green variant
    forest: '#006341',       // Dark green
  },
  
  // Enterprise Neutrals
  neutral: {
    50: '#F8FAFC',
    100: '#F1F5F9',
    200: '#E2E8F0',
    300: '#CBD5E1',
    400: '#94A3B8',
    500: '#64748B',
    600: '#475569',
    700: '#334155',
    800: '#1E293B',
    900: '#0F172A',
  },
  
  // Semantic Colors
  semantic: {
    success: '#10B981',      // Green for success states
    warning: '#F59E0B',      // Amber for warnings
    error: '#EF4444',        // Red for errors
    info: '#3B82F6',         // Blue for information
  },
  
  // Role-Based Colors
  roles: {
    si: '#0054B0',           // System Integrator (TaxPoynt blue)
    app: '#008751',          // Access Point Provider (Nigerian green)
    hybrid: '#6366F1',       // Hybrid users (indigo)
    admin: '#7C3AED',        // Admin interface (purple)
  }
} as const;

export const typography = {
  fonts: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'Consolas', 'monospace'],
    display: ['Inter', 'system-ui', 'sans-serif'],
  },
  
  sizes: {
    xs: '0.75rem',     // 12px
    sm: '0.875rem',    // 14px
    base: '1rem',      // 16px
    lg: '1.125rem',    // 18px
    xl: '1.25rem',     // 20px
    '2xl': '1.5rem',   // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
    '5xl': '3rem',     // 48px
    '6xl': '3.75rem',  // 60px
  },
  
  weights: {
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },
  
  lineHeights: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  }
} as const;

export const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
  32: '8rem',     // 128px
} as const;

export const borders = {
  radius: {
    none: '0',
    sm: '0.125rem',   // 2px
    md: '0.375rem',   // 6px
    lg: '0.5rem',     // 8px
    xl: '0.75rem',    // 12px
    '2xl': '1rem',    // 16px
    full: '9999px',
  },
  
  width: {
    0: '0',
    1: '1px',
    2: '2px',
    4: '4px',
    8: '8px',
  }
} as const;

export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
} as const;

export const animations = {
  transition: {
    fast: '150ms ease-in-out',
    base: '200ms ease-in-out',
    slow: '300ms ease-in-out',
  },
  
  easing: {
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
  }
} as const;

// Strategic Theme Configuration
export const themes = {
  light: {
    background: colors.neutral[50],
    surface: '#FFFFFF',
    text: {
      primary: colors.neutral[900],
      secondary: colors.neutral[600],
      muted: colors.neutral[400],
    },
    border: colors.neutral[200],
  },
  
  dark: {
    background: colors.neutral[900],
    surface: colors.neutral[800],
    text: {
      primary: colors.neutral[100],
      secondary: colors.neutral[300],
      muted: colors.neutral[500],
    },
    border: colors.neutral[700],
  }
} as const;

// Role-specific theme variations
export const roleThemes = {
  si: {
    primary: colors.brand.primary,
    accent: colors.brand.accent,
    background: colors.brand.light,
  },
  
  app: {
    primary: colors.nigeria.green,
    accent: colors.nigeria.emerald,
    background: '#F0F8FF',
  },
  
  hybrid: {
    primary: '#6366F1',
    accent: '#8B5CF6',
    background: '#F8FAFF',
  },
  
  admin: {
    primary: colors.roles.admin,
    accent: '#A855F7',
    background: '#FAF5FF',
  }
} as const;