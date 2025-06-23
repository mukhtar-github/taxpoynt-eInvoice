/**
 * Responsive Chart Components for Mobile/Desktop
 * Week 7 Implementation: Mobile-first responsive design for charts
 */

import React, { useState, useEffect, useRef } from 'react';
import { MoreHorizontal, Maximize2, Download, Filter, RefreshCw } from 'lucide-react';
import { ChartWithTooltip } from './InteractiveTooltips';
import { Button } from './Button';

interface ResponsiveChartWrapperProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  minHeight?: number;
  maxHeight?: number;
  actions?: React.ReactNode;
  fullscreen?: boolean;
  onFullscreenToggle?: () => void;
}

export const ResponsiveChartWrapper: React.FC<ResponsiveChartWrapperProps> = ({
  children,
  title,
  subtitle,
  className = '',
  minHeight = 300,
  maxHeight = 600,
  actions,
  fullscreen = false,
  onFullscreenToggle
}) => {
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const [isMobile, setIsMobile] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        setContainerSize({ width: clientWidth, height: clientHeight });
        setIsMobile(clientWidth < 768);
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  const dynamicHeight = Math.max(
    minHeight,
    Math.min(maxHeight, containerSize.width * 0.6)
  );

  return (
    <div 
      className={`
        bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden
        ${fullscreen ? 'fixed inset-0 z-50 m-4' : ''}
        ${className}
      `}
    >
      {/* Header */}
      {(title || subtitle || actions) && (
        <div className="px-4 py-3 border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-start justify-between">
            <div className="min-w-0 flex-1">
              {title && (
                <h3 className="text-base font-semibold text-gray-900 truncate">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                  {subtitle}
                </p>
              )}
            </div>
            
            {/* Actions */}
            <div className="flex items-center gap-2 ml-4">
              {actions}
              {onFullscreenToggle && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onFullscreenToggle}
                  className="p-1"
                >
                  <Maximize2 className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Chart Content */}
      <div 
        ref={containerRef}
        className="p-4"
        style={{ 
          height: fullscreen ? 'calc(100vh - 120px)' : `${dynamicHeight}px`,
          minHeight: `${minHeight}px`
        }}
      >
        <ChartWithTooltip className="w-full h-full">
          {children}
        </ChartWithTooltip>
      </div>

      {/* Mobile-specific controls */}
      {isMobile && (
        <div className="px-4 py-3 border-t border-gray-100 bg-gray-50/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm">
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

// Grid layout for multiple charts with responsive breakpoints
interface ChartGridProps {
  children: React.ReactNode;
  columns?: 1 | 2 | 3 | 4;
  gap?: number;
  className?: string;
}

export const ChartGrid: React.FC<ChartGridProps> = ({
  children,
  columns = 2,
  gap = 6,
  className = ''
}) => {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 lg:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 xl:grid-cols-4'
  };

  const gapClass = `gap-${gap}`;

  return (
    <div className={`grid ${gridCols[columns]} ${gapClass} ${className}`}>
      {children}
    </div>
  );
};

// Adaptive chart sizing based on screen size
export const useAdaptiveChartSize = () => {
  const [size, setSize] = useState({
    width: 0,
    height: 0,
    isMobile: false,
    isTablet: false,
    isDesktop: false
  });

  useEffect(() => {
    const updateSize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;

      setSize({
        width,
        height,
        isMobile: width < 768,
        isTablet: width >= 768 && width < 1024,
        isDesktop: width >= 1024
      });
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  return size;
};

// Chart size configurations for different screen sizes
export const getResponsiveChartConfig = (screenSize: ReturnType<typeof useAdaptiveChartSize>) => {
  if (screenSize.isMobile) {
    return {
      height: 250,
      fontSize: 10,
      padding: { top: 10, right: 10, bottom: 20, left: 20 },
      legend: { position: 'bottom' as const, fontSize: 10 },
      tooltip: { compact: true }
    };
  }

  if (screenSize.isTablet) {
    return {
      height: 300,
      fontSize: 11,
      padding: { top: 15, right: 15, bottom: 25, left: 25 },
      legend: { position: 'top' as const, fontSize: 11 },
      tooltip: { compact: false }
    };
  }

  return {
    height: 400,
    fontSize: 12,
    padding: { top: 20, right: 30, bottom: 30, left: 40 },
    legend: { position: 'top' as const, fontSize: 12 },
    tooltip: { compact: false }
  };
};

// Enhanced metrics card for mobile
interface MobileMetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  icon?: React.ReactNode;
  compact?: boolean;
}

export const MobileMetricCard: React.FC<MobileMetricCardProps> = ({
  title,
  value,
  change,
  trend,
  icon,
  compact = false
}) => {
  const getTrendColor = (trend?: string) => {
    switch (trend) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (compact) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-3">
        <div className="flex items-center justify-between">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-gray-600 truncate">{title}</p>
            <p className="text-lg font-bold text-gray-900">{value}</p>
          </div>
          {icon && (
            <div className="ml-2 text-gray-400">
              {icon}
            </div>
          )}
        </div>
        {change !== undefined && (
          <div className="mt-1">
            <span className={`text-xs font-medium ${getTrendColor(trend)}`}>
              {change > 0 ? '+' : ''}{change}%
            </span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium text-gray-600">{title}</p>
        {icon && (
          <div className="text-gray-400">
            {icon}
          </div>
        )}
      </div>
      <p className="text-2xl font-bold text-gray-900 mb-1">{value}</p>
      {change !== undefined && (
        <p className={`text-sm font-medium ${getTrendColor(trend)}`}>
          {change > 0 ? '+' : ''}{change}% vs last period
        </p>
      )}
    </div>
  );
};

export default {
  ResponsiveChartWrapper,
  ChartGrid,
  useAdaptiveChartSize,
  getResponsiveChartConfig,
  MobileMetricCard
};