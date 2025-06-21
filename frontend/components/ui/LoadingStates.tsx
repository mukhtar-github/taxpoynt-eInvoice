/**
 * Loading States and Micro-animations Components
 * 
 * Week 3 Implementation: Advanced loading states with:
 * - Multiple loading animation types
 * - Skeleton loaders for different content types
 * - Progress indicators with animations
 * - Micro-animations for state transitions
 * - Mobile-optimized touch feedback
 */

import React from 'react';
import { Loader2, RefreshCw, Zap, Database, Users, FileText, TrendingUp } from 'lucide-react';
import { cn } from '@/utils/cn';

// Base loading spinner with different sizes and variants
export interface LoadingSpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'white';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  variant = 'primary',
  className
}) => {
  const sizeClasses = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  };

  const variantClasses = {
    primary: 'text-primary',
    secondary: 'text-secondary',
    success: 'text-success',
    warning: 'text-warning',
    error: 'text-error',
    white: 'text-white'
  };

  return (
    <Loader2 
      className={cn(
        'animate-spin',
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
    />
  );
};

// Enhanced loading button with state transitions
export interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  loadingText?: string;
  loadingIcon?: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg' | 'touch';
  children: React.ReactNode;
}

export const LoadingButton: React.FC<LoadingButtonProps> = ({
  isLoading = false,
  loadingText,
  loadingIcon,
  variant = 'primary',
  size = 'md',
  children,
  disabled,
  className,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    primary: 'bg-primary text-white hover:bg-primary-dark focus:ring-primary',
    secondary: 'bg-secondary text-white hover:bg-secondary-dark focus:ring-secondary',
    outline: 'border border-primary text-primary hover:bg-primary hover:text-white focus:ring-primary',
    ghost: 'text-primary hover:bg-primary/10 focus:ring-primary'
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
    touch: 'px-6 py-4 text-base min-h-[48px]' // Mobile-optimized
  };

  return (
    <button
      {...props}
      disabled={disabled || isLoading}
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        isLoading && 'cursor-wait',
        className
      )}
    >
      {isLoading ? (
        <>
          {loadingIcon || <LoadingSpinner size="sm" variant="white" className="mr-2" />}
          {loadingText || 'Loading...'}
        </>
      ) : (
        children
      )}
    </button>
  );
};

// Skeleton loader components for different content types
export interface SkeletonProps {
  className?: string;
  animate?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({ 
  className, 
  animate = true 
}) => (
  <div 
    className={cn(
      'bg-gray-200 rounded',
      animate && 'animate-pulse',
      className
    )}
  />
);

// Card skeleton for loading integration cards
export const IntegrationCardSkeleton: React.FC = () => (
  <div className="p-6 border border-gray-200 rounded-lg animate-pulse">
    {/* Header */}
    <div className="flex items-start justify-between mb-4">
      <div className="flex items-center gap-3">
        <Skeleton className="w-12 h-12 rounded-xl" />
        <div>
          <Skeleton className="h-5 w-32 mb-2" />
          <Skeleton className="h-4 w-24" />
        </div>
      </div>
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>

    {/* Metrics */}
    <div className="grid grid-cols-3 gap-3 mb-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="text-center p-3 bg-gray-50 rounded-lg">
          <Skeleton className="h-6 w-8 mx-auto mb-1" />
          <Skeleton className="h-3 w-12 mx-auto" />
        </div>
      ))}
    </div>

    {/* Actions */}
    <div className="flex gap-2">
      <Skeleton className="h-10 flex-1" />
      <Skeleton className="h-10 flex-1" />
    </div>
  </div>
);

// Dashboard metrics skeleton
export const MetricsCardSkeleton: React.FC = () => (
  <div className="p-6 border border-gray-200 rounded-lg animate-pulse">
    <div className="flex items-center justify-between mb-4">
      <div>
        <Skeleton className="h-4 w-24 mb-2" />
        <Skeleton className="h-8 w-16" />
      </div>
      <Skeleton className="w-12 h-12 rounded-full" />
    </div>
    <div className="flex items-center gap-2">
      <Skeleton className="h-4 w-4" />
      <Skeleton className="h-3 w-20" />
    </div>
  </div>
);

// Table skeleton
export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({ 
  rows = 5, 
  columns = 4 
}) => (
  <div className="border border-gray-200 rounded-lg overflow-hidden">
    {/* Header */}
    <div className="bg-gray-50 p-4 border-b border-gray-200">
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-20" />
        ))}
      </div>
    </div>
    
    {/* Rows */}
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div key={rowIndex} className="p-4 border-b border-gray-200 last:border-b-0">
        <div className="grid gap-4 animate-pulse" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} className="h-4 w-full" />
          ))}
        </div>
      </div>
    ))}
  </div>
);

// Progress indicators with animations
export interface ProgressBarProps {
  value: number;
  max?: number;
  className?: string;
  showPercentage?: boolean;
  variant?: 'primary' | 'success' | 'warning' | 'error';
  animated?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  className,
  showPercentage = false,
  variant = 'primary',
  animated = true
}) => {
  const percentage = Math.min((value / max) * 100, 100);
  
  const variantClasses = {
    primary: 'bg-primary',
    success: 'bg-success',
    warning: 'bg-warning',
    error: 'bg-error'
  };

  return (
    <div className={cn('w-full', className)}>
      <div className="flex justify-between items-center mb-1">
        {showPercentage && (
          <span className="text-sm font-medium text-gray-700">
            {Math.round(percentage)}%
          </span>
        )}
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className={cn(
            'h-2 rounded-full transition-all duration-500 ease-out',
            variantClasses[variant],
            animated && 'animate-progress-bar'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

// Circular progress indicator
export interface CircularProgressProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'success' | 'warning' | 'error';
  showPercentage?: boolean;
  className?: string;
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
  value,
  max = 100,
  size = 'md',
  variant = 'primary',
  showPercentage = false,
  className
}) => {
  const percentage = Math.min((value / max) * 100, 100);
  const circumference = 2 * Math.PI * 20; // radius = 20
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16'
  };

  const variantClasses = {
    primary: 'stroke-primary',
    success: 'stroke-success',
    warning: 'stroke-warning',
    error: 'stroke-error'
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };

  return (
    <div className={cn('relative', sizeClasses[size], className)}>
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 44 44">
        {/* Background circle */}
        <circle
          cx="22"
          cy="22"
          r="20"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="text-gray-200"
        />
        {/* Progress circle */}
        <circle
          cx="22"
          cy="22"
          r="20"
          fill="none"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className={cn('transition-all duration-500 ease-out', variantClasses[variant])}
        />
      </svg>
      
      {showPercentage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn('font-medium', textSizeClasses[size])}>
            {Math.round(percentage)}%
          </span>
        </div>
      )}
    </div>
  );
};

// Pulse animation for real-time indicators
export const PulseIndicator: React.FC<{
  variant?: 'primary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}> = ({
  variant = 'primary',
  size = 'md',
  className
}) => {
  const variantClasses = {
    primary: 'bg-primary',
    success: 'bg-success',
    warning: 'bg-warning',
    error: 'bg-error'
  };

  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };

  return (
    <div className={cn('relative', className)}>
      <div className={cn(
        'rounded-full animate-ping',
        variantClasses[variant],
        sizeClasses[size]
      )} />
      <div className={cn(
        'absolute top-0 left-0 rounded-full',
        variantClasses[variant],
        sizeClasses[size]
      )} />
    </div>
  );
};

// Loading overlay for content areas
export interface LoadingOverlayProps {
  isLoading?: boolean;
  message?: string;
  variant?: 'spinner' | 'dots' | 'bars';
  className?: string;
  children?: React.ReactNode;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  isLoading = false,
  message = 'Loading...',
  variant = 'spinner',
  className,
  children
}) => {
  const renderLoader = () => {
    switch (variant) {
      case 'dots':
        return (
          <div className="flex space-x-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2 h-2 bg-primary rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.1}s` }}
              />
            ))}
          </div>
        );
      
      case 'bars':
        return (
          <div className="flex space-x-1">
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="w-1 bg-primary animate-pulse"
                style={{ 
                  height: `${20 + Math.sin(i) * 10}px`,
                  animationDelay: `${i * 0.1}s` 
                }}
              />
            ))}
          </div>
        );
      
      default:
        return <LoadingSpinner size="lg" />;
    }
  };

  if (!isLoading) return <>{children}</>;

  return (
    <div className={cn('relative', className)}>
      {children}
      <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-10">
        <div className="text-center">
          {renderLoader()}
          {message && (
            <p className="mt-2 text-sm text-gray-600">{message}</p>
          )}
        </div>
      </div>
    </div>
  );
};

// Micro-animation wrapper for state changes
export interface AnimatedStateProps {
  children: React.ReactNode;
  isVisible?: boolean;
  animation?: 'fade' | 'slide-up' | 'slide-down' | 'scale' | 'bounce';
  duration?: 'fast' | 'normal' | 'slow';
  delay?: number;
  className?: string;
}

export const AnimatedState: React.FC<AnimatedStateProps> = ({
  children,
  isVisible = true,
  animation = 'fade',
  duration = 'normal',
  delay = 0,
  className
}) => {
  const animationClasses = {
    fade: isVisible ? 'animate-fade-in' : 'animate-fade-out',
    'slide-up': isVisible ? 'animate-slide-up' : 'animate-slide-down',
    'slide-down': isVisible ? 'animate-slide-down' : 'animate-slide-up',
    scale: isVisible ? 'animate-scale-in' : 'animate-scale-out',
    bounce: isVisible ? 'animate-bounce-in' : 'animate-bounce-out'
  };

  const durationClasses = {
    fast: 'duration-150',
    normal: 'duration-300',
    slow: 'duration-500'
  };

  return (
    <div
      className={cn(
        'transition-all ease-out',
        animationClasses[animation],
        durationClasses[duration],
        className
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
};

export default {
  LoadingSpinner,
  LoadingButton,
  Skeleton,
  IntegrationCardSkeleton,
  MetricsCardSkeleton,
  TableSkeleton,
  ProgressBar,
  CircularProgress,
  PulseIndicator,
  LoadingOverlay,
  AnimatedState
};