/**
 * LineChart Component
 * ==================
 * 
 * Line chart implementation using SVG with TaxPoynt design system.
 * Supports multiple series, animations, data points, and trend analysis.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useMemo } from 'react';
import { BaseChart, BaseChartProps, ChartDataPoint, ChartSeries } from './BaseChart';
import { colors, typography, animations } from '../../design_system/tokens';

export interface LineChartProps extends Omit<BaseChartProps, 'data'> {
  data: ChartSeries[] | ChartDataPoint[];
  showPoints?: boolean;
  showArea?: boolean;
  smooth?: boolean;
  animated?: boolean;
  strokeWidth?: number;
  pointRadius?: number;
}

export const LineChart: React.FC<LineChartProps> = ({
  data,
  showPoints = true,
  showArea = false,
  smooth = true,
  animated = true,
  strokeWidth = 2,
  pointRadius = 4,
  role,
  onDataPointClick,
  ...baseProps
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<{seriesIndex: number, pointIndex: number} | null>(null);
  
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

  // Normalize data to series format
  const normalizedData: ChartSeries[] = useMemo(() => {
    if (Array.isArray(data) && data.length > 0 && 'name' in data[0]) {
      return data as ChartSeries[];
    } else if (Array.isArray(data)) {
      return [{
        name: 'Series 1',
        data: data as ChartDataPoint[],
        color: roleColor,
      }];
    }
    return [];
  }, [data, roleColor]);

  // Calculate chart dimensions and scales
  const chartMetrics = useMemo(() => {
    if (normalizedData.length === 0) return null;

    const allDataPoints = normalizedData.flatMap(series => series.data);
    const allValues = allDataPoints.map(d => d.value);
    
    const maxValue = Math.max(...allValues);
    const minValue = Math.min(...allValues, 0);
    const range = maxValue - minValue;
    
    // Chart area dimensions
    const chartWidth = 400;
    const chartHeight = 250;
    const padding = { top: 20, right: 20, bottom: 40, left: 60 };
    
    const plotWidth = chartWidth - padding.left - padding.right;
    const plotHeight = chartHeight - padding.top - padding.bottom;
    
    // X-axis scale (assuming equal spacing)
    const maxPoints = Math.max(...normalizedData.map(series => series.data.length));
    
    return {
      maxValue,
      minValue,
      range,
      chartWidth,
      chartHeight,
      padding,
      plotWidth,
      plotHeight,
      maxPoints,
    };
  }, [normalizedData]);

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
    maxPoints,
  } = chartMetrics;

  // Scale functions
  const scaleY = (value: number) => {
    if (range === 0) return plotHeight / 2;
    return plotHeight - ((value - minValue) / range) * plotHeight;
  };

  const scaleX = (index: number, totalPoints: number) => {
    if (totalPoints <= 1) return plotWidth / 2;
    return (index / (totalPoints - 1)) * plotWidth;
  };

  // Generate path for smooth curves
  const generateSmoothPath = (points: {x: number, y: number}[]) => {
    if (points.length < 2) return '';
    
    if (!smooth || points.length === 2) {
      // Straight lines
      const pathCommands = points.map((point, index) => 
        index === 0 ? `M ${point.x} ${point.y}` : `L ${point.x} ${point.y}`
      );
      return pathCommands.join(' ');
    }
    
    // Smooth curve using quadratic Bezier curves
    const pathCommands = [`M ${points[0].x} ${points[0].y}`];
    
    for (let i = 1; i < points.length; i++) {
      const prevPoint = points[i - 1];
      const currentPoint = points[i];
      const nextPoint = points[i + 1];
      
      if (nextPoint) {
        // Calculate control point
        const cpX = (prevPoint.x + currentPoint.x) / 2;
        const cpY = currentPoint.y;
        pathCommands.push(`Q ${cpX} ${cpY} ${(currentPoint.x + nextPoint.x) / 2} ${currentPoint.y}`);
      } else {
        // Last point
        pathCommands.push(`L ${currentPoint.x} ${currentPoint.y}`);
      }
    }
    
    return pathCommands.join(' ');
  };

  // Generate area path for filled areas
  const generateAreaPath = (points: {x: number, y: number}[]) => {
    if (points.length === 0) return '';
    
    const linePath = generateSmoothPath(points);
    const baseY = padding.top + scaleY(Math.max(0, minValue));
    
    return `${linePath} L ${points[points.length - 1].x} ${baseY} L ${points[0].x} ${baseY} Z`;
  };

  // Grid lines
  const gridLines = [];
  if (baseProps.showGrid !== false) {
    const gridSteps = 5;
    
    // Horizontal grid lines
    for (let i = 0; i <= gridSteps; i++) {
      const value = minValue + (range * i / gridSteps);
      const y = padding.top + scaleY(value);
      
      gridLines.push(
        <g key={`h-${i}`}>
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
    }
    
    // Vertical grid lines (using first series for x-axis labels)
    if (normalizedData[0]?.data) {
      normalizedData[0].data.forEach((dataPoint, index) => {
        const x = padding.left + scaleX(index, normalizedData[0].data.length);
        
        gridLines.push(
          <g key={`v-${index}`}>
            <line
              x1={x}
              y1={padding.top}
              x2={x}
              y2={padding.top + plotHeight}
              stroke={colors.neutral[200]}
              strokeWidth={1}
              strokeDasharray="2,2"
            />
            <text
              x={x}
              y={chartHeight - 10}
              textAnchor="middle"
              fontSize={typography.sizes.xs}
              fill={colors.neutral[500]}
              fontFamily={typography.fonts.sans.join(', ')}
            >
              {dataPoint.label}
            </text>
          </g>
        );
      });
    }
  }

  // Generate series paths and points
  const seriesElements = normalizedData.map((series, seriesIndex) => {
    const seriesColor = series.color || chartColors[seriesIndex % chartColors.length];
    
    // Calculate points
    const points = series.data.map((dataPoint, pointIndex) => ({
      x: padding.left + scaleX(pointIndex, series.data.length),
      y: padding.top + scaleY(dataPoint.value),
      dataPoint,
      pointIndex,
    }));
    
    const linePath = generateSmoothPath(points.map(p => ({x: p.x, y: p.y})));
    const areaPath = showArea ? generateAreaPath(points.map(p => ({x: p.x, y: p.y}))) : '';
    
    return (
      <g key={seriesIndex}>
        {/* Area fill */}
        {showArea && areaPath && (
          <path
            d={areaPath}
            fill={`${seriesColor}20`}
            stroke="none"
            style={{
              animation: animated ? `fadeIn 0.8s ease-out ${seriesIndex * 0.2}s both` : 'none',
            }}
          />
        )}
        
        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke={seriesColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            animation: animated ? `drawLine 1s ease-out ${seriesIndex * 0.2}s both` : 'none',
            strokeDasharray: animated ? '1000' : 'none',
            strokeDashoffset: animated ? '1000' : '0',
          }}
        />
        
        {/* Data points */}
        {showPoints && points.map(({ x, y, dataPoint, pointIndex }) => {
          const isHovered = hoveredPoint?.seriesIndex === seriesIndex && hoveredPoint?.pointIndex === pointIndex;
          
          return (
            <circle
              key={pointIndex}
              cx={x}
              cy={y}
              r={isHovered ? pointRadius + 2 : pointRadius}
              fill={seriesColor}
              stroke="#FFFFFF"
              strokeWidth={2}
              style={{
                cursor: onDataPointClick ? 'pointer' : 'default',
                transition: animations.transition.fast,
                filter: isHovered ? `drop-shadow(0 2px 8px ${seriesColor}50)` : 'none',
                animation: animated ? `popIn 0.4s ease-out ${(seriesIndex * 0.1) + (pointIndex * 0.05)}s both` : 'none',
              }}
              onMouseEnter={() => setHoveredPoint({seriesIndex, pointIndex})}
              onMouseLeave={() => setHoveredPoint(null)}
              onClick={() => onDataPointClick?.(dataPoint, seriesIndex)}
            />
          );
        })}
      </g>
    );
  });

  return (
    <BaseChart
      data={normalizedData}
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
        
        {/* Series lines and points */}
        <g>{seriesElements}</g>
        
        {/* Hover tooltip */}
        {hoveredPoint && (
          <g>
            {(() => {
              const series = normalizedData[hoveredPoint.seriesIndex];
              const dataPoint = series.data[hoveredPoint.pointIndex];
              const x = padding.left + scaleX(hoveredPoint.pointIndex, series.data.length);
              const y = padding.top + scaleY(dataPoint.value);
              
              return (
                <>
                  <rect
                    x={x - 40}
                    y={y - 35}
                    width={80}
                    height={25}
                    fill={colors.neutral[900]}
                    rx={4}
                    ry={4}
                    opacity={0.9}
                  />
                  <text
                    x={x}
                    y={y - 20}
                    textAnchor="middle"
                    fontSize={typography.sizes.sm}
                    fill="#FFFFFF"
                    fontFamily={typography.fonts.sans.join(', ')}
                  >
                    {dataPoint.value.toLocaleString()}
                  </text>
                </>
              );
            })()}
          </g>
        )}
      </svg>
      
      {/* Animation keyframes */}
      {animated && (
        <style jsx>{`
          @keyframes drawLine {
            to {
              stroke-dashoffset: 0;
            }
          }
          
          @keyframes fadeIn {
            from {
              opacity: 0;
            }
            to {
              opacity: 1;
            }
          }
          
          @keyframes popIn {
            from {
              transform: scale(0);
              opacity: 0;
            }
            to {
              transform: scale(1);
              opacity: 1;
            }
          }
        `}</style>
      )}
    </BaseChart>
  );
};

export default LineChart;