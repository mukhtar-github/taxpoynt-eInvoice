/**
 * Enhanced Responsive Utilities for Week 4: Mobile Optimization & Polish
 * 
 * Features:
 * - Advanced responsive breakpoints and utilities
 * - Touch-first interaction helpers
 * - Mobile-specific layout components
 * - Gesture support utilities
 * - Accessibility-first responsive patterns
 */

import React, { useState, useEffect, useRef, RefObject } from 'react';
import { cn } from '../../utils/cn';

// Enhanced breakpoint utilities
export const breakpoints = {
  xs: 475,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;

// Custom hook for responsive breakpoints
export const useBreakpoint = (breakpoint: keyof typeof breakpoints = 'md') => {
  const [isAbove, setIsAbove] = useState(false);

  useEffect(() => {
    const checkBreakpoint = () => {
      setIsAbove(window.innerWidth >= breakpoints[breakpoint]);
    };

    checkBreakpoint();
    window.addEventListener('resize', checkBreakpoint);
    return () => window.removeEventListener('resize', checkBreakpoint);
  }, [breakpoint]);

  return isAbove;
};

// Mobile-first responsive container
interface ResponsiveContainerProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
}

export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  className = '',
  maxWidth = 'xl',
  padding = 'md'
}) => {
  const maxWidthClasses = {
    xs: 'max-w-xs',
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    full: 'max-w-full'
  };

  const paddingClasses = {
    none: '',
    sm: 'px-4 sm:px-6',
    md: 'px-4 sm:px-6 lg:px-8',
    lg: 'px-6 sm:px-8 lg:px-12',
    xl: 'px-8 sm:px-12 lg:px-16'
  };

  return (
    <div className={cn(
      'w-full mx-auto',
      maxWidthClasses[maxWidth],
      paddingClasses[padding],
      className
    )}>
      {children}
    </div>
  );
};

// Responsive grid with auto-fit columns
interface ResponsiveGridProps {
  children: React.ReactNode;
  className?: string;
  minColumnWidth?: string;
  gap?: 'sm' | 'md' | 'lg' | 'xl';
  columns?: {
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
    '2xl'?: number;
  };
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  className = '',
  minColumnWidth = '280px',
  gap = 'md',
  columns
}) => {
  const gapClasses = {
    sm: 'gap-3',
    md: 'gap-4 md:gap-6',
    lg: 'gap-6 md:gap-8',
    xl: 'gap-8 md:gap-10'
  };

  // If specific columns are defined, use responsive grid classes
  if (columns) {
    const gridClasses = [
      columns.xs && `grid-cols-${columns.xs}`,
      columns.sm && `sm:grid-cols-${columns.sm}`,
      columns.md && `md:grid-cols-${columns.md}`,
      columns.lg && `lg:grid-cols-${columns.lg}`,
      columns.xl && `xl:grid-cols-${columns.xl}`,
      columns['2xl'] && `2xl:grid-cols-${columns['2xl']}`
    ].filter(Boolean).join(' ');

    return (
      <div className={cn(
        'grid',
        gridClasses,
        gapClasses[gap],
        className
      )}>
        {children}
      </div>
    );
  }

  // Auto-fit grid based on minimum column width
  return (
    <div 
      className={cn('grid', gapClasses[gap], className)}
      style={{
        gridTemplateColumns: `repeat(auto-fit, minmax(${minColumnWidth}, 1fr))`
      }}
    >
      {children}
    </div>
  );
};

// Touch-friendly button wrapper
interface TouchTargetProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  minTouchSize?: boolean;
}

export const TouchTarget: React.FC<TouchTargetProps> = ({
  children,
  className = '',
  onClick,
  disabled = false,
  minTouchSize = true
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'touch-manipulation select-none transition-all duration-200',
        minTouchSize && 'min-h-touch min-w-touch',
        'active:scale-95 active:opacity-70',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      {children}
    </button>
  );
};

// Responsive typography scale
interface ResponsiveTextProps {
  children: React.ReactNode;
  size?: 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl';
  responsive?: boolean;
  className?: string;
}

export const ResponsiveText: React.FC<ResponsiveTextProps> = ({
  children,
  size = 'base',
  responsive = true,
  className = ''
}) => {
  const sizeClasses = {
    xs: responsive ? 'text-xs sm:text-sm' : 'text-xs',
    sm: responsive ? 'text-sm sm:text-base' : 'text-sm',
    base: responsive ? 'text-base sm:text-lg' : 'text-base',
    lg: responsive ? 'text-lg sm:text-xl' : 'text-lg',
    xl: responsive ? 'text-xl sm:text-2xl' : 'text-xl',
    '2xl': responsive ? 'text-2xl sm:text-3xl' : 'text-2xl',
    '3xl': responsive ? 'text-3xl sm:text-4xl' : 'text-3xl',
    '4xl': responsive ? 'text-4xl sm:text-5xl' : 'text-4xl'
  };

  return (
    <span className={cn(sizeClasses[size], className)}>
      {children}
    </span>
  );
};

// Responsive spacing utility
export const getResponsiveSpacing = (spacing: {
  xs?: string;
  sm?: string;
  md?: string;
  lg?: string;
  xl?: string;
}) => {
  return [
    spacing.xs,
    spacing.sm && `sm:${spacing.sm}`,
    spacing.md && `md:${spacing.md}`,
    spacing.lg && `lg:${spacing.lg}`,
    spacing.xl && `xl:${spacing.xl}`
  ].filter(Boolean).join(' ');
};

// Hook for device detection
export const useDeviceDetection = () => {
  const [deviceInfo, setDeviceInfo] = useState({
    isMobile: false,
    isTablet: false,
    isDesktop: false,
    isTouch: false,
    userAgent: ''
  });

  useEffect(() => {
    const checkDevice = () => {
      const userAgent = navigator.userAgent.toLowerCase();
      const isMobile = /mobile|android|iphone|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
      const isTablet = /tablet|ipad/i.test(userAgent);
      const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      
      setDeviceInfo({
        isMobile,
        isTablet,
        isDesktop: !isMobile && !isTablet,
        isTouch,
        userAgent
      });
    };

    checkDevice();
  }, []);

  return deviceInfo;
};

// Responsive visibility utilities
interface ResponsiveShowProps {
  children: React.ReactNode;
  above?: keyof typeof breakpoints;
  below?: keyof typeof breakpoints;
  only?: keyof typeof breakpoints;
}

export const ResponsiveShow: React.FC<ResponsiveShowProps> = ({
  children,
  above,
  below,
  only
}) => {
  let classes = '';

  if (above) {
    classes = `hidden ${above}:block`;
  } else if (below) {
    const breakpointKeys = Object.keys(breakpoints) as Array<keyof typeof breakpoints>;
    const belowIndex = breakpointKeys.indexOf(below);
    if (belowIndex > 0) {
      const hideAtBreakpoint = breakpointKeys[belowIndex];
      classes = `block ${hideAtBreakpoint}:hidden`;
    }
  } else if (only) {
    const breakpointKeys = Object.keys(breakpoints) as Array<keyof typeof breakpoints>;
    const onlyIndex = breakpointKeys.indexOf(only);
    const nextBreakpoint = breakpointKeys[onlyIndex + 1];
    
    if (onlyIndex === 0) {
      classes = nextBreakpoint ? `block ${nextBreakpoint}:hidden` : 'block';
    } else {
      const prevBreakpoint = breakpointKeys[onlyIndex - 1];
      classes = nextBreakpoint 
        ? `hidden ${only}:block ${nextBreakpoint}:hidden`
        : `hidden ${only}:block`;
    }
  }

  return <div className={classes}>{children}</div>;
};

// Hook for intersection observer
export const useIntersectionObserver = (
  ref: RefObject<Element>,
  options?: IntersectionObserverInit
) => {
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    if (!ref.current) return;

    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    observer.observe(ref.current);

    return () => observer.disconnect();
  }, [ref, options]);

  return isIntersecting;
};

// Responsive image component
interface ResponsiveImageProps {
  src: string;
  alt: string;
  className?: string;
  sizes?: string;
  priority?: boolean;
  fill?: boolean;
}

export const ResponsiveImage: React.FC<ResponsiveImageProps> = ({
  src,
  alt,
  className = '',
  sizes = '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw',
  priority = false,
  fill = false
}) => {
  return (
    <div className={cn('relative overflow-hidden', className)}>
      <img
        src={src}
        alt={alt}
        className={cn(
          'object-cover transition-all duration-300',
          fill ? 'absolute inset-0 w-full h-full' : 'w-full h-auto'
        )}
        loading={priority ? 'eager' : 'lazy'}
        sizes={sizes}
      />
    </div>
  );
};

const ResponsiveUtilitiesExports = {
  ResponsiveContainer,
  ResponsiveGrid,
  TouchTarget,
  ResponsiveText,
  ResponsiveShow,
  ResponsiveImage,
  useBreakpoint,
  useDeviceDetection,
  useIntersectionObserver,
  getResponsiveSpacing,
  breakpoints
};

export default ResponsiveUtilitiesExports;