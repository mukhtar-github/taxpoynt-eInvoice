/**
 * Interactive Tooltips for Chart Components
 * Week 7 Implementation: Enhanced tooltips with interactive data points
 */

import React, { useState, useRef, useEffect } from 'react';
import { TrendingUp, TrendingDown, Info, Calendar } from 'lucide-react';

export interface TooltipData {
  label: string;
  value: string | number;
  change?: number;
  color?: string;
  metadata?: {
    trend?: 'up' | 'down' | 'stable';
    percentage?: number;
    category?: string;
    timestamp?: string;
  };
}

interface InteractiveTooltipProps {
  data: TooltipData;
  position: { x: number; y: number };
  visible: boolean;
  animate?: boolean;
}

export const InteractiveTooltip: React.FC<InteractiveTooltipProps> = ({
  data,
  position,
  visible,
  animate = true
}) => {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [adjustedPosition, setAdjustedPosition] = useState(position);

  useEffect(() => {
    if (tooltipRef.current && visible) {
      const tooltip = tooltipRef.current;
      const rect = tooltip.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      let { x, y } = position;

      // Adjust horizontal position if tooltip goes off-screen
      if (x + rect.width > viewportWidth - 20) {
        x = viewportWidth - rect.width - 20;
      }
      if (x < 20) {
        x = 20;
      }

      // Adjust vertical position if tooltip goes off-screen
      if (y + rect.height > viewportHeight - 20) {
        y = y - rect.height - 20;
      }
      if (y < 20) {
        y = 20;
      }

      setAdjustedPosition({ x, y });
    }
  }, [position, visible]);

  if (!visible) return null;

  const formatValue = (value: string | number): string => {
    if (typeof value === 'number') {
      if (value > 1000000) {
        return `${(value / 1000000).toFixed(1)}M`;
      }
      if (value > 1000) {
        return `${(value / 1000).toFixed(1)}K`;
      }
      return value.toLocaleString();
    }
    return value;
  };

  return (
    <div
      ref={tooltipRef}
      className={`
        fixed z-50 bg-gray-900 text-white rounded-lg shadow-xl border border-gray-700
        px-4 py-3 max-w-xs pointer-events-none
        ${animate ? 'transition-all duration-200 ease-out' : ''}
        ${visible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}
      `}
      style={{
        left: adjustedPosition.x,
        top: adjustedPosition.y,
        transform: 'translate(-50%, -100%)'
      }}
    >
      {/* Arrow */}
      <div className="absolute top-full left-1/2 transform -translate-x-1/2">
        <div className="border-l-8 border-r-8 border-t-8 border-transparent border-t-gray-900"></div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-semibold text-sm">{data.label}</h4>
        {data.metadata?.trend && (
          <div className="flex items-center">
            {data.metadata.trend === 'up' ? (
              <TrendingUp className="w-4 h-4 text-green-400" />
            ) : data.metadata.trend === 'down' ? (
              <TrendingDown className="w-4 h-4 text-red-400" />
            ) : (
              <div className="w-4 h-4 bg-gray-400 rounded-full"></div>
            )}
          </div>
        )}
      </div>

      {/* Value */}
      <div className="mb-2">
        <span className="text-xl font-bold" style={{ color: data.color || '#3b82f6' }}>
          {formatValue(data.value)}
        </span>
        {data.metadata?.percentage && (
          <span className="text-sm text-gray-300 ml-2">
            ({data.metadata.percentage}%)
          </span>
        )}
      </div>

      {/* Change indicator */}
      {data.change !== undefined && (
        <div className="flex items-center text-sm">
          {data.change > 0 ? (
            <TrendingUp className="w-3 h-3 text-green-400 mr-1" />
          ) : (
            <TrendingDown className="w-3 h-3 text-red-400 mr-1" />
          )}
          <span className={data.change > 0 ? 'text-green-400' : 'text-red-400'}>
            {data.change > 0 ? '+' : ''}{data.change}%
          </span>
          <span className="text-gray-400 ml-1">vs previous</span>
        </div>
      )}

      {/* Metadata */}
      {data.metadata && (
        <div className="mt-2 pt-2 border-t border-gray-700">
          {data.metadata.category && (
            <div className="flex items-center text-xs text-gray-300 mb-1">
              <Info className="w-3 h-3 mr-1" />
              <span>Category: {data.metadata.category}</span>
            </div>
          )}
          {data.metadata.timestamp && (
            <div className="flex items-center text-xs text-gray-300">
              <Calendar className="w-3 h-3 mr-1" />
              <span>{data.metadata.timestamp}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Custom hook for managing tooltip state
export const useInteractiveTooltip = () => {
  const [tooltip, setTooltip] = useState<{
    data: TooltipData | null;
    position: { x: number; y: number };
    visible: boolean;
  }>({
    data: null,
    position: { x: 0, y: 0 },
    visible: false
  });

  const showTooltip = (data: TooltipData, event: React.MouseEvent) => {
    setTooltip({
      data,
      position: { x: event.clientX, y: event.clientY },
      visible: true
    });
  };

  const hideTooltip = () => {
    setTooltip(prev => ({ ...prev, visible: false }));
  };

  const updatePosition = (event: React.MouseEvent) => {
    if (tooltip.visible) {
      setTooltip(prev => ({
        ...prev,
        position: { x: event.clientX, y: event.clientY }
      }));
    }
  };

  return {
    tooltip,
    showTooltip,
    hideTooltip,
    updatePosition
  };
};

// Enhanced Chart wrapper with interactive tooltips
interface ChartWithTooltipProps {
  children: React.ReactNode;
  tooltipData?: TooltipData[];
  className?: string;
}

export const ChartWithTooltip: React.FC<ChartWithTooltipProps> = ({
  children,
  tooltipData = [],
  className = ''
}) => {
  const { tooltip, showTooltip, hideTooltip, updatePosition } = useInteractiveTooltip();

  return (
    <div 
      className={`relative ${className}`}
      onMouseLeave={hideTooltip}
      onMouseMove={updatePosition}
    >
      {children}
      
      {tooltip.data && (
        <InteractiveTooltip
          data={tooltip.data}
          position={tooltip.position}
          visible={tooltip.visible}
          animate={true}
        />
      )}
    </div>
  );
};

export default {
  InteractiveTooltip,
  useInteractiveTooltip,
  ChartWithTooltip
};