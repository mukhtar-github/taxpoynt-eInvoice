/**
 * BarChart Component
 * =================
 * 
 * Simple bar chart implementation using SVG with TaxPoynt design system.
 * Supports horizontal and vertical bars, animations, and interactive features.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useMemo } from 'react';
import { BaseChart, BaseChartProps, ChartDataPoint } from './BaseChart';
import { colors, typography, spacing, animations } from '../../design_system/tokens';

export interface BarChartProps extends Omit<BaseChartProps, 'data'> {
  data: ChartDataPoint[];
  orientation?: 'vertical' | 'horizontal';
  showValues?: boolean;
  animated?: boolean;
  barRadius?: number;
  maxBarWidth?: number;
  spacing?: number;
}

export const BarChart: React.FC<BarChartProps> = ({
  data,
  orientation = 'vertical',
  showValues = true,
  animated = true,
  barRadius = 4,
  maxBarWidth = 40,
  spacing: barSpacing = 8,
  role,
  onDataPointClick,
  ...baseProps
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  
  const roleColor = role ? colors.roles[role] : colors.brand.primary;
  const chartColors = [
    roleColor,
    colors.semantic.success,
    colors.semantic.warning,
    colors.semantic.info,
    colors.nigeria.green,
    colors.neutral[600],
    colors.semantic.error,
  ];

  // Calculate chart dimensions and scales
  const chartMetrics = useMemo(() => {
    if (!data || data.length === 0) return null;

    const maxValue = Math.max(...data.map(d => d.value));
    const minValue = Math.min(...data.map(d => d.value), 0);
    const range = maxValue - minValue;
    
    // Chart area dimensions (leaving space for labels and padding)
    const chartWidth = orientation === 'vertical' ? 400 : 300;
    const chartHeight = orientation === 'vertical' ? 200 : 300;
    const padding = { top: 20, right: 20, bottom: 40, left: 60 };
    
    const plotWidth = chartWidth - padding.left - padding.right;
    const plotHeight = chartHeight - padding.top - padding.bottom;
    
    // Calculate bar dimensions
    const barCount = data.length;
    const availableSpace = orientation === 'vertical' ? plotWidth : plotHeight;
    const barWidth = Math.min(
      maxBarWidth,
      (availableSpace - (barSpacing * (barCount - 1))) / barCount
    );
    
    return {
      maxValue,
      minValue,
      range,
      chartWidth,
      chartHeight,
      padding,
      plotWidth,
      plotHeight,
      barWidth,
      barSpacing,
    };
  }, [data, orientation, maxBarWidth, barSpacing]);

  if (!chartMetrics) return null;

  const {
    maxValue,
    minValue,
    range,
    chartWidth,
    chartHeight,
    padding,
    plotWidth,
    plotHeight,
    barWidth,
  } = chartMetrics;

  // Scale functions
  const scaleValue = (value: number) => {
    if (range === 0) return 0;
    return ((value - minValue) / range) * (orientation === 'vertical' ? plotHeight : plotWidth);
  };

  const scalePosition = (index: number) => {
    const totalSpacing = (data.length - 1) * barSpacing;
    const totalBarWidth = data.length * barWidth;
    const availableSpace = orientation === 'vertical' ? plotWidth : plotHeight;
    const startOffset = (availableSpace - totalBarWidth - totalSpacing) / 2;
    
    return startOffset + (index * (barWidth + barSpacing));
  };

  // Generate bars
  const bars = data.map((dataPoint, index) => {
    const value = dataPoint.value;
    const scaledValue = scaleValue(value);
    const position = scalePosition(index);
    const color = dataPoint.color || chartColors[index % chartColors.length];
    const isHovered = hoveredIndex === index;
    
    if (orientation === 'vertical') {
      const barHeight = scaledValue;
      const x = padding.left + position;
      const y = padding.top + (plotHeight - barHeight);
      
      return (
        <g key={index}>
          {/* Bar */}
          <rect
            x={x}
            y={y}
            width={barWidth}
            height={barHeight}
            fill={color}
            rx={barRadius}
            ry={barRadius}
            style={{
              cursor: onDataPointClick ? 'pointer' : 'default',
              opacity: isHovered ? 0.8 : 1,
              transition: animated ? animations.transition.base : 'none',
              filter: isHovered ? `drop-shadow(0 2px 4px ${color}50)` : 'none',
            }}
            onMouseEnter={() => setHoveredIndex(index)}
            onMouseLeave={() => setHoveredIndex(null)}
            onClick={() => onDataPointClick?.(dataPoint)}
          />
          
          {/* Value label */}
          {showValues && (
            <text
              x={x + barWidth / 2}
              y={y - 5}
              textAnchor="middle"
              fontSize={typography.sizes.sm}
              fill={colors.neutral[700]}
              fontFamily={typography.fonts.sans.join(', ')}
            >
              {value.toLocaleString()}
            </text>
          )}
          
          {/* X-axis label */}
          <text
            x={x + barWidth / 2}
            y={chartHeight - 10}
            textAnchor="middle"
            fontSize={typography.sizes.sm}
            fill={colors.neutral[600]}
            fontFamily={typography.fonts.sans.join(', ')}
          >
            {dataPoint.label}
          </text>
        </g>
      );
    } else {
      // Horizontal bars
      const barLength = scaledValue;
      const x = padding.left;
      const y = padding.top + position;
      
      return (
        <g key={index}>
          {/* Bar */}
          <rect
            x={x}
            y={y}
            width={barLength}
            height={barWidth}
            fill={color}
            rx={barRadius}
            ry={barRadius}
            style={{
              cursor: onDataPointClick ? 'pointer' : 'default',
              opacity: isHovered ? 0.8 : 1,
              transition: animated ? animations.transition.base : 'none',
              filter: isHovered ? `drop-shadow(0 2px 4px ${color}50)` : 'none',
            }}
            onMouseEnter={() => setHoveredIndex(index)}
            onMouseLeave={() => setHoveredIndex(null)}
            onClick={() => onDataPointClick?.(dataPoint)}
          />
          
          {/* Value label */}
          {showValues && (
            <text
              x={x + barLength + 5}
              y={y + barWidth / 2 + 4}
              fontSize={typography.sizes.sm}
              fill={colors.neutral[700]}
              fontFamily={typography.fonts.sans.join(', ')}
            >
              {value.toLocaleString()}
            </text>
          )}
          
          {/* Y-axis label */}
          <text
            x={padding.left - 10}
            y={y + barWidth / 2 + 4}
            textAnchor="end"
            fontSize={typography.sizes.sm}
            fill={colors.neutral[600]}
            fontFamily={typography.fonts.sans.join(', ')}
          >
            {dataPoint.label}
          </text>
        </g>
      );
    }
  });

  // Grid lines
  const gridLines = [];
  if (baseProps.showGrid !== false) {
    const gridSteps = 5;
    for (let i = 0; i <= gridSteps; i++) {
      const value = minValue + (range * i / gridSteps);
      const scaledValue = scaleValue(value);
      
      if (orientation === 'vertical') {
        const y = padding.top + (plotHeight - scaledValue);
        gridLines.push(
          <g key={i}>
            <line
              x1={padding.left}
              y1={y}
              x2={padding.left + plotWidth}
              y2={y}
              stroke={colors.neutral[200]}
              strokeWidth={1}
              strokeDasharray={i === 0 ? '0' : '2,2'}
            />
            <text
              x={padding.left - 10}
              y={y + 4}
              textAnchor="end"
              fontSize={typography.sizes.xs}
              fill={colors.neutral[500]}
              fontFamily={typography.fonts.sans.join(', ')}
            >
              {value.toLocaleString()}
            </text>
          </g>
        );
      } else {
        const x = padding.left + scaledValue;
        gridLines.push(
          <g key={i}>
            <line
              x1={x}
              y1={padding.top}
              x2={x}
              y2={padding.top + plotHeight}
              stroke={colors.neutral[200]}
              strokeWidth={1}
              strokeDasharray={i === 0 ? '0' : '2,2'}
            />
            <text
              x={x}
              y={chartHeight - 25}
              textAnchor="middle"
              fontSize={typography.sizes.xs}
              fill={colors.neutral[500]}
              fontFamily={typography.fonts.sans.join(', ')}
            >
              {value.toLocaleString()}
            </text>
          </g>
        );
      }
    }
  }

  return (
    <BaseChart
      data={data}
      role={role}
      onDataPointClick={onDataPointClick}
      width={chartWidth}
      height={chartHeight}
      {...baseProps}
    >
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        style={{ overflow: 'visible' }}
      >
        {/* Grid lines */}
        <g>{gridLines}</g>
        
        {/* Bars with animation */}
        <g>
          {animated ? (
            <g>
              {bars.map((bar, index) => (
                <g key={index}>
                  {React.cloneElement(bar, {
                    style: {
                      ...bar.props.style,
                      animation: `slideIn${orientation === 'vertical' ? 'Up' : 'Right'} 0.6s ease-out ${index * 0.1}s both`,
                    }
                  })}
                </g>
              ))}
            </g>
          ) : (
            bars
          )}
        </g>
      </svg>
      
      {/* Animation keyframes */}
      {animated && (
        <style jsx>{`
          @keyframes slideInUp {
            from {
              transform: translateY(20px);
              opacity: 0;
            }
            to {
              transform: translateY(0);
              opacity: 1;
            }
          }
          
          @keyframes slideInRight {
            from {
              transform: translateX(-20px);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}</style>
      )}
    </BaseChart>
  );
};

export default BarChart;