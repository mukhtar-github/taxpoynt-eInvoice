/**
 * Enhanced Metric Card Component with Animated Counters
 * 
 * Features:
 * - Animated number counting from 0 to target value
 * - Mobile-first responsive design
 * - Micro-interactions and hover effects
 * - Loading states with shimmer effects
 * - Trend indicators with smooth animations
 * - Touch-friendly interactions
 */

import React, { useState, useEffect, useRef } from 'react';
import { TrendingUp, TrendingDown, Minus, Eye, EyeOff } from 'lucide-react';
import { Card } from '../ui/Card';
import { cn } from '../../utils/cn';

interface MetricCardProps {
  title: string;
  value: number;
  previousValue?: number;
  prefix?: string; // e.g., "₦", "$", "#"
  suffix?: string; // e.g., "%", "K", "M"
  icon?: React.ReactNode;
  loading?: boolean;
  className?: string;
  onClick?: () => void;
  animationDuration?: number; // in milliseconds
  countUp?: boolean; // Enable count-up animation
  precision?: number; // Decimal places for display
  formatValue?: (value: number) => string; // Custom formatter
}

// Custom hook for animated counter
const useAnimatedCounter = (
  endValue: number,
  duration: number = 2000,
  precision: number = 0,
  enabled: boolean = true
) => {
  const [displayValue, setDisplayValue] = useState(0);
  const frameRef = useRef<number>();
  const startTimeRef = useRef<number>();

  useEffect(() => {
    if (!enabled) {
      setDisplayValue(endValue);
      return;
    }

    const animateValue = (timestamp: number) => {
      if (!startTimeRef.current) {
        startTimeRef.current = timestamp;
      }

      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function for smooth animation
      const easeOutCubic = 1 - Math.pow(1 - progress, 3);
      const currentValue = easeOutCubic * endValue;

      setDisplayValue(Number(currentValue.toFixed(precision)));

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animateValue);
      }
    };

    frameRef.current = requestAnimationFrame(animateValue);

    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
      startTimeRef.current = undefined;
    };
  }, [endValue, duration, precision, enabled]);

  return displayValue;
};

// Format large numbers (e.g., 1000 → 1K, 1000000 → 1M)
const formatLargeNumber = (value: number): string => {
  if (value >= 1000000) {
    return (value / 1000000).toFixed(1) + 'M';
  }
  if (value >= 1000) {
    return (value / 1000).toFixed(1) + 'K';
  }
  return value.toString();
};

// Calculate percentage change between current and previous values
const calculateChange = (current: number, previous: number): {
  percentage: number;
  type: 'increase' | 'decrease' | 'neutral';
} => {
  if (previous === 0) return { percentage: 0, type: 'neutral' };
  
  const percentage = ((current - previous) / previous) * 100;
  
  return {
    percentage: Math.abs(percentage),
    type: percentage > 0 ? 'increase' : percentage < 0 ? 'decrease' : 'neutral'
  };
};

export const EnhancedMetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  previousValue,
  prefix = '',
  suffix = '',
  icon,
  loading = false,
  className = '',
  onClick,
  animationDuration = 2000,
  countUp = true,
  precision = 0,
  formatValue
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  // Animated counter value
  const animatedValue = useAnimatedCounter(
    value,
    animationDuration,
    precision,
    countUp && isVisible
  );

  // Calculate trend information
  const trend = previousValue !== undefined ? calculateChange(value, previousValue) : null;

  // Intersection Observer to trigger animation when card becomes visible
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect(); // Only animate once
        }
      },
      { threshold: 0.3 }
    );

    if (cardRef.current) {
      observer.observe(cardRef.current);
    }

    return () => observer.disconnect();
  }, []);

  // Format the display value
  const displayValue = formatValue 
    ? formatValue(countUp ? animatedValue : value)
    : formatLargeNumber(countUp ? animatedValue : value);

  // Trend configuration
  const trendConfig = trend ? {
    increase: {
      icon: <TrendingUp className="w-3 h-3" />,
      color: 'text-success',
      bgColor: 'bg-success/10'
    },
    decrease: {
      icon: <TrendingDown className="w-3 h-3" />,
      color: 'text-error',
      bgColor: 'bg-error/10'
    },
    neutral: {
      icon: <Minus className="w-3 h-3" />,
      color: 'text-text-secondary',
      bgColor: 'bg-gray-100'
    }
  }[trend.type] : null;

  if (loading) {
    return (
      <Card 
        variant="elevated" 
        className={cn("animate-pulse-subtle", className)}
      >
        <div className="space-y-3">
          <div className="flex justify-between items-start">
            <div className="space-y-2 flex-1">
              <div className="h-3 bg-gray-200 rounded animate-pulse w-2/3" />
              <div className="h-8 bg-gray-200 rounded animate-pulse w-1/2" />
            </div>
            <div className="w-10 h-10 bg-gray-200 rounded-lg animate-pulse" />
          </div>
          <div className="h-4 bg-gray-200 rounded animate-pulse w-1/3" />
        </div>
      </Card>
    );
  }

  return (
    <Card
      ref={cardRef}
      variant={onClick ? "interactive" : "elevated"}
      className={cn(
        "group transition-all duration-300",
        "hover:shadow-lg hover:-translate-y-1",
        className
      )}
      onClick={onClick}
    >
      {/* Header with title and icon */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="text-sm xs:text-base font-medium text-text-secondary mb-2 group-hover:text-text-primary transition-colors">
            {title}
          </h3>
          
          {/* Main value with prefix/suffix */}
          <div className="flex items-baseline gap-1">
            {prefix && (
              <span className="text-lg xs:text-xl font-semibold text-text-secondary">
                {prefix}
              </span>
            )}
            <span className="text-2xl xs:text-3xl font-bold text-text-primary tabular-nums">
              {displayValue}
            </span>
            {suffix && (
              <span className="text-lg xs:text-xl font-semibold text-text-secondary">
                {suffix}
              </span>
            )}
          </div>
        </div>

        {/* Icon container with micro-animation */}
        {icon && (
          <div className="w-10 h-10 xs:w-12 xs:h-12 bg-primary/10 rounded-lg flex items-center justify-center group-hover:bg-primary/20 transition-colors duration-300 group-hover:scale-110">
            <div className="text-primary w-5 h-5 xs:w-6 xs:h-6">
              {icon}
            </div>
          </div>
        )}
      </div>

      {/* Trend indicator and details */}
      <div className="flex items-center justify-between">
        {/* Trend information */}
        {trend && trendConfig && (
          <div className={cn(
            "flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium transition-all duration-300",
            trendConfig.bgColor,
            trendConfig.color
          )}>
            {trendConfig.icon}
            <span>
              {trend.percentage.toFixed(1)}%
            </span>
            <span className="hidden xs:inline text-text-secondary">
              vs last period
            </span>
          </div>
        )}

        {/* Details toggle (mobile-friendly) */}
        {previousValue !== undefined && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowDetails(!showDetails);
            }}
            className="ml-auto p-1 rounded-full hover:bg-gray-100 transition-colors"
            aria-label="Toggle details"
          >
            {showDetails ? (
              <EyeOff className="w-4 h-4 text-text-secondary" />
            ) : (
              <Eye className="w-4 h-4 text-text-secondary" />
            )}
          </button>
        )}
      </div>

      {/* Expanded details */}
      {showDetails && previousValue !== undefined && (
        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-text-secondary space-y-1 animate-fade-in">
          <div className="flex justify-between">
            <span>Current:</span>
            <span className="font-medium">{prefix}{formatLargeNumber(value)}{suffix}</span>
          </div>
          <div className="flex justify-between">
            <span>Previous:</span>
            <span className="font-medium">{prefix}{formatLargeNumber(previousValue)}{suffix}</span>
          </div>
          <div className="flex justify-between">
            <span>Difference:</span>
            <span className={cn(
              "font-medium",
              trend?.type === 'increase' ? 'text-success' :
              trend?.type === 'decrease' ? 'text-error' : 'text-text-secondary'
            )}>
              {trend?.type === 'increase' ? '+' : trend?.type === 'decrease' ? '-' : ''}
              {formatLargeNumber(Math.abs(value - previousValue))}
            </span>
          </div>
        </div>
      )}
    </Card>
  );
};

// Grid container for metric cards with responsive layout
export const MetricCardGrid: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={cn(
    "grid grid-cols-1 xs:grid-cols-2 lg:grid-cols-4 gap-4 xs:gap-6",
    className
  )}>
    {children}
  </div>
);

export default EnhancedMetricCard;